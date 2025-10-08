# Copyright (c) 2025 Browserbase, Inc.
# Licensed under the MIT License.

import asyncio
import weakref
from playwright.async_api import BrowserContext, Page, CDPSession

from typing import TYPE_CHECKING, Optional, Dict, MutableMapping

if TYPE_CHECKING:
    from .stagehand import Stagehand
    from .stagehand_page import StagehandPage

from browser_common.browser_logging import get_logger
logger = get_logger("browser_wrapper.context", enable_file_logging=False)

class StagehandContext:
    def __init__(self, context: BrowserContext, stagehand: "Stagehand"):
        self.stagehand = stagehand
        self._int_context = context
        # self._context = context

        # Use a weak key dictionary to map Playwright Pages to our StagehandPage wrappers
        self._page_map:MutableMapping[Page, "StagehandPage"] = weakref.WeakKeyDictionary()
        self._active_stagehand_page: Optional["StagehandPage"] = None
        # Map frame IDs to StagehandPage instances
        self._frame_id_map: Dict[str, "StagehandPage"] = {}

    def __getattr__(self, name):
        # Forward attribute lookups to the underlying BrowserContext
        attr = getattr(self._int_context, name)

        # Special handling for methods that return pages
        if name == "new_page":
            # Replace with our own implementation that wraps the page
            async def wrapped_new_page(*args, **kwargs):
                pw_page = await self._int_context.new_page(*args, **kwargs)
                stagehand_page = await self._create_stagehand_page(pw_page)
                self._set_active_page(stagehand_page)
                return stagehand_page

            return wrapped_new_page
        elif name == "pages":

            async def wrapped_pages():
                pw_pages = self._int_context.pages
                # Return StagehandPage objects
                result = []
                for pw_page in pw_pages:
                    stagehand_page = await self.get_stagehand_page(pw_page)
                    result.append(stagehand_page)
                return result

            return wrapped_pages
        return attr

    @classmethod
    async def init(cls, context: BrowserContext, stagehand: "Stagehand"):
        instance = cls(context, stagehand)
        # Pre-initialize StagehandPages for any existing pages
        logger.debug(
            f"Found {len(instance._int_context.pages)} existing pages", category="context"
        )

        for pw_page in context.pages:
            stagehand_page = await instance._create_stagehand_page(pw_page)

        # Set the first page as active
        if instance._int_context.pages:
            first_page = instance._int_context.pages[0]
            stagehand_page = await instance.get_stagehand_page(first_page)
            instance._set_active_page(stagehand_page)

        # Set up page event handler
        async def handle_page_event(page: Page):
            try:
                asyncio.create_task(instance._handle_new_page(pw_page))
            except Exception as err:
                logger.error(f"Failed to attach frameNavigated listener: {err}")
            finally:
                try:
                    await instance._handle_new_playwright_page(page)
                except Exception as err:
                    logger.error(f"Failed to initialise new page: {err}")

        context.on("page", handle_page_event)

        return instance

    async def _create_stagehand_page(self, pw_page: Page) -> "StagehandPage":
        # Create a StagehandPage wrapper for the given Playwright page
        from .stagehand_page import StagehandPage
        stagehand_page = await StagehandPage(pw_page, self.stagehand, self).init()
        # await self.inject_custom_scripts(pw_page)
        self._page_map[pw_page] = stagehand_page
        # Initialize frame tracking for this page
        await self._attach_frame_navigated_listener(pw_page)
        return stagehand_page

    async def _handle_new_playwright_page(self, pw_page: Page) -> None:
        """Handle new Playwright page creation"""
        stagehand_page = self._page_map.get(pw_page)
        if not stagehand_page:
            stagehand_page = await self._create_stagehand_page(pw_page)
        self._set_active_page(stagehand_page)
        await self._attach_frame_navigated_listener(pw_page)

    def _set_active_page(self, stagehand_page: "StagehandPage"):
        self._active_stagehand_page = stagehand_page
        # Update the active page in the stagehand client
        # Update the active page in the stagehand client
        if hasattr(self.stagehand, "_set_active_page"):
            self.stagehand._set_active_page(stagehand_page)
            logger.debug(
                f"Set active page to: {stagehand_page.url}", category="context"
            )
        else:
            logger.debug(
                "Stagehand does not have _set_active_page method", category="context"
            )

    async def new_page(self) -> "StagehandPage":
        pw_page: Page = await self._int_context.new_page()
        stagehand_page = await self._create_stagehand_page(pw_page)
        self._set_active_page(stagehand_page)
        return stagehand_page

    async def get_stagehand_page(self, pw_page: Page) -> "StagehandPage":
        if pw_page not in self._page_map:
            return await self._create_stagehand_page(pw_page)
        stagehand_page = self._page_map[pw_page]
        return stagehand_page

    async def get_stagehand_pages(self) -> list:
        # Return a list of StagehandPage wrappers for all pages in the context
        pages = self._int_context.pages
        result = []
        for pw_page in pages:
            stagehand_page = await self.get_stagehand_page(pw_page)
            result.append(stagehand_page)
        return result

    @property
    def context(self) -> BrowserContext:
        """Get the browser context"""
        return self._int_context

    def register_frame_id(self, frame_id: str, page: "StagehandPage"):
        """Register a frame ID to StagehandPage mapping."""
        self._frame_id_map[frame_id] = page

    def unregister_frame_id(self, frame_id: str):
        """Unregister a frame ID from the mapping."""
        if frame_id in self._frame_id_map:
            del self._frame_id_map[frame_id]

    def get_active_page(self) -> "StagehandPage":
        return self._active_stagehand_page

    def get_stagehand_page_by_frame_id(self, frame_id: str) -> "StagehandPage":
        """Get StagehandPage by frame ID."""
        return self._frame_id_map.get(frame_id)

    async def _handle_new_page(self, pw_page: Page):
        """
        Handle new pages created by the browser (popups, window.open, etc.).
        Uses the page switch lock to prevent race conditions with ongoing operations.
        """
        try:
            # Use wait_for for Python 3.10 compatibility (timeout prevents indefinite blocking)
            async def handle_with_lock():
                async with self.stagehand._page_switch_lock:
                    logger.debug(
                        f"Creating StagehandPage for new page with URL: {pw_page.url}",
                        category="context",
                    )
                    stagehand_page = await self._create_stagehand_page(pw_page)
                    self._set_active_page(stagehand_page)
                    logger.debug(
                        "New page detected and initialized", category="context"
                    )

            await asyncio.wait_for(handle_with_lock(), timeout=30)
        except asyncio.TimeoutError:
            logger.error(
                f"Timeout waiting for page switch lock when handling new page: {pw_page.url}",
                category="context",
            )
        except Exception as e:
            logger.error(
                f"Failed to initialize new page: {str(e)}", category="context"
            )

    async def _attach_frame_navigated_listener(self, pw_page: Page) -> None:
        """
        Attach CDP listener for frame navigation events to track frame IDs.
        This mirrors the TypeScript implementation's frame tracking.
        """
        sh_page = self._page_map.get(pw_page)
        if not sh_page:
            return
        try:
            cdp_session: CDPSession = await self._int_context.new_cdp_session(pw_page)
            await cdp_session.send("Page.enable")

            # Get the current root frame ID
            frame_tree = await cdp_session.send("Page.getFrameTree")
            root_frame_id = frame_tree.get("frameTree", {}).get("frame", {}).get("id")

            if root_frame_id:
                # Initialize the page with its frame ID
                sh_page.update_root_frame_id(root_frame_id)
                self.register_frame_id(root_frame_id, sh_page)

            def on_close():
                if sh_page.frame_id:
                    self.unregister_frame_id(sh_page.frame_id)

            pw_page.once("close", on_close)

            def on_frame_navigated(params):
                """Handle Page.frameNavigated events"""
                frame = params.get("frame", {})
                frame_id = frame.get("id")
                parent_id = frame.get("parentId")

                # Only track root frames (no parent)
                if not parent_id and frame_id:
                    # Skip if it's the same frame ID
                    if frame_id == sh_page.frame_id:
                        return

                    # Unregister old frame ID if exists
                    old_id = sh_page.frame_id
                    if old_id:
                        self.unregister_frame_id(old_id)

                    # Register new frame ID
                    self.register_frame_id(frame_id, sh_page)
                    sh_page.update_root_frame_id(frame_id)

                    logger.debug(
                        f"Frame navigated from {old_id} to {frame_id}",
                        category="context",
                    )

                cdp_session.on("Page.frameNavigated", on_frame_navigated)
        except Exception as e:
            logger.error(
                f"Failed to attach frame navigation listener: {str(e)}",
                category="context",
            )