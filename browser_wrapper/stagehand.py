# Copyright (c) 2025 Browserbase, Inc.
# Licensed under the MIT License.

import asyncio
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from playwright.async_api import (
    BrowserContext,
    Playwright,
)

from .browser_types import StagehandNotInitializedError, BrowserResult

from typing import TYPE_CHECKING

from .utils import get_browser
from .utils.browser import cleanup_browser_resources

if TYPE_CHECKING:
    from .stagehand_context import StagehandContext
    from .stagehand_page import StagehandPage

from browser_common.browser_logging import get_logger
logger = get_logger("browser_wrapper.hand", enable_file_logging=False)

load_dotenv()

class LivePageProxy:
    """
    A proxy object that dynamically delegates all operations to the current active page.
    This mimics the behavior of the JavaScript Proxy in the original implementation.
    """

    def __init__(self, stagehand_instance):
        # Use object.__setattr__ to avoid infinite recursion
        object.__setattr__(self, "_stagehand", stagehand_instance)

    async def _ensure_page_stability(self):
        """Wait for any pending page switches to complete"""
        if hasattr(self._stagehand, "_page_switch_lock"):
            try:
                # Use wait_for for Python 3.10 compatibility (timeout prevents indefinite blocking)
                async def acquire_lock():
                    async with self._stagehand._page_switch_lock:
                        pass  # Just wait for any ongoing switches

                await asyncio.wait_for(acquire_lock(), timeout=30)
            except asyncio.TimeoutError:
                # Log the timeout and raise to let caller handle it
                logger.error(
                        "Timeout waiting for page stability lock", category="live_proxy")
                raise RuntimeError from asyncio.TimeoutError(
                    "Page stability lock timeout - possible deadlock detected"
                )

    def __getattr__(self, name):
        """Delegate all attribute access to the current active page."""
        stagehand = object.__getattribute__(self, "_stagehand")

        # Get the current page
        if hasattr(stagehand, "_stagehand_page") and stagehand._stagehand_page:
            page = stagehand._stagehand_page
        else:
            raise RuntimeError("No active page available")

        # For async operations, make them wait for stability
        attr = getattr(page, name)
        if callable(attr) and asyncio.iscoroutinefunction(attr):
            # Don't wait for stability on navigation methods
            if name in ["goto", "reload", "go_back", "go_forward"]:
                return attr

            async def wrapped(*args, **kwargs):
                await self._ensure_page_stability()
                return await attr(*args, **kwargs)

            return wrapped
        return attr

    def __setattr__(self, name, value):
        """Delegate all attribute setting to the current active page."""
        if name.startswith("_"):
            # Internal attributes are set on the proxy itself
            object.__setattr__(self, name, value)
        else:
            stagehand = object.__getattribute__(self, "_stagehand")

            # Get the current page
            if hasattr(stagehand, "_page") and stagehand._page:
                page = stagehand._page
            else:
                raise RuntimeError("No active page available")

            # Set the attribute on the page
            setattr(page, name, value)

    def __dir__(self):
        """Return attributes of the current active page."""
        stagehand = object.__getattribute__(self, "_stagehand")

        if hasattr(stagehand, "_page") and stagehand._page:
            page = stagehand._page
        else:
            return []

        return dir(page)

    def __repr__(self):
        """Return representation of the current active page."""
        stagehand = object.__getattribute__(self, "_stagehand")

        if hasattr(stagehand, "_page") and stagehand._page:
            return f"<LivePageProxy -> {repr(stagehand._page)}>"
        else:
            return "<LivePageProxy -> No active page>"


class Stagehand:
    """
    Main Stagehand class.
    """

    _session_locks = {}
    _cleanup_called = False

    def __init__(
        self,
        **config_overrides,
    ):
        """
        Initialize the Stagehand client.

        Args:
            config (Optional[StagehandConfig]): Configuration object. If not provided, uses default_config.
            **config_overrides: Additional configuration overrides to apply to the config.
        """

        self.dom_settle_timeout_ms = 3000

        self.local_browser_launch_options = ({})

        # Handle browserbase session create params

        # Handle streaming response setting
        self.streamed_response = True

        self._local_user_data_dir_temp: Optional[Path] = (
            None  # To store path if created temporarily
        )

        # Register signal handlers for graceful shutdown
        self._register_signal_handlers()

        self._playwright: Optional[Playwright] = None
        self._browser = None
        self._pw_context: Optional[BrowserContext] = None
        self._page: Optional["StagehandPage"] = None
        self._stagehand_context: Optional["StagehandContext"] = None
        self.use_api = False
        self._initialized = False  # Flag to track if init() has run
        self._closed = False  # Flag to track if resources have been closed
        self._live_page_proxy = None  # Live page proxy
        self._page_switch_lock = asyncio.Lock()  # Lock for page stability
        self._session_id: Optional[str] = None
        self._context_path: Optional[str] = None
        self._headless: bool = False

    @property
    def page(self) -> Optional["StagehandPage"]:
        """
        Get the current active page. This property returns a live proxy that
        always points to the currently focused page when multiple tabs are open.

        Returns:
            A LivePageProxy that delegates to the active StagehandPage or None if not initialized
        """
        if not self._initialized:
            return None

        # Create the live page proxy if it doesn't exist
        if not self._live_page_proxy:
            self._live_page_proxy = LivePageProxy(self)

        return self._live_page_proxy
    # TODO: This code should not be needed after translation
    """Get the current page proxy"""
    # if not self._stagehand_context:
    #     raise StagehandNotInitializedError("stagehandContext")
    # if not self._live_page_proxy:
    #     self._live_page_proxy = self._create_live_page_proxy()
    # return self._live_page_proxy

    @property
    def context(self) -> BrowserContext:
        """Get the browser context"""
        if not self._stagehand_context:
            raise StagehandNotInitializedError("stagehandContext")
        return self._stagehand_context.context

    @property
    def is_closed(self) -> bool:
        """Check if stagehand is closed"""
        return self._closed

    @property
    def downloads_path(self) -> str:
        """Get downloads path"""
        return str(Path.cwd() / "downloads")

    def _create_live_page_proxy(self) :
        """Create a live page proxy that delegates to StagehandPage"""
        if not self._stagehand_page:
            raise StagehandNotInitializedError("stagehandPage")

        # Create a proxy that delegates method calls to StagehandPage
        class PageProxy:
            def __init__(self, stagehand_page: "StagehandPage"):
                self._stagehand_page = stagehand_page

            def __getattr__(self, name: str):
                # First check if the property exists on the StagehandPage
                if hasattr(self._stagehand_page, name):
                    value = getattr(self._stagehand_page, name)
                    if callable(value):
                        return value
                    return value

                # Otherwise, get it from the Playwright page
                return getattr(self._stagehand_page.page, name)

            def __setattr__(self, name: str, value: Any) -> None:
                if name.startswith("_"):
                    super().__setattr__(name, value)
                    return

                # First try to set on StagehandPage
                if hasattr(self._stagehand_page, name):
                    setattr(self._stagehand_page, name, value)
                    return

                # Otherwise, set on the Playwright page
                setattr(self._stagehand_page.page, name, value)

        return PageProxy(self._stagehand_page) # type: ignore

    def _set_active_page(self, stagehand_page: "StagehandPage") -> None:
        """
        Internal method called by StagehandContext to update the active page.

        Args:
            stagehand_page: The StagehandPage to set as active
        """
        self._page = stagehand_page

    def _register_signal_handlers(self):
        """Register signal handlers for SIGINT and SIGTERM to ensure proper cleanup."""

        def cleanup_handler(sig, frame):
            # Prevent multiple cleanup calls
            if self.__class__._cleanup_called:
                return

            self.__class__._cleanup_called = True
            print(
                f"\n[{signal.Signals(sig).name}] received. Ending Browserbase session..."
            )

            try:
                # Try to get the current event loop
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No event loop running - create one to run cleanup
                    print("No event loop running, creating one for cleanup...")
                    try:
                        asyncio.run(self._async_cleanup())
                    except Exception as e:
                        print(f"Error during cleanup: {str(e)}")
                    finally:
                        sys.exit(0)

                # Schedule cleanup in the existing event loop
                # Use call_soon_threadsafe since signal handlers run in a different thread context
                def schedule_cleanup():
                    task = asyncio.create_task(self._async_cleanup())
                    # Shield the task to prevent it from being cancelled
                    asyncio.shield(task)
                    # We don't need to await here since we're in call_soon_threadsafe

                loop.call_soon_threadsafe(schedule_cleanup)

            except Exception as e:
                print(f"Error during signal cleanup: {str(e)}")
                sys.exit(1)

        # Register signal handlers
        signal.signal(signal.SIGINT, cleanup_handler)
        signal.signal(signal.SIGTERM, cleanup_handler)

    async def _async_cleanup(self):
        """Async cleanup method called from signal handler."""
        try:
            await self.close()
            print(f"Session {self.session_id} ended successfully")
        except Exception as e:
            print(f"Error ending Browserbase session: {str(e)}")
        finally:
            # Force exit after cleanup completes (or fails)
            # Use os._exit to avoid any further Python cleanup that might hang
            os._exit(0)

    def start_inference_timer(self):
        """Start timer for tracking inference time."""
        self._inference_start_time = time.time()

    def get_inference_time_ms(self) -> int:
        """Get elapsed inference time in milliseconds."""
        if self._inference_start_time == 0:
            return 0
        return int((time.time() - self._inference_start_time) * 1000)

    def _get_lock_for_session(self) -> asyncio.Lock:
        """
        Return an asyncio.Lock for this session. If one doesn't exist yet, create it.
        """
        if self.session_id not in self._session_locks:
            self._session_locks[self.session_id] = asyncio.Lock()
        return self._session_locks[self.session_id]

    async def __aenter__(self):
        logger.debug("Entering Stagehand context manager (__aenter__)...")
        # Just call init() if not already done
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.debug("Exiting Stagehand context manager (__aexit__)...")
        await self.close()

    async def init(self):
        """
        Public init() method.
        For BROWSERBASE: Creates or resumes the server session, starts Playwright, connects to remote browser.
        For LOCAL: Starts Playwright, launches a local persistent context or connects via CDP.
        Sets up self.page in both cases.
        """
        if self._initialized:
            logger.debug("Stagehand is already initialized; skipping init()")
            return {}

        """Initialize Stagehand"""
        try:
            browser_result = await get_browser(self._headless)
        except Exception as e:
            print(f"Error getting browser: {e}")
            # Create a fallback browser result
            browser_result: BrowserResult = {
                "browser": None,
                "context": None,  # type: ignore
                "debug_url": None,
                "session_url": None,
                "session_id": None,
            }

        self._context_path = browser_result.get("context_path")
        self._browser = browser_result.get("browser")

        context = browser_result.get("context")
        if not context:
            print("Context is None, trying to create a new one...")
            # Try to create a new context
            from playwright.async_api import async_playwright
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=self._headless)
            context = await browser.new_context()
            browser_result["context"] = context
            browser_result["browser"] = browser

        from .stagehand_context import StagehandContext
        self._stagehand_context = await StagehandContext.init(context, self)

        # Get existing pages or create a new one
        pages = await self._stagehand_context.get_stagehand_pages()
        if pages:
            self._stagehand_page = pages[0]
        else:
            # Create a new page if none exist
            new_page = await context.new_page()
            self._stagehand_page = await self._stagehand_context._create_stagehand_page(new_page)

        if self._headless:
            await self.page.set_viewport_size({"width": 1024, "height": 768})

        # Add initialization script
        script_content = self._get_script_content()
        guarded_script = f"""
                if (!window.__stagehandInjected) {{
                    window.__stagehandInjected = true;
                    {script_content}
                }}
                """

        await self.context.add_init_script(guarded_script)

        # Set up download behavior
        session = await self.context.new_cdp_session(self._stagehand_page._page)
        await session.send("Browser.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": self.downloads_path,
            "eventsEnabled": True,
        })

        self._session_id = browser_result.get("session_id")

        self._initialized = True
        return {
            "debug_url": browser_result.get("debug_url"),
            "session_url": browser_result.get("session_url"),
            "session_id": self._session_id,
        }

    async def close(self):
        """
        Clean up resources.
        Closes the local context, stops Playwright, and removes temporary directories.
        """
        if self._closed:
            return

        logger.debug("Closing resources...")
        # Use the centralized cleanup function for browser resources
        await cleanup_browser_resources(
            self._browser,
            self._pw_context,
            self._playwright,
            self._local_user_data_dir_temp,
        )

        self._closed = True

    def _get_script_content(self) -> str:
        """Get the injected script content"""
        from .dom.script_content import SCRIPT_CONTENT
        return SCRIPT_CONTENT

    def __getattribute__(self, name):
        """
        Intercept access to 'metrics' to fetch from API when use_api=True.
        """
        if name == "metric":
            pass

        # For all other attributes, use normal behavior
        return object.__getattribute__(self, name)

