import json
from typing import Any, Dict

from .flow_types import ReActState, plan_output_parser, Plan, conditional_output_parser
from .prompts import plan_prompt_template, next_step_prompt_template
from .utils.utils import generate_tools_description
import os

from dotenv import load_dotenv

load_dotenv()


if os.getenv("DASHSCOPE_API_KEY"):
    from browser_common.llm.llm_qwen import llm
else:
    from browser_common.llm.llm_deepseek import llm

from .registry import get_available_tools, get_tool_by_name

from browser_common.browser_logging import get_logger
logger = get_logger("browser_flow.nodes", enable_file_logging=False)

async def plan_node(state: ReActState) -> Dict[str, Any]:
    """Plan node for creating execution plans."""

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
            serialized = [item.model_dump() if hasattr(item, 'model_dump') else item.dict() if hasattr(item, 'dict') else item for item in obj_list]
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
        return {
            "done": True,
            "error": str(error),
            "next_action": "done",
        }

async def executor_node(state: ReActState) -> Dict[str, Any]:
    """Executor node for executing actions."""
    action = state.next_action or "done"

    if state.done or action == "done":
        logger.info("⏹️ Workflow completed, skipping execution")
        return {"done": True}

    logger.info(f"Action Tool and Action parameters:{action} {state.action_params}")
    # Find tool
    logger.debug(f"🔧 Looking for tool: {action}")
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
        # fn = getattr(action_params, "function_name", None)
        params = getattr(action_params, "parameters", action_params.model_dump()) if hasattr(action_params, "parameters") else action_params.model_dump()
    else:
        # Regular dict
        # fn = action_params.get("function_name") if action_params else None
        params = action_params.get("parameters") if action_params and "parameters" in action_params else (action_params or {})

    logger.debug(f"📋 Final parameters: {params}")

    # Execute tool
    exe_result = None
    if tool:
        try:
            logger.info(f"🚀 Starting tool execution: {action}")

            exe_result = await tool.ainvoke(params)
            exe_result = await exe_result if hasattr(exe_result, '__await__') else exe_result
            
            logger.info(f"✅ Tool execution successful: {action}")
            logger.debug(f"📊 Execution result: {exe_result}")
            
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            logger.error(f"❌ {error_msg}, {action},{state.action_params}")
            exe_result = {"error": error_msg}

    # Create step record
    step = Plan(
        action=state.next_action or "",
        params=params,
        id=(len(state.steps or []) if state.steps else 0) + 1,
        description=""
    )
    
    logger.info(f"📝 Recording execution step: {step.action} (ID: {step.id})")

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

# Counter node for aggregating data from previous stages
async def counter_node(state: ReActState) -> Dict[str, Any]:
    """All staged task information is in issues"""
    print(state.issues)
    return {}

async def conditional_node(state: ReActState) -> Dict[str, Any]:
    """Conditional node for determining next steps."""
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
            serialized = [item.model_dump() if hasattr(item, 'model_dump') else item.dict() if hasattr(item, 'dict') else item for item in obj_list]
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
