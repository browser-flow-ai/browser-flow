"""
Type definitions for the browser wrapper
"""

from typing import Dict, List, Optional, Union, Any, Protocol, TypedDict, Literal
from playwright.async_api import Browser, BrowserContext, Page, Frame
from .context import A11Result, EnhancedContext, EncodedId

# Type aliases (re-exported from context)
FrameId = str
LoaderId = str

class BrowserResult(TypedDict, total=False):
    """Browser initialization result"""
    browser: Optional[Browser]
    context: BrowserContext
    debug_url: Optional[str]
    session_url: Optional[str]
    context_path: Optional[str]
    session_id: Optional[str]

class GotoOptions(TypedDict, total=False):
    """Options for page navigation"""
    timeout: Optional[int]
    wait_until: Optional[Literal['load', 'domcontentloaded', 'networkidle', 'commit']]
    referer: Optional[str]
    frame_id: Optional[str]

# Re-export Playwright types
PlaywrightPage = Page
PlaywrightBrowser = Browser
PlaywrightBrowserContext = BrowserContext
