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


class ReActState(BaseModel):
    """ReAct state interface."""
    session_id: str = Field(description="Session ID")
    input: Optional[str] = Field(None, description="Input string")
    plan: Optional[List[Plan]] = Field(None, description="Execution plan steps")
    steps: Optional[List[Plan]] = Field(None, description="Steps that have been executed")
    next_action: Optional[str] = Field(None, description="Next action to execute")
    action_params: Optional[Dict[str, Any]] = Field(None, description="Action parameters")
    execution_results: Optional[List[str]] = Field(None, description="Execution results")
    done: bool = Field(description="Whether all tasks are completed")
    error: Optional[str] = Field(None, description="Error message if any")
    step_count: int = Field(description="Current step count")
    max_steps: int = Field(description="Maximum number of steps")
    thoughts: Optional[List[str]] = Field(None, description="Thoughts during execution")
    current_a11ytree:  Optional[str] = Field(None, description="A11y Tree of the current page")
    issues: Optional[List[str]] = Field(None, description="outputs of extract action")

    
    class Config:
        extra = "allow"  # Allow additional fields like in TypeScript


# Create structured output parsers
plan_output_parser = PydanticOutputParser(pydantic_object=PlanOutputSchema)
conditional_output_parser = PydanticOutputParser(pydantic_object=ConditionalOutputSchema)
