# Copyright (c) 2025 Browserbase, Inc.
# Licensed under the MIT License.

"""Page method handlers for Playwright operations."""

import asyncio
from typing import Callable, Awaitable, TYPE_CHECKING

from typing import TYPE_CHECKING, Optional, Dict, MutableMapping

from playwright.async_api import Page

if TYPE_CHECKING:
    from browser_wrapper import StagehandPage

from browser_common.browser_logging import get_logger
logger = get_logger("browser_wrapper.page_methods", enable_file_logging=False)

from browser_control.browser_types import MethodHandlerContext

# Type alias for method handler function
MethodHandler = Callable[[MethodHandlerContext], Awaitable[None]]

async def click_element(ctx: MethodHandlerContext) -> None:
    """Click an element."""
    locator = ctx.locator
    dom_settle_timeout_ms = ctx.domSettleTimeoutMs

    try:
        # Try multiple click methods
        try:
            # Method 1: Direct JavaScript click
            await locator.evaluate("(el) => el.click()")
            logger.debug("JavaScript click executed successfully")
        except Exception as js_error:
            print(f"JavaScript click failed: {js_error}")
            try:
                # Method 2: Playwright native click, seems not working well.
                await locator.click(force=True, timeout=5000)
                logger.debug("Playwright force click executed successfully")
            except Exception as pw_error:
                logger.info(f"Playwright click failed: {pw_error}")
                # Method 3: Simulate mouse click
                await locator.hover()
                await locator.click(force=True, timeout=5000)
                logger.debug("Mouse simulation click executed successfully")

        # Wait for DOM to stabilize
        if dom_settle_timeout_ms:
            await asyncio.sleep(dom_settle_timeout_ms / 1000)
        else:
            # Default wait 3 seconds for page response
            await asyncio.sleep(3)
        await handle_possible_page_navigation(
            "click",
            ctx.xpath,
            "",
            ctx.stagehand_page,
            ctx.domSettleTimeoutMs,
        )
    except Exception as error:
        print(f"All click methods failed: {error}")
        if isinstance(error, Exception):
            raise error


async def fill_or_type(ctx: MethodHandlerContext) -> None:
    """Fill or type text into an element."""
    locator = ctx.locator
    args = ctx.args

    try:
        # Clear first, then fill
        await locator.fill("", force=True)
        text = str(args[0]) if args and args[0] is not None else ""
        await locator.fill(text, force=True)

        # Wait for DOM to stabilize
        if ctx.domSettleTimeoutMs:
            await asyncio.sleep(ctx.domSettleTimeoutMs / 1000)
    except Exception as error:
        if isinstance(error, Exception):
            pass
        raise error


async def press_key(ctx: MethodHandlerContext) -> None:
    """Press a key on an element."""
    locator = ctx.locator
    args = ctx.args
    key = str(args[0]) if args and args[0] is not None else ""

    try:
        await locator.press(key)
    except Exception as error:
        if isinstance(error, Exception):
            pass
        try:
            ey = str(ctx.args[0]) if ctx.args and ctx.args[0] is not None else ""
            await ctx.stagehand_page._page.keyboard.press(key)

            await handle_possible_page_navigation(
                "press key",
                ctx.xpath,
                "",
                ctx.stagehand_page,
                ctx.domSettleTimeoutMs,
            )
        except Exception as error:
            logger.error(f"Failed to press key: {error}")

async def scroll_element_into_view(ctx: MethodHandlerContext) -> None:
    """Scroll element into view."""
    locator = ctx.locator

    try:
        # await locator.scrollIntoViewIfNeeded();
        await locator.evaluate("""
            (element) => {
                element.scrollIntoView({ behavior: "smooth", block: "center" });
            }
        """)
    except Exception as error:
        if isinstance(error, Exception):
            pass
        raise error


async def scroll_element_to_percentage(ctx: MethodHandlerContext) -> None:
    """Scroll element to percentage position."""
    locator = ctx.locator
    args = ctx.args

    try:
        # Get first parameter as percentage value, default to "0%"
        y_arg = str(args[0]) if args and args[0] is not None else "0%"

        await locator.evaluate("""
            (element, { yArg }) => {
                function parsePercent(val) {
                    const cleaned = val.trim().replace("%", "");
                    const num = parseFloat(cleaned);
                    return Number.isNaN(num) ? 0 : Math.max(0, Math.min(num, 100));
                }

                const yPct = parsePercent(yArg);

                if (element.tagName.toLowerCase() === "html") {
                    const scrollHeight = document.body.scrollHeight;
                    const viewportHeight = window.innerHeight;
                    const scrollTop = (scrollHeight - viewportHeight) * (yPct / 100);
                    window.scrollTo({
                        top: scrollTop,
                        left: window.scrollX,
                        behavior: "smooth",
                    });
                } else {
                    const scrollHeight = element.scrollHeight;
                    const clientHeight = element.clientHeight;
                    const scrollTop = (scrollHeight - clientHeight) * (yPct / 100);
                    element.scrollTo({
                        top: scrollTop,
                        left: element.scrollLeft,
                        behavior: "smooth",
                    });
                }
            }
        """, {"yArg": y_arg}, timeout=10000)
    except Exception as error:
        if isinstance(error, Exception):
            pass
        raise error


async def scroll_to_next_chunk(ctx: MethodHandlerContext) -> None:
    """Scroll to next chunk."""
    locator = ctx.locator
    xpath = ctx.xpath

    try:
        await locator.evaluate("""
            (element) => {
                const waitForScrollEnd = (el) =>
                    new Promise((resolve) => {
                        let last = el.scrollTop ?? 0;
                        const check = () => {
                            const cur = el.scrollTop ?? 0;
                            if (cur === last) return resolve();
                            last = cur;
                            requestAnimationFrame(check);
                        };
                        requestAnimationFrame(check);
                    });

                const tagName = element.tagName.toLowerCase();

                if (tagName === "html" || tagName === "body") {
                    const height = window.visualViewport?.height ?? window.innerHeight;

                    window.scrollBy({ top: height, left: 0, behavior: "smooth" });

                    const scrollingRoot = (document.scrollingElement ??
                        document.documentElement);

                    return waitForScrollEnd(scrollingRoot);
                }

                const height = element.getBoundingClientRect().height;

                element.scrollBy({
                    top: height,
                    left: 0,
                    behavior: "smooth",
                });

                return waitForScrollEnd(element);
            }
        """, timeout=10000)
    except Exception as error:
        if isinstance(error, Exception):
            pass
        raise error


async def scroll_to_previous_chunk(ctx: MethodHandlerContext) -> None:
    """Scroll to previous chunk."""
    locator = ctx.locator
    xpath = ctx.xpath

    try:
        # await locator.evaluate((element: Element) => {
        #   element.scrollTop -= element.clientHeight;
        # });
        await locator.evaluate("""
            (element) => {
                const waitForScrollEnd = (el) =>
                    new Promise((resolve) => {
                        let last = el.scrollTop ?? 0;
                        const check = () => {
                            const cur = el.scrollTop ?? 0;
                            if (cur === last) return resolve();
                            last = cur;
                            requestAnimationFrame(check);
                        };
                        requestAnimationFrame(check);
                    });

                const tagName = element.tagName.toLowerCase();

                if (tagName === "html" || tagName === "body") {
                    const height = window.visualViewport?.height ?? window.innerHeight;
                    window.scrollBy({ top: -height, left: 0, behavior: "smooth" });

                    const rootScrollingEl = (document.scrollingElement ??
                        document.documentElement);

                    return waitForScrollEnd(rootScrollingEl);
                }
                const height = element.getBoundingClientRect().height;
                element.scrollBy({
                    top: -height,
                    left: 0,
                    behavior: "smooth",
                });
                return waitForScrollEnd(element);
            }
        """, timeout=10000)
    except Exception as error:
        if isinstance(error, Exception):
            pass
        raise error


async def select_option(ctx: MethodHandlerContext) -> None:
    """Select option from dropdown."""
    locator = ctx.locator
    args = ctx.args
    option_value = str(args[0]) if args and args[0] is not None else ""

    try:
        await locator.select_option(option_value, timeout=5_000)
    except Exception as error:
        if isinstance(error, Exception):
            pass
        raise error


async def handle_possible_page_navigation(
    action_description: str,
    xpath: str,
    initial_url: str,
    stagehand_page: "StagehandPage",
    dom_settle_timeout_ms: Optional[int] = None,
) -> None:

    logger.debug(
        message=f"{action_description}, checking for page navigation",
        category="action",
        auxiliary={"xpath": {"value": xpath, "type": "string"}},
    )

    new_opened_tab: Optional[Page] = None
    try:
        async with stagehand_page.context.expect_page(timeout=1500) as new_page_info:
            # The action that might open a new tab should have already been performed
            # This is a bit different from JS Promise.race.
            # We are checking if a page was opened recently.
            # A more robust way might involve listening to 'page' event *before* the action.
            # However, to closely match the TS logic's timing:
            pass  # If a page was opened by the action, it should be caught here.
        new_opened_tab = await new_page_info.value
    except Exception:
        new_opened_tab = None

        logger.info(
            message=f"{action_description} complete",
            category="action",
            auxiliary={
                "newOpenedTab": {
                    "value": (
                        "opened a new tab" if new_opened_tab else "no new tabs opened"
                    ),
                    "type": "string",
                }
            },
        )

    if new_opened_tab and new_opened_tab.url != "about:blank":
        logger.info(
            message="new page detected (new tab) with URL",
            category="action",
            auxiliary={"url": {"value": new_opened_tab.url, "type": "string"}},
        )

    try:
        await stagehand_page._wait_for_settled_dom(dom_settle_timeout_ms)
    except Exception as e:
        logger.debug(
            message="wait for settled DOM timeout hit",
            category="action",
            auxiliary={
                "trace": {
                    "value": getattr(e, "__traceback__", ""),
                    "type": "string",
                },
                "message": {"value": str(e), "type": "string"},
            },
        )

    logger.info(
        message="finished waiting for (possible) page navigation",
        category="action",
    )

    if stagehand_page._page.url != initial_url:
        logger.info(
            message="new page detected with URL",
            category="action",
            auxiliary={"url": {"value": stagehand_page._page.url, "type": "string"}},
        )


# Method handler mapping
method_handler_map: Dict[str, MethodHandler] = {
    "scrollIntoView": scroll_element_into_view,
    "scrollTo": scroll_element_to_percentage,
    "scroll": scroll_element_to_percentage,
    "mouse.wheel": scroll_element_to_percentage,
    "fill": fill_or_type,
    "type": fill_or_type,
    "press": press_key,
    "click": click_element,
    "nextChunk": scroll_to_next_chunk,
    "prevChunk": scroll_to_previous_chunk,
    "selectOptionFromDropdown": select_option,
}
