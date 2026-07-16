"""
Strategy pattern base class for accuracy evaluation logic.
All custom evaluation strategies must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class EvaluationStrategy(ABC):
    """Base class for all evaluation strategies."""
    
    @abstractmethod
    def evaluate(self, expected: Any, actual: Any) -> bool:
        """
        Evaluate if the actual value matches the expected value.
        
        Args:
            expected: The expected value from the dataset
            actual: The actual value from API response
            
        Returns:
            bool: True if match, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the display name of this strategy."""
        pass
    
    @property
    def description(self) -> str:
        """Return a description of this strategy."""
        return ""
