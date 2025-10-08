# Copyright (c) 2025 Browserbase, Inc.
# Licensed under the MIT License.

"""
Browser Wrapper - A Python wrapper for browser automation with Playwright and Stagehand.

This package provides high-level browser automation capabilities including:
- Page navigation and interaction
- Context management across multiple pages
- Integration with Stagehand server for enhanced capabilities

Main Components:
- Stagehand: Main browser automation class
- StagehandContext: Manages browser contexts and page instances
- StagehandPage: Wrapper around Playwright Page with additional features
- LivePageProxy: Dynamic proxy for current active page operations
"""

from .stagehand import Stagehand, LivePageProxy
from .stagehand_context import StagehandContext
from .stagehand_page import StagehandPage
from .version import STAGEHAND_VERSION

# Main exports
__all__ = [
    "Stagehand",
    "StagehandContext", 
    "StagehandPage",
    "LivePageProxy",
    "STAGEHAND_VERSION",
]

# Version info
__version__ = STAGEHAND_VERSION
