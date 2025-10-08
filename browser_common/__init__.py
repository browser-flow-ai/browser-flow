"""browser-common package - Browser common functionality module

This package provides common functionality for browser automation, including:
- Unified logging management system
- Browser control tools
- Common utility functions
"""

# Import logging management functionality
from .browser_logging import (
    BrowserCommonLogger,
    get_logger,
    get_cached_logger,
    JsonFormatter,
    setup_logging_from_config,
    LoggingConfig,
    setup_logging,
    get_config
)

# Import LLM functionality
from .llm import llm_qwen, llm_deepseek

# Version information
__version__ = "1.0.0"
__author__ = "BeamSearch Team"

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
    
    # *****important don't import llm module here*******
    # LLM module
    # "llm_qwen",
    # "llm_deepseek",
    
    # Version information
    "__version__",
    "__author__"
]
