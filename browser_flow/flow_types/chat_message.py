from typing import Union, List, Optional, Literal
from pydantic import BaseModel


class ChatMessageImageContent(BaseModel):
    """Image content for chat messages."""
    type: str
    image_url: Optional[dict] = None  # { url: str }
    text: Optional[str] = None
    source: Optional[dict] = None  # { type: str, media_type: str, data: str }


class ChatMessageTextContent(BaseModel):
    """Text content for chat messages."""
    type: str
    text: str


# Union type for chat message content
ChatMessageContent = Union[
    str,
    List[Union[ChatMessageImageContent, ChatMessageTextContent]]
]


class ChatMessage(BaseModel):
    """Chat message interface."""
    role: Literal["system", "user", "assistant"]
    content: ChatMessageContent
