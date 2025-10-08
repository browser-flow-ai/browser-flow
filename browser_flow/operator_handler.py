from typing import Any, Dict, List, TYPE_CHECKING
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from browser_control.agent_hand import AgentHand
from browser_common.browser_logging import get_logger
logger = get_logger("browser_wrapper.operator_handler", enable_file_logging=False)


class ActToolInput(BaseModel):
    """Input schema for act tool."""
    action: str = Field(description="The action to perform. Do not combine two actions together, such as: 'type [email] in the email input box and then press enter'. Should be separate actions like: 'click submit button', or 'type [email] in the email input box', then 'press enter in the email input box'.")


class ExtractToolInput(BaseModel):
    """Input schema for extract tool."""
    instruction: str = Field(None,
                             description="What data to extract. For example: 'article title' or 'all links on the page'. Leave this empty if you want to extract all text.")

class GotoToolInput(BaseModel):
    """Input schema for goto tool."""
    url: str = Field(description="The URL to navigate to. For example: 'https://www.google.com'")


class WaitToolInput(BaseModel):
    """Input schema for wait tool."""
    milliseconds: int = Field(description="The time to wait in milliseconds.")


class CloseToolInput(BaseModel):
    """Input schema for close tool."""
    reason: str = Field(description="The reason for closing the task")
    success: bool = Field(description="Whether the task has been completed successfully")


class EmptyInput(BaseModel):
    """Empty input schema for tools that don't need parameters."""
    pass


def build_ql_tools(service: AgentHand) -> List[StructuredTool]:
    """Build QL tools for the service."""
    async def act_func(action: str) -> Dict[str, Any]:
        """Execute an action on the page. Use this function to interact with elements, such as clicking buttons, entering text, or navigating. If there are multiple actions, please separate them, for example:
        'type browse in the input box then press enter' should be split into 'type browse in the input box' and 'press enter in the input box' as two separate actions."""
        result = await service.act(action)
        if result.success:
            current_a11ytree = await  service.get_atree_last()
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

    async def extract_func(instruction: str = None) -> Dict[str, Any]:
        """Extract data from the page. Use this function to get information such as text, links, or structured data."""
        try:
            extraction_result = await service.extract(instruction)
            # Could consider using meta for evaluation
            current_a11ytree = await service.get_atree_last()

            # Check if extraction_result has success attribute, default to True if not
            success = getattr(extraction_result, 'success', True)

            return {
                "success": success,
                "instruction": instruction or "all page text",
                "result": extraction_result,
                "current_a11ytree": current_a11ytree,
            }
        except Exception as e:
            current_a11ytree = await service.get_atree_last()
            return {
                "success": False,
                "instruction": instruction or "all page text",
                "result": f"Extraction failed: {str(e)}",
                "current_a11ytree": current_a11ytree,
            }

    async def goto_func(url: str) -> Dict[str, Any]:
        """Navigate to the specified URL."""
        await service.goto(url)
        current_a11ytree = await service.get_atree_last()
        return {
            "success": True,
            "url": url,
            "result": f"Successfully navigated to {url}",
            "current_a11ytree": current_a11ytree,
        }

    async def wait_func(milliseconds: int) -> Dict[str, Any]:
        """Wait for a period of time (in milliseconds)."""
        await service.wait(milliseconds)
        current_a11ytree = await service.get_atree_last()
        return {
            "success": True,
            "waitTime": milliseconds,
            "result": f"Waited for {milliseconds} milliseconds",
            "current_a11ytree": current_a11ytree,
        }

    async def navback_func() -> Dict[str, Any]:
        """Go back to the previous page. If already on the first page, please do not use this operation."""
        await service.nav_back()
        current_a11ytree = await service.get_atree_last()
        return {
            "success": True,
            "result": "Successfully navigated back to the previous page",
            "current_a11ytree": current_a11ytree,
        }

    async def refresh_func() -> Dict[str, Any]:
        """Refresh the current page."""
        await service.refresh()
        current_a11ytree, _ = await service.get_atree_last()
        return {
            "success": True,
            "result": "Successfully refreshed the page",
            "current_a11ytree": current_a11ytree,
        }

    async def close_func(reason: str, success: bool) -> Dict[str, Any]:
        """Close the task and end execution. Use this operation when the task is completed or cannot be completed."""
        await service.close()
        current_a11ytree, _ = await service.get_atree_last()
        return {
            "success": True,
            "reason": reason,
            "taskCompleted": success,
            "result": f"Task closed: {reason}",
            "current_a11ytree": current_a11ytree,
        }

    # Create tools using StructuredTool.from_function
    act_tool = StructuredTool.from_function(
        func=act_func,
        name="act",
        args_schema=ActToolInput,
        description="Execute an action on the page. Use this function to interact with elements, such as clicking buttons, entering text, or navigating. Do not combine two actions together, such as: 'type [email] in the email input box then press enter'. Should be done sequentially: 'type [email] in the email input box', then 'press enter in the email input box'.",
 )

    extract_tool = StructuredTool.from_function(
        func=extract_func,
        name="extract",
        args_schema=ExtractToolInput,
        description='Extract data from the page. Use this function to get information such as text, links, or structured data.',
    )

    goto_tool = StructuredTool.from_function(
        func=goto_func,
        name="goto",
        args_schema=GotoToolInput,
        description='Navigate to the specified URL.',

    )

    wait_tool = StructuredTool.from_function(
        func=wait_func,
        name="wait",
        args_schema=WaitToolInput,
        description='Wait for a period of time (in milliseconds).',
    )

    navback_tool = StructuredTool.from_function(
        func=navback_func,
        name="navback",
        args_schema=EmptyInput,
        description='Go back to the previous page. If already on the first page, please do not use this operation.',
    )

    refresh_tool = StructuredTool.from_function(
        func=refresh_func,
        name="refresh",
        args_schema=EmptyInput,
        description='Refresh the current page.',
    )

    close_tool = StructuredTool.from_function(
        func=close_func,
        name="close",
        args_schema=CloseToolInput,
        description='Close the task and end execution. Use this operation when the task is completed or cannot be completed.',
    )

    return [act_tool, extract_tool, goto_tool, wait_tool, navback_tool, refresh_tool, close_tool]
