from enum import Enum
from typing import Any, Dict, List, Optional, Union, Protocol
from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from browser_wrapper import StagehandPage

class SupportedPlaywrightAction(Enum):
    """Supported Playwright actions."""
    CLICK = "click"
    FILL = "fill"
    TYPE = "type"
    PRESS = "press"
    SCROLL = "scrollTo"
    NEXT_CHUNK = "nextChunk"
    PREV_CHUNK = "prevChunk"
    SELECT_OPTION_FROM_DROPDOWN = "selectOptionFromDropdown"


@dataclass
class QLQuery:
    """Query interface for QL operations."""
    pass


@dataclass
class QLResult:
    """Result interface for QL operations."""
    pass


@dataclass
class QLBridgeConfig:
    """Configuration for QL bridge operations."""
    pass


@dataclass
class ActOptions:
    """Options for act operations."""
    action: str
    variables: Optional[Dict[str, str]] = None
    domSettleTimeoutMs: Optional[int] = None
    timeoutMs: Optional[int] = None
    iframes: Optional[bool] = None
    frameId: Optional[str] = None


@dataclass
class ExtractOptions:
    """Options for extract operations."""
    instruction: Optional[str] = None
    output_schema: Optional[Any] = None  # Pydantic model or similar
    domSettleTimeoutMs: Optional[int] = None
    useTextExtract: Optional[bool] = None  # Deprecated
    selector: Optional[str] = None
    iframes: Optional[bool] = None
    frameId: Optional[str] = None


@dataclass
class ObserveOptions:
    """Options for observe operations."""
    instruction: Optional[str] = None
    domSettleTimeoutMs: Optional[int] = None
    returnAction: Optional[bool] = None
    onlyVisible: Optional[bool] = None  # Deprecated
    drawOverlay: Optional[bool] = None
    iframes: Optional[bool] = None
    frameId: Optional[str] = None


@dataclass
class ObserveResult:
    """Result from observe operations."""
    selector: str  # XPath selector
    description: str  # Element description
    backendNodeId: Optional[int] = None  # Backend node ID
    method: Optional[str] = None  # Operation method
    arguments: Optional[List[str]] = None  # Operation arguments

@dataclass
class ActResult:
    """Result from act operations."""
    success: bool  # Whether operation was successful
    message: str  # Result message
    action: str  # Executed action description


@dataclass
class MethodHandlerContext:
    """Context for method handler operations."""
    method: str
    locator: Any  # Playwright Locator
    xpath: str
    args: List[Any]
    stagehand_page: "StagehandPage"
    domSettleTimeoutMs: Optional[int] = None


class PageTextSchema(BaseModel):
    """Schema for page text extraction."""
    page_text: str = Field(description="Extracted page text")


class DefaultExtractSchema(BaseModel):
    """Default schema for extraction operations."""
    extraction: str = Field(description="Extracted content")


# Type aliases
ExtractResult = Any  # Generic type for extract results
