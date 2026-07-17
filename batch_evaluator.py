#!/usr/bin/env python3
"""
AI 批阅项目评测工具

该脚本用于 AI 批改准确率的评测流程，包含两个步骤：
1. 批量提交任务：读取 Excel/CSV 文件中的 image_url 列，批量提交到任务接口，获取 taskid 并保存到新文件
2. 获取任务结果：根据评测策略获取任务结果并进行准确率评测

使用方法：
    # 第一步：批量提交任务
    python batch_evaluator.py --step 1 --input-file input.xlsx --output-file tasks.xlsx --api-url http://your-api/submit
    
    # 第二步：获取任务结果并评测
    python batch_evaluator.py --step 2 --input-file tasks.xlsx --result-file results.xlsx --strategy exact_match
"""

import os
import sys
import time
import argparse
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

# 将父目录添加到路径以便导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from core.api_client import APIClient
from core.file_handler import FileHandler
from strategies.registry import StrategyRegistry
from strategies.base import EvaluationStrategy
from core.evaluation_engine import EvaluationResult


class BatchEvaluator:
    """批量评测器，负责任务提交和结果获取。"""
    
    def __init__(self, api_timeout: int = 30):
        """
        初始化批量评测器。
        
        参数:
            api_timeout: API 请求超时时间（秒）
        """
        self.api_client = APIClient(timeout=api_timeout)
        self.progress_callback: Optional[Callable[[int, int], None]] = None
    
    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """设置进度更新的回调函数。"""
        self.progress_callback = callback
    
    def submit_tasks(
        self,
        input_file: str,
        output_file: str,
        api_url: str,
        image_url_column: str = "image_url",
        api_method: str = "POST",
        api_headers: Optional[Dict[str, str]] = None,
        api_input_field: str = "image_url",
        taskid_response_path: str = "taskid",
        batch_size: int = 1,
        delay_between_requests: float = 0.1,
    ) -> Dict[str, Any]:
        """
        第一步：批量提交任务到 API，获取 taskid 并保存到新的 Excel 文件。
        
        参数:
            input_file: 输入的 Excel/CSV 文件路径（包含 image_url 列）
            output_file: 输出的 Excel 文件路径（包含 taskid 列）
            api_url: 任务提交接口 URL
            image_url_column: 包含图片 URL 的列名
            api_method: HTTP 请求方法
            api_headers: HTTP 请求头
            api_input_field: API 请求中输入字段的名称
            taskid_response_path: 从 API 响应中提取 taskid 的路径（点号表示法）
            batch_size: 批量大小（目前支持逐个提交，预留批量扩展）
            delay_between_requests: 请求间隔时间（秒）
            
        返回:
            包含提交结果的字典
        """
        result = {
            "success": False,
            "total_count": 0,
            "success_count": 0,
            "fail_count": 0,
            "error_count": 0,
            "errors": [],
            "output_file": output_file,
            "start_time": None,
            "end_time": None,
            "duration": 0.0,
        }
        
        start_time = datetime.now()
        result["start_time"] = start_time.isoformat()
        
        # 读取输入文件
        print(f"📖 正在读取输入文件：{input_file}")
        df = FileHandler.read_file(input_file)
        if df is None:
            result["errors"].append("无法读取输入文件")
            result["end_time"] = datetime.now().isoformat()
            result["duration"] = (datetime.now() - start_time).total_seconds()
            return result
        
        # 验证 image_url 列是否存在
        if image_url_column not in df.columns:
            error_msg = f"缺少列 '{image_url_column}'，可用列：{', '.join(df.columns)}"
            result["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            result["end_time"] = datetime.now().isoformat()
            result["duration"] = (datetime.now() - start_time).total_seconds()
            return result
        
        # 提取 image_url 列表
        image_urls = df[image_url_column].dropna().tolist()
        result["total_count"] = len(image_urls)
        
        if result["total_count"] == 0:
            result["errors"].append(f"'{image_url_column}' 列中没有有效数据")
            result["end_time"] = datetime.now().isoformat()
            result["duration"] = (datetime.now() - start_time).total_seconds()
            return result
        
        print(f"📊 找到 {result['total_count']} 条记录需要提交")
        
        # 批量提交任务
        taskids = []
        original_indices = []
        
        for idx, image_url in enumerate(image_urls):
            if self.progress_callback:
                self.progress_callback(idx + 1, result["total_count"])
            
            # 发送请求
            response = self.api_client.send_request(
                url=api_url,
                method=api_method,
                headers=api_headers,
                json_data={api_input_field: image_url},
                extract_path=taskid_response_path,
            )
            
            if response["success"] and response["data"] is not None:
                taskids.append(response["data"])
                original_indices.append(idx)
                result["success_count"] += 1
                print(f"✓ [{idx + 1}/{result['total_count']}] 提交成功，taskid: {response['data']}")
            else:
                result["fail_count"] += 1
                error_info = f"行 {idx + 1}: {response.get('error', '未知错误')}"
                result["errors"].append(error_info)
                print(f"✗ [{idx + 1}/{result['total_count']}] 提交失败：{response.get('error', '未知错误')}")
            
            # 请求间隔
            if delay_between_requests > 0 and idx < len(image_urls) - 1:
                time.sleep(delay_between_requests)
        
        # 创建输出 DataFrame
        output_df = pd.DataFrame({
            "taskid": taskids,
            "original_index": original_indices,
        })
        
        # 如果需要保留原始文件的其他列，可以合并
        if len(output_df) > 0:
            # 只保留成功提交的行对应的原始数据
            original_df_subset = df.iloc[original_indices].reset_index(drop=True)
            # 添加 taskid 列
            output_df_with_data = pd.concat([original_df_subset, output_df["taskid"]], axis=1)
        else:
            output_df_with_data = output_df
        
        # 保存到新文件
        try:
            if output_file.endswith('.csv'):
                output_df_with_data.to_csv(output_file, index=False, encoding='utf-8-sig')
            else:
                output_df_with_data.to_excel(output_file, index=False)
            result["output_file"] = output_file
            result["success"] = True
            print(f"✅ 任务 ID 已保存到：{output_file}")
        except Exception as e:
            result["errors"].append(f"保存文件失败：{str(e)}")
            print(f"❌ 保存文件失败：{str(e)}")
        
        end_time = datetime.now()
        result["end_time"] = end_time.isoformat()
        result["duration"] = (end_time - start_time).total_seconds()
        
        # 打印统计信息
        print("\n" + "="*50)
        print("📈 提交统计:")
        print(f"   总记录数：{result['total_count']}")
        print(f"   成功：{result['success_count']}")
        print(f"   失败：{result['fail_count']}")
        print(f"   耗时：{result['duration']:.2f} 秒")
        print("="*50)
        
        return result
    
    def get_task_results(
        self,
        input_file: str,
        result_file: str,
        taskid_column: str = "taskid",
        result_api_url: Optional[str] = None,
        result_api_method: str = "GET",
        result_api_headers: Optional[Dict[str, str]] = None,
        result_response_path: str = "result",
        status_response_path: Optional[str] = "status",
        pending_status_values: Optional[List[Any]] = None,
        max_retries: int = 10,
        retry_delay: float = 2.0,
        expected_column: str = "expected",
        actual_column_name: str = "actual_result",
        strategy: Optional[EvaluationStrategy] = None,
    ) -> Dict[str, Any]:
        """
        第二步：根据 taskid 获取任务结果，并进行评测。
        
        参数:
            input_file: 包含 taskid 列的 Excel/CSV 文件路径
            result_file: 输出结果文件路径
            taskid_column: 包含 taskid 的列名
            result_api_url: 查询任务结果的接口 URL（如果为 None，则需要提供实际值列）
            result_api_method: HTTP 请求方法
            result_api_headers: HTTP 请求头
            result_response_path: 从 API 响应中提取结果的路径
            status_response_path: 从 API 响应中提取状态的路径（如果任务可能异步）
            pending_status_values: 表示任务未完成的状态值列表
            max_retries: 最大重试次数（针对异步任务）
            retry_delay: 重试间隔时间（秒）
            expected_column: 包含预期结果的列名（用于评测）
            actual_column_name: 实际结果列名
            strategy: 评测策略（如果提供，则进行评测）
            
        返回:
            包含获取结果和评测结果的字典
        """
        result = {
            "success": False,
            "total_count": 0,
            "retrieved_count": 0,
            "pending_count": 0,
            "error_count": 0,
            "evaluated_count": 0,
            "match_count": 0,
            "errors": [],
            "output_file": result_file,
            "evaluation": None,
            "start_time": None,
            "end_time": None,
            "duration": 0.0,
        }
        
        start_time = datetime.now()
        result["start_time"] = start_time.isoformat()
        
        if pending_status_values is None:
            pending_status_values = ["pending", "processing", "running", "queued"]
        
        # 读取输入文件
        print(f"📖 正在读取任务文件：{input_file}")
        df = FileHandler.read_file(input_file)
        if df is None:
            result["errors"].append("无法读取输入文件")
            result["end_time"] = datetime.now().isoformat()
            result["duration"] = (datetime.now() - start_time).total_seconds()
            return result
        
        # 验证 taskid 列是否存在
        if taskid_column not in df.columns:
            error_msg = f"缺少列 '{taskid_column}'，可用列：{', '.join(df.columns)}"
            result["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            result["end_time"] = datetime.now().isoformat()
            result["duration"] = (datetime.now() - start_time).total_seconds()
            return result
        
        result["total_count"] = len(df)
        print(f"📊 找到 {result['total_count']} 个任务需要获取结果")
        
        # 获取任务结果
        actual_results = []
        errors = []
        
        for idx, row in df.iterrows():
            if self.progress_callback:
                self.progress_callback(idx + 1, result["total_count"])
            
            taskid = row[taskid_column]
            actual_result = None
            error_msg = None
            
            if result_api_url:
                # 通过 API 获取结果
                task_result = self._fetch_task_result(
                    taskid=taskid,
                    api_url=result_api_url,
                    api_method=result_api_method,
                    api_headers=result_api_headers,
                    result_response_path=result_response_path,
                    status_response_path=status_response_path,
                    pending_status_values=pending_status_values,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                )
                
                if task_result["success"]:
                    actual_result = task_result["result"]
                    if task_result["retried"]:
                        print(f"✓ [{idx + 1}/{result['total_count']}] 任务 {taskid} 完成（重试 {task_result['retry_count']} 次）")
                    else:
                        print(f"✓ [{idx + 1}/{result['total_count']}] 任务 {taskid} 完成")
                    result["retrieved_count"] += 1
                else:
                    error_msg = task_result.get("error", "未知错误")
                    result["error_count"] += 1
                    if task_result.get("is_pending"):
                        result["pending_count"] += 1
                        print(f"⏳ [{idx + 1}/{result['total_count']}] 任务 {taskid} 仍在处理中")
                    else:
                        print(f"✗ [{idx + 1}/{result['total_count']}] 任务 {taskid} 获取失败：{error_msg}")
            else:
                # 如果没有提供 API，尝试从已有列获取实际值
                if "actual" in df.columns or actual_column_name in df.columns:
                    actual_col = "actual" if "actual" in df.columns else actual_column_name
                    actual_result = row.get(actual_col)
                    if actual_result is not None:
                        result["retrieved_count"] += 1
                        print(f"✓ [{idx + 1}/{result['total_count']}] 从文件读取结果")
                    else:
                        error_msg = "实际值为空"
                        result["error_count"] += 1
                else:
                    error_msg = "未提供 API URL 且文件中没有实际结果列"
                    result["error_count"] += 1
            
            actual_results.append(actual_result)
            errors.append(error_msg)
        
        # 添加实际结果列到 DataFrame
        df[actual_column_name] = actual_results
        if any(errors):
            df["error"] = errors
        
        # 如果提供了评测策略，进行评测
        evaluation_result = None
        if strategy and expected_column in df.columns:
            print("\n🔍 开始评测...")
            match_results = []
            
            for idx, row in df.iterrows():
                expected = row.get(expected_column)
                actual = row.get(actual_column_name)
                
                if expected is not None and actual is not None:
                    is_match = strategy.evaluate(expected, actual)
                    match_results.append(is_match)
                    if is_match:
                        result["match_count"] += 1
                    result["evaluated_count"] += 1
                else:
                    match_results.append(None)
            
            df["match"] = match_results
            
            # 计算准确率
            if result["evaluated_count"] > 0:
                accuracy = result["match_count"] / result["evaluated_count"]
                evaluation_result = {
                    "strategy_name": strategy.name,
                    "total_evaluated": result["evaluated_count"],
                    "match_count": result["match_count"],
                    "accuracy": accuracy,
                    "accuracy_percentage": f"{accuracy * 100:.2f}%",
                }
                result["evaluation"] = evaluation_result
                
                print("\n" + "="*50)
                print("📊 评测结果:")
                print(f"   评测策略：{strategy.name}")
                print(f"   评测数量：{result['evaluated_count']}")
                print(f"   匹配数量：{result['match_count']}")
                print(f"   准确率：{evaluation_result['accuracy_percentage']}")
                print("="*50)
        
        # 保存结果文件
        try:
            if result_file.endswith('.csv'):
                df.to_csv(result_file, index=False, encoding='utf-8-sig')
            else:
                df.to_excel(result_file, index=False)
            result["output_file"] = result_file
            result["success"] = True
            print(f"\n✅ 结果已保存到：{result_file}")
        except Exception as e:
            result["errors"].append(f"保存文件失败：{str(e)}")
            print(f"❌ 保存文件失败：{str(e)}")
        
        end_time = datetime.now()
        result["end_time"] = end_time.isoformat()
        result["duration"] = (end_time - start_time).total_seconds()
        
        return result
    
    def _fetch_task_result(
        self,
        taskid: str,
        api_url: str,
        api_method: str = "GET",
        api_headers: Optional[Dict[str, str]] = None,
        result_response_path: str = "result",
        status_response_path: Optional[str] = "status",
        pending_status_values: Optional[List[Any]] = None,
        max_retries: int = 10,
        retry_delay: float = 2.0,
    ) -> Dict[str, Any]:
        """
        获取单个任务的结果（支持异步任务轮询）。
        
        参数:
            taskid: 任务 ID
            api_url: 查询接口 URL
            api_method: HTTP 请求方法
            api_headers: HTTP 请求头
            result_response_path: 结果在响应中的路径
            status_response_path: 状态在响应中的路径
            pending_status_values: 表示待处理的状态值
            max_retries: 最大重试次数
            retry_delay: 重试间隔
            
        返回:
            包含结果的字典
        """
        if pending_status_values is None:
            pending_status_values = ["pending", "processing", "running", "queued"]
        
        # 构建请求 URL（通常 taskid 作为参数或路径的一部分）
        if "{taskid}" in api_url:
            url = api_url.replace("{taskid}", str(taskid))
        elif api_method.upper() == "GET":
            # GET 请求通常将 taskid 作为查询参数
            separator = "&" if "?" in api_url else "?"
            url = f"{api_url}{separator}taskid={taskid}"
        else:
            url = api_url
        
        # 请求头
        if api_headers is None:
            api_headers = {}
        
        # 对于 GET 请求，通常不需要 body
        json_data = None
        if api_method.upper() in ["POST", "PUT"]:
            json_data = {"taskid": taskid}
        
        retry_count = 0
        is_pending = False
        
        while retry_count <= max_retries:
            response = self.api_client.send_request(
                url=url,
                method=api_method,
                headers=api_headers,
                json_data=json_data,
            )
            
            if not response["success"]:
                return {
                    "success": False,
                    "result": None,
                    "error": response.get("error", "请求失败"),
                    "is_pending": False,
                    "retried": False,
                    "retry_count": retry_count,
                }
            
            raw_response = response.get("raw_response", {})
            
            # 检查状态（如果有状态字段）
            if status_response_path:
                status = self.api_client._extract_field(raw_response, status_response_path)
                if status is not None and str(status).lower() in [str(v).lower() for v in pending_status_values]:
                    is_pending = True
                    if retry_count < max_retries:
                        retry_count += 1
                        time.sleep(retry_delay)
                        continue
                    else:
                        return {
                            "success": False,
                            "result": None,
                            "error": f"任务超时（状态：{status}）",
                            "is_pending": True,
                            "retried": retry_count > 0,
                            "retry_count": retry_count,
                        }
            
            # 提取结果
            actual_result = self.api_client._extract_field(raw_response, result_response_path)
            
            if actual_result is not None:
                return {
                    "success": True,
                    "result": actual_result,
                    "error": None,
                    "is_pending": False,
                    "retried": retry_count > 0,
                    "retry_count": retry_count,
                }
            else:
                # 结果为空，可能是任务未完成
                if retry_count < max_retries:
                    retry_count += 1
                    time.sleep(retry_delay)
                else:
                    return {
                        "success": False,
                        "result": None,
                        "error": "无法从响应中提取结果",
                        "is_pending": is_pending,
                        "retried": retry_count > 0,
                        "retry_count": retry_count,
                    }
        
        return {
            "success": False,
            "result": None,
            "error": "达到最大重试次数",
            "is_pending": is_pending,
            "retried": retry_count > 0,
            "retry_count": retry_count,
        }


def main():
    """主函数，解析命令行参数并执行相应操作。"""
    parser = argparse.ArgumentParser(
        description="AI 批阅项目评测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 第一步：批量提交任务
  python batch_evaluator.py --step 1 --input-file input.xlsx --output-file tasks.xlsx --api-url http://api/submit
  
  # 第二步：获取任务结果并评测
  python batch_evaluator.py --step 2 --input-file tasks.xlsx --result-file results.xlsx --strategy exact_match --expected-column expected
  
  # 完整流程（一步提交 + 一步获取结果）
  python batch_evaluator.py --step 1 --input-file input.xlsx --output-file tasks.xlsx --api-url http://api/submit && \\
  python batch_evaluator.py --step 2 --input-file tasks.xlsx --result-file results.xlsx --strategy exact_match --expected-column expected
        """,
    )
    
    # 基本参数
    parser.add_argument("--step", type=int, choices=[1, 2], help="执行步骤：1=提交任务，2=获取结果")
    parser.add_argument("--input-file", type=str, help="输入文件路径（Excel/CSV）")
    parser.add_argument("--output-file", type=str, help="输出文件路径（步骤 1 使用）")
    parser.add_argument("--result-file", type=str, help="结果文件路径（步骤 2 使用）")
    
    # API 相关参数（步骤 1）
    parser.add_argument("--api-url", type=str, help="任务提交或结果查询接口 URL")
    parser.add_argument("--api-method", type=str, default="POST", help="HTTP 请求方法（默认：POST）")
    parser.add_argument("--api-headers", type=str, help="HTTP 请求头（JSON 格式字符串）")
    parser.add_argument("--api-input-field", type=str, default="image_url", help="API 请求中输入字段的名称")
    parser.add_argument("--taskid-response-path", type=str, default="taskid", help="从响应中提取 taskid 的路径")
    
    # API 相关参数（步骤 2）
    parser.add_argument("--result-api-url", type=str, help="查询任务结果的接口 URL")
    parser.add_argument("--result-api-method", type=str, default="GET", help="结果查询 HTTP 方法（默认：GET）")
    parser.add_argument("--result-response-path", type=str, default="result", help="从响应中提取结果的路径")
    parser.add_argument("--status-response-path", type=str, help="从响应中提取状态的路径")
    parser.add_argument("--max-retries", type=int, default=10, help="最大重试次数（默认：10）")
    parser.add_argument("--retry-delay", type=float, default=2.0, help="重试间隔时间（秒，默认：2.0）")
    
    # 列配置
    parser.add_argument("--image-url-column", type=str, default="image_url", help="图片 URL 列名（默认：image_url）")
    parser.add_argument("--taskid-column", type=str, default="taskid", help="任务 ID 列名（默认：taskid）")
    parser.add_argument("--expected-column", type=str, default="expected", help="预期结果列名（默认：expected）")
    
    # 评测策略
    parser.add_argument("--strategy", type=str, help="评测策略 ID（如：exact_match, case_insensitive 等）")
    parser.add_argument("--list-strategies", action="store_true", help="列出所有可用的评测策略")
    
    # 其他参数
    parser.add_argument("--delay", type=float, default=0.1, help="请求间隔时间（秒，默认：0.1）")
    parser.add_argument("--verbose", action="store_true", help="显示详细输出")
    
    args = parser.parse_args()
    
    # 初始化策略注册表（确保插件被加载）
    _ = StrategyRegistry()
    
    # 列出策略（可以在没有指定 step 的情况下单独使用）
    if args.list_strategies:
        print("\n可用的评测策略:")
        print("-" * 50)
        strategies = StrategyRegistry.get_strategy_list()
        if not strategies:
            print("暂无可用策略，请在 strategies/plugins 目录下添加策略插件")
        else:
            for s in strategies:
                custom_mark = " [自定义]" if s.get("is_custom") else ""
                print(f"  - {s['id']}{custom_mark}: {s['name']}")
                if s.get("description"):
                    print(f"    描述：{s['description']}")
        print()
        return
    
    # 验证必需参数
    if not args.step:
        print("❌ 错误：必须指定 --step 参数（1 或 2）")
        parser.print_help()
        return
    
    if not args.input_file:
        print("❌ 错误：必须指定 --input-file 参数")
        parser.print_help()
        return
    
    # 创建评测器
    evaluator = BatchEvaluator()
    
    # 步骤 1：提交任务
    if args.step == 1:
        if not args.output_file:
            print("❌ 错误：步骤 1 需要指定 --output-file")
            return
        if not args.api_url:
            print("❌ 错误：步骤 1 需要指定 --api-url")
            return
        
        # 解析请求头
        api_headers = None
        if args.api_headers:
            import json
            try:
                api_headers = json.loads(args.api_headers)
            except json.JSONDecodeError:
                print("❌ 错误：--api-headers 必须是有效的 JSON 格式")
                return
        
        print("="*60)
        print("🚀 步骤 1：批量提交任务")
        print("="*60)
        
        result = evaluator.submit_tasks(
            input_file=args.input_file,
            output_file=args.output_file,
            api_url=args.api_url,
            image_url_column=args.image_url_column,
            api_method=args.api_method,
            api_headers=api_headers,
            api_input_field=args.api_input_field,
            taskid_response_path=args.taskid_response_path,
            delay_between_requests=args.delay,
        )
        
        if result["success"]:
            print(f"\n✅ 步骤 1 完成！输出文件：{result['output_file']}")
        else:
            print(f"\n❌ 步骤 1 失败：{', '.join(result['errors'])}")
    
    # 步骤 2：获取结果并评测
    elif args.step == 2:
        if not args.result_file:
            print("❌ 错误：步骤 2 需要指定 --result-file")
            return
        
        # 获取策略
        strategy = None
        if args.strategy:
            strategy = StrategyRegistry.get_strategy(args.strategy)
            if not strategy:
                print(f"❌ 错误：未知策略 '{args.strategy}'")
                print("💡 使用 --list-strategies 查看所有可用策略")
                return
        
        print("="*60)
        print("🚀 步骤 2：获取任务结果" + (" 并评测" if strategy else ""))
        print("="*60)
        
        result = evaluator.get_task_results(
            input_file=args.input_file,
            result_file=args.result_file,
            taskid_column=args.taskid_column,
            result_api_url=args.result_api_url or args.api_url,
            result_api_method=args.result_api_method,
            result_response_path=args.result_response_path,
            status_response_path=args.status_response_path,
            max_retries=args.max_retries,
            retry_delay=args.retry_delay,
            expected_column=args.expected_column,
            strategy=strategy,
        )
        
        if result["success"]:
            print(f"\n✅ 步骤 2 完成！结果文件：{result['output_file']}")
            if result["evaluation"]:
                eval_info = result["evaluation"]
                print(f"📊 准确率：{eval_info['accuracy_percentage']} ({eval_info['match_count']}/{eval_info['total_evaluated']})")
        else:
            print(f"\n❌ 步骤 2 失败：{', '.join(result['errors'])}")


if __name__ == "__main__":
    main()
