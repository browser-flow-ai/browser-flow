"""Base handler class definition"""
from abc import ABC, abstractmethod
from typing import Any


class BaseHandler(ABC):
    """Base class for handlers

    All handlers must inherit from this class and implement the execute method
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Handler name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Handler description"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute handler logic

        Args:
            **kwargs: Handler parameters

        Returns:
            Execution result
        """
        pass
