"""
内置评测策略模块，用于准确率计算。
"""

from typing import Any
from .base import EvaluationStrategy


class ExactMatchStrategy(EvaluationStrategy):
    """精确匹配比较策略。"""
    
    @property
    def name(self) -> str:
        return "精确匹配"
    
    @property
    def description(self) -> str:
        return "预期值和实际值必须完全相同"
    
    def evaluate(self, expected: Any, actual: Any) -> bool:
        return str(expected).strip() == str(actual).strip()


class CaseInsensitiveMatchStrategy(EvaluationStrategy):
    """忽略大小写匹配比较策略。"""
    
    @property
    def name(self) -> str:
        return "忽略大小写匹配"
    
    @property
    def description(self) -> str:
        return "比较时忽略字母大小写差异"
    
    def evaluate(self, expected: Any, actual: Any) -> bool:
        return str(expected).strip().lower() == str(actual).strip().lower()


class NumericToleranceStrategy(EvaluationStrategy):
    """数值容差比较策略。"""
    
    def __init__(self, tolerance: float = 0.01):
        self.tolerance = tolerance
    
    @property
    def name(self) -> str:
        return f"数值容差匹配 (±{self.tolerance})"
    
    @property
    def description(self) -> str:
        return f"允许数值差异在 {self.tolerance} 范围内"
    
    def evaluate(self, expected: Any, actual: Any) -> bool:
        try:
            exp_val = float(expected)
            act_val = float(actual)
            return abs(exp_val - act_val) <= self.tolerance
        except (ValueError, TypeError):
            return False


class ContainsMatchStrategy(EvaluationStrategy):
    """包含匹配策略 - 检查实际值是否包含预期值。"""
    
    @property
    def name(self) -> str:
        return "包含匹配"
    
    @property
    def description(self) -> str:
        return "实际值包含预期值即为匹配"
    
    def evaluate(self, expected: Any, actual: Any) -> bool:
        return str(expected).strip() in str(actual).strip()


class JSONMatchStrategy(EvaluationStrategy):
    """JSON 结构匹配策略。"""
    
    @property
    def name(self) -> str:
        return "JSON 结构匹配"
    
    @property
    def description(self) -> str:
        return "比较 JSON 对象的关键字段是否匹配"
    
    def evaluate(self, expected: Any, actual: Any) -> bool:
        import json
        try:
            exp_json = json.loads(str(expected)) if isinstance(expected, str) else expected
            act_json = json.loads(str(actual)) if isinstance(actual, str) else actual
            
            if isinstance(exp_json, dict) and isinstance(act_json, dict):
                return exp_json == act_json
            elif isinstance(exp_json, list) and isinstance(act_json, list):
                return exp_json == act_json
            else:
                return str(exp_json) == str(act_json)
        except (json.JSONDecodeError, TypeError):
            return str(expected).strip() == str(actual).strip()
