"""工具函数模块"""
import os
import logging
from pathlib import Path
from typing import List, Optional, Union
import hashlib
import time
from functools import wraps


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """设置日志器"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def ensure_dir(path: Union[str, Path]) -> Path:
    """确保目录存在"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_hash(file_path: Path) -> str:
    """获取文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_file_size(file_path: Path) -> int:
    """获取文件大小（字节）"""
    return file_path.stat().st_size


def is_video_file(file_path: Path) -> bool:
    """检查是否为支持的视频文件"""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
    return file_path.suffix.lower() in video_extensions


def get_video_files(directory: Path) -> List[Path]:
    """获取目录下所有视频文件"""
    video_files = []
    for file_path in directory.iterdir():
        if file_path.is_file() and is_video_file(file_path):
            video_files.append(file_path)
    return sorted(video_files)


def format_duration(seconds: float) -> str:
    """格式化时长为 HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def retry(max_attempts: int = 3, delay: float = 1.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (attempt + 1))
                    else:
                        raise last_exception
            return None
        return wrapper
    return decorator


def clean_filename(filename: str) -> str:
    """清理文件名中的非法字符"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def get_output_path(
    input_path: Path, 
    suffix: str, 
    output_dir: Optional[Path] = None
) -> Path:
    """生成输出文件路径"""
    if output_dir is None:
        output_dir = input_path.parent
    else:
        ensure_dir(output_dir)
    
    base_name = input_path.stem
    output_name = f"{base_name}{suffix}"
    return output_dir / output_name


def process_path_arguments(path_segments: tuple) -> Path:
    """处理可能被空格分割的路径参数
    
    Args:
        path_segments: 路径片段元组
        
    Returns:
        完整的路径对象
        
    Raises:
        click.BadParameter: 如果无法找到有效路径
    """
    import click
    
    if not path_segments:
        raise click.BadParameter("No path provided")
    
    # 如果只有一个片段，直接处理
    if len(path_segments) == 1:
        path = Path(path_segments[0])
        if path.exists():
            return path
        raise click.BadParameter(f"Path does not exist: {path}")
    
    # 尝试不同的拼接方式
    # 1. 直接用空格拼接所有片段
    full_path = " ".join(path_segments)
    path = Path(full_path)
    if path.exists():
        return path
    
    # 2. 处理可能的选项参数混入
    # 找到第一个以 -- 开头的参数位置
    path_parts = []
    for segment in path_segments:
        if segment.startswith('-'):
            break
        path_parts.append(segment)
    
    if path_parts:
        full_path = " ".join(path_parts)
        path = Path(full_path)
        if path.exists():
            return path
    
    # 3. 尝试处理转义的反斜杠（如果是从终端拖拽）
    # 将 "San\ Diego.mp4" 转换为 "San Diego.mp4"
    escaped_path = " ".join(path_segments).replace('\\ ', ' ')
    path = Path(escaped_path)
    if path.exists():
        return path
    
    # 如果都失败了，提供有用的错误信息
    attempted_path = " ".join(path_segments)
    raise click.BadParameter(
        f"Cannot find file: {attempted_path}\n"
        f"Please check the file path and try again."
    )