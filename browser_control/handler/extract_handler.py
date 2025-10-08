# Copyright (c) 2025 Browserbase, Inc.
# Licensed under the MIT License.

from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel

from browser_control.inference import infer_extract
from browser_control.browser_types import ExtractOptions, ExtractResult, DefaultExtractSchema
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from browser_wrapper.stagehand import Stagehand

T = TypeVar('T', bound=BaseModel)

class ExtractHandler:
    """Handler for extracting data from web elements."""
    
    def __init__(self, stagehand: "Stagehand"):
        self._stagehand = stagehand
    
    async def extract(
        self, 
        instruction: Optional[str] = None,
        schema: Optional[Type[T]] = None
    ) -> Any:
        """Extract data using instruction and schema."""
        if not instruction:
            instruction = "Extract all text content from the page"
        
        if not schema:
            schema = DefaultExtractSchema
        
        return await self.dom_extract(instruction, schema)
    
    async def dom_extract(
        self, 
        instruction: str, 
        schema: Type[T]
    ) -> T:
        """Extract data from DOM using instruction and schema."""
        transformed_schema, _ = transform_url_strings_to_numeric_ids(schema)

        atree = await self._stagehand.page.get_a11y_tree()
        combined_tree = atree["combinedTree"]
        # combined_xpath_map = atree["combinedXpathMap"]
        # discovered_iframes = atree["discoveredIframes"]
        
        extraction_response = await infer_extract(instruction, combined_tree, transformed_schema)
        return extraction_response


def transform_url_strings_to_numeric_ids(schema: Type[BaseModel]) -> tuple[Type[BaseModel], List[Dict]]:
    """Transform URL strings to numeric IDs in schema - equivalent to transformUrlStringsToNumericIds in TS."""

    # Get model fields - Pydantic v2 compatibility
    fields = schema.model_fields
    new_fields = {}
    url_paths = []
    changed = False
    
    for field_name, field_info in fields.items():
        # Pydantic v2 uses annotation instead of type_
        field_type = field_info.annotation
        
        # Transform each field using the recursive transform_schema function
        from .utils.utils import transform_schema
        transformed_field, child_paths = transform_schema(field_type, [field_name])
        
        if transformed_field != field_type:
            changed = True
            # Pydantic v2 field creation
            from pydantic import FieldInfo
            new_fields[field_name] = FieldInfo(
                default=field_info.default,
                annotation=transformed_field,
                **{k: v for k, v in field_info.__dict__.items() if k not in ['annotation', 'default']}
            )
        else:
            new_fields[field_name] = field_info
        
        # Collect URL paths
        for cp in child_paths:
            url_paths.append({"segments": [field_name] + cp.segments})
    
    if changed:
        # Create new model class with transformed fields - Pydantic v2 compatibility
        new_model = type(
            f"{schema.__name__}Transformed",
            (BaseModel,),
            {'model_fields': new_fields}
        )
        return new_model, url_paths
    
    return schema, url_paths
