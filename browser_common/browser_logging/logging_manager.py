"""Unified logging manager - Provides logging functionality for browser-common package"""

import logging
import logging.config
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union
from contextlib import contextmanager


class BrowserCommonLogger:
    """Browser common logging manager"""
    
    def __init__(self, 
                 module_name: str,
                 level: str = "INFO",
                 log_dir: str = "logs",
                 enable_file_logging: bool = True,
                 enable_console_logging: bool = True,
                 enable_json_logging: bool = False,
                 session_id: Optional[str] = None):
        """
        Initialize logging manager
        
        Args:
            module_name: Module name
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Log file directory
            enable_file_logging: Whether to enable file logging
            enable_console_logging: Whether to enable console logging
            enable_json_logging: Whether to enable JSON format logging
            session_id: Session ID for distinguishing logs from different sessions
        """
        self.module_name = module_name
        self.session_id = session_id
        self.enable_json_logging = enable_json_logging
        
        # Create log directory
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Get log level from environment variable
        env_level = os.getenv("BROWSER_COMMON_LOG_LEVEL", level)
        
        self.logger = self._setup_logger(
            module_name, 
            env_level,
            enable_file_logging,
            enable_console_logging
        )
    
    def _setup_logger(self, name: str, level: str, 
                     file_logging: bool, console_logging: bool) -> logging.Logger:
        """Setup logger"""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create formatter
        if self.enable_json_logging:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Console handler
        if console_logging:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler
        if file_logging:
            log_file = self.log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        logger.propagate = False
        return logger
    
    def debug(self, message: str, **context):
        """Log debug message"""
        self._log(logging.DEBUG, message, context)
    
    def info(self, message: str, **context):
        """Log info message"""
        self._log(logging.INFO, message, context)
    
    def warning(self, message: str, **context):
        """Log warning message"""
        self._log(logging.WARNING, message, context)
    
    def error(self, message: str, **context):
        """Log error message"""
        self._log(logging.ERROR, message, context)
    
    def critical(self, message: str, **context):
        """Log critical error message"""
        self._log(logging.CRITICAL, message, context)
    
    def _log(self, level: int, message: str, context: Dict[str, Any]):
        """Internal logging method"""
        if self.enable_json_logging:
            # JSON format logging
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "level": logging.getLevelName(level),
                "module": self.module_name,
                "message": message,
                "session_id": self.session_id,
                "context": context
            }
            self.logger.log(level, json.dumps(log_data, ensure_ascii=False))
        else:
            # Text format logging
            if context:
                context_str = self._format_context(context)
                message = f"{message} | {context_str}"
            self.logger.log(level, message)
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information"""
        return " | ".join([f"{k}={v}" for k, v in context.items()])
    
    @contextmanager
    def log_execution_time(self, operation: str, **context):
        """Context manager for logging operation execution time"""
        start_time = datetime.now()
        self.info(f"Starting execution: {operation}", **context)
        
        try:
            yield
            execution_time = (datetime.now() - start_time).total_seconds()
            self.info(f"Completed execution: {operation}", 
                     execution_time=f"{execution_time:.2f}s", **context)
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.error(f"Execution failed: {operation}", 
                      error=str(e), 
                      execution_time=f"{execution_time:.2f}s", **context)
            raise


class JsonFormatter(logging.Formatter):
    """JSON format log formatter"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "thread": record.thread,
            "process": record.process
        }
        
        # Add exception information
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def get_logger(module_name: str, **kwargs) -> BrowserCommonLogger:
    """
    Get module logger
    
    Args:
        module_name: Module name
        **kwargs: Parameters passed to BrowserCommonLogger
        
    Returns:
        BrowserCommonLogger instance
    """
    return BrowserCommonLogger(module_name, **kwargs)


def setup_logging_from_config(config_path: str):
    """
    Setup logging from configuration file
    
    Args:
        config_path: Configuration file path
    """
    if os.path.exists(config_path):
        logging.config.fileConfig(config_path)
    else:
        # Use default configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


# Global logger instance cache
_logger_cache: Dict[str, BrowserCommonLogger] = {}


def get_cached_logger(module_name: str, **kwargs) -> BrowserCommonLogger:
    """
    Get cached logger instance
    
    Args:
        module_name: Module name
        **kwargs: Parameters passed to BrowserCommonLogger
        
    Returns:
        Cached BrowserCommonLogger instance
    """
    cache_key = f"{module_name}_{kwargs.get('session_id', 'default')}"
    
    if cache_key not in _logger_cache:
        _logger_cache[cache_key] = BrowserCommonLogger(module_name, **kwargs)
    
    return _logger_cache[cache_key]
