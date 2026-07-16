"""
评测引擎模块，负责编排准确率评测流程。
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

# 将父目录添加到路径以便导入
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.file_handler import FileHandler
from core.api_client import APIClient
from strategies.registry import StrategyRegistry
from strategies.base import EvaluationStrategy


class EvaluationResult:
    """表示评测结果。"""
    
    def __init__(self):
        self.total_count: int = 0
        self.success_count: int = 0
        self.fail_count: int = 0
        self.error_count: int = 0
        self.accuracy: float = 0.0
        self.details: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration: float = 0.0
        self.strategy_name: str = ""
        self.errors: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """将结果转换为字典。"""
        return {
            "total_count": self.total_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "error_count": self.error_count,
            "accuracy": self.accuracy,
            "accuracy_percentage": f"{self.accuracy:.2f}%",
            "duration_seconds": self.duration,
            "strategy_name": self.strategy_name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "errors": self.errors,
            "details": self.details,
        }


class EvaluationEngine:
    """用于运行准确率评测的主引擎。"""
    
    def __init__(self, strategy: EvaluationStrategy):
        """
        初始化评测引擎。
        
        参数:
            strategy: 要使用的评测策略
        """
        self.strategy = strategy
        self.api_client = APIClient()
        self.progress_callback: Optional[Callable[[int, int], None]] = None
    
    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """设置进度更新的回调函数。"""
        self.progress_callback = callback
    
    def evaluate_from_file(
        self,
        file_path: str,
        input_column: str,
        expected_column: str,
        actual_column: Optional[str] = None,
        api_url: Optional[str] = None,
        api_method: str = "POST",
        api_headers: Optional[Dict[str, str]] = None,
        api_input_field: str = "input",
        api_extract_path: Optional[str] = None,
    ) -> EvaluationResult:
        """
        使用文件中的数据运行评测。
        
        参数:
            file_path: Excel/CSV 文件路径
            input_column: 包含输入数据的列
            expected_column: 包含预期结果的列
            actual_column: 包含实际结果的列（如果已存在）
            api_url: API 端点 URL（如果要获取实际结果）
            api_method: API 调用的 HTTP 方法
            api_headers: API 调用的 HTTP 请求头
            api_input_field: API 请求中输入字段的名称
            api_extract_path: 从 API 响应中提取的路径
            
        返回:
            EvaluationResult 对象
        """
        result = EvaluationResult()
        result.start_time = datetime.now()
        result.strategy_name = self.strategy.name
        
        # 验证文件
        validation = FileHandler.validate_columns(file_path, [input_column, expected_column])
        if not validation["valid"]:
            result.errors.append(validation["error"])
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            return result
        
        # 从文件中提取数据
        data = FileHandler.extract_data(
            file_path=file_path,
            input_column=input_column,
            expected_column=expected_column,
            actual_column=actual_column,
        )
        
        if not data:
            result.errors.append("无法从文件中提取数据")
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            return result
        
        result.total_count = len(data)
        
        # 处理每一行
        for idx, item in enumerate(data):
            expected = item["expected"]
            actual = item.get("actual")
            
            # 如果没有提供实际结果列且提供了 API URL，则从 API 获取
            if actual is None and api_url:
                response = self.api_client.send_request(
                    url=api_url,
                    method=api_method,
                    headers=api_headers,
                    json_data={api_input_field: item["input"]},
                    extract_path=api_extract_path,
                )
                
                if response["success"]:
                    actual = response["data"]
                else:
                    result.error_count += 1
                    result.details.append({
                        "row": idx + 1,
                        "input": item["input"],
                        "expected": expected,
                        "actual": None,
                        "match": False,
                        "error": response["error"],
                    })
                    continue
            
            # 使用策略进行评测
            if actual is not None:
                is_match = self.strategy.evaluate(expected, actual)
                
                if is_match:
                    result.success_count += 1
                else:
                    result.fail_count += 1
                
                result.details.append({
                    "row": idx + 1,
                    "input": item["input"],
                    "expected": expected,
                    "actual": actual,
                    "match": is_match,
                    "error": None,
                })
            else:
                result.error_count += 1
                result.details.append({
                    "row": idx + 1,
                    "input": item["input"],
                    "expected": expected,
                    "actual": None,
                    "match": False,
                    "error": "没有可用的实际值",
                })
            
            # 报告进度
            if self.progress_callback:
                self.progress_callback(idx + 1, result.total_count)
        
        # 计算准确率
        if result.total_count > 0:
            valid_count = result.success_count + result.fail_count
            if valid_count > 0:
                result.accuracy = result.success_count / valid_count
            else:
                result.accuracy = 0.0
        
        result.end_time = datetime.now()
        result.duration = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    def evaluate_with_actuals(
        self,
        expected_values: List[Any],
        actual_values: List[Any],
    ) -> EvaluationResult:
        """
        使用预先提供的预期值和实际值运行评测。
        
        参数:
            expected_values: 预期值列表
            actual_values: 实际值列表
            
        返回:
            EvaluationResult 对象
        """
        result = EvaluationResult()
        result.start_time = datetime.now()
        result.strategy_name = self.strategy.name
        
        if len(expected_values) != len(actual_values):
            result.errors.append("预期值和实际值列表的长度必须相同")
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            return result
        
        result.total_count = len(expected_values)
        
        for idx, (expected, actual) in enumerate(zip(expected_values, actual_values)):
            is_match = self.strategy.evaluate(expected, actual)
            
            if is_match:
                result.success_count += 1
            else:
                result.fail_count += 1
            
            result.details.append({
                "row": idx + 1,
                "expected": expected,
                "actual": actual,
                "match": is_match,
                "error": None,
            })
            
            if self.progress_callback:
                self.progress_callback(idx + 1, result.total_count)
        
        # 计算准确率
        if result.total_count > 0:
            result.accuracy = result.success_count / result.total_count
        
        result.end_time = datetime.now()
        result.duration = (result.end_time - result.start_time).total_seconds()
        
        return result
