"""
File handler module for processing uploaded files (Excel, CSV).
"""

import pandas as pd
from typing import Optional, Dict, List, Any
from pathlib import Path


class FileHandler:
    """Handle file uploads and data extraction."""
    
    SUPPORTED_EXTENSIONS = ['.csv', '.xlsx', '.xls']
    
    @classmethod
    def read_file(cls, file_path: str) -> Optional[pd.DataFrame]:
        """
        Read a file and return its content as a DataFrame.
        
        Args:
            file_path: Path to the file
            
        Returns:
            pd.DataFrame or None if reading fails
        """
        try:
            path = Path(file_path)
            extension = path.suffix.lower()
            
            if extension == '.csv':
                # Try different encodings
                for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        return df
                    except UnicodeDecodeError:
                        continue
                raise ValueError("Unable to decode CSV file with supported encodings")
            elif extension in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                return df
            else:
                raise ValueError(f"Unsupported file type: {extension}")
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
    
    @classmethod
    def get_columns(cls, file_path: str) -> List[str]:
        """
        Get column names from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of column names
        """
        df = cls.read_file(file_path)
        if df is not None:
            return df.columns.tolist()
        return []
    
    @classmethod
    def validate_columns(
        cls, 
        file_path: str, 
        required_columns: List[str]
    ) -> Dict[str, Any]:
        """
        Validate that required columns exist in the file.
        
        Args:
            file_path: Path to the file
            required_columns: List of required column names
            
        Returns:
            Dict with validation result and details
        """
        df = cls.read_file(file_path)
        if df is None:
            return {
                "valid": False,
                "error": "Failed to read file",
                "available_columns": []
            }
        
        available_columns = df.columns.tolist()
        missing_columns = [col for col in required_columns if col not in available_columns]
        
        if missing_columns:
            return {
                "valid": False,
                "error": f"Missing columns: {', '.join(missing_columns)}",
                "available_columns": available_columns
            }
        
        return {
            "valid": True,
            "error": None,
            "available_columns": available_columns,
            "row_count": len(df)
        }
    
    @classmethod
    def extract_data(
        cls, 
        file_path: str,
        input_column: str,
        expected_column: str,
        actual_column: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract relevant data from the file.
        
        Args:
            file_path: Path to the file
            input_column: Column containing input data
            expected_column: Column containing expected results
            actual_column: Column containing actual results (optional)
            
        Returns:
            List of dictionaries with extracted data
        """
        df = cls.read_file(file_path)
        if df is None:
            return []
        
        data = []
        for idx, row in df.iterrows():
            item = {
                "row_index": idx,
                "input": row.get(input_column),
                "expected": row.get(expected_column),
            }
            if actual_column:
                item["actual"] = row.get(actual_column)
            data.append(item)
        
        return data
