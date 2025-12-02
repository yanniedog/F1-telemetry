"""
Comprehensive logging utility for F1 dataset operations.
Provides structured logging with file and console output.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class F1DatasetLogger:
    """Custom logger for F1 dataset operations."""
    
    def __init__(
        self,
        name: str = "f1_dataset",
        log_dir: str = "logs",
        log_level: int = logging.INFO,
        log_to_file: bool = True,
        log_to_console: bool = True
    ):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Whether to log to file
            log_to_console: Whether to log to console
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create log directory
        if log_to_file:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            
            # File handler with date-based filename
            log_file = log_path / f"f1_dataset_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            
            # File formatter
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            
            # Console formatter (simpler)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, **kwargs)


# Global logger instance
_logger_instance: Optional[F1DatasetLogger] = None


def get_logger(
    name: str = "f1_dataset",
    log_dir: str = "logs",
    log_level: int = logging.INFO
) -> F1DatasetLogger:
    """
    Get or create the global logger instance.
    
    Args:
        name: Logger name
        log_dir: Directory for log files
        log_level: Logging level
        
    Returns:
        F1DatasetLogger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = F1DatasetLogger(name, log_dir, log_level)
    return _logger_instance

