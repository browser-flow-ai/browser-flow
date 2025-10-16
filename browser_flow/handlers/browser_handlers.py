from typing import Any

from browser_common.browser_logging import get_logger
from browser_control.agent_hand import AgentHand
from browser_flow.handlers.base import BaseHandler

logger = get_logger("browser_flow.handlers.browser_handlers", enable_file_logging=False)

class ActHandler(BaseHandler):
    def __init__(self, hand: AgentHand):
        self._hand = hand

    @property
    def name(self):
        return "ActHandler"

    @property
    def description(self) -> str:
        return """
        act one step action in the browser
        """

    async def execute(self, action: str = None) -> Any:
        if not action:
            raise ValueError("Action parameter is required")

        result = await self._hand.act(action)
        if result.success:
            current_a11ytree = await self._hand.get_atree_last()
            return {
                "success": True,
                "action": action,
                "result": f"Successfully performed action: {action}",
                "current_a11ytree": current_a11ytree,
            }
        else:
            return {
                "success": False,
                "action": action,
                "result": f"Successfully performed action: {action}",
            }


class ExtractHandler(BaseHandler):
    def __init__(self, hand: AgentHand):
        self._hand = hand

    @property
    def name(self):
        return "ExtractHandler"

    @property
    def description(self) -> str:
        return """
        For extracting information from pages.  
        Extract data from the page. Use this function to get information such as text, links, or structured data.
         """

    async def execute(self, instruction: str = None, **kwargs) -> Any:
        if not instruction:
            raise ValueError("instruction parameter is required")

        try:
            extraction_result = await self._hand.extract(instruction)
            # Could consider using meta for evaluation
            current_a11ytree = await self._hand.get_atree_last()

            # Check if extraction_result has success attribute, default to True if not
            success = getattr(extraction_result, 'success', True)

            return {
                "success": success,
                "instruction": instruction or "all page text",
                "result": extraction_result,
                "current_a11ytree": current_a11ytree,
            }
        except Exception as e:
            current_a11ytree = await self._hand.get_atree_last()
            return {
                "success": False,
                "instruction": instruction or "all page text",
                "result": f"Extraction failed: {str(e)}",
                "current_a11ytree": current_a11ytree,
            }

class GotoHandler(BaseHandler):
    def __init__(self, hand: AgentHand):
        self._hand = hand

    @property
    def name(self):
        return "GotoHandler"

    @property
    def description(self) -> str:
        return """
        For jumping to specific URLs.  
        Navigate to the specified URL.
        """

    async def execute(self, url: str = None, **kwargs) -> Any:
        if not url:
            raise ValueError("url parameter is required")

        await self._hand.goto(url)
        current_a11ytree = await self._hand.get_atree_last()
        return {
            "success": True,
            "url": url,
            "result": f"Successfully navigated to {url}",
            "current_a11ytree": current_a11ytree,
        }


class WaitHandler(BaseHandler):
    def __init__(self, hand: AgentHand):
        self._hand = hand

    @property
    def name(self):
        return "WaitHandler"

    @property
    def description(self) -> str:
        return """
        For waiting for a period of time.  
        Wait for a period of time (in milliseconds).
        """

    async def execute(self, milliseconds: int = 0) -> Any:
        if not milliseconds:
            raise ValueError("milliseconds parameter is required")
        await self._hand.wait(milliseconds)
        current_a11ytree = await self._hand.get_atree_last()
        return {
            "success": True,
            "waitTime": milliseconds,
            "result": f"Waited for {milliseconds} milliseconds",
            "current_a11ytree": current_a11ytree,
        }


class NavBackHandler(BaseHandler):
    def __init__(self, hand: AgentHand):
        self._hand = hand

    @property
    def name(self):
        return "NavBackHandler"

    @property
    def description(self) -> str:
        return """
                For returning to the previous page.  
                Go back to the previous page. If already on the first page, please do not use this operation.
                """

    async def execute(self) -> Any:
        await self._hand.nav_back()
        current_a11ytree = await self._hand.get_atree_last()
        return {
            "success": True,
            "result": "Successfully navigated back to the previous page",
            "current_a11ytree": current_a11ytree,
        }


class RefreshHandler(BaseHandler):
    def __init__(self, hand: AgentHand):
        self._hand = hand

    @property
    def name(self):
        return "RefreshHandler"

    @property
    def description(self) -> str:
        return """
        For refreshing the current page.  
        Refresh the current page.
        """

    async def execute(self) -> Any:
        await self._hand.refresh()
        current_a11ytree, _ = await self._hand.get_atree_last()
        return {
            "success": True,
            "result": "Successfully refreshed the page",
            "current_a11ytree": current_a11ytree,
        }

class CloseHandler(BaseHandler):
    def __init__(self, hand: AgentHand):
        self._hand = hand

    @property
    def name(self):
        return "CloseHandler"

    @property
    def description(self) -> str:
        return """
        Only use when the task is completed or cannot be completed.  
        Close the task and end execution. Use this operation when the task is completed or cannot be completed.
        """

    async def execute(self, reason: str, success: bool) -> Any:
        await self._hand.close()
        # current_a11ytree, _ = await self._hand.get_atree_last()
        return {
            "success": True,
            "reason": reason,
            "taskCompleted": success,
            "result": f"Task closed: {reason}",
            "current_a11ytree": "",
        }
