"""Registry for managing sessions and graphs."""

from typing import Any, Dict
from langgraph.graph import StateGraph
from browser_control.agent_hand import AgentHand
from browser_flow.graphs.sh_graph import build_graph
from browser_flow.utils.tools_registry import service_registry

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
        runnable = build_graph(session_id)
        graph_registry[session_id] = runnable
    return runnable


async def dispose_session(session_id: str) -> None:
    """Dispose of session resources."""

    service_removed = service_registry.pop(session_id, None)
    await service_removed.close()

    graph_removed = graph_registry.pop(session_id, None)


