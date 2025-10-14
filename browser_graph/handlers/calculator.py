"""Calculator handlers"""
from browser_common.browser_logging import get_logger
from browser_graph.handlers.base import BaseHandler

logger = get_logger("browser_graph.handlers.calculator", enable_file_logging=False)


class AddHandler(BaseHandler):
    """Addition handler"""
    
    @property
    def name(self) -> str:
        return "add"
    
    @property
    def description(self) -> str:
        return "Add two numbers together"
    
    def execute(self, a: int, b: int) -> int:
        """Execute addition operation
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            Sum of the two numbers
        """
        logger.info(f"Executing addition: {a} + {b}")
        result = a + b
        logger.info(f"Result: {result}")
        return result


class MultiplyHandler(BaseHandler):
    """Multiplication handler"""
    
    @property
    def name(self) -> str:
        return "multiply"
    
    @property
    def description(self) -> str:
        return "Multiply two numbers together"
    
    def execute(self, a: int, b: int) -> int:
        """Execute multiplication operation
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            Product of the two numbers
        """
        logger.info(f"Executing multiplication: {a} * {b}")
        result = a * b
        logger.info(f"Result: {result}")
        return result
