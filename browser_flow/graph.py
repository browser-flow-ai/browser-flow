from typing import Any, Dict, List, Optional, Annotated
from langgraph.graph import StateGraph, START, END

from .flow_types import ReActState, Plan
from .nodes import plan_node, executor_node, conditional_node, counter_node

from browser_common.browser_logging import get_logger
logger = get_logger("browser_flow.graph", enable_file_logging=False)

def build_graph(session_id: str = "default") -> StateGraph:
    """Build the workflow graph with proper state management."""
    # Define state with reducers
    class State(ReActState):
        session_id: Annotated[str, lambda x, y: y if y is not None else x] = ""
        input: Annotated[Optional[str], lambda x, y: y if y is not None else x] = None
        plan: Annotated[Optional[List[Plan]], lambda x, y: y if y and len(y) > 0 else (x or [])] = None
        steps: Annotated[Optional[List[Plan]], lambda x, y: (x or []) + (y or [])] = None
        next_action: Annotated[Optional[str], lambda x, y: y if y is not None else x] = None
        action_params: Annotated[Optional[Dict[str, Any]], lambda x, y: y if y is not None else x] = None
        execution_results: Annotated[Optional[List[str]], lambda x, y: (x or []) + (y or [])] = None
        done: Annotated[bool, lambda x, y: y if y is not None else x] = False
        error: Annotated[Optional[str], lambda x, y: y if y is not None else x] = None
        step_count: Annotated[int, lambda x, y: y if y is not None else x] = 0
        max_steps: Annotated[int, lambda x, y: y if y is not None else x] = 10
        thoughts: Annotated[Optional[List[str]], lambda x, y: (x or []) + (y or [])] = None
        current_a11ytree: Annotated[Optional[str], lambda x, y: y if y is not None else x] = None
        issues: Annotated[Optional[List[str]], lambda x, y: (x or []) + (y or [])] = None

    workflow = StateGraph(State)

    # Wrap nodes with middleware

    # Add nodes with logging middleware
    workflow.add_node("exeplan", plan_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("conditional", conditional_node)
    workflow.add_node("count", counter_node)

    # Add edges
    workflow.add_edge(START, "exeplan")
    workflow.add_edge("exeplan", "executor")
    workflow.add_edge("executor", "conditional")
    workflow.add_edge("count", END)

    # Conditional edge from conditional node
    # Branch from conditional: if done then END, otherwise back to executor
    def should_continue(state: State) -> str:
        done = getattr(state, "done", False)
        step_count = getattr(state, "step_count", 0)
        max_steps = getattr(state, "max_steps", 10)
        
        # Add state transition logging
        if done:
            return "COUNT"
        else:
            return "EXECUTOR"

    workflow.add_conditional_edges(
        "conditional",
        should_continue,
        {
            "COUNT": "count",
            "EXECUTOR": "executor",
        }
    )

    return workflow.compile()


# Create initial state
def create_initial_state(
    session_id: str,
    user_message: str,
    max_steps: int = 10
) -> ReActState:
    """Create initial state for workflow."""
    logger.info(f"🔧 Creating initial state...")

    state = ReActState(
        session_id=session_id,
        input=user_message,
        done=False,
        step_count=0,
        max_steps=max_steps,
        thoughts=[],
    )
    
    logger.info("✅ Initial state created successfully")
    return state
