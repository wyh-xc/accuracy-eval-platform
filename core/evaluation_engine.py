"""
Evaluation engine that orchestrates the accuracy evaluation process.
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.file_handler import FileHandler
from core.api_client import APIClient
from strategies.registry import StrategyRegistry
from strategies.base import EvaluationStrategy


class EvaluationResult:
    """Represents the result of an evaluation."""
    
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
        """Convert result to dictionary."""
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
    """Main engine for running accuracy evaluations."""
    
    def __init__(self, strategy: EvaluationStrategy):
        """
        Initialize the evaluation engine.
        
        Args:
            strategy: The evaluation strategy to use
        """
        self.strategy = strategy
        self.api_client = APIClient()
        self.progress_callback: Optional[Callable[[int, int], None]] = None
    
    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """Set a callback function for progress updates."""
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
        Run evaluation using data from a file.
        
        Args:
            file_path: Path to the Excel/CSV file
            input_column: Column containing input data
            expected_column: Column containing expected results
            actual_column: Column containing actual results (if already present)
            api_url: API endpoint URL (if fetching actual results)
            api_method: HTTP method for API calls
            api_headers: HTTP headers for API calls
            api_input_field: Field name for input in API request
            api_extract_path: Path to extract from API response
            
        Returns:
            EvaluationResult object
        """
        result = EvaluationResult()
        result.start_time = datetime.now()
        result.strategy_name = self.strategy.name
        
        # Validate file
        validation = FileHandler.validate_columns(file_path, [input_column, expected_column])
        if not validation["valid"]:
            result.errors.append(validation["error"])
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            return result
        
        # Extract data from file
        data = FileHandler.extract_data(
            file_path=file_path,
            input_column=input_column,
            expected_column=expected_column,
            actual_column=actual_column,
        )
        
        if not data:
            result.errors.append("No data extracted from file")
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            return result
        
        result.total_count = len(data)
        
        # Process each row
        for idx, item in enumerate(data):
            expected = item["expected"]
            actual = item.get("actual")
            
            # If no actual column provided and API URL is given, fetch from API
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
            
            # Evaluate using strategy
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
                    "error": "No actual value available",
                })
            
            # Report progress
            if self.progress_callback:
                self.progress_callback(idx + 1, result.total_count)
        
        # Calculate accuracy
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
        Run evaluation with pre-provided expected and actual values.
        
        Args:
            expected_values: List of expected values
            actual_values: List of actual values
            
        Returns:
            EvaluationResult object
        """
        result = EvaluationResult()
        result.start_time = datetime.now()
        result.strategy_name = self.strategy.name
        
        if len(expected_values) != len(actual_values):
            result.errors.append("Expected and actual value lists must have same length")
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
        
        # Calculate accuracy
        if result.total_count > 0:
            result.accuracy = result.success_count / result.total_count
        
        result.end_time = datetime.now()
        result.duration = (result.end_time - result.start_time).total_seconds()
        
        return result
