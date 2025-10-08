# Copyright (c) 2025 Browserbase, Inc.
# Licensed under the MIT License.

import asyncio
from typing import Any, List, Optional

from browser_control.inference import infer_observe
from browser_control.browser_types import ObserveOptions, ObserveResult
from .utils.utils import trim_trailing_text_node
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from browser_wrapper.stagehand import Stagehand

class ObserveHandler:
    """Handler for observing web elements."""

    def __init__(self, stagehand: "Stagehand"):
        self._stagehand = stagehand

    async def observe(
        self,
        instruction: Optional[str] = None,
        from_act: bool = False
    ) -> List[ObserveResult]:
        """Observe elements on the page."""
        if not instruction:
            instruction = (
                "Please find elements on the page that can be used for subsequent operations. These elements may include navigation links, related page links, "
                "chapter/subchapter links, buttons, or other interactive elements. Please be as comprehensive as possible: "
                "If there are multiple elements that may be related to subsequent operations, please return all of them."
            )

        atree = await self._stagehand.page.get_a11y_tree()
        combined_tree = atree["combinedTree"]
        combined_xpath_map = atree["combinedXpathMap"]
        discovered_iframes = atree["discoveredIframes"]


        observation_response = await infer_observe(instruction, combined_tree, from_act, True)

        # Add iframes to the observation response if there are any on the page
        if discovered_iframes:
            for iframe in discovered_iframes:
                observation_response["elements"].append({
                    "elementId": self._stagehand.page.encode_with_frame_id(
                        None,
                        int(iframe["node_id"]) if iframe.get("node_id") else 0,
                    ),
                    "description": "an iframe",
                    "method": "not-supported",
                    "arguments": [],
                })

        elements_with_selectors = []

        for element in observation_response["elements"]:
            element_id = element["elementId"]
            rest = {k: v for k, v in element.items() if k != "elementId"}

            if "-" in element_id:
                look_up_index = element_id
                xpath: Optional[str] = combined_xpath_map.get(look_up_index)

                trimmed_xpath = trim_trailing_text_node(xpath)

                if not trimmed_xpath or trimmed_xpath == "":
                    continue

                elements_with_selectors.append({
                    **rest,
                    "selector": f"xpath={trimmed_xpath}",
                    # Provisioning or future use if we want to use direct CDP
                    # backendNodeId: elementId,
                })
            else:
                elements_with_selectors.append({
                    "description": "an element inside a shadow DOM",
                    "method": "not-supported",
                    "arguments": [],
                    "selector": "not-supported",
                })

        return elements_with_selectors
        