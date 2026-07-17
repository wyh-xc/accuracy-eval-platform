"""
应用程序的工具函数模块。
"""

import os
import uuid
from typing import Optional
from werkzeug.utils import secure_filename


def generate_unique_filename(original_filename: str) -> str:
    """
    生成唯一文件名，同时保留原始扩展名。
    
    参数:
        original_filename: 原始上传的文件名
        
    返回:
        具有相同扩展名的唯一文件名
    """
    ext = os.path.splitext(original_filename)[1].lower()
    unique_id = uuid.uuid4().hex
    return f"{unique_id}{ext}"


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    检查文件是否具有允许的扩展名。
    
    参数:
        filename: 要检查的文件名
        allowed_extensions: 允许的扩展名集合
        
    返回:
        如果允许返回 True，否则返回 False
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, upload_folder: str, allowed_extensions: set) -> Optional[str]:
    """
    安全地保存上传的文件。
    
    参数:
        file: 上传的文件对象
        upload_folder: 保存文件的目录
        allowed_extensions: 允许的扩展名集合
        
    返回:
        保存文件的路径，如果失败则返回 None
    """
    if file.filename == '':
        return None
    
    if not allowed_file(file.filename, allowed_extensions):
        return None
    
    # 如果上传文件夹不存在则创建
    os.makedirs(upload_folder, exist_ok=True)
    
    # 生成唯一文件名
    filename = generate_unique_filename(secure_filename(file.filename))
    filepath = os.path.join(upload_folder, filename)
    
    try:
        file.save(filepath)
        return filepath
    except Exception as e:
        print(f"保存文件时出错：{e}")
        return None


def format_accuracy(accuracy: float) -> str:
    """将准确率格式化为百分比字符串。"""
    return f"{accuracy * 100:.2f}%"


def truncate_string(s: str, max_length: int = 50) -> str:
    """将字符串截断为最大长度并添加省略号。"""
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."
