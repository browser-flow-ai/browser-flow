"""Registry for managing tools without circular imports."""

from typing import Any, Dict, List, Optional
from browser_control.agent_hand import AgentHand
from browser_flow.flow_types import LLMError
from browser_flow.tools.browser_tools import ActTool, ExtractTool, GotoTool, WaitTool, NavBackTool, RefreshTool, \
    CloseTool

service_registry: Dict[str, AgentHand] = {}


def get_available_tools(session_id: str) -> List[Any]:
    """Get available tools for session."""

    service = service_registry.get(session_id)
    if not service:
        raise LLMError("Have no this Session, Cannot get available tools")

    tools = []
    try:
        tools = [
            ActTool(service).to_structured_tool(),
            ExtractTool(service).to_structured_tool(),
            GotoTool(service).to_structured_tool(),
            WaitTool(service).to_structured_tool(),
            NavBackTool(service).to_structured_tool(),
            RefreshTool(service).to_structured_tool(),
            CloseTool(service).to_structured_tool(),
        ]
    except Exception as e:
        print(f"Error creating tools: {e}")
        raise e
    
    return tools


def get_tool_names(session_id: str) -> List[str]:
    """Get tool names for session."""

    tools = get_available_tools(session_id)
    tool_names = [tool.name for tool in tools]

    return tool_names


def get_tool_by_name(session_id: str, name: str) -> Optional[Any]:
    """Get specific tool by name for session."""
    tools = get_available_tools(session_id)
    tool = next((tool for tool in tools if tool.name == name), None)

    return tool
