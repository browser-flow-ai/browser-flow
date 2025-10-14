"""Generate tool descriptions"""
import json
from typing import List, Any
from browser_common.browser_logging import get_logger

logger = get_logger("browser_graph.utils.tools_description", enable_file_logging=False)


def generate_tools_description(tools: List[Any]) -> str:
    """Generate text description of tools
    
    Args:
        tools: List of tools
        
    Returns:
        Tool description text
    """
    descriptions = []
    for tool in tools:
        # Get parameter information
        schema_info = "No parameters"
        if hasattr(tool, 'args_schema') and tool.args_schema:
            try:
                # For Pydantic models, get field information
                if hasattr(tool.args_schema, 'model_fields'):
                    fields = tool.args_schema.model_fields
                    schema_info = json.dumps(
                        {name: field.description or str(field.annotation) for name, field in fields.items()},
                        indent=2,
                        ensure_ascii=False
                    )
                else:
                    schema_info = str(tool.args_schema)
            except Exception:
                schema_info = "Unable to get parameter information"

        descriptions.append(f"- {tool.name}: {tool.description}\n  Parameters: {schema_info}")

    return "\n\n".join(descriptions)
