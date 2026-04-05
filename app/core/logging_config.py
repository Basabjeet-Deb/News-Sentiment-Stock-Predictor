"""
Logging configuration
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import os


def setup_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """
    Configure application logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Get log level from environment or parameter
    level = getattr(logging, os.getenv("LOG_LEVEL", log_level).upper())
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    
    # Fi