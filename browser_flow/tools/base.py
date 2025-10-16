"""Base tool class definition"""
from abc import ABC, abstractmethod
from typing import Type, TypeVar

from pydantic import BaseModel

from browser_control.agent_hand import AgentHand
from browser_flow.handlers.base import BaseHandler
from langchain_core.tools import StructuredTool

# Type variable for handler types
HandlerType = TypeVar('HandlerType', bound=BaseHandler)


class BaseTool(ABC):
    """Base class for tools

    All tools must inherit from this class
    """

    @property
    @abstractmethod
    def handler(self) -> BaseHandler:
        """Associated handler"""
        pass

    @abstractmethod
    def to_structured_tool(self) -> StructuredTool:
        """Convert to StructuredTool

        Returns:
            StructuredTool instance
        """
        pass


class GenericTool(BaseTool):
    """Generic tool class that reduces code duplication."""

    def __init__(self, hand: AgentHand, handler_class: Type[HandlerType], args_schema: Type[BaseModel]):
        self._handler = handler_class(hand)
        self._args_schema = args_schema

    @property
    def handler(self) -> HandlerType:
        return self._handler

    def to_structured_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=self._handler.execute,
            name=self._handler.name,
            description=self._handler.description,
            args_schema=self._args_schema
        )
