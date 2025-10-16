import json
import os

from browser_flow.flow_types import plan_output_parser, conditional_output_parser
from browser_flow.flow_types.sh_graph_state import SHState
from browser_flow.nodes.base import BaseNode
from dotenv import load_dotenv

from browser_flow.utils.tools_registry import get_available_tools
from browser_flow.utils.prompts import next_step_prompt_template
from browser_flow.utils.utils import generate_tools_description

load_dotenv()

if os.getenv("DASHSCOPE_API_KEY"):
    from browser_common.llm.llm_qwen import llm
else:
    from browser_common.llm.llm_deepseek import llm

from browser_common.browser_logging import get_logger
logger = get_logger("browser_flow.conditional_node", enable_file_logging=False)

class ConditionalNode(BaseNode[SHState]):
    def __init__(self, tools=None):
        self.tools = tools

    @property
    def name(self) -> str:
        return "CONDITIONAL_NODE"

    async def execute(self, state: SHState) -> dict:
        step_count = state.step_count or 0
        max_steps = state.max_steps or 10

        # Check if maximum steps exceeded
        if step_count >= max_steps:
            error_msg = f"Maximum step limit reached: {max_steps}"
            logger.warning(f"⚠️ {error_msg}")
            return {
                "done": True,
                "step_count": step_count,
                "error": error_msg,
            }

        try:
            # Get tool descriptions
            logger.debug("🔧 Getting tool descriptions...")
            tools_description = generate_tools_description(get_available_tools(state.session_id))
            logger.debug("✅ Tool descriptions retrieved")

            # Build prompt
            logger.debug("🔧 Building conditional judgment prompt...")

            # Serialize Pydantic objects to JSON
            def serialize_pydantic_list(obj_list):
                if not obj_list:
                    return "None"
                serialized = [
                    item.model_dump() if hasattr(item, 'model_dump') else item.dict() if hasattr(item, 'dict') else item
                    for item in obj_list]
                return json.dumps(serialized, ensure_ascii=False)

            prompt = next_step_prompt_template.format(
                user_task=state.input,
                user_plan=serialize_pydantic_list(state.plan),
                steps=serialize_pydantic_list(state.steps),
                execution_result=state.execution_results,
                # message_history=state.message_history,
                tools_description=tools_description,
                thoughts=state.thoughts,
                format_instructions=conditional_output_parser.get_format_instructions(),
                domElement=state.current_a11ytree,
            )
            logger.debug("✅ Conditional judgment prompt built successfully")

            # Call LLM
            response = await llm.ainvoke(prompt)

            # Handle both string and coroutine content
            content = response.content
            if hasattr(content, '__await__'):
                content = await content
            raw = str(content or "")

            logger.debug(f"🤖 LLM response length: {len(raw)} characters")

            # Parse output
            logger.debug("🔧 Parsing conditional judgment output...")
            conditional_output = conditional_output_parser.parse(raw)
            logger.debug("✅ Conditional judgment output parsed successfully")

            # Extract results
            done = conditional_output.done or False
            next_action = conditional_output.next_action or ""
            action_params_obj = conditional_output.action_params
            reasoning = conditional_output.reasoning

            # Convert action_params to dictionary format
            if action_params_obj and hasattr(action_params_obj, 'model_dump'):
                action_params = action_params_obj.model_dump()
            elif action_params_obj and hasattr(action_params_obj, 'dict'):
                action_params = action_params_obj.dict()
            else:
                action_params = action_params_obj or {}

            logger.info(f"🎯 Conditional judgment result: done={done}, next={next_action}")
            if reasoning:
                logger.debug(f"💭 Reasoning process: {reasoning}")

            return {
                "done": done,
                "next_action": next_action,
                "action_params": action_params,
                "step_count": step_count + 1,
                "thoughts": [reasoning] if reasoning else [],
            }

        except Exception as error:
            return {
                "done": True,
                "error": str(error),
                "step_count": step_count + 1,
            }
