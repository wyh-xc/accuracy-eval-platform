"""
API 客户端模块，用于向自定义端点发送 HTTP 请求。
"""

import requests
from typing import Dict, Any, Optional, List
import json


class APIClient:
    """用于发送 API 请求的 HTTP 客户端。"""
    
    def __init__(self, timeout: int = 30):
        """
        初始化 API 客户端。
        
        参数:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout
        self.session = requests.Session()
    
    def send_request(
        self,
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        extract_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求并返回响应。
        
        参数:
            url: API 端点 URL
            method: HTTP 方法（GET、POST、PUT、DELETE）
            headers: HTTP 请求头
            params: 查询参数
            data: 表单数据
            json_data: JSON 请求体数据
            extract_path: 使用点号表示法从响应中提取特定字段
            
        返回:
            包含响应数据和元数据的字典
        """
        try:
            # 默认请求头
            if headers is None:
                headers = {}
            
            if json_data and 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                timeout=self.timeout,
            )
            
            # 尝试解析 JSON 响应
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw": response.text}
            
            # 如果提供了路径则提取特定字段
            result = response_data
            if extract_path:
                result = self._extract_field(response_data, extract_path)
            
            return {
                "success": True,
                "status_code": response.status_code,
                "data": result,
                "raw_response": response_data,
                "error": None,
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "status_code": None,
                "data": None,
                "raw_response": None,
                "error": f"请求在 {self.timeout} 秒后超时",
            }
        except requests.exceptions.ConnectionError as e:
            return {
                "success": False,
                "status_code": None,
                "data": None,
                "raw_response": None,
                "error": f"连接错误：{str(e)}",
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": None,
                "data": None,
                "raw_response": None,
                "error": f"请求失败：{str(e)}",
            }
    
    def _extract_field(self, data: Dict[str, Any], path: str) -> Any:
        """
        使用点号表示法从嵌套字典中提取字段。
        
        参数:
            data: 要从中提取的字典
            path: 点号表示法路径（例如："result.data.value"）
            
        返回:
            提取的值，如果未找到则返回 None
        """
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list):
                try:
                    index = int(key)
                    current = current[index] if index < len(current) else None
                except (ValueError, IndexError):
                    return None
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    def batch_requests(
        self,
        url: str,
        inputs: List[Any],
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        input_field: str = "input",
        extract_path: Optional[str] = None,
        progress_callback=None,
    ) -> List[Dict[str, Any]]:
        """
        批量发送多个请求。
        
        参数:
            url: API 端点 URL
            inputs: 要发送的输入值列表
            method: HTTP 方法
            headers: HTTP 请求头
            input_field: 请求体中输入字段的名称
            extract_path: 从响应中提取的路径
            progress_callback: 用于进度更新的可选回调函数
            
        返回:
            响应结果列表
        """
        results = []
        total = len(inputs)
        
        for idx, input_value in enumerate(inputs):
            # 构建请求负载
            json_data = {input_field: input_value}
            
            response = self.send_request(
                url=url,
                method=method,
                headers=headers,
                json_data=json_data,
                extract_path=extract_path,
            )
            
            results.append({
                "input": input_value,
                "response": response["data"] if response["success"] else None,
                "success": response["success"],
                "error": response["error"],
            })
            
            # 报告进度
            if progress_callback:
                progress_callback(idx + 1, total)
        
        return results
