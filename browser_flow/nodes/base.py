"""Base node class definition"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from pydantic import BaseModel

StateT = TypeVar('StateT', bound=BaseModel)

class BaseNode(ABC, Generic[StateT]):
    """Base class for nodes

    All nodes must inherit from this class
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Node name"""
        pass

    @abstractmethod
    async def execute(self, state: StateT) -> dict:
        """Execute node logic

        Args:
            state: Graph state

        Returns:
            Updated state
        """
        pass
