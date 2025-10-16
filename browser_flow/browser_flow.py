"""Browser Flow - Simple wrapper for browser automation workflows."""

from datetime import datetime
from typing import Optional, Any

from browser_common.browser_logging import get_logger
from browser_flow.graphs import create_initial_state
from browser_flow.utils.graph_session_manager import get_runnable_by_session, dispose_session

logger = get_logger("browser_flow", enable_file_logging=False)


class BrowserFlow:
    """Simple wrapper for browser automation workflows."""

    def __init__(self, session_id: Optional[str] = None):
        """Initialize BrowserFlow with optional session ID."""
        if session_id is None:
            now = datetime.now()
            session_id = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.session_id = session_id
        self._graph = None

    async def run(self, instruction: str, max_steps: int = 10) -> Any:
        """
        Run a browser automation workflow.

        Args:
            instruction: The instruction for the browser to execute
            max_steps: Maximum number of steps to execute (default: 10)

        Returns:
            The result of the workflow execution
        """
        try:
            logger.info(f"🚀 Starting BrowserFlow execution for session: {self.session_id}")
            logger.info(f"📝 Instruction: {instruction}")
            logger.info(f"⏳ Max steps: {max_steps}")

            # Get graph instance
            self._graph = await get_runnable_by_session(self.session_id)

            # Create initial state
            initial_state = create_initial_state(self.session_id, instruction, max_steps)

            # Execute workflow
            logger.info("🔄 Executing workflow...")
            result = await self._graph.ainvoke(initial_state)

            logger.info("✅ Workflow execution completed successfully")
            return result

        except Exception as error:
            logger.error(f"❌ Workflow execution failed: {error}")
            raise
        finally:
            # Cleanup resources
            await self._cleanup()

    async def _cleanup(self):
        """Clean up browser resources."""
        try:
            if self.session_id:
                logger.info("🗑️ Cleaning up browser resources...")
                await dispose_session(self.session_id)
                logger.info("✅ Browser resources cleanup completed")
        except Exception as cleanup_error:
            logger.warning(f"⚠️ Warning during resource cleanup: {cleanup_error}")

    async def close(self):
        """Manually close and cleanup resources."""
        await self._cleanup()


# Convenience function for simple usage
async def run_workflow(instruction: str, max_steps: int = 10, session_id: Optional[str] = None) -> Any:
    """
    Convenience function to run a browser workflow.

    Args:
        instruction: The instruction for the browser to execute
        max_steps: Maximum number of steps to execute (default: 10)
        session_id: Optional session ID (auto-generated if not provided)

    Returns:
        The result of the workflow execution
    """
    flow = BrowserFlow(session_id)
    try:
        return await flow.run(instruction, max_steps)
    finally:
        await flow.close()
