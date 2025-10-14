"""Tool node definition"""
from browser_graph.graph_types.state import GraphState
from browser_graph.nodes.base import BaseNode
from browser_graph.tools.calculator_tools import all_tools
from langchain_core.messages import ToolMessage
from browser_common.browser_logging import get_logger

logger = get_logger("browser_graph.nodes.tool_node", enable_file_logging=False)


class ToolNode(BaseNode):
    """Tool execution node
    
    Responsible for finding and executing tool calls
    """
    
    def __init__(self, tools=None):
        """Initialize tool node
        
        Args:
            tools: List of available tools, defaults to all_tools
        """
        self._tools = tools or all_tools
    
    @property
    def name(self) -> str:
        return "tools"
    
    def execute(self, state: GraphState) -> GraphState:
        """Execute tool calls
        
        Args:
            state: Graph state
            
        Returns:
            State update containing tool execution results
        """
        logger.info("Executing tool node")
        
        messages = state["messages"]
        last_message = messages[-1]
        
        # Get tool call information
        tool_calls = last_message.additional_kwargs.get("tool_calls", [])
        
        if not tool_calls:
            logger.warning("No tool calls found")
            return {"messages": []}
        
        result_messages = []
        
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            logger.info(f"Calling tool: {tool_name}")
            logger.info(f"Arguments: {tool_args}")
            
            # Find the corresponding tool
            tool = None
            for t in self._tools:
                if t.name == tool_name:
                    tool = t
                    break
            
            if not tool:
                error_msg = f"Tool not found: {tool_name}"
                logger.error(error_msg)
                result_messages.append(ToolMessage(
                    content=error_msg,
                    tool_call_id=tool_name
                ))
                continue
            
            # Execute tool
            try:
                result = tool.invoke(tool_args)
                logger.info(f"Tool execution result: {result}")
                
                result_messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_name
                ))
            except Exception as e:
                error_msg = f"Tool execution failed: {str(e)}"
                logger.error(error_msg)
                result_messages.append(ToolMessage(
                    content=error_msg,
                    tool_call_id=tool_name
                ))
        
        return {"messages": result_messages}
