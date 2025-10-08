import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

if os.getenv("DASHSCOPE_API_KEY"):
    from browser_common.llm.llm_qwen import llm
else:
    from browser_common.llm.llm_deepseek import llm

from browser_control.prompts import extract_prompt_template, observe_prompt_template, extract_meta_prompt_template
from typing import TypeVar

TModel = TypeVar("TModel", bound=BaseModel)

class ExtractionResponse(BaseModel):
    """Response schema for extraction operations."""
    pass  # Will be dynamically created based on input schema


class ElementSchema(BaseModel):
    """Schema for observed elements."""
    elementId: str = Field(description="id string associated with this element. Do not include square brackets.")
    iframePath: str = Field(description="iframe name that the element belongs to, return empty string if none")
    description: str = Field(description="Description of the accessible element and its purpose")
    method: Optional[str] = Field(None, description="Candidate method/action for interacting with this element")
    arguments: List[str] = Field(default_factory=list, description="Parameters to pass to the method")


class ObserveResponse(BaseModel):
    """Response schema for observe operations."""
    elements: List[ElementSchema] = Field(description="Array of accessible elements matching the instruction")


async def infer_extract(
    instruction: str,
    dom_element: str,
    schema: type[TModel]
) -> TModel:
    """Infer extraction from DOM element using instruction and schema."""
    extract_output_parser = PydanticOutputParser(pydantic_object=schema)
    # extract_parser = PydanticOutputParser(pydantic_object=schema)

    prompt = extract_prompt_template.format(
        format_instructions=extract_output_parser.get_format_instructions(),
        instruction=instruction,
        domElement=dom_element,
    )

    response = await llm.ainvoke(prompt)
    # Handle both string and coroutine content
    content = response.content
    if hasattr(content, '__await__'):
        content = await content
    raw = str(content or "")

    extraction_response = {}
    try:
        extraction_response = extract_output_parser.parse(raw)
    except Exception as err:
        pass

    class MetadataModel(BaseModel):
        # Equivalent to metadataSchema in TS
        progress: str = Field(description="progress of what has been extracted so far, as concise as possible")
        completed: bool = Field(description="true if the goal is accomplished; use conservatively")

    metadata_output_parser = PydanticOutputParser(pydantic_object=MetadataModel)
    prompt = extract_meta_prompt_template.format(
        format_instructions=metadata_output_parser.get_format_instructions(),
        instruction=instruction,
        extractcontent=raw,
        chunksSeen=1,
        chunksTotal=1,
    )

    # The combination of extract+meta is used to verify if the page is correct, values are stored in meta.
    meta_response = await llm.ainvoke(prompt)
    
    # Handle both string and coroutine content
    content = meta_response.content
    if hasattr(content, '__await__'):
        content = await content
    raw_meta = str(content or "")
    
    try:
        meta_response = metadata_output_parser.parse(raw_meta)
    except Exception as err:
        # If parsing fails, log error but don't interrupt flow
        print(f"Warning: Failed to parse metadata response: {err}")

    return extraction_response


async def infer_observe(
    instruction: str,
    dom_elements: str,
    from_act: bool = False,
    return_action: bool = True
) -> Dict[str, Any]:
    """Infer observation from DOM elements using instruction."""

    # Dynamically create schema, decide whether to include method and arguments fields based on return_action parameter
    if return_action:
        class DynamicElementSchema(BaseModel):
            elementId: str = Field(description="id string associated with this element. Do not include square brackets.")
            iframePath: str = Field(description="iframe name that the element belongs to, return empty string if none")
            description: str = Field(description="Description of the accessible element and its purpose")
            method: Optional[str] = Field(None, description="Candidate method/action for interacting with this element. Please choose one from available Playwright interaction methods.")
            arguments: List[str] = Field(default_factory=list, description="Parameters to pass to the method. For example, for `click`, parameters are empty; for `fill`, parameters are the values to fill.")
    else:
        class DynamicElementSchema(BaseModel):
            elementId: str = Field(description="id string associated with this element. Do not include square brackets.")
            iframePath: str = Field(description="iframe name that the element belongs to, return empty string if none")
            description: str = Field(description="Description of the accessible element and its purpose")

    class DynamicObserveResponse(BaseModel):
        elements: List[DynamicElementSchema] = Field(description="Array of accessible elements matching the instruction")

    observe_parser = PydanticOutputParser(pydantic_object=DynamicObserveResponse)

    prompt = observe_prompt_template.format(
        format_instructions=observe_parser.get_format_instructions(),
        instruction=instruction,
        accessibilityTree=dom_elements,
    )

    response = await llm.ainvoke(prompt)
    # Handle both string and coroutine content
    content = response.content
    if hasattr(content, '__await__'):
        content = await content
    raw = str(content or "")

    observe_response = None
    try:
        observe_response = observe_parser.parse(raw)
    except Exception as err:
        raise err

    parsed_elements = []
    if observe_response and observe_response.elements:
        for el in observe_response.elements:
            base = {
                "elementId": el.elementId,
                "description": str(el.description),
                "iframe_path": el.iframePath,
            }

            if return_action:
                parsed_elements.append({
                    **base,
                    "method": str(el.method) if hasattr(el, 'method') and el.method else None,
                    "arguments": el.arguments if hasattr(el, 'arguments') and el.arguments else [],
                })
            else:
                parsed_elements.append({
                    **base,
                    "method": None,
                    "arguments": [],
                })

    return {"elements": parsed_elements}
