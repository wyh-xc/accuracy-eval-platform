"""
策略注册表模块，用于管理评测策略。
提供注册和检索策略的中心位置。
"""

from typing import Dict, List, Type, Optional
from .base import EvaluationStrategy
from .builtin_strategies import (
    ExactMatchStrategy,
    CaseInsensitiveMatchStrategy,
    NumericToleranceStrategy,
    ContainsMatchStrategy,
    JSONMatchStrategy,
)


class StrategyRegistry:
    """用于管理评测策略的注册表。"""
    
    _instance = None
    _strategies: Dict[str, EvaluationStrategy] = {}
    _custom_strategies: Dict[str, Type[EvaluationStrategy]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initialize_builtin_strategies()
        return cls._instance
    
    @classmethod
    def _initialize_builtin_strategies(cls):
        """初始化内置策略。"""
        cls._strategies = {
            "exact_match": ExactMatchStrategy(),
            "case_insensitive": CaseInsensitiveMatchStrategy(),
            "numeric_tolerance": NumericToleranceStrategy(),
            "contains": ContainsMatchStrategy(),
            "json_match": JSONMatchStrategy(),
        }
    
    @classmethod
    def get_strategy(cls, strategy_id: str) -> Optional[EvaluationStrategy]:
        """根据 ID 获取策略。"""
        return cls._strategies.get(strategy_id)
    
    @classmethod
    def get_all_strategies(cls) -> Dict[str, EvaluationStrategy]:
        """获取所有已注册的策略。"""
        return cls._strategies.copy()
    
    @classmethod
    def get_strategy_list(cls) -> List[Dict[str, str]]:
        """获取策略名称和描述列表。"""
        result = []
        for strategy_id, strategy in cls._strategies.items():
            result.append({
                "id": strategy_id,
                "name": strategy.name,
                "description": strategy.description,
                "is_custom": strategy_id in cls._custom_strategies
            })
        return result
    
    @classmethod
    def register_custom_strategy(
        cls, 
        strategy_id: str, 
        strategy_class: Type[EvaluationStrategy],
        **kwargs
    ) -> bool:
        """
        注册自定义策略。
        
        参数:
            strategy_id: 策略的唯一标识符
            strategy_class: 要注册的策略类
            **kwargs: 传递给策略构造函数的额外参数
            
        返回:
            bool: 注册成功返回 True，否则返回 False
        """
        try:
            instance = strategy_class(**kwargs) if kwargs else strategy_class()
            cls._strategies[strategy_id] = instance
            cls._custom_strategies[strategy_id] = strategy_class
            return True
        except Exception as e:
            print(f"注册自定义策略失败：{e}")
            return False
    
    @classmethod
    def unregister_custom_strategy(cls, strategy_id: str) -> bool:
        """
        注销自定义策略。
        
        参数:
            strategy_id: 要移除的策略 ID
            
        返回:
            bool: 注销成功返回 True，否则返回 False
        """
        if strategy_id in cls._custom_strategies:
            del cls._strategies[strategy_id]
            del cls._custom_strategies[strategy_id]
            return True
        return False
    
    @classmethod
    def is_custom_strategy(cls, strategy_id: str) -> bool:
        """检查策略是否为自定义策略。"""
        return strategy_id in cls._custom_strategies
