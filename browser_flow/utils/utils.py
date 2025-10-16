import re
from typing import Any, Dict, List, Tuple, Union, Type, get_origin, get_args
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
import json

# ID pattern for element IDs in form 'frameId-backendId' (e.g. "0-432")
ID_PATTERN = re.compile(r'^\d+-\d+$')


class ZodPathSegments:
    """Path segments for schema transformation."""
    
    def __init__(self, segments: List[Union[str, int]]):
        self.segments = segments


def is_string_type(field_type: Type) -> bool:
    """Check if field type is a string type."""
    return field_type == str or (hasattr(field_type, '__origin__') and field_type.__origin__ is Union and str in get_args(field_type))


def is_optional_type(field_type: Type) -> bool:
    """Check if field type is Optional (Union with None)."""
    if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
        args = get_args(field_type)
        return type(None) in args
    return False


def is_list_type(field_type: Type) -> bool:
    """Check if field type is a list type."""
    return (hasattr(field_type, '__origin__') and 
            field_type.__origin__ in (list, List))


def is_union_type(field_type: Type) -> bool:
    """Check if field type is a Union type."""
    return (hasattr(field_type, '__origin__') and 
            field_type.__origin__ is Union and 
            type(None) not in get_args(field_type))


def make_id_string_schema(orig_field: FieldInfo) -> FieldInfo:
    """Create ID string schema for element IDs."""
    user_desc = orig_field.description or ""
    
    base = "This field must be the element-ID in the form 'frameId-backendId' (e.g. \"0-432\")."
    composed = f"{base} that follows this user-defined description: {user_desc}" if user_desc.strip() else base
    
    return Field(
        description=composed,
        pattern=ID_PATTERN.pattern,
        **orig_field.kwargs
    )


def transform_schema(
    field_type: Type, 
    current_path: List[Union[str, int]] = None
) -> Tuple[Type, List[ZodPathSegments]]:
    """Transform schema field by converting URL strings to numeric IDs - equivalent to transformSchema in TS."""
    if current_path is None:
        current_path = []
    
    # 1) If it's a string with URL validation, convert to ID string schema
    if is_string_type(field_type):
        # Check if field has URL validation (simplified check)
        # In a real implementation, you would check field constraints
        has_url_check = False  # This would need to be determined from field info
        
        if has_url_check:
            # Create a new field with ID pattern validation
            # This is a simplified implementation
            return str, [ZodPathSegments(segments=[])]
        return field_type, []
    
    # 2) If it's a Pydantic model, transform each field
    if hasattr(field_type, '__fields__'):  # It's a Pydantic model
        fields = field_type.__fields__
        new_fields = {}
        url_paths = []
        changed = False
        
        for field_name, field_info in fields.items():
            child_path = current_path + [field_name]
            transformed_child, child_paths = transform_schema(field_info.type_, child_path)
            
            if transformed_child != field_info.type_:
                changed = True
                new_fields[field_name] = field_info.__class__(
                    default=field_info.default,
                    type_=transformed_child,
                    **field_info.kwargs
                )
            else:
                new_fields[field_name] = field_info
            
            for cp in child_paths:
                url_paths.append(ZodPathSegments(segments=[field_name] + cp.segments))
        
        if changed:
            new_model = type(
                f"{field_type.__name__}Transformed",
                (BaseModel,),
                {'__fields__': new_fields}
            )
            return new_model, url_paths
        
        return field_type, url_paths
    
    # 3) If it's a list, transform its item type
    if is_list_type(field_type):
        item_type = get_args(field_type)[0]
        transformed_item, child_paths = transform_schema(item_type, current_path + ["*"])
        
        if transformed_item != item_type:
            return List[transformed_item], [ZodPathSegments(segments=["*"] + cp.segments) for cp in child_paths]
        
        return field_type, [ZodPathSegments(segments=["*"] + cp.segments) for cp in child_paths]
    
    # 4) If it's a union, transform each option
    if is_union_type(field_type):
        union_args = get_args(field_type)
        new_options = []
        all_paths = []
        changed = False
        
        for idx, option in enumerate(union_args):
            new_option, child_paths = transform_schema(option, current_path + [f"union_{idx}"])
            if new_option != option:
                changed = True
            new_options.append(new_option)
            all_paths.extend(child_paths)
        
        if changed:
            return Union[tuple(new_options)], all_paths
        
        return field_type, all_paths
    
    # 5) If it's optional, transform inner
    if is_optional_type(field_type):
        inner_type = get_args(field_type)[0]
        inner, inner_paths = transform_schema(inner_type, current_path)
        
        if inner != inner_type:
            from typing import Optional
            return Optional[inner], inner_paths
        
        return field_type, inner_paths
    
    # 6) If none of the above, return as-is
    return field_type, []


def transform_url_strings_to_numeric_ids(schema: Type[BaseModel]) -> Tuple[Type[BaseModel], List[Dict]]:
    """Transform URL strings to numeric IDs in schema."""
    transformed_schema, path_segments = transform_schema(schema)
    
    # Convert ZodPathSegments to dictionaries for compatibility
    path_dicts = [{"segments": ps.segments} for ps in path_segments]
    
    return transformed_schema, path_dicts


"""Utility functions for workflow."""
# Generate tool descriptions
def generate_tools_description(tools: List[Any]) -> str:
    """Generate description for available tools."""
    descriptions = []
    for tool in tools:
        # Get schema information safely
        schema_info = "No parameters"
        
        # Check if tool has args_schema attribute
        if hasattr(tool, 'args_schema') and tool.args_schema:
            try:
                # For Pydantic models, get field information
                if hasattr(tool.args_schema, 'model_fields'):
                    fields = tool.args_schema.model_fields
                    schema_info = json.dumps(
                        {name: field.description or str(field.annotation) for name, field in fields.items()}, indent=2,
                        ensure_ascii=False)
                else:
                    schema_info = str(tool.args_schema)
            except Exception:
                schema_info = "Failed to get parameter information"
        # For StructuredTool, try to get schema from the tool itself
        elif hasattr(tool, 'args') and tool.args:
            try:
                schema_info = str(tool.args)
            except Exception:
                schema_info = "Failed to get parameter information"

        descriptions.append(f"- {tool.name}: {tool.description}\n  Parameters: {schema_info}")

    return "\n\n".join(descriptions)
