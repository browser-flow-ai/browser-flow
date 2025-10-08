from enum import Enum
from typing import Optional


class QLErrorCode(Enum):
    """Error codes for QL operations."""
    PARSE = "QL_PARSE_ERROR"
    EXECUTION = "QL_EXECUTION_ERROR"


class QLErrorName(Enum):
    """Error names for QL operations."""
    BRIDGE = "QLBridgeError"
    PARSE = "QLParseError"
    EXECUTION = "QLExecutionError"


class QLBridgeError(Exception):
    """Base error class for QL bridge operations."""
    
    def __init__(self, message: str, code: Optional[QLErrorCode] = None):
        super().__init__(message)
        self.code = code
        self.name = QLErrorName.BRIDGE.value


class QLParseError(QLBridgeError):
    """Error raised when parsing QL queries fails."""
    
    def __init__(self, message: str, query: Optional[str] = None):
        super().__init__(message, QLErrorCode.PARSE)
        self.query = query
        self.name = QLErrorName.PARSE.value


class QLExecutionError(QLBridgeError):
    """Error raised when executing QL queries fails."""
    
    def __init__(self, message: str, step: Optional[str] = None):
        super().__init__(message, QLErrorCode.EXECUTION)
        self.step = step
        self.name = QLErrorName.EXECUTION.value


