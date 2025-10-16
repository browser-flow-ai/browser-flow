"""Base tool class definition"""
from abc import ABC, abstractmethod
from langchain_core.tools import StructuredTool

from browser_flow.handlers.base import BaseHandler


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
