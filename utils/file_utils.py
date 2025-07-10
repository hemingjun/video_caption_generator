"""
File utility functions for Video Caption Generator
"""
import os
import shutil
from pathlib import Path
from typing import List, Optional, Union
import tempfile


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if not
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """
    Get file size in megabytes
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in MB
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return 0.0
    
    size_bytes = file_path.stat().st_size
    return size_bytes / (1024 * 1024)


def cleanup_temp_files(
    temp_dir: Union[str, Path],
    patterns: Optional[List[str]] = None,
    older_than_hours: Optional[int] = None
) -> int:
    """
    Clean up temporary files
    
    Args:
        temp_dir: Temporary directory
        patterns: File patterns to clean (e.g., ['*.wav', '*.tmp'])
        older_than_hours: Only delete files older than this
        
    Returns:
        Number of files deleted
    """
    temp_dir = Path(temp_dir)
    if not temp_dir.exists():
        return 0
    
    if patterns is None:
        patterns = ['*.wav', '*.tmp', '*_temp*']
    
    deleted_count = 0
    
    for pattern in patterns:
        for file_path in temp_dir.glob(pattern):
            if file_path.is_file():
                # Check age if specified
                if older_than_hours:
                    import time
                    file_age_hours = (time.time() - file_path.stat().st_mtime) / 3600
                    if file_age_hours < older_than_hours:
                        continue
                
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception:
                    pass
    
    return deleted_count


def get_safe_filename(filename: str) -> str:
    """
    Get a safe filename by removing/replacing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    # Remove path separators and other invalid characters
    invalid_chars = '<>:"|?*\\/\r\n'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = 'unnamed'
    
    return filename


def create_temp_dir(prefix: str = "vcg_") -> Path:
    """
    Create a temporary directory
    
    Args:
        prefix: Directory prefix
        
    Returns:
        Path to temporary directory
    """
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
    return temp_dir


def copy_file_with_progress(
    src: Union[str, Path],
    dst: Union[str, Path],
    chunk_size: int = 1024 * 1024  # 1MB chunks
) -> Path:
    """
    Copy file with progress tracking
    
    Args:
        src: Source file path
        dst: Destination file path
        chunk_size: Copy chunk size
        
    Returns:
        Destination path
    """
    src = Path(src)
    dst = Path(dst)
    
    # Ensure destination directory exists
    dst.parent.mkdir(parents=True, exist_ok=True)
    
    total_size = src.stat().st_size
    
    with open(src, 'rb') as fsrc:
        with open(dst, 'wb') as fdst:
            copied = 0
            while True:
                chunk = fsrc.read(chunk_size)
                if not chunk:
                    break
                fdst.write(chunk)
                copied += len(chunk)
    
    return dst


def get_unique_filename(
    directory: Union[str, Path],
    base_name: str,
    extension: str
) -> Path:
    """
    Get a unique filename by appending numbers if file exists
    
    Args:
        directory: Target directory
        base_name: Base filename without extension
        extension: File extension (with or without dot)
        
    Returns:
        Unique file path
    """
    directory = Path(directory)
    
    # Ensure extension starts with dot
    if not extension.startswith('.'):
        extension = f'.{extension}'
    
    # Try original name first
    file_path = directory / f"{base_name}{extension}"
    if not file_path.exists():
        return file_path
    
    # Add numbers until we find a unique name
    counter = 1
    while True:
        file_path = directory / f"{base_name}_{counter}{extension}"
        if not file_path.exists():
            return file_path
        counter += 1


def estimate_processing_time(
    file_size_mb: float,
    has_gpu: bool = False
) -> float:
    """
    Estimate processing time based on file size
    
    Args:
        file_size_mb: File size in megabytes
        has_gpu: Whether GPU is available
        
    Returns:
        Estimated time in seconds
    """
    # Rough estimates based on testing
    # These are very approximate and depend on many factors
    if has_gpu:
        # GPU: ~1 minute per 100MB
        time_per_mb = 0.6
    else:
        # CPU: ~3 minutes per 100MB
        time_per_mb = 1.8
    
    return file_size_mb * time_per_mb