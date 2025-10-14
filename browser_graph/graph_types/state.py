"""Graph state type definition"""
from typing import Annotated, TypedDict, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    """Graph state definition"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
