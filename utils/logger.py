"""
Logging utilities for Video Caption Generator
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console

console = Console()


def setup_logger(
    name: str = "video_caption_generator",
    level: str = "INFO",
    log_file: Optional[Path] = None,
    log_format: str = "detailed"
) -> logging.Logger:
    """
    Set up logger with Rich formatting
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        log_format: Format style ('simple' or 'detailed')
        
    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with Rich
    if log_format == "detailed":
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            rich_tracebacks=True
        )
    else:
        console_handler = RichHandler(
            console=console,
            show_time=False,
            show_path=False,
            rich_tracebacks=True
        )
    
    console_handler.setLevel(getattr(logging, level.upper()))
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        
        # File format
        if log_format == "detailed":
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
            )
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
        
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "video_caption_generator") -> logging.Logger:
    """Get or create a logger"""
    return logging.getLogger(name)