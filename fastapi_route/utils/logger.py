"""
Logging utilities with color support and different log levels.

This module provides a flexible logging system with:
- Colored output for better readability
- Configurable time format
- Production mode filtering (reduces noise)
- Singleton logger instance for consistent logging
- Support for both sync and async logging

The logger is designed to be configured once and used throughout the
application, with different behaviors in development vs production.
"""

import logging
import sys
from typing import Optional
from datetime import datetime
import os

# ANSI color codes for terminal output
COLORS = {
    'black': '\033[30m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',
    'bright_black': '\033[90m',
    'bright_red': '\033[91m',
    'bright_green': '\033[92m',
    'bright_yellow': '\033[93m',
    'bright_blue': '\033[94m',
    'bright_magenta': '\033[95m',
    'bright_cyan': '\033[96m',
    'bright_white': '\033[97m',
    'reset': '\033[0m',
}

# Map log levels to colors
LEVEL_COLORS = {
    'DEBUG': COLORS['bright_black'],
    'INFO': COLORS['bright_green'],
    'WARNING': COLORS['bright_yellow'],
    'ERROR': COLORS['bright_red'],
    'CRITICAL': COLORS['bright_red'],
}

# Default settings (can be overridden by config)
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_TIME_FORMAT = "[%Y-%m-%d %H:%M:%S]"
DEFAULT_USE_COLOR = True


class TimeFormatter(logging.Formatter):
    """
    Custom formatter that supports configurable time formats.
    
    This formatter allows the timestamp format to be customized at runtime,
    unlike the standard logging.Formatter which requires recompilation.
    """
    
    def __init__(self, fmt=None, datefmt=None, style='%', time_format=DEFAULT_TIME_FORMAT):
        super().__init__(fmt, datefmt, style)
        self.time_format = time_format
    
    def formatTime(self, record, datefmt=None):
        """
        Format the time component of the log record.
        
        Uses the configured time_format instead of the standard datefmt,
        allowing dynamic changes without recreating the formatter.
        """
        ct = datetime.fromtimestamp(record.created)
        return ct.strftime(self.time_format)


class ColoredFormatter(TimeFormatter):
    """
    Formatter that adds ANSI color codes to log levels.
    
    Colors are applied only to the level name (INFO, WARNING, etc.),
    making it easy to scan log output for important messages.
    """
    
    def format(self, record):
        levelname = record.levelname
        level_color = LEVEL_COLORS.get(levelname, COLORS['white'])
        
        message = super().format(record)
        colored_level = f"{level_color}{levelname}{COLORS['reset']}"
        message = message.replace(levelname, colored_level, 1)
        
        return message


class LoggerFilter(logging.Filter):
    """
    Filter that reduces log noise in production mode.
    
    In production mode, only WARNING and ERROR logs are shown,
    with the exception of a few important INFO messages like
    server startup and application built notifications.
    """
    
    def __init__(self, is_production: bool = False):
        self.is_production = is_production
    
    def filter(self, record):
        if self.is_production:
            # Only show WARNING and above in production
            if record.levelno < logging.WARNING:
                # Allow important INFO messages
                if record.levelno == logging.INFO:
                    msg = record.getMessage()
                    important_patterns = [
                        "Server running",
                        "Application built",
                        "Starting production server",
                        "Application starting up",
                        "Application shutting down",
                        "Registered.*routes",
                    ]
                    import re
                    for pattern in important_patterns:
                        if re.search(pattern, msg):
                            return True
                    return False
                return False
        return True


def setup_logger(name: str = "fastapi_route", is_production: bool = False, 
                 log_level: str = None, time_format: str = None, use_color: bool = None) -> logging.Logger:
    """
    Setup and return a configured logger instance.
    
    Args:
        name: Logger name (default: "fastapi_route")
        is_production: If True, reduces log verbosity
        log_level: Override default log level (e.g., "DEBUG", "INFO")
        time_format: Custom time format string (strftime format)
        use_color: Enable/disable colored output
    
    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    logger.handlers.clear()
    
    # Use provided values or defaults
    level = getattr(logging, (log_level or DEFAULT_LOG_LEVEL).upper(), logging.INFO)
    fmt = time_format or DEFAULT_TIME_FORMAT
    color = use_color if use_color is not None else DEFAULT_USE_COLOR
    
    logger.setLevel(level)
    
    # Console handler for stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if color:
        formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            time_format=fmt
        )
    else:
        formatter = TimeFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            time_format=fmt
        )
    
    console_handler.setFormatter(formatter)
    
    # Add production filter if needed
    if is_production:
        logger.addFilter(LoggerFilter(is_production=True))
    
    logger.addHandler(console_handler)
    
    return logger


class Logger:
    """
    Singleton wrapper for the application logger.
    
    This class ensures a single logger instance is used throughout the
    application. It supports dynamic reconfiguration (e.g., switching
    to production mode) without recreating the logger.
    
    Usage:
        from fastapi_route.utils.logger import logger
        
        logger.info("Application started")
        logger.error("Something went wrong", exc_info=True)
    
    The logger can be reconfigured at runtime:
        Logger.set_production_mode(True)  # Reduce log noise
    """
    
    _instance = None
    _is_production = False
    _log_level = None
    _time_format = None
    _use_color = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logger = setup_logger(
                is_production=cls._is_production,
                log_level=cls._log_level,
                time_format=cls._time_format,
                use_color=cls._use_color
            )
        return cls._instance
    
    @classmethod
    def configure(cls, log_level: str = None, time_format: str = None, 
                  use_color: bool = None, is_production: bool = False):
        """
        Configure logger settings before initialization.
        
        Call this before any logging occurs to set custom defaults.
        
        Args:
            log_level: Default log level (DEBUG, INFO, WARNING, ERROR)
            time_format: Custom time format for timestamps
            use_color: Enable/disable colored output
            is_production: Run in production mode (reduced noise)
        """
        cls._log_level = log_level
        cls._time_format = time_format
        cls._use_color = use_color
        cls._is_production = is_production
        if cls._instance:
            cls._instance.logger = setup_logger(
                is_production=is_production,
                log_level=log_level,
                time_format=time_format,
                use_color=use_color
            )
    
    @classmethod
    def set_production_mode(cls, is_production: bool):
        """
        Toggle production mode to reduce log noise.
        
        In production mode, only WARNING, ERROR, and a few important
        INFO messages are shown.
        
        Args:
            is_production: True for production mode, False for development
        """
        cls._is_production = is_production
        if cls._instance:
            cls._instance.logger = setup_logger(
                is_production=is_production,
                log_level=cls._log_level,
                time_format=cls._time_format,
                use_color=cls._use_color
            )
    
    # Logging methods that delegate to the underlying logger
    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)


# Create the singleton logger instance
logger = Logger()