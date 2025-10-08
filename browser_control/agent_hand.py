from typing import Any, Optional, Union, List, Dict

from browser_control.browser_types import ObserveResult, ObserveOptions, ActOptions, ActResult, ExtractOptions, \
    ExtractResult, DefaultExtractSchema

from browser_wrapper.stagehand import Stagehand
from .handler import ExtractHandler, ObserveHandler, ActHandler

class AgentHand:
    def __init__(self, session_id: str):
        self.act_handler = None
        self.observe_handler = None
        self.extract_handler = None
        self.stagehand: Stagehand = None
        self.session_id = session_id

    async def init(self):
        self.stagehand = Stagehand()
        await self.stagehand.init()
        self.extract_handler = ExtractHandler(self.stagehand)
        self.observe_handler = ObserveHandler(self.stagehand)
        self.act_handler = ActHandler(self.stagehand)

    async def observe(
        self,
        instruction_or_options: Optional[Union[str, ObserveOptions]] = None
    ) -> List[ObserveResult]:
        """Observe elements on the page."""
        options = {}
        if isinstance(instruction_or_options, str):
            options = {"instruction": instruction_or_options}
        elif instruction_or_options is not None:
            options = instruction_or_options

        instruction = options.get("instruction") if isinstance(options, dict) else getattr(options, 'instruction', None)
        result = await self.observe_handler.observe(instruction, False)
        return result

    async def act(
        self,
        action_or_options: Union[str, ActOptions, ObserveResult]
    ) -> ActResult:
        """Perform action on the page."""
        if isinstance(action_or_options, dict) and action_or_options is not None:
            # If it has selector AND method => treat as ObserveResult
            if "selector" in action_or_options and "method" in action_or_options:
                observe_result = action_or_options
                return await self.act_handler.actFromObserveResult(observe_result)
            else:
                # If it's an object but no selector/method,
                # check that it's truly ActOptions (i.e., has an `action` field).
                if "action" not in action_or_options:
                    raise ValueError(
                        "Invalid argument. Valid arguments are: a string, an ActOptions object, " +
                        "or an ObserveResult WITH 'selector' and 'method' fields."
                    )
        elif isinstance(action_or_options, str):
            # Convert string to ActOptions
            action_or_options = {"action": action_or_options}
        else:
            raise ValueError(
                "Invalid argument: you may have called act with an empty ObserveResult.\n" +
                "Valid arguments are: a string, an ActOptions object, or an ObserveResult " +
                "WITH 'selector' and 'method' fields."
            )

        action = action_or_options.get("action") if isinstance(action_or_options, dict) else action_or_options.action
        result = await self.act_handler.observeAct(
            action_or_options,
            self.observe_handler
        )
        return result

    async def extract(
        self,
        instruction_or_options: Optional[Union[str, ExtractOptions, Dict[str, Any]]] = None
    ) -> ExtractResult:
        """Extract data from the page."""
        if not self.extract_handler:
            raise ValueError('ExtractHandler: ExtractHandler not found')

        if not instruction_or_options:
            raise ValueError("Extract options must be an instance of ExtractResult")

        # Handle string input - convert to ExtractOptions with default schema
        if isinstance(instruction_or_options, str):
            options = ExtractOptions(
                instruction=instruction_or_options,
                output_schema=DefaultExtractSchema
            )
        elif isinstance(instruction_or_options, dict):
            # Handle dict input
            if "output_schema" in instruction_or_options and instruction_or_options["output_schema"]:
                options = instruction_or_options
            else:
                options = {
                    **instruction_or_options,
                    "output_schema": DefaultExtractSchema
                }
        else:
            # Handle ExtractOptions object
            if hasattr(instruction_or_options, 'output_schema') and instruction_or_options.output_schema:
                options = instruction_or_options
            else:
                options = ExtractOptions(
                    instruction=instruction_or_options.instruction,
                    output_schema=DefaultExtractSchema,
                    **{k: v for k, v in instruction_or_options.__dict__.items()
                       if k not in ['instruction', 'output_schema']}
                )

        instruction = options.get("instruction") if isinstance(options, dict) else options.instruction
        schema = options.get("output_schema") if isinstance(options, dict) else options.output_schema

        result = await self.extract_handler.extract(instruction, schema)
        return result

    async def refresh(self):
        await self.stagehand.page.refresh()

    async def close(self):
        await self.stagehand.close()

    # Delegate other methods to the underlying page
    async def goto(self, url: str, **kwargs):
        """Navigate to URL."""
        return await self.stagehand.page.goto(url, **kwargs)

    async def go_back(self):
        """Navigate back."""
        return await self.stagehand.page.go_back()

    async def wait_for_timeout(self, timeout: int):
        """Wait for specified time."""
        return await self.stagehand.page.wait_for_timeout(timeout)

    async def wait(self, timeout: int):
        return await self.stagehand.page.wait_for_timeout(timeout)

    async def nav_back(self):
        return await self.stagehand.page.go_back()

    async def get_atree_last(self):
        atree = await self.stagehand.page.get_a11y_tree()
        combined_tree = atree["combinedTree"]
        # combined_xpath_map = atree["combinedXpathMap"]
        # discovered_iframes = atree["discoveredIframes"]
        return combined_tree

