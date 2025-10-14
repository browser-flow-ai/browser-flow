"""Output schema definition"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser


class ToolCallSchema(BaseModel):
    """Tool call schema"""
    tool_name: Optional[str] = Field(None, description="Name of the tool to call, null if no tool call is needed")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Tool parameters")
    reasoning: str = Field(description="Reasoning process and decision rationale")
    final_answer: Optional[str] = Field(None, description="Final answer if no tool call is needed")


# Create output parser
tool_call_parser = PydanticOutputParser(pydantic_object=ToolCallSchema)
