"""
Strategy registry for managing evaluation strategies.
Provides a central place to register and retrieve strategies.
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
    """Registry for managing evaluation strategies."""
    
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
        """Initialize built-in strategies."""
        cls._strategies = {
            "exact_match": ExactMatchStrategy(),
            "case_insensitive": CaseInsensitiveMatchStrategy(),
            "numeric_tolerance": NumericToleranceStrategy(),
            "contains": ContainsMatchStrategy(),
            "json_match": JSONMatchStrategy(),
        }
    
    @classmethod
    def get_strategy(cls, strategy_id: str) -> Optional[EvaluationStrategy]:
        """Get a strategy by its ID."""
        return cls._strategies.get(strategy_id)
    
    @classmethod
    def get_all_strategies(cls) -> Dict[str, EvaluationStrategy]:
        """Get all registered strategies."""
        return cls._strategies.copy()
    
    @classmethod
    def get_strategy_list(cls) -> List[Dict[str, str]]:
        """Get a list of strategy names and descriptions."""
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
        Register a custom strategy.
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_class: The strategy class to register
            **kwargs: Additional arguments to pass to the strategy constructor
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            instance = strategy_class(**kwargs) if kwargs else strategy_class()
            cls._strategies[strategy_id] = instance
            cls._custom_strategies[strategy_id] = strategy_class
            return True
        except Exception as e:
            print(f"Failed to register custom strategy: {e}")
            return False
    
    @classmethod
    def unregister_custom_strategy(cls, strategy_id: str) -> bool:
        """
        Unregister a custom strategy.
        
        Args:
            strategy_id: The ID of the strategy to remove
            
        Returns:
            bool: True if unregistration successful, False otherwise
        """
        if strategy_id in cls._custom_strategies:
            del cls._strategies[strategy_id]
            del cls._custom_strategies[strategy_id]
            return True
        return False
    
    @classmethod
    def is_custom_strategy(cls, strategy_id: str) -> bool:
        """Check if a strategy is custom."""
        return strategy_id in cls._custom_strategies
