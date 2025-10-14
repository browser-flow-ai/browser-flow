"""Base graph class definition"""
from abc import ABC, abstractmethod
from langgraph.graph import StateGraph


class BaseGraph(ABC):
    """Base class for graphs
    
    All graphs must inherit from this class
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Graph name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Graph description"""
        pass
    
    @abstractmethod
    def build(self) -> StateGraph:
        """Build the graph
        
        Returns:
            StateGraph instance
        """
        pass
    
    def compile(self):
        """Compile the graph
        
        Returns:
            Compiled graph
        """
        return self.build().compile()
