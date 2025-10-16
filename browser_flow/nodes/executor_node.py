import json
import os

from browser_flow.flow_types import plan_output_parser, Plan
from browser_flow.flow_types.sh_graph_state import SHState
from browser_flow.nodes.base import BaseNode

from browser_flow.utils.tools_registry import get_tool_by_name
from browser_common.browser_logging import get_logger

logger = get_logger("browser_flow.executor_node", enable_file_logging=False)


class ExecutorNode(BaseNode[SHState]):
    def __init__(self, tools=None):
        self.tools = tools

    @property
    def name(self) -> str:
        return "EXECUTOR_NODE"

    async def execute(self, state: SHState) -> dict:
        action = state.next_action or "done"
        logger.info(f"Execution node is starting: {action}")

        if state.done or action == "done":
            logger.info("Workflow completed, skipping execution")
            return {"done": True}

        # Find tool
        tool = get_tool_by_name(state.session_id, action)
        if not tool:
            error_msg = f"No callable tool found: {action},{state.action_params}"
            logger.error(f"❌ {error_msg}")
            return {
                "done": True,
                "error": error_msg,
            }

        # Process parameters
        action_params = state.action_params or {}

        # Handle both dict and Pydantic model cases
        if hasattr(action_params, 'model_dump'):
            # Pydantic model
            params = getattr(action_params, "parameters", action_params.model_dump()) if hasattr(action_params,
                                                                                                 "parameters") else action_params.model_dump()
        else:
            # Regular dict
            params = action_params.get("parameters") if action_params and "parameters" in action_params else (
                    action_params or {})

        # Execute tool
        exe_result = None
        if tool:
            try:
                exe_result = await tool.ainvoke(params)
                exe_result = await exe_result if hasattr(exe_result, '__await__') else exe_result
            except Exception as e:
                error_msg = f"Tool execution failed: {str(e)}"
                logger.error(f"{error_msg}, {action},{state.action_params}")
                exe_result = {"error": error_msg}

        # Create step record
        step = Plan(
            action=state.next_action or "",
            params=params,
            id=(len(state.steps or []) if state.steps else 0) + 1,
            description=""
        )

        current_a11ytree = exe_result.get("current_a11ytree")
        others = {k: v for k, v in exe_result.items() if k != "current_a11ytree"}

        extraction_result = exe_result.get("result")

        # Serialize others dictionary, handle Pydantic objects
        def serialize_for_json(obj):
            """Recursively serialize objects to JSON-serializable format"""
            if hasattr(obj, 'model_dump'):
                return obj.model_dump()
            elif hasattr(obj, 'dict'):
                return obj.dict()
            elif isinstance(obj, dict):
                return {k: serialize_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_for_json(item) for item in obj]
            elif isinstance(obj, tuple):
                return tuple(serialize_for_json(item) for item in obj)
            else:
                return obj

        others_serialized = serialize_for_json(others)
        others_str = json.dumps(others_serialized, ensure_ascii=False)
        # Convert execution result to string format
        execution_result_str = str(extraction_result) if others else "No result"

        return {
            "last_executed_action": action,
            "current_a11ytree": current_a11ytree or "",
            "execution_results": [others_str],
            "steps": [step],
            "issues": [execution_result_str] if extraction_result is not None else [],
        }
