"""
Context type definitions
"""

from typing import Dict, List, Optional, Any, TypedDict, NewType
from playwright.async_api import Frame

# Type aliases
EncodedId = NewType('EncodedId', str)  # Format: "number-number"

class AXNode(TypedDict, total=False):
    """Accessibility node from CDP"""
    role: Optional[Dict[str, str]]
    name: Optional[Dict[str, str]]
    description: Optional[Dict[str, str]]
    value: Optional[Dict[str, str]]
    node_id: str
    backend_dom_node_id: Optional[int]
    parent_id: Optional[str]
    child_ids: Optional[List[str]]
    properties: Optional[List[Dict[str, Any]]]

class AccessibilityNode(TypedDict, total=False):
    """Simplified accessibility node"""
    role: str
    name: Optional[str]
    description: Optional[str]
    value: Optional[str]
    children: Optional[List['AccessibilityNode']]
    child_ids: Optional[List[str]]
    parent_id: Optional[str]
    node_id: Optional[str]
    backend_dom_node_id: Optional[int]
    properties: Optional[List[Dict[str, Any]]]

class TreeResult(TypedDict, total=False):
    """Tree processing result"""
    tree: List[AccessibilityNode]
    simplified: str
    iframes: Optional[List[AccessibilityNode]]
    id_to_url: Dict[EncodedId, str]
    xpath_map: Dict[EncodedId, str]

class DOMNode(TypedDict, total=False):
    """DOM node representation"""
    backend_node_id: Optional[int]
    node_name: Optional[str]
    children: Optional[List['DOMNode']]
    shadow_roots: Optional[List['DOMNode']]
    content_document: Optional['DOMNode']
    node_type: int
    frame_id: Optional[str]

class BackendIdMaps(TypedDict, total=False):
    """Backend ID mappings"""
    tag_name_map: Dict[int, str]
    xpath_map: Dict[int, str]
    iframe_xpath: Optional[str]

class CdpFrame(TypedDict, total=False):
    """CDP frame representation"""
    id: str
    parent_id: Optional[str]
    loader_id: str
    name: Optional[str]
    url: str
    url_fragment: Optional[str]
    domain_and_registry: Optional[str]
    security_origin: str
    security_origin_details: Optional[Dict[str, Any]]
    mime_type: str
    unreachable_url: Optional[str]
    ad_frame_status: Optional[str]
    secure_context_type: Optional[str]
    cross_origin_isolated_context_type: Optional[str]
    gated_api_features: Optional[List[str]]

class CdpFrameTree(TypedDict, total=False):
    """CDP frame tree"""
    frame: CdpFrame
    child_frames: Optional[List['CdpFrameTree']]

class FrameOwnerResult(TypedDict, total=False):
    """Frame owner result"""
    backend_node_id: Optional[int]

class CombinedA11yResult(TypedDict, total=False):
    """Combined accessibility result"""
    combined_tree: str
    combined_xpath_map: Dict[EncodedId, str]
    combined_url_map: Dict[EncodedId, str]

class A11Result(TypedDict, total=False):
    """Accessibility result"""
    combined_tree: str
    combined_xpath_map: Dict[EncodedId, str]
    combined_url_map: Optional[Dict[EncodedId, str]]
    discovered_iframes: List[AccessibilityNode]

class FrameSnapshot(TypedDict, total=False):
    """Frame snapshot"""
    frame: Frame
    tree: str
    xpath_map: Dict[EncodedId, str]
    url_map: Dict[EncodedId, str]
    frame_xpath: str
    backend_node_id: Optional[int]
    parent_frame: Optional[Frame]
    frame_id: Optional[str]

class RichNode(AccessibilityNode):
    """Rich accessibility node with encoded ID"""
    encoded_id: Optional[EncodedId]

# Pattern for ID validation
ID_PATTERN = r"^\d+-\d+$"

# Alias for backward compatibility
A11Resut = A11Result

class EnhancedContext(TypedDict, total=False):
    """Enhanced context interface"""
    # This extends PlaywrightBrowserContext with custom methods
    # The actual implementation would be in the context class
    pass
