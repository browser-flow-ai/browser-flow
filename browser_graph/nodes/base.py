"""Base node class definition"""
from abc import ABC, abstractmethod
from browser_graph.graph_types.state import GraphState


class BaseNode(ABC):
    """Base class for nodes
    
    All nodes must inherit from this class
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Node name"""
        pass
    
    @abstractmethod
    def execute(self, state: GraphState) -> GraphState:
        """Execute node logic
        
        Args:
            state: Graph state
            
        Returns:
            Updated state
        """
        pass
