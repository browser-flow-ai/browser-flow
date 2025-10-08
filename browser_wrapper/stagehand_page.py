# Copyright (c) 2025 Browserbase, Inc.
# Licensed under the MIT License.

import asyncio
import time
from typing import Optional, Union, Dict, Any

from playwright.async_api import CDPSession, Page, Frame

from browser_common.browser_logging import get_logger
from .browser_types import StagehandDefaultError, GotoOptions
from .utils import get_current_root_frame_id, clear_overlays
from .dom.script_content import SCRIPT_CONTENT

logger = get_logger("browser_wrapper.page", enable_file_logging=False)

_INJECTION_SCRIPT = None

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .stagehand import Stagehand
    from .stagehand_context import StagehandContext

class StagehandPage:
    """Wrapper around Playwright Page that integrates with Stagehand server"""

    _cdp_client: Optional[CDPSession] = None

    def __init__(self, page: Page, stagehand: "Stagehand", context: "StagehandContext"=None):
        """
        Initialize a StagehandPage instance.

        Args:
            page (Page): The underlying Playwright page.
            stagehand: The client used to interface with the Stagehand server.
            context: The StagehandContext instance (optional).
        """
        self._page = page
        # self._int_page = page  # Will be replaced with proxy
        self._stagehand = stagehand
        self._int_context = context
        self._root_frame_id:str = ""
        self._cdp_clients: Dict[Union[Page, Frame], CDPSession] = {}
        self._fid_ordinals: Dict[Optional[str], int] = {None: 0}
        self._initialized: bool = False

    @property
    def frame_id(self) -> Optional[str]:
        """Get the current root frame ID."""
        return self._root_frame_id

    def update_root_frame_id(self, new_id: str):
        """Update the root frame ID."""
        self._root_frame_id = new_id
        logger.debug(f"Updated frame ID to {new_id}", category="page")

    @property
    def page(self) :
        """Get the enhanced page"""
        return self._page  # type: ignore

    @property
    def context(self) -> "StagehandContext":
        """Get the context"""
        return self._int_context

    def int_context(self) -> "StagehandContext":
        """Get the internal context"""
        return self._int_context

    async def init(self) -> "StagehandPage":
        """Initialize the page"""
        try:
            # Set up CDP session
            session = await self.get_cdp_client(self._page)
            await session.send("Page.enable")

            root_id = await get_current_root_frame_id(session)
            self.update_root_frame_id(root_id)
            self._int_context.register_frame_id(root_id, self)

            # Ensure backdoor and selector engine are ready
            await self._ensure_stagehand_selector_engine()

            self._initialized = True
            return self

        except Exception as err:
            raise StagehandDefaultError(err)

    def ordinal_for_frame_id(self, fid: Optional[str]) -> int:
        """Get ordinal for frame ID"""
        if fid is None:
            return 0

        cached = self._fid_ordinals.get(fid)
        if cached is not None:
            return cached

        next_ordinal = len(self._fid_ordinals)
        self._fid_ordinals[fid] = next_ordinal
        return next_ordinal

    def encode_with_frame_id(self, fid: Optional[str], backend_id: int) -> str:
        """Encode with frame ID"""
        return f"{self.ordinal_for_frame_id(fid)}-{backend_id}"

    def reset_frame_ordinals(self) -> None:
        """Reset frame ordinals"""
        self._fid_ordinals = {None: 0}

    async def _ensure_stagehand_script(self) -> None:
        """Ensure Stagehand script is injected"""
        try:
            injected = await self._page.evaluate("!!window.__stagehandInjected")
            if injected:
                return

            script_content = self._get_script_content()
            guarded_script = f"""
            if (!window.__stagehandInjected) {{
                window.__stagehandInjected = true;
                {script_content}
            }}
            """

            await self._page.add_init_script(guarded_script)
            await self._page.evaluate(guarded_script)
        except Exception as err:
            if not self._stagehand.is_closed:
                raise err

    async def _ensure_stagehand_selector_engine(self) -> None:
        """Register the custom selector engine"""
        # Skip selector engine registration for now
        # This is a simplified implementation
        pass

    async def get_cdp_client(self, target: Union[Page, Frame] = None) -> CDPSession:
        """Get CDP client for target"""
        if target is None:
            target = self.page

        cached = self._cdp_clients.get(target)
        if cached:
            return cached

        try:
            session = await self.context.context.new_cdp_session(target)
            self._cdp_clients[target] = session
            return session
        except Exception as err:
            if "does not have a separate CDP session" in str(err):
                # Fallback for same-process iframes
                root_session = await self.get_cdp_client(self._page)
                self._cdp_clients[target] = root_session
                return root_session
            raise err

    async def get_a11y_tree(self) -> Dict[str, Any]:
        """Get accessibility tree"""
        await self._wait_for_settled_dom()
        try:
            await clear_overlays(self.page)
        except Exception as e:
            # 如果clear_overlays失败，继续执行，不影响iframe处理
            print(f"[warning] clear_overlays failed: {e}")

        # Use real accessibility tree implementation (matching TypeScript logic)
        from .utils.a11y_utils import get_accessibility_tree_with_frames, get_accessibility_tree

        def custom_logger(log_line):
            category = log_line.get('category', 'unknown')
            message = log_line.get('message', '')
            print(f"[{category}] {message}")
            if 'auxiliary' in log_line and 'error' in log_line['auxiliary']:
                error_info = log_line['auxiliary']['error']
                if isinstance(error_info, dict):
                    print(f"  Error details: {error_info}")
                else:
                    print(f"  Error details: {error_info}")

        # Match TypeScript logic: iframes = true, experimental = false
        iframes = True
        experimental = False

        if iframes:
            # Use getAccessibilityTreeWithFrames (like TypeScript)
            result = await get_accessibility_tree_with_frames(experimental, self, custom_logger)
            return {
                "combinedTree": result.get("combinedTree", ""),
                "combinedXpathMap": result.get("combinedXpathMap", {}),
                "discoveredIframes": [],  # 与TypeScript版本保持一致
            }
        else:
            # Use getAccessibilityTree (like TypeScript)
            result = await get_accessibility_tree(experimental, self, custom_logger)
            return {
                "combinedTree": result.get("simplified", ""),
                "combinedXpathMap": result.get("xpathMap", {}),
                "combinedUrlMap": result.get("idToUrl", {}),
                "discoveredIframes": result.get("iframes", []),
            }

    async def _wait_for_settled_dom(self, timeout_ms: int = None):
        """
        Wait for the DOM to settle (stop changing) before proceeding.

        **Definition of "settled"**
          • No in-flight network requests (except WebSocket / Server-Sent-Events).
          • That idle state lasts for at least **500 ms** (the "quiet-window").

        **How it works**
          1. Subscribes to CDP Network and Page events for the main target and all
             out-of-process iframes (via `Target.setAutoAttach { flatten:true }`).
          2. Every time `Network.requestWillBeSent` fires, the request ID is added
             to an **`inflight`** set.
          3. When the request finishes—`loadingFinished`, `loadingFailed`,
             `requestServedFromCache`, or a *data:* response—the request ID is
             removed.
          4. *Document* requests are also mapped **frameId → requestId**; when
             `Page.frameStoppedLoading` fires the corresponding Document request is
             removed immediately (covers iframes whose network events never close).
          5. A **stalled-request sweep timer** runs every 500 ms. If a *Document*
             request has been open for ≥ 2 s it is forcibly removed; this prevents
             ad/analytics iframes from blocking the wait forever.
          6. When `inflight` becomes empty the helper starts a 500 ms timer.
             If no new request appears before the timer fires, the promise
             resolves → **DOM is considered settled**.
          7. A global guard (`timeoutMs` or `stagehand.domSettleTimeoutMs`,
             default ≈ 30 s) ensures we always resolve; if it fires we log how many
             requests were still outstanding.

        Args:
            timeout_ms (int, optional): Maximum time to wait in milliseconds.
                If None, uses the stagehand client's dom_settle_timeout_ms.
        """

        timeout = timeout_ms or getattr(self._stagehand, "dom_settle_timeout_ms", 30000)
        client = await self.get_cdp_client()

        # Check if document exists
        try:
            await self._page.title()
        except Exception:
            await self._page.wait_for_load_state("domcontentloaded")

        # Enable CDP domains
        await client.send("Network.enable")
        await client.send("Page.enable")
        await client.send(
            "Target.setAutoAttach",
            {
                "autoAttach": True,
                "waitForDebuggerOnStart": False,
                "flatten": True,
                "filter": [
                    {"type": "worker", "exclude": True},
                    {"type": "shared_worker", "exclude": True},
                ],
            },
        )

        # Set up tracking structures
        inflight = set()  # Set of request IDs
        meta = {}  # Dict of request ID -> {"url": str, "start": float}
        doc_by_frame = {}  # Dict of frame ID -> request ID

        # Event tracking
        quiet_timer = None
        stalled_request_sweep_task = None
        loop = asyncio.get_event_loop()
        done_event = asyncio.Event()

        def clear_quiet():
            nonlocal quiet_timer
            if quiet_timer:
                quiet_timer.cancel()
                quiet_timer = None

        def resolve_done():
            """Cleanup and mark as done"""
            clear_quiet()
            if stalled_request_sweep_task and not stalled_request_sweep_task.done():
                stalled_request_sweep_task.cancel()
            done_event.set()

        def maybe_quiet():
            """Start quiet timer if no requests are in flight"""
            nonlocal quiet_timer
            if len(inflight) == 0 and not quiet_timer:
                quiet_timer = loop.call_later(0.5, resolve_done)

        def finish_req(request_id: str):
            """Mark a request as finished"""
            if request_id not in inflight:
                return
            inflight.remove(request_id)
            meta.pop(request_id, None)
            # Remove from frame mapping
            for fid, rid in list(doc_by_frame.items()):
                if rid == request_id:
                    doc_by_frame.pop(fid)
            clear_quiet()
            maybe_quiet()

        # Event handlers
        def on_request(params):
            """Handle Network.requestWillBeSent"""
            if params.get("type") in ["WebSocket", "EventSource"]:
                return

            request_id = params["requestId"]
            inflight.add(request_id)
            meta[request_id] = {"url": params["request"]["url"], "start": time.time()}

            if params.get("type") == "Document" and params.get("frameId"):
                doc_by_frame[params["frameId"]] = request_id

            clear_quiet()

        def on_finish(params):
            """Handle Network.loadingFinished"""
            finish_req(params["requestId"])

        def on_failed(params):
            """Handle Network.loadingFailed"""
            finish_req(params["requestId"])

        def on_cached(params):
            """Handle Network.requestServedFromCache"""
            finish_req(params["requestId"])

        def on_data_url(params):
            """Handle Network.responseReceived for data: URLs"""
            if params.get("response", {}).get("url", "").startswith("data:"):
                finish_req(params["requestId"])

        def on_frame_stop(params):
            """Handle Page.frameStoppedLoading"""
            frame_id = params["frameId"]
            if frame_id in doc_by_frame:
                finish_req(doc_by_frame[frame_id])

        # Register event handlers
        client.on("Network.requestWillBeSent", on_request)
        client.on("Network.loadingFinished", on_finish)
        client.on("Network.loadingFailed", on_failed)
        client.on("Network.requestServedFromCache", on_cached)
        client.on("Network.responseReceived", on_data_url)
        client.on("Page.frameStoppedLoading", on_frame_stop)

        async def sweep_stalled_requests():
            """Remove stalled document requests after 2 seconds"""
            while not done_event.is_set():
                await asyncio.sleep(0.5)
                now = time.time()
                for request_id, request_meta in list(meta.items()):
                    if now - request_meta["start"] > 2.0:
                        inflight.discard(request_id)
                        meta.pop(request_id, None)
                        logger.debug(
                            "⏳ forcing completion of stalled iframe document",
                            auxiliary={"url": request_meta["url"][:120]},
                        )
                maybe_quiet()

        # Start stalled request sweeper
        stalled_request_sweep_task = asyncio.create_task(sweep_stalled_requests())

        # Set up timeout guard
        async def timeout_guard():
            await asyncio.sleep(timeout / 1000)
            if not done_event.is_set():
                if len(inflight) > 0:
                    logger.debug(
                        "⚠️ DOM-settle timeout reached – network requests still pending",
                        auxiliary={"count": len(inflight)},
                    )
                resolve_done()

        timeout_task = asyncio.create_task(timeout_guard())

        # Initial check
        maybe_quiet()

        try:
            # Wait for completion
            await done_event.wait()
        finally:
            # Cleanup
            client.remove_listener("Network.requestWillBeSent", on_request)
            client.remove_listener("Network.loadingFinished", on_finish)
            client.remove_listener("Network.loadingFailed", on_failed)
            client.remove_listener("Network.requestServedFromCache", on_cached)
            client.remove_listener("Network.responseReceived", on_data_url)
            client.remove_listener("Page.frameStoppedLoading", on_frame_stop)

            if quiet_timer:
                quiet_timer.cancel()
            if stalled_request_sweep_task and not stalled_request_sweep_task.done():
                stalled_request_sweep_task.cancel()
                try:
                    await stalled_request_sweep_task
                except asyncio.CancelledError:
                    pass
            if timeout_task and not timeout_task.done():
                timeout_task.cancel()
                try:
                    await timeout_task
                except asyncio.CancelledError:
                    pass

    async def send_cdp(self, method: str, params: Dict[str, Any] = None, target: Union[Page, Frame] = None) -> Any:
        """Send CDP command"""
        if params is None:
            params = {}
        if target is None:
            target = self.page

        client = await self.get_cdp_client(target)
        return await client.send(method, params)

    async def enable_cdp(self, domain: str, target: Union[Page, Frame] = None) -> None:
        """Enable CDP domain"""
        await self.send_cdp(f"{domain}.enable", {}, target)

    async def disable_cdp(self, domain: str, target: Union[Page, Frame] = None) -> None:
        """Disable CDP domain"""
        await self.send_cdp(f"{domain}.disable", {}, target)

    async def _handle_on_event(self, event: str, listener):
        """Handle event listeners"""
        if event == "popup":
            def popup_handler(page: Page):
                # This would create a new StagehandPage
                pass

            return self._page.on(event, popup_handler)
        return self._page.on(event, listener)

    async def _handle_goto(self, url: str, options: GotoOptions = None) -> None:
        """Handle page navigation"""
        if options is None:
            options = {}
        await self._page.goto(url, **options)
        await self._page.wait_for_load_state("domcontentloaded")
        await self._wait_for_settled_dom()

    async def _handle_screenshot(self, **options) -> bytes:
        """Handle screenshots with CDP"""
        cdp_options = {
            "format": options.get("type", "png"),
            "quality": options.get("quality"),
            "clip": options.get("clip"),
            "omitBackground": options.get("omit_background"),
            "fromSurface": True,
        }

        if options.get("full_page"):
            cdp_options["captureBeyondViewport"] = True

        data = await self.send_cdp("Page.captureScreenshot", cdp_options)
        import base64
        return base64.b64decode(data["data"])

    def _handle_evaluate_method(self, method_name: str):
        """Handle evaluate methods with script injection"""

        async def wrapper(*args, **kwargs):
            await self._ensure_stagehand_script()
            method = getattr(self._page, method_name)
            return await method(*args, **kwargs)

        return wrapper

    def _get_script_content(self) -> str:
        """Get the injected script content"""
        return SCRIPT_CONTENT



    # TODO raw stagehand python code
    async def goto(
        self,
        url: str,
        *,
        referer: Optional[str] = None,
        timeout: Optional[int] = None,
        wait_until: Optional[str] = None,
    ):
        """
        Navigate to URL using the Stagehand server.

        Args:
            url (str): The URL to navigate to.
            referer (Optional[str]): Optional referer URL.
            timeout (Optional[int]): Optional navigation timeout in milliseconds.
            wait_until (Optional[str]): Optional wait condition; one of ('load', 'domcontentloaded', 'networkidle', 'commit').

        Returns:
            The result from the Stagehand server's navigation execution.
        """
        await self._page.goto(
            url, referer=referer, timeout=timeout, wait_until=wait_until
        )
        await self._page.wait_for_load_state("domcontentloaded")
        await self._wait_for_settled_dom()
        return

    # Method to enable a specific CDP domain
    async def enable_cdp_domain(self, domain: str):
        """Enables a specific CDP domain."""
        try:
            await self.send_cdp(f"{domain}.enable")
        except Exception as e:
            logger.debug(f"Failed to enable CDP domain '{domain}': {e}")

    # Method to disable a specific CDP domain
    async def disable_cdp_domain(self, domain: str):
        """Disables a specific CDP domain."""
        try:
            await self.send_cdp(f"{domain}.disable")
        except Exception:
            # Ignore errors during disable, often happens during cleanup
            pass

    # Method to detach the persistent CDP client
    async def detach_cdp_client(self):
        """Detaches the persistent CDP client if it exists."""
        if self._cdp_client and self._cdp_client.is_connected():
            try:
                await self._cdp_client.detach()
                self._cdp_client = None
            except Exception as e:
                logger.debug(f"Error detaching CDP client: {e}")
        self._cdp_client = None

    # Forward other Page methods to underlying Playwright page
    # TODO: I Think this is not useable.
    def __getattr__(self, name):
        """
        Forward attribute lookups to the underlying Playwright page.

        Args:
            name (str): Name of the attribute to access.

        Returns:
            The attribute from the underlying Playwright page.
        """
        logger.debug(f"Getting attribute: {name}")

        if name == "on":
            return self._handle_on_event
        elif name == "screenshot":
            return self._handle_screenshot
        elif name in ["evaluate", "evaluateHandle", "$eval", "$$eval"]:
            return self._handle_evaluate_method(name)

        return getattr(self._page, name)

    def __setattr__(self, name: str, value: Any) -> None:
        logger.debug(f"Setting attribute: {name}")

        if name.startswith("_"):
            super().__setattr__(name, value)
            return
        setattr(self._page, name, value)