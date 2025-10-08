"""Handler utilities for web2str Python implementation."""

from .page_methods import (
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
from .utils import trim_trailing_text_node
# from .act_handler_utils import (
#     SupportedPlaywrightAction,
#     ActOptions,
#     ExtractOptions,
#     ObserveOptions,
#     ObserveResult,
#     ActResult,
#     MethodHandlerContext,
#     PageTextSchema,
#     DefaultExtractSchema,
#     ExtractResult,
#     act_from_observe_result,
# )

__all__ = [
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
    # "SupportedPlaywrightAction",
    # "ActOptions",
    # "ExtractOptions",
    # "ObserveOptions",
    # "ObserveResult",
    # "ActResult",
    # "MethodHandlerContext",
    # "PageTextSchema",
    # "DefaultExtractSchema",
    # "ExtractResult",
    # "act_from_observe_result",
]
