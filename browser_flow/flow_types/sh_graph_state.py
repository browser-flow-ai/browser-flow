from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from browser_flow.flow_types.graph_chain import Plan
from typing_extensions import TypedDict, Annotated


def merge_lists(x: Optional[List], y: Optional[List]) -> List:
    if y and len(y) > 0:
        return y
    return x or []


def append_lists(x: Optional[List], y: Optional[List]) -> List:
    return (x or []) + (y or [])


def use_new_or_keep_old(x, y):
    return y if y is not None else x


class SHState(BaseModel):
    session_id: Annotated[str, use_new_or_keep_old] = Field(default="", description="Session ID")
    input: Annotated[Optional[str], use_new_or_keep_old] = Field(default=None, description="Input string")
    plan: Annotated[Optional[List[Plan]], merge_lists] = Field(default=None, description="Execution plan steps")
    steps: Annotated[Optional[List[Plan]], append_lists] = Field(default=None,
                                                                 description="Steps that have been executed")
    next_action: Annotated[Optional[str], use_new_or_keep_old] = Field(default=None,
                                                                       description="Next action to execute")
    action_params: Annotated[Optional[Dict[str, Any]], use_new_or_keep_old] = Field(default=None,
                                                                                    description="Action parameters")
    execution_results: Annotated[Optional[List[str]], append_lists] = Field(default=None,
                                                                            description="Execution results")
    done: Annotated[bool, use_new_or_keep_old] = Field(default=False, description="Whether all tasks are completed")
    error: Annotated[Optional[str], use_new_or_keep_old] = Field(default=None, description="Error message if any")
    step_count: Annotated[int, use_new_or_keep_old] = Field(default=0, description="Current step count")
    max_steps: Annotated[int, use_new_or_keep_old] = Field(default=10, description="Maximum number of steps")
    thoughts: Annotated[Optional[List[str]], append_lists] = Field(default=None,
                                                                   description="Thoughts during execution")
    current_a11ytree: Annotated[Optional[str], use_new_or_keep_old] = Field(default=None,
                                                                            description="A11y Tree of the current page")
    issues: Annotated[Optional[List[str]], append_lists] = Field(default=None, description="Outputs of extract action")

    class Config:
        extra = "allow"
