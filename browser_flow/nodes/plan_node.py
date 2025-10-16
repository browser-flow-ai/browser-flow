import json
import os

from browser_flow.flow_types import plan_output_parser
from browser_flow.flow_types.sh_graph_state import SHState
from browser_flow.nodes.base import BaseNode
from dotenv import load_dotenv

from browser_flow.utils.tools_registry import get_available_tools
from browser_flow.utils.prompts import plan_prompt_template
from browser_flow.utils.utils import generate_tools_description

load_dotenv()

if os.getenv("DASHSCOPE_API_KEY"):
    from browser_common.llm.llm_qwen import llm
else:
    from browser_common.llm.llm_deepseek import llm

from browser_common.browser_logging import get_logger
logger = get_logger("browser_flow.plan_node", enable_file_logging=False)

class PlanNode(BaseNode[SHState]):
    def __init__(self, tools=None):
        self.tools = tools

    @property
    def name(self) -> str:
        return "PLAN_NODE"

    async def execute(self, state: SHState) -> dict:
        try:
            # Get tool descriptions
            logger.debug("🔧 Getting available tool descriptions...")
            tools_description = generate_tools_description(get_available_tools(state.session_id))
            logger.debug(f"✅ Retrieved {len(tools_description.split('\\n'))} tool descriptions")

            user_task = state.input or "Unknown task"
            execution_result = state.execution_results or "None"

            logger.debug(f"📋 User task: {user_task}")
            logger.debug(f"📋 Execution result: {execution_result}")

            # Build prompt
            logger.debug("🔧 Building planning prompt...")

            # Serialize Pydantic objects to JSON
            def serialize_pydantic_list(obj_list):
                if not obj_list:
                    return "None"
                serialized = [
                    item.model_dump() if hasattr(item, 'model_dump') else item.dict() if hasattr(item, 'dict') else item
                    for item in obj_list]
                return json.dumps(serialized, ensure_ascii=False)

            prompt = plan_prompt_template.format(
                user_plan=serialize_pydantic_list(state.plan),
                steps=serialize_pydantic_list(state.steps),
                execution_result=execution_result,
                user_task=user_task,
                tools_description=tools_description,
                format_instructions=plan_output_parser.get_format_instructions(),
                thoughts=state.thoughts
            )
            logger.debug("✅ Planning prompt built successfully")

            # Call LLM
            response = await llm.ainvoke(prompt)

            # Handle both string and coroutine content
            content = response.content
            if hasattr(content, '__await__'):
                content = await content
            raw = str(content or "")

            logger.debug(f"🤖 LLM response length: {len(raw)} characters")

            # Parse output
            logger.debug("🔧 Parsing plan output...")
            plan_output = {}
            try:
                plan_output = plan_output_parser.parse(raw)
                logger.debug("✅ Plan output parsed successfully")
            except Exception as err:
                logger.error(f"❌ Plan output parsing failed: {str(err)}")
                return {
                    "done": True,
                    "error": str(err),
                    "next_action": "done",
                }

            # Extract results

            next_action = plan_output.next_action
            action_params_obj = plan_output.action_params
            plan = plan_output.plan or []
            reasoning = plan_output.reasoning

            # Convert action_params to dictionary format
            if action_params_obj and hasattr(action_params_obj, 'model_dump'):
                action_params = action_params_obj.model_dump()
            elif action_params_obj and hasattr(action_params_obj, 'dict'):
                action_params = action_params_obj.dict()
            else:
                action_params = action_params_obj or {}

            logger.info(f"📋 Generated plan: {len(plan)} steps")
            logger.info(f"🎯 Next action: {next_action}")
            if reasoning:
                logger.debug(f"💭 Reasoning process: {reasoning}")

            return {
                "next_action": next_action,
                "action_params": action_params,
                "plan": plan,
                "done": False,
                "thoughts": [reasoning] if reasoning else [],
            }

        except Exception as error:
            logger.error(str(error))
            return {
                "done": True,
                "error": str(error),
                "next_action": "done",
            }

