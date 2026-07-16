"""
API client module for making HTTP requests to custom endpoints.
"""

import requests
from typing import Dict, Any, Optional, List
import json


class APIClient:
    """HTTP client for making API requests."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the API client.
        
        Args:
            timeout: Request timeout in seconds
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
        Send an HTTP request and return the response.
        
        Args:
            url: The API endpoint URL
            method: HTTP method (GET, POST, PUT, DELETE)
            headers: HTTP headers
            params: Query parameters
            data: Form data
            json_data: JSON body data
            extract_path: Dot-notation path to extract specific field from response
            
        Returns:
            Dict containing response data and metadata
        """
        try:
            # Default headers
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
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw": response.text}
            
            # Extract specific field if path provided
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
                "error": f"Request timed out after {self.timeout} seconds",
            }
        except requests.exceptions.ConnectionError as e:
            return {
                "success": False,
                "status_code": None,
                "data": None,
                "raw_response": None,
                "error": f"Connection error: {str(e)}",
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": None,
                "data": None,
                "raw_response": None,
                "error": f"Request failed: {str(e)}",
            }
    
    def _extract_field(self, data: Dict[str, Any], path: str) -> Any:
        """
        Extract a field from nested dictionary using dot notation.
        
        Args:
            data: The dictionary to extract from
            path: Dot-notation path (e.g., "result.data.value")
            
        Returns:
            The extracted value or None if not found
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
        Send multiple requests in batch.
        
        Args:
            url: The API endpoint URL
            inputs: List of input values to send
            method: HTTP method
            headers: HTTP headers
            input_field: Field name for the input in the request body
            extract_path: Path to extract from response
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of response results
        """
        results = []
        total = len(inputs)
        
        for idx, input_value in enumerate(inputs):
            # Build request payload
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
            
            # Report progress
            if progress_callback:
                progress_callback(idx + 1, total)
        
        return results
