"""
Utility functions for the application.
"""

import os
import uuid
from typing import Optional
from werkzeug.utils import secure_filename


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename while preserving the original extension.
    
    Args:
        original_filename: The original uploaded filename
        
    Returns:
        A unique filename with the same extension
    """
    ext = os.path.splitext(original_filename)[1].lower()
    unique_id = uuid.uuid4().hex
    return f"{unique_id}{ext}"


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Check if a file has an allowed extension.
    
    Args:
        filename: The filename to check
        allowed_extensions: Set of allowed extensions
        
    Returns:
        True if allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, upload_folder: str, allowed_extensions: set) -> Optional[str]:
    """
    Save an uploaded file securely.
    
    Args:
        file: The uploaded file object
        upload_folder: Directory to save the file
        allowed_extensions: Set of allowed extensions
        
    Returns:
        Path to saved file or None if failed
    """
    if file.filename == '':
        return None
    
    if not allowed_file(file.filename, allowed_extensions):
        return None
    
    # Create upload folder if it doesn't exist
    os.makedirs(upload_folder, exist_ok=True)
    
    # Generate unique filename
    filename = generate_unique_filename(secure_filename(file.filename))
    filepath = os.path.join(upload_folder, filename)
    
    try:
        file.save(filepath)
        return filepath
    except Exception as e:
        print(f"Error saving file: {e}")
        return None


def format_accuracy(accuracy: float) -> str:
    """Format accuracy as percentage string."""
    return f"{accuracy * 100:.2f}%"


def truncate_string(s: str, max_length: int = 50) -> str:
    """Truncate string to max length with ellipsis."""
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."
