"""Simple LangGraph example"""
from typing import Literal
from langgraph.graph import StateGraph, END
from browser_graph.graph_types.state import GraphState
from browser_graph.graph.base import BaseGraph
from browser_graph.nodes.agent_node import AgentNode
from browser_graph.nodes.tool_node import ToolNode
from browser_common.browser_logging import get_logger

logger = get_logger("browser_graph.graph.simple_graph", enable_file_logging=False)


class SimpleGraph(BaseGraph):
    """Simple Agent graph
    
    Contains Agent node and Tool node with tool calling support
    """
    
    def __init__(self):
        """Initialize simple graph"""
        self._agent_node = AgentNode()
        self._tool_node = ToolNode()
    
    @property
    def name(self) -> str:
        return "simple_graph"
    
    @property
    def description(self) -> str:
        return "A simple Agent graph with tool calling support"
    
    def _should_continue(self, state: GraphState) -> Literal["tools", "end"]:
        """Determine whether to continue execution
        
        Args:
            state: Graph state
            
        Returns:
            Next node name or end marker
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        # Check if there are tool calls
        if hasattr(last_message, "additional_kwargs"):
            tool_calls = last_message.additional_kwargs.get("tool_calls", [])
            if tool_calls:
                logger.info("Tool calls detected, continuing to tool node")
                return "tools"
        
        # Otherwise end
        logger.info("No tool calls, ending execution")
        return "end"
    
    def build(self) -> StateGraph:
        """Build the graph
        
        Returns:
            StateGraph instance
        """
        logger.info(f"Building graph: {self.name}")
        
        # Create graph
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node(self._agent_node.name, self._agent_node.execute)
        workflow.add_node(self._tool_node.name, self._tool_node.execute)
        
        # Set entry point
        workflow.set_entry_point(self._agent_node.name)
        
        # Add conditional edges
        workflow.add_conditional_edges(
            self._agent_node.name,
            self._should_continue,
            {
                "tools": self._tool_node.name,
                "end": END,
            }
        )
        
        # Return to agent after tool node execution
        workflow.add_edge(self._tool_node.name, self._agent_node.name)
        
        logger.info(f"Graph {self.name} built successfully")
        
        return workflow


def create_simple_graph():
    """Factory function to create simple graph
    
    Returns:
        Compiled graph
    """
    graph = SimpleGraph()
    return graph.compile()
