"""Calculator tool wrappers"""
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from browser_graph.tools.base import BaseTool
from browser_graph.handlers.base import BaseHandler
from browser_graph.handlers.calculator import AddHandler, MultiplyHandler


class CalculatorInputSchema(BaseModel):
    """Calculator input parameter schema"""
    a: int = Field(description="First number")
    b: int = Field(description="Second number")


class AddTool(BaseTool):
    """Addition tool"""
    
    def __init__(self):
        self._handler = AddHandler()
    
    @property
    def handler(self) -> BaseHandler:
        return self._handler
    
    def to_structured_tool(self) -> StructuredTool:
        """Convert to StructuredTool"""
        return StructuredTool.from_function(
            func=self._handler.execute,
            name=self._handler.name,
            description=self._handler.description,
            args_schema=CalculatorInputSchema,
        )


class MultiplyTool(BaseTool):
    """Multiplication tool"""
    
    def __init__(self):
        self._handler = MultiplyHandler()
    
    @property
    def handler(self) -> BaseHandler:
        return self._handler
    
    def to_structured_tool(self) -> StructuredTool:
        """Convert to StructuredTool"""
        return StructuredTool.from_function(
            func=self._handler.execute,
            name=self._handler.name,
            description=self._handler.description,
            args_schema=CalculatorInputSchema,
        )


# Create tool instances
add_tool_instance = AddTool()
multiply_tool_instance = MultiplyTool()

# Export StructuredTools
add_tool = add_tool_instance.to_structured_tool()
multiply_tool = multiply_tool_instance.to_structured_tool()

# Export all tools
all_tools = [add_tool, multiply_tool]

# Export tool classes
__all__ = ["AddTool", "MultiplyTool", "add_tool", "multiply_tool", "all_tools"]
