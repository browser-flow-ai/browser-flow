"""browser-common logging management module

This module provides unified logging management functionality, including:
- Logging manager (BrowserCommonLogger)
- Logging configuration management (LoggingConfig)
- Utility functions and factory methods
"""

# Import logging management functionality
from .logging_manager import (
    BrowserCommonLogger,
    get_logger,
    get_cached_logger,
    JsonFormatter,
    setup_logging_from_config
)

from .logging_config import (
    LoggingConfig,
    setup_logging,
    get_config
)

# Version information
__version__ = "1.0.0"

# Export main functionality
__all__ = [
    # Logging manager
    "BrowserCommonLogger",
    "get_logger", 
    "get_cached_logger",
    "JsonFormatter",
    "setup_logging_from_config",
    
    # Logging configuration
    "LoggingConfig",
    "setup_logging",
    "get_config",
    
    # Version information
    "__version__"
]
