"""
策略模式的基类，用于准确率评测逻辑。
所有自定义评测策略必须继承自此类。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class EvaluationStrategy(ABC):
    """所有评测策略的基类。"""
    
    @abstractmethod
    def evaluate(self, expected: Any, actual: Any) -> bool:
        """
        评估实际值是否与预期值匹配。
        
        参数:
            expected: 数据集中的预期值
            actual: API 响应中的实际值
            
        返回:
            bool: 匹配返回 True，否则返回 False
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """返回此策略的显示名称。"""
        pass
    
    @property
    def description(self) -> str:
        """返回此策略的描述。"""
        return ""
