from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser


class PlanStepSchema(BaseModel):
    """Schema for plan step."""
    id: int = Field(description="Step ID, sequential number starting from 1")
    action: str = Field(description="Tool name or action to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for this action")
    description: Optional[str] = Field(None, description="Brief description of this step")


class ActionParamsSchema(BaseModel):
    """Schema for action parameters."""
    function_name: str = Field(description="Function name to call")
    parameters: Dict[str, Any] = Field(description="Function parameters")
    reasoning: str = Field(description="Reason for choosing this action")


class PlanOutputSchema(BaseModel):
    """Schema for plan output."""
    plan: Optional[List[PlanStepSchema]] = Field(None, description="Complete execution plan steps")
    next_action: Optional[str] = Field(None, description="Next action to execute, usually plan[0]")
    action_params: Optional[ActionParamsSchema] = Field(None, description="Parameters for next action")
    reasoning: Optional[str] = Field(None, description="Reasoning for choosing this action")


class ConditionalOutputSchema(BaseModel):
    """Schema for conditional output."""
    done: bool = Field(description="Whether all tasks are completed")
    reasoning: str = Field(description="Reasoning for completion status")
    action_params: Optional[ActionParamsSchema] = Field(None, description="Next action parameters")
    next_action: Optional[str] = Field(
        None, 
        description="Next action if not completed, should be a directly callable tool"
    )


# Type aliases
Plan = PlanStepSchema
PlanOutput = PlanOutputSchema
ConditionalOutput = ConditionalOutputSchema

# Create structured output parsers
plan_output_parser = PydanticOutputParser(pydantic_object=PlanOutputSchema)
conditional_output_parser = PydanticOutputParser(pydantic_object=ConditionalOutputSchema)
