from browser_common.browser_logging import get_logger
from browser_flow.flow_types.sh_graph_state import SHState

logger = get_logger("browser_flow.graphs", enable_file_logging=False)

# Create initial state
def create_initial_state(
        session_id: str,
        user_message: str,
        max_steps: int = 10
) -> SHState:
    """Create initial state for workflow."""
    logger.info(f"🔧 Creating initial state...")

    state = SHState(
        session_id=session_id,
        input=user_message,
        done=False,
        step_count=0,
        max_steps=max_steps,
        thoughts=[],
    )

    logger.info("✅ Initial state created successfully")
    return state
