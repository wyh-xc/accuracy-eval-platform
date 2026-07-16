"""
Core package initialization.
"""

from .file_handler import FileHandler
from .api_client import APIClient
from .evaluation_engine import EvaluationEngine, EvaluationResult

__all__ = [
    "FileHandler",
    "APIClient",
    "EvaluationEngine",
    "EvaluationResult",
]
