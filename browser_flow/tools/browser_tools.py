from pydantic import BaseModel, Field

from browser_common.browser_logging import get_logger
from browser_control.agent_hand import AgentHand
from browser_flow.handlers.browser_handlers import ActHandler, ExtractHandler, GotoHandler, WaitHandler, NavBackHandler, \
    RefreshHandler, CloseHandler
from browser_flow.tools.base import GenericTool

logger = get_logger("browser_wrapper.browser_tools", enable_file_logging=False)


class ActToolInput(BaseModel):
    """Input schema for act tool."""
    action: str = Field(
        description="The action to perform. Do not combine two actions together, such as: 'type [email] in the email input box and then press enter'. Should be separate actions like: 'click submit button', or 'type [email] in the email input box', then 'press enter in the email input box'.")


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


class ActTool(GenericTool):
    def __init__(self, hand: AgentHand):
        super().__init__(hand, ActHandler, ActToolInput)


class ExtractTool(GenericTool):
    def __init__(self, hand: AgentHand):
        super().__init__(hand, ExtractHandler, ExtractToolInput)


class GotoTool(GenericTool):
    def __init__(self, hand: AgentHand):
        super().__init__(hand, GotoHandler, GotoToolInput)


class WaitTool(GenericTool):
    def __init__(self, hand: AgentHand):
        super().__init__(hand, WaitHandler, WaitToolInput)


class NavBackTool(GenericTool):
    def __init__(self, hand: AgentHand):
        super().__init__(hand, NavBackHandler, EmptyInput)


class RefreshTool(GenericTool):
    def __init__(self, hand: AgentHand):
        super().__init__(hand, RefreshHandler, EmptyInput)


class CloseTool(GenericTool):
    def __init__(self, hand: AgentHand):
        super().__init__(hand, CloseHandler, CloseToolInput)
