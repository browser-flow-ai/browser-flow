from typing import Optional

from ..version import FLOW_VERSION


class LLMError(Exception):
    """Base error class for LLM operations."""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.name = self.__class__.__name__


class DefaultError(LLMError):
    """Default error with helpful message and version info."""
    
    def __init__(self, error: Optional[Exception] = None):
        if isinstance(error, (Exception, LLMError)):
            error_message = str(error) if hasattr(error, '__str__') else str(error)
            message = (
                f"\nHey! We're sorry you ran into an error. "
                f"web2str version: {FLOW_VERSION} "
                f"\nIf you need help, please open a Github issue or reach out to us on Slack: "
                f"https://stagehand.dev/slack\n\nFull error:\n{error_message}"
            )
            super().__init__(message)
        # If no error parameter is provided, do not call super(), consistent with TypeScript version
