"""
策略包初始化。
"""

from .base import EvaluationStrategy
from .builtin_strategies import (
    ExactMatchStrategy,
    CaseInsensitiveMatchStrategy,
    NumericToleranceStrategy,
    ContainsMatchStrategy,
    JSONMatchStrategy,
)
from .registry import StrategyRegistry

__all__ = [
    "EvaluationStrategy",
    "ExactMatchStrategy",
    "CaseInsensitiveMatchStrategy",
    "NumericToleranceStrategy",
    "ContainsMatchStrategy",
    "JSONMatchStrategy",
    "StrategyRegistry",
]
