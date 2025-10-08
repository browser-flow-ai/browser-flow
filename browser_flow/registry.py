"""Registry for managing sessions and tools."""

from typing import Any, Dict, List, Optional

from langgraph.graph import StateGraph

from browser_control.agent_hand import AgentHand
from .flow_types import LLMError
from .operator_handler import build_ql_tools

service_registry: Dict[str, AgentHand] = {}
graph_registry: Dict[str, StateGraph] = {}  # Graph type

async def get_runnable_by_session(session_id: str) -> Any:
    """Get runnable graph for session, creating if needed."""

    # Get or create service
    svc = service_registry.get(session_id)
    if not svc:
        svc = AgentHand(session_id)
        service_registry[session_id] = svc
        await svc.init()

    # Get or create graph
    runnable = graph_registry.get(session_id)
    if not runnable:
        from .graph import build_graph
        runnable = build_graph(session_id)
        graph_registry[session_id] = runnable
    return runnable

async def dispose_session(session_id: str) -> None:
    """Dispose of session resources."""

    service_removed = service_registry.pop(session_id, None)
    await service_removed.close()

    graph_removed = graph_registry.pop(session_id, None)

def get_available_tools(session_id: str) -> List[Any]:
    """Get available tools for session."""

    service = service_registry.get(session_id)
    if not service:
        raise LLMError("Have no this Session, Cannot get available tools")
    
    tools = build_ql_tools(service)
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
