# Copyright (c) 2025 Browserbase, Inc.
# Licensed under the MIT License.

import asyncio
from typing import Any, Dict, List, Optional, Union

from browser_control.prompts import build_act_observe_prompt
from browser_control.browser_types import ActOptions, ActResult, ObserveResult, SupportedPlaywrightAction, MethodHandlerContext
from browser_wrapper.utils import deep_locator
from .utils.page_methods import method_handler_map
from typing import TYPE_CHECKING

from browser_common.browser_logging import get_logger
logger = get_logger("browser_control.act_handler", enable_file_logging=False)

if TYPE_CHECKING:
    from browser_wrapper.stagehand import Stagehand

class ActHandler:
    """Handler for performing actions on web elements."""

    def __init__(self, stagehand: "Stagehand"):
        self._stagehand = stagehand

    async def actFromObserveResult(
        self,
        observe: ObserveResult,
        dom_settle_timeout_ms: Optional[int] = None
    ) -> ActResult:
        """Perform action from observe result."""
        method = observe.method
        args = observe.arguments or []
        selector = observe.selector.replace("xpath=", "")

        try:
            await self._perform_playwright_method(
                method,
                args,
                selector,
                dom_settle_timeout_ms,
            )
            return ActResult(
                success=True,
                message=f"Action [{method}] performed successfully on selector: {selector}",
                action=observe.description or f"ObserveResult action ({method})",
            )
        except Exception as err:
            return ActResult(
                success=False,
                message=f"Action failed: {str(err)}",
                action=observe.description or f"ObserveResult action ({method})",
            )

    async def observeAct(
        self,
        action_or_options: Union[str, ActOptions, ObserveResult],
        observe_handler: Any  # ObserveHandler type
    ) -> ActResult:
        """Observe and act based on action or options."""
        action: str
        observe_options: Dict[str, Any] = {}

        if isinstance(action_or_options, str):
            action = action_or_options
        elif isinstance(action_or_options, dict) and action_or_options is not None:
            if "action" not in action_or_options:
                raise ValueError("Invalid argument. Action options must have an `action` field.")

            action = action_or_options["action"]
            if not isinstance(action, str) or len(action) == 0:
                raise ValueError("Invalid argument. No action provided.")

            observe_options = {k: v for k, v in action_or_options.items() if k != "action"}
        else:
            raise ValueError(
                "Invalid argument. Valid arguments are: a string, an ActOptions object with an `action` field not empty, or an ObserveResult with a `selector` and `method` field."
            )

        async def do_observe_and_act(action_input) -> ActResult:

            instruction = build_act_observe_prompt(
                action_input,
                [_action.value for _action in SupportedPlaywrightAction],
                action_or_options.get("variables") if isinstance(action_or_options, dict) else None,
            )

            observe_results = await observe_handler.observe(instruction, True)

            if not observe_results:
                return ActResult(
                    success=False,
                    message="Failed to perform act: No observe results found for action",
                    action=action_input,
                )

            element = observe_results[0]

            # Apply variable substitution
            if isinstance(action_or_options, dict) and action_or_options.get("variables") and element.arguments:
                variables = action_or_options["variables"]
                element.arguments = [
                    arg.replace(f"%{key}%", variables[key])
                    for arg in element.arguments
                    for key in variables
                ]

            # Convert dict to ObserveResult object
            if isinstance(element, dict):
                element = ObserveResult(
                    selector=element.get("selector", ""),
                    description=element.get("description", ""),
                    backendNodeId=element.get("backendNodeId"),
                    method=element.get("method"),
                    arguments=element.get("arguments", []),
                )
            
            return await self.actFromObserveResult(
                element,
                action_or_options.get("domSettleTimeoutMs") if isinstance(action_or_options, dict) else None,
            )

        if isinstance(action_or_options, dict) and action_or_options.get("timeoutMs"):
            timeout_ms = action_or_options["timeoutMs"]

            async def timeout_handler():
                await asyncio.sleep(timeout_ms / 1000)
                return ActResult(
                    success=False,
                    message=f"Action timed out after {timeout_ms}ms",
                    action=action,
                )

            return await asyncio.wait_for(
                do_observe_and_act(action),
                timeout=timeout_ms / 1000
            )
        else:
            return await do_observe_and_act(action)

    async def _perform_playwright_method(
        self,
        method: str,
        args: List[Any],
        raw_xpath: str,
        dom_settle_timeout_ms: Optional[int] = None,
    ) -> None:
        """Perform Playwright method on element."""
        # Remove xpath prefix
        xpath = raw_xpath.replace("xpath=", "").strip()
        locator = None
        try:
            locator = deep_locator(self._stagehand.page.page, xpath)
            logger.debug("Locator created successfully")
        except Exception as locator_error:
            logger.error(f"Failed to create locator: {locator_error}")
            raise locator_error

        context = MethodHandlerContext(
            method=method,
            locator=locator,
            xpath=xpath,
            args=args,
            stagehand_page=self._stagehand.page,
            domSettleTimeoutMs=dom_settle_timeout_ms,
        )

        try:
            # Look up function in the map
            method_fn = method_handler_map.get(method)
            if method_fn:
                await method_fn(context)
        except Exception as e:
            raise Exception(str(e))
