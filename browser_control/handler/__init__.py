"""Handler module for web2str Python implementation."""

from .act_handler import ActHandler
from .extract_handler import ExtractHandler
from .observe_handler import ObserveHandler
from .utils.page_methods import (
    method_handler_map,
    click_element,
    fill_or_type,
    press_key,
    scroll_element_into_view,
    scroll_element_to_percentage,
    scroll_to_next_chunk,
    scroll_to_previous_chunk,
    select_option,
)
from .utils.utils import trim_trailing_text_node

__all__ = [
    "ActHandler",
    "ExtractHandler", 
    "ObserveHandler",
    "method_handler_map",
    "click_element",
    "fill_or_type",
    "press_key",
    "scroll_element_into_view",
    "scroll_element_to_percentage",
    "scroll_to_next_chunk",
    "scroll_to_previous_chunk",
    "select_option",
    "trim_trailing_text_node",
]
