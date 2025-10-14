"""Agent node definition"""
from browser_common.llm.llm_deepseek import llm
from browser_graph.graph_types.state import GraphState
from browser_graph.graph_types.output_schema import tool_call_parser
from browser_graph.nodes.base import BaseNode
from browser_graph.tools.calculator_tools import all_tools
from browser_graph.utils.tools_description import generate_tools_description
from langchain_core.messages import AIMessage, ToolMessage
from browser_common.browser_logging import get_logger

logger = get_logger("browser_graph.nodes.agent_node", enable_file_logging=False)


class AgentNode(BaseNode):
    """Agent node
    
    Uses LLM for decision-making with tool calling support
    """
    
    def __init__(self, tools=None):
        """Initialize Agent node
        
        Args:
            tools: List of available tools, defaults to all_tools
        """
        self._tools = tools or all_tools
        self._tools_description = generate_tools_description(self._tools)
        self._system_prompt = self._build_system_prompt()
    
    @property
    def name(self) -> str:
        return "agent"
    
    def _build_system_prompt(self) -> str:
        """Build system prompt"""
        return f"""You are an intelligent assistant that can use the following tools to help users:

Available tools:
{self._tools_description}

You need to decide whether to call tools based on the user's question.

{tool_call_parser.get_format_instructions()}

Notes:
1. If calculation is needed, call the appropriate tool
2. For simple conversations, answer directly without calling tools
3. Your output must be in valid JSON format
"""
    
    def _handle_tool_result(self, messages: list) -> GraphState:
        """Handle tool execution results
        
        Args:
            messages: List of messages
            
        Returns:
            State update containing final answer
        """
        logger.info("Handling tool execution results")
        
        # Build context
        context = "\n".join([f"{msg.type}: {msg.content}" for msg in messages[-3:]])
        final_prompt = f"""Based on the following conversation history and tool execution results, generate a friendly answer for the user:

{context}

Please provide the final answer directly without calling tools again. Your answer should be concise and clear."""
        
        response = llm.invoke(final_prompt)
        ai_message = AIMessage(content=response.content)
        return {"messages": [ai_message]}
    
    def _handle_user_input(self, user_input: str) -> GraphState:
        """Handle user input
        
        Args:
            user_input: User input content
            
        Returns:
            State update containing AI response
        """
        logger.info(f"User input: {user_input}")
        
        # Build full prompt
        full_prompt = f"{self._system_prompt}\n\nUser question: {user_input}"
        
        # Call LLM
        response = llm.invoke(full_prompt)
        content = response.content
        
        logger.debug(f"LLM raw response: {content}")
        
        # Parse output
        try:
            parsed_output = tool_call_parser.parse(content)
            logger.info(f"Reasoning: {parsed_output.reasoning}")
            
            # Check if tool call is needed
            if parsed_output.tool_name:
                logger.info(f"Tool to call: {parsed_output.tool_name}")
                logger.info(f"Tool parameters: {parsed_output.parameters}")
                
                # Create AI message with tool call
                ai_message = AIMessage(
                    content=parsed_output.reasoning,
                    additional_kwargs={
                        "tool_calls": [{
                            "name": parsed_output.tool_name,
                            "args": parsed_output.parameters or {}
                        }]
                    }
                )
            else:
                # No tool call needed, return answer directly
                logger.info(f"Direct answer: {parsed_output.final_answer}")
                ai_message = AIMessage(content=parsed_output.final_answer or parsed_output.reasoning)
            
            return {"messages": [ai_message]}
            
        except Exception as e:
            logger.error(f"Failed to parse LLM output: {e}")
            logger.error(f"Raw content: {content}")
            # Return error message
            return {"messages": [AIMessage(content=f"Sorry, an error occurred: {str(e)}")]}
    
    def execute(self, state: GraphState) -> GraphState:
        """Execute Agent node logic
        
        Args:
            state: Graph state
            
        Returns:
            Updated state
        """
        logger.info("Executing agent node")
        messages = state["messages"]
        
        # Check if last message is a tool execution result
        last_message = messages[-1]
        
        if isinstance(last_message, ToolMessage):
            return self._handle_tool_result(messages)
        else:
            # This is a new user question
            return self._handle_user_input(last_message.content)
