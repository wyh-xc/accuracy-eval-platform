"""
文件处理模块，用于处理上传的文件（Excel、CSV）。
"""

import pandas as pd
from typing import Optional, Dict, List, Any
from pathlib import Path


class FileHandler:
    """处理文件上传和数据提取。"""
    
    SUPPORTED_EXTENSIONS = ['.csv', '.xlsx', '.xls']
    
    @classmethod
    def read_file(cls, file_path: str) -> Optional[pd.DataFrame]:
        """
        读取文件并将其内容作为 DataFrame 返回。
        
        参数:
            file_path: 文件路径
            
        返回:
            pd.DataFrame，如果读取失败则返回 None
        """
        try:
            path = Path(file_path)
            extension = path.suffix.lower()
            
            if extension == '.csv':
                # 尝试不同的编码
                for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        return df
                    except UnicodeDecodeError:
                        continue
                raise ValueError("无法使用支持的编码解码 CSV 文件")
            elif extension in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                return df
            else:
                raise ValueError(f"不支持的文件类型：{extension}")
        except Exception as e:
            print(f"读取文件时出错：{e}")
            return None
    
    @classmethod
    def get_columns(cls, file_path: str) -> List[str]:
        """
        从文件中获取列名。
        
        参数:
            file_path: 文件路径
            
        返回:
            列名列表
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
        验证文件中是否存在必需的列。
        
        参数:
            file_path: 文件路径
            required_columns: 必需的列名列表
            
        返回:
            包含验证结果和详细信息的字典
        """
        df = cls.read_file(file_path)
        if df is None:
            return {
                "valid": False,
                "error": "读取文件失败",
                "available_columns": []
            }
        
        available_columns = df.columns.tolist()
        missing_columns = [col for col in required_columns if col not in available_columns]
        
        if missing_columns:
            return {
                "valid": False,
                "error": f"缺少列：{', '.join(missing_columns)}",
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
        从文件中提取相关数据。
        
        参数:
            file_path: 文件路径
            input_column: 包含输入数据的列
            expected_column: 包含预期结果的列
            actual_column: 包含实际结果的列（可选）
            
        返回:
            包含提取数据的字典列表
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
