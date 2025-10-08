"""
Accessibility utilities for getting accessibility trees
"""

import asyncio
import re
import json
from typing import Dict, List, Any, Optional, Callable, Set, Tuple, Union
from playwright.async_api import CDPSession, Frame
from ..browser_types import (
    AccessibilityNode, EncodedId, TreeResult, AXNode, DOMNode, BackendIdMaps,
    CdpFrameTree, FrameOwnerResult, FrameSnapshot, CombinedA11yResult, RichNode,
    ID_PATTERN, CdpFrame
)
from ..stagehand_page import StagehandPage
from ..browser_types import (
    ContentFrameNotFoundError, StagehandDomProcessError, StagehandElementNotFoundError,
    StagehandIframeError, XPathResolutionError
)

IFRAME_STEP_RE = re.compile(r'iframe\[\d+]$', re.IGNORECASE)
PUA_START = 0xe000
PUA_END = 0xf8ff

NBSP_CHARS = {0x00a0, 0x202f, 0x2007, 0xfeff}

WORLD_NAME = 'stagehand-world'


def clean_text(input_str: str) -> str:
    """
    Clean a string by removing private-use unicode characters, normalizing whitespace,
    and trimming the result.

    Args:
        input_str: The text to clean, potentially containing PUA and NBSP characters.

    Returns:
        A cleaned string with PUA characters removed, NBSP variants collapsed,
        consecutive spaces merged, and leading/trailing whitespace trimmed.
    """
    out = ''
    prev_was_space = False

    for i in range(len(input_str)):
        code = ord(input_str[i])

        # Skip private-use area glyphs
        if PUA_START <= code <= PUA_END:
            continue

        # Convert NBSP-family characters to a single space, collapsing repeats
        if code in NBSP_CHARS:
            if not prev_was_space:
                out += ' '
                prev_was_space = True
            continue

        # Append the character and update space tracker
        out += input_str[i]
        prev_was_space = input_str[i] == ' '

    # Trim leading/trailing spaces before returning
    return out.strip()


def format_simplified_tree(
        node: AccessibilityNode,
        level: int = 0
) -> str:
    """
    Generate a human-readable, indented outline of an accessibility node tree.

    Args:
        node: The accessibility node to format, optionally with an encodedId.
        level: The current depth level for indentation (used internally).

    Returns:
        A string representation of the node and its descendants, with one node per line.
    """
    # Compute indentation based on depth level
    indent = '  ' * level

    # Use encodedId if available, otherwise fallback to nodeId
    id_label = node.get('encodedId', None) or node.get('nodeId', '')

    # Prepare the formatted name segment if present
    name_part = f": {clean_text(node.get('name', ''))}" if node.get('name') else ''

    # Build current line and recurse into child nodes
    current_line = f"{indent}[{id_label}] {node.get('role', '')}{name_part}\n"
    children_lines = ''
    if node.get('children'):
        children_lines = ''.join(format_simplified_tree(child, level + 1) for child in node['children'])

    return current_line + children_lines


_lower_cache = {}


def lc(raw: str) -> str:
    """
    Memoized lowercase conversion for strings to avoid repeated .toLowerCase() calls.

    Args:
        raw: The original string to convert.

    Returns:
        The lowercase version of the input string, cached for future reuse.
    """
    if raw not in _lower_cache:
        _lower_cache[raw] = raw.lower()
    return _lower_cache[raw]


async def build_backend_id_maps(
        experimental: bool,
        sp: StagehandPage,
        target_frame: Optional[Frame] = None
) -> BackendIdMaps:
    """
    Build mappings from CDP backendNodeIds to HTML tag names and relative XPaths.

    Args:
        experimental: Whether to use experimental behaviour.
        sp: The StagehandPage wrapper for Playwright and CDP calls.
        target_frame: Optional Playwright.Frame whose DOM subtree to map; defaults to main frame.

    Returns:
        A Promise resolving to BackendIdMaps containing tagNameMap and xpathMap.
    """
    # 0. choose CDP session
    if not target_frame or target_frame == sp.page.main_frame:
        session = await sp.get_cdp_client()
    else:
        try:
            session = await sp.context.new_cdp_session(target_frame)  # OOPIF
        except:
            session = await sp.get_cdp_client()  # same-proc iframe

    await sp.enable_cdp('DOM', session == (await sp.get_cdp_client()) if target_frame is None else target_frame)

    try:
        # 1. full DOM tree
        result = await session.send('DOM.getDocument', {
            'depth': -1,
            'pierce': True,
        })
        root = result.get('root', {})

        # 2. pick start node + root frame-id
        start_node = root
        root_fid = target_frame and (await get_cdp_frame_id(sp, target_frame)) if target_frame else None

        if (target_frame and
                target_frame != sp.page.main_frame and
                session == (await sp.get_cdp_client())):
            # same-proc iframe: walk down to its contentDocument
            frame_id = root_fid
            frame_owner_result = await sp.send_cdp('DOM.getFrameOwner', {
                'frameId': frame_id,
            })
            backend_node_id = frame_owner_result.get('backendNodeId')

            iframe_node = None

            def locate(n):
                nonlocal iframe_node
                if experimental:
                    if n.get('backendNodeId') == backend_node_id:
                        iframe_node = n
                        return True
                    if n.get('shadowRoots') and any(locate(sr) for sr in n['shadowRoots']):
                        return True
                    if n.get('children') and any(locate(c) for c in n['children']):
                        return True
                    if n.get('contentDocument') and locate(n['contentDocument']):
                        return True
                    return False
                else:
                    if n.get('backendNodeId') == backend_node_id:
                        iframe_node = n
                        return True
                    return ((n.get('children') and any(locate(c) for c in n['children'])) or
                            (n.get('contentDocument') and locate(n['contentDocument'])) if n.get(
                        'contentDocument') else False)

            if not locate(root) or not iframe_node or not iframe_node.get('contentDocument'):
                raise Exception('iframe element or its contentDocument not found')
            start_node = iframe_node['contentDocument']
            root_fid = iframe_node['contentDocument'].get('frameId') or frame_id

        # 3. DFS walk: fill maps
        tag_name_map = {}
        xpath_map = {}

        class StackEntry:
            def __init__(self, node, path: str, fid: Optional[str] = None):
                self.node = node
                self.path = path
                self.fid = fid  # CDP frame-id of this node's doc

        stack = [StackEntry(start_node, '', root_fid)]
        seen = set()

        def join_step(base: str, step: str) -> str:
            return f"{base}{step}" if base.endswith('//') else f"{base}/{step}"

        while stack:
            entry = stack.pop()
            node = entry.node
            path = entry.path
            fid = entry.fid

            if not node.get('backendNodeId'):
                continue
            enc = sp.encode_with_frame_id(fid, node['backendNodeId'])
            if enc in seen:
                continue
            seen.add(enc)

            tag_name_map[enc] = lc(str(node.get('nodeName', '')))
            xpath_map[enc] = path

            # recurse into sub-document if <iframe>
            if (node.get('nodeName') and
                    lc(node.get('nodeName')) == 'iframe' and
                    node.get('contentDocument')):
                child_fid = node['contentDocument'].get('frameId') or fid
                stack.append(StackEntry(node['contentDocument'], '', child_fid))

            if node.get('shadowRoots') and experimental:
                for shadow_root in node['shadowRoots']:
                    stack.append(StackEntry(
                        shadow_root,
                        f"{path}//",
                        fid
                    ))

            # push children
            kids = node.get('children', [])
            if kids:
                # build per-child XPath segment (L→R)
                segs = []
                ctr = {}
                for child in kids:
                    tag = lc(str(child.get('nodeName', '')))
                    key = f"{child.get('nodeType', 1)}:{tag}"
                    idx = ctr.get(key, 0) + 1
                    ctr[key] = idx
                    if child.get('nodeType') == 3:
                        segs.append(f"text()[{idx}]")
                    elif child.get('nodeType') == 8:
                        segs.append(f"comment()[{idx}]")
                    else:
                        # Element node: if qualified (e.g. "as:ajaxinclude"), switch to name()='as:ajaxinclude'
                        segs.append(f"*[name()='{tag}'][{idx}]" if ':' in tag else f"{tag}[{idx}]")
                # push R→L so traversal remains L→R
                for i in range(len(kids) - 1, -1, -1):
                    stack.append(StackEntry(
                        kids[i],
                        join_step(path, segs[i]),
                        fid
                    ))

        return {'tagNameMap': tag_name_map, 'xpathMap': xpath_map}
    finally:
        await sp.disable_cdp('DOM', session == (await sp.get_cdp_client()) if target_frame is None else target_frame)


async def get_cdp_frame_id(sp: StagehandPage, frame: Optional[Frame] = None) -> Optional[str]:
    """
    Resolve the CDP frame identifier for a Playwright Frame, handling same-process and OOPIF.

    Args:
        sp: The StagehandPage instance for issuing CDP commands.
        frame: The target Playwright.Frame; undefined or main frame yields undefined.

    Returns:
        A Promise resolving to the CDP frameId string, or undefined for main document.
    """
    if not frame or frame == sp.page.main_frame:
        return None

    # 1. Same-proc search in the page-session tree
    root_resp = await sp.send_cdp('Page.getFrameTree')
    root = root_resp.get('frameTree', {})

    target_url = frame.url
    depth = 0
    p = frame.parent_frame
    while p:
        depth += 1
        p = p.parent_frame

    def with_fragment(f):
        return f.get('url', '') + (f.get('urlFragment', '') or '')

    def find_by_url_depth(node, lvl=0):
        if lvl == depth and with_fragment(node.get('frame', {})) == target_url:
            return node.get('frame', {}).get('id')
        for child in node.get('childFrames', []):
            id_result = find_by_url_depth(child, lvl + 1)
            if id_result:
                return id_result
        return None

    same_proc_id = find_by_url_depth(root)
    if same_proc_id:
        return same_proc_id  # found in page tree

    # 2. OOPIF path: open its own target
    try:
        sess = await sp.context.new_cdp_session(frame)  # throws if detached

        own_resp = await sess.send('Page.getFrameTree')
        frame_tree = own_resp.get('frameTree', {})

        return frame_tree.get('frame', {}).get('id')  # root of OOPIF
    except Exception as err:
        raise StagehandIframeError(target_url, str(err))


def inject_subtrees(tree: str, id_to_tree: Dict[EncodedId, str]) -> str:
    """
    Inject simplified subtree outlines into the main frame outline for nested iframes.
    Walks the main tree text, looks for EncodedId labels, and inserts matching subtrees.

    Args:
        tree: The indented AX outline of the main frame.
        id_to_tree: Map of EncodedId to subtree outlines for nested frames.

    Returns:
        A single combined text outline with iframe subtrees injected.
    """

    def unique_by_backend(backend_id: int) -> Optional[EncodedId]:
        """Return the *only* EncodedId that ends with this backend-id.
        If several frames share that backend-id we return None
        (avoids guessing the wrong subtree)."""
        found = None
        hit = 0
        for enc in id_to_tree.keys():
            parts = enc.split('-')  # "ff-bbb"
            if len(parts) == 2:
                try:
                    b = int(parts[1])
                    if b == backend_id:
                        hit += 1
                        if hit > 1:
                            return None  # collision → abort
                        found = enc
                except ValueError:
                    continue
        return found if hit == 1 else None

    class StackFrame:
        def __init__(self, lines: List[str], idx: int, indent: str):
            self.lines = lines
            self.idx = idx
            self.indent = indent

    stack = [StackFrame(tree.split('\n'), 0, '')]
    out = []
    visited = set()  # avoid infinite loops

    # Depth-first injection walk
    while stack:
        top = stack[-1]

        if top.idx >= len(top.lines):
            stack.pop()
            continue

        raw = top.lines[top.idx]
        top.idx += 1
        line = top.indent + raw
        out.append(line)

        # grab whatever sits inside the first brackets, e.g. "[0-42]" or "[42]"
        m = re.match(r'^\s*\[([^\]]+)\]', raw)
        if not m:
            continue

        label = m[1]  # could be "1-13" or "13"
        enc = None
        child = None

        # 1 exact match ("<ordinal>-<backend>") or fallback by backend ID
        if label in id_to_tree:
            enc = label
            child = id_to_tree[enc]
        else:
            # attempt to extract backendId from "<ordinal>-<backend>" or pure numeric label
            backend_id = None
            dash_match = re.match(ID_PATTERN, label) if hasattr(ID_PATTERN, 'match') else None
            if dash_match:
                backend_id = int(dash_match.group(0).split('-')[1])
            elif re.match(r'^\d+$', label):
                backend_id = int(label)
            if backend_id is not None:
                alt = unique_by_backend(backend_id)
                if alt:
                    enc = alt
                    child = id_to_tree[alt]

        if not enc or not child or enc in visited:
            continue

        visited.add(enc)
        indent_match = re.match(r'^\s*', line)
        indent_str = indent_match.group(0) if indent_match else ''
        stack.append(StackFrame(
            child.split('\n'),
            0,
            indent_str + '  '
        ))

    return '\n'.join(out)


async def get_accessibility_tree_with_frames(
        experimental: bool,
        stagehand_page: StagehandPage,
        logger: Callable,
        root_xpath: Optional[str] = None
) -> CombinedA11yResult:
    """
    Retrieve and merge accessibility trees for the main document and nested iframes.
    Walks through frame chains if a root XPath is provided, then stitches subtree outlines.

    Args:
        experimental: Whether to use experimental behaviour.
        stagehand_page: The StagehandPage instance for Playwright and CDP interaction.
        logger: Logging function for diagnostics and performance.
        root_xpath: Optional absolute XPath to focus the crawl on a subtree across frames.

    Returns:
        A Promise resolving to CombinedA11yResult with combined tree text, xpath map, and URL map.
    """
    # 0. main-frame bookkeeping
    main = stagehand_page.page.main_frame

    # 1. "focus XPath" → frame chain + inner XPath
    target_frames = None  # full chain, main-first
    inner_xpath = None

    if root_xpath and root_xpath.strip():
        frame_chain_result = await resolve_frame_chain(stagehand_page, root_xpath.strip())
        target_frames = frame_chain_result['frames'] if frame_chain_result['frames'] else None
        inner_xpath = frame_chain_result['rest']

    main_only_filter = bool(inner_xpath and not target_frames)

    # 2. depth-first walk – collect snapshots
    snapshots = []
    frame_stack = [main]

    while frame_stack:
        frame = frame_stack.pop()

        # unconditional: enqueue children so we can reach deep targets
        for c in frame.child_frames:
            frame_stack.append(c)

        # skip frames that are outside the requested chain / slice
        if target_frames and frame not in target_frames:
            continue
        if not target_frames and frame != main and inner_xpath:
            continue

        # selector to forward (unchanged)
        selector = None
        if target_frames:
            if frame == target_frames[-1]:
                selector = inner_xpath
        else:
            if frame == main:
                selector = inner_xpath

        try:
            res = await get_accessibility_tree(experimental, stagehand_page, logger, selector, frame)

            # guard: main frame has no backendNodeId
            backend_id = None if frame == main else await get_frame_root_backend_node_id(stagehand_page, frame)

            if experimental:
                frame_xpath = '/' if frame == main else await get_frame_root_xpath_with_shadow(frame)
            else:
                frame_xpath = '/' if frame == main else await get_frame_root_xpath(frame)

            # Resolve the CDP frameId for this Playwright Frame (undefined for main)
            frame_id = await get_cdp_frame_id(stagehand_page, frame)

            snapshots.append({
                'frame': frame,
                'tree': res['simplified'].rstrip(),
                'xpathMap': res['xpathMap'],
                'urlMap': res['idToUrl'],
                'frameXpath': frame_xpath,
                'backendNodeId': backend_id,
                'parentFrame': frame.parent_frame,
                'frameId': frame_id,
            })

            if main_only_filter:
                break  # nothing else to fetch
        except Exception as err:
            # 安全地处理错误信息，避免JSON序列化问题
            error_msg = str(err).replace("'", '"').replace('\n', ' ').replace('\r', ' ')
            logger({
                'category': 'observation',
                'message': f"⚠️ failed to get AX tree for {'main frame' if frame == main else f'iframe ({frame.url})'}",
                'level': 1,
                'auxiliary': {'error': {'value': error_msg, 'type': 'string'}}
            })

    # 3. merge per-frame maps
    combined_xpath_map = {}
    combined_url_map = {}

    seg = {}
    for s in snapshots:
        seg[s['frame']] = s['frameXpath']

    def full_prefix(f):
        """recursively build the full prefix for a frame"""
        if not f or f == main:
            return ''
        parent = f.parent_frame
        above = full_prefix(parent)
        hop = seg.get(f, '')
        if hop == '/':
            return above
        elif above:
            return f"{above.rstrip('/')}/{hop.lstrip('/')}"
        else:
            return hop

    for snap in snapshots:
        prefix = '' if snap['frameXpath'] == '/' else f"{full_prefix(snap['parentFrame'])}{snap['frameXpath']}"

        for enc, local in snap['xpathMap'].items():
            if local == '':
                combined_xpath_map[enc] = prefix or '/'
            elif prefix:
                combined_xpath_map[enc] = f"{prefix.rstrip('/')}/{local.lstrip('/')}"
            else:
                combined_xpath_map[enc] = local

        combined_url_map.update(snap['urlMap'])

    # 4. EncodedId → subtree map (skip main)
    id_to_tree = {}
    for snap in snapshots:
        backend_node_id = snap['backendNodeId']
        frame_id = snap['frameId']
        tree = snap['tree']
        if backend_node_id is not None and frame_id is not None:
            # ignore main frame and snapshots without a CDP frameId
            id_to_tree[stagehand_page.encode_with_frame_id(frame_id, backend_node_id)] = tree

    # 5. stitch everything together
    root_snap = next((s for s in snapshots if s['frameXpath'] == '/'), None)
    combined_tree = ''
    if root_snap:
        combined_tree = inject_subtrees(root_snap['tree'], id_to_tree)
    elif snapshots:
        combined_tree = snapshots[0]['tree']

    return {
        'combinedTree': combined_tree,
        'combinedXpathMap': combined_xpath_map,
        'combinedUrlMap': combined_url_map,
        'discoveredIframes': []  # 与TypeScript版本保持一致
    }


async def get_accessibility_tree(
        experimental: bool,
        stagehand_page: StagehandPage,
        logger: Callable,
        selector: Optional[str] = None,
        target_frame: Optional[Frame] = None
) -> TreeResult:
    """
    Retrieve and build a cleaned accessibility tree for a document or specific iframe.
    Prunes, formats, and optionally filters by XPath, including scrollable role decoration.

    Args:
        experimental: Whether to use experimental behaviour.
        stagehand_page: The StagehandPage instance for Playwright and CDP interaction.
        logger: Logging function for diagnostics and performance metrics.
        selector: Optional XPath to filter the AX tree to a specific subtree.
        target_frame: Optional Playwright.Frame to scope the AX tree retrieval.

    Returns:
        A Promise resolving to a TreeResult with the hierarchical AX tree and related metadata.
    """
    # 0. DOM helpers (maps, xpath)
    backend_maps = await build_backend_id_maps(experimental, stagehand_page, target_frame)
    tag_name_map = backend_maps['tagNameMap']
    xpath_map = backend_maps['xpathMap']

    await stagehand_page.enable_cdp('Accessibility', target_frame)

    try:
        # 1. Decide params + session for the CDP call
        params = {}
        session_frame = target_frame  # default: talk to that frame

        if target_frame and target_frame != stagehand_page.page.main_frame:
            # 更准确的OOPIF检测逻辑
            # 对于file://协议的iframe，即使能创建CDP会话也应该是same-proc
            main_url = stagehand_page.page.main_frame.url
            target_url = target_frame.url

            # 检查是否是真正的OOPIF（不同origin）
            main_origin = main_url.split('/')[0:3] if '://' in main_url else ['file', '', '']
            target_origin = target_url.split('/')[0:3] if '://' in target_url else ['file', '', '']

            # 如果origin相同，则认为是same-proc iframe
            if main_origin == target_origin:
                is_oopif = False
            else:
                # try opening a CDP session: succeeds only for OOPIFs
                is_oopif = True
                try:
                    await stagehand_page.context.new_cdp_session(target_frame)
                except:
                    is_oopif = False

            if not is_oopif:
                # same-proc → use *page* session + { frameId }
                frame_id = await get_cdp_frame_id(stagehand_page, target_frame)
                logger({
                    'message': f"same-proc iframe: frameId={frame_id}. Using existing CDP session.",
                    'level': 1,
                })
                if frame_id:
                    params = {'frameId': frame_id}
                session_frame = None  # page session
            else:
                logger({'message': 'OOPIF iframe: starting new CDP session', 'level': 1})
                params = {}  # no frameId allowed
                session_frame = target_frame  # talk to OOPIF session

        # 2. Fetch raw AX nodes
        if session_frame:
            client = await stagehand_page.context.new_cdp_session(session_frame)
        else:
            client = await stagehand_page.get_cdp_client()

        result = await client.send('Accessibility.getFullAXTree', params)
        full_nodes = result.get('nodes', [])

        # 3. Scrollable detection
        scrollable_ids = await find_scrollable_element_ids(stagehand_page, target_frame)

        # 4. Filter by xpath if one is given
        nodes = full_nodes
        if selector:
            nodes = await filter_ax_tree_by_xpath(stagehand_page, full_nodes, selector, target_frame)

        # 5. Build hierarchical tree
        start = asyncio.get_event_loop().time()
        tree = await build_hierarchical_tree(
            decorate_roles(nodes, scrollable_ids),
            tag_name_map,
            logger,
            xpath_map
        )

        logger({
            'category': 'observation',
            'message': f"got accessibility tree in {(asyncio.get_event_loop().time() - start) * 1000:.0f} ms",
            'level': 1,
        })
        return tree
    finally:
        await stagehand_page.disable_cdp('Accessibility', target_frame)


async def build_hierarchical_tree(
        nodes: List[AccessibilityNode],
        tag_name_map: Dict[EncodedId, str],
        logger: Optional[Callable] = None,
        xpath_map: Optional[Dict[EncodedId, str]] = None
) -> TreeResult:
    """
    Convert a flat array of AccessibilityNodes into a cleaned, hierarchical tree.
    Nodes are pruned, structural wrappers removed, and each kept node is stamped
    with its EncodedId for later lookup or subtree injection.

    Args:
        nodes: Raw flat list of AX nodes retrieved via CDP.
        tag_name_map: Mapping of EncodedId to HTML tag names for structural decisions.
        logger: Optional function for logging diagnostic messages.
        xpath_map: Optional mapping of EncodedId to relative XPath for element lookup.

    Returns:
        A Promise resolving to a TreeResult with cleaned tree, simplified text outline,
        iframe list, URL map, and inherited xpathMap.
    """
    # EncodedId → URL (only if the backend-id is unique)
    id_to_url = {}

    # nodeId (string) → mutable copy of the AX node we keep
    node_map = {}

    # list of iframe AX nodes
    iframe_list = []

    # helper: keep only roles that matter to the LLM
    def is_interactive(n: AccessibilityNode) -> bool:
        return n.get('role', '') not in ['none', 'generic', 'InlineTextBox']

    # Build "backendId → EncodedId[]" lookup from tagNameMap keys
    backend_to_ids = {}
    for enc in tag_name_map.keys():
        parts = enc.split('-')  # "ff-bb"
        if len(parts) == 2:
            try:
                backend_id = int(parts[1])
                if backend_id not in backend_to_ids:
                    backend_to_ids[backend_id] = []
                backend_to_ids[backend_id].append(enc)
            except ValueError:
                continue

    # Pass 1 – copy / filter CDP nodes we want to keep
    for node in nodes:
        if int(node.get('nodeId', '0')) < 0:
            continue  # skip pseudo-nodes

        url = extract_url_from_ax_node(node)

        keep = ((node.get('name') or '').strip() or
                len(node.get('childIds', [])) > 0 or
                is_interactive(node))
        if not keep:
            continue

        # resolve our EncodedId (unique per backendId)
        encoded_id = None
        if node.get('backendDOMNodeId') is not None:
            matches = backend_to_ids.get(node['backendDOMNodeId'], [])
            if len(matches) == 1:
                encoded_id = matches[0]  # unique → keep
            # if there are collisions we leave encodedId undefined; subtree
            # injection will fall back to backend-id matching

        # store URL only when we have an unambiguous EncodedId
        if url and encoded_id:
            id_to_url[encoded_id] = url

        node_map[node['nodeId']] = {
            'encodedId': encoded_id,
            'role': node.get('role', ''),
            'nodeId': node.get('nodeId'),
            **({'name': node['name']} if node.get('name') else {}),
            **({'description': node['description']} if node.get('description') else {}),
            **({'value': node['value']} if node.get('value') else {}),
            **({'backendDOMNodeId': node['backendDOMNodeId']} if node.get('backendDOMNodeId') is not None else {}),
        }

    # Pass 2 – parent-child wiring
    for node in nodes:
        if node.get('role') == 'Iframe':
            iframe_list.append({'role': node['role'], 'nodeId': node['nodeId']})

        if not node.get('parentId'):
            continue
        parent = node_map.get(node['parentId'])
        current = node_map.get(node['nodeId'])
        if parent and current:
            if 'children' not in parent:
                parent['children'] = []
            parent['children'].append(current)

    # Pass 3 – prune structural wrappers & tidy tree
    roots = [node_map[node['nodeId']] for node in nodes
             if not node.get('parentId') and node['nodeId'] in node_map]

    cleaned_roots = []
    for n in roots:
        cleaned = await clean_structural_nodes(n, tag_name_map, logger)
        if cleaned:
            cleaned_roots.append(cleaned)

    # pretty outline for logging / LLM input
    simplified = '\n'.join(format_simplified_tree(root) for root in cleaned_roots)

    return {
        'tree': cleaned_roots,
        'simplified': simplified,
        'iframes': iframe_list,
        'idToUrl': id_to_url,
        'xpathMap': xpath_map or {},
    }


async def clean_structural_nodes(
        node: AccessibilityNode,
        tag_name_map: Dict[EncodedId, str],
        logger: Optional[Callable] = None
) -> Optional[AccessibilityNode]:
    """
    Recursively prune or collapse structural nodes in the AX tree to simplify hierarchy.

    Args:
        node: The accessibility node to clean, potentially collapsing or dropping generic/none roles.
        tag_name_map: Mapping from EncodedId to HTML tag names for potential role reassignment.
        logger: Optional logging callback for diagnostic messages.

    Returns:
        A Promise resolving to a cleaned AccessibilityNode or null if the node should be removed.
    """
    # 0. ignore negative pseudo-nodes
    if int(node.get('nodeId', '0')) < 0:
        return None

    # 1. leaf check
    if not node.get('children') or len(node['children']) == 0:
        return None if node.get('role') in ['generic', 'none'] else node

    # 2. recurse into children
    cleaned_children = []
    for c in node.get('children', []):
        cleaned = await clean_structural_nodes(c, tag_name_map, logger)
        if cleaned:
            cleaned_children.append(cleaned)

    # 3. collapse / prune generic wrappers
    if node.get('role') in ['generic', 'none']:
        if len(cleaned_children) == 1:
            # Collapse single-child structural node
            return cleaned_children[0]
        elif len(cleaned_children) == 0:
            # Remove empty structural node
            return None

    # 4. replace generic role with real tag name (if we know it)
    if (node.get('role') in ['generic', 'none'] and
            node.get('encodedId') is not None and
            node['encodedId'] in tag_name_map):
        node = node.copy()
        node['role'] = tag_name_map[node['encodedId']]

    if (node.get('role') == 'combobox' and
            node.get('encodedId') is not None and
            tag_name_map.get(node['encodedId']) == 'select'):
        node = node.copy()
        node['role'] = 'select'

    # 5. drop redundant StaticText children
    pruned = remove_redundant_static_text_children(node, cleaned_children)
    if not pruned and node.get('role') in ['generic', 'none']:
        return None

    # 6. return updated node
    return {**node, 'children': pruned}


def remove_redundant_static_text_children(
        parent: AccessibilityNode,
        children: List[AccessibilityNode]
) -> List[AccessibilityNode]:
    """
    Remove StaticText children whose combined text matches the parent's accessible name.

    Args:
        parent: The parent AccessibilityNode whose `.name` is used for comparison.
        children: The list of child nodes to filter.

    Returns:
        A new array of children with redundant StaticText nodes removed when they duplicate the parent's name.
    """
    # If the parent has no accessible name, there is nothing to compare
    if not parent.get('name'):
        return children

    # Normalize and trim the parent's name for accurate string comparison
    parent_norm = normalise_spaces(parent['name']).strip()
    combined_text = ''

    # Concatenate all StaticText children's normalized names
    for child in children:
        if child.get('role') == 'StaticText' and child.get('name'):
            combined_text += normalise_spaces(child['name']).strip()

    # If combined StaticText equals the parent's name, filter them out
    if combined_text == parent_norm:
        return [c for c in children if c.get('role') != 'StaticText']
    return children


def normalise_spaces(s: str) -> str:
    """
    Collapse consecutive whitespace characters (spaces, tabs, newlines, carriage returns)
    into single ASCII spaces.

    Args:
        s: The string in which to normalize whitespace.

    Returns:
        A string where runs of whitespace have been replaced by single spaces.
    """
    # Initialize output buffer and state flag for whitespace grouping
    out = ''
    in_ws = False

    # Iterate through each character of the input string
    for i in range(len(s)):
        ch = ord(s[i])
        is_ws = ch in [32, 9, 10, 13]  # space, tab, newline, carriage return

        if is_ws:
            # If this is the first whitespace in a sequence, append a single space
            if not in_ws:
                out += ' '
                in_ws = True
        else:
            # Non-whitespace character: append it and reset whitespace flag
            out += s[i]
            in_ws = False

    return out


def extract_url_from_ax_node(ax_node: AccessibilityNode) -> Optional[str]:
    """
    Extract the URL string from an AccessibilityNode's properties, if present.

    Args:
        ax_node: The AccessibilityNode to inspect for a 'url' property.

    Returns:
        The URL string if found and valid; otherwise, None.
    """
    # Exit early if there are no properties on this node
    if not ax_node.get('properties'):
        return None

    # Find a property named 'url'
    url_prop = next((prop for prop in ax_node['properties'] if prop.get('name') == 'url'), None)
    # Return the trimmed URL string if the property exists and is valid
    if url_prop and url_prop.get('value') and isinstance(url_prop['value'].get('value'), str):
        return url_prop['value']['value'].strip()
    return None


async def find_scrollable_element_ids(
        stagehand_page: StagehandPage,
        target_frame: Optional[Frame] = None
) -> Set[int]:
    """
    `findScrollableElementIds` is a function that identifies elements in
    the browser that are deemed "scrollable". At a high level, it does the
    following:
    - Calls the browser-side `window.getScrollableElementXpaths()` function,
      which returns a list of XPaths for scrollable containers.
    - Iterates over the returned list of XPaths, locating each element in the DOM
      using `stagehandPage.sendCDP(...)`
        - During each iteration, we call `Runtime.evaluate` to run `document.evaluate(...)`
          with each XPath, obtaining a `RemoteObject` reference if it exists.
        - Then, for each valid object reference, we call `DOM.describeNode` to retrieve
          the element's `backendNodeId`.
    - Collects all resulting `backendNodeId`s in a Set and returns them.

    Args:
        stagehand_page: A StagehandPage instance with built-in CDP helpers.
        target_frame: Optional target frame for evaluation.

    Returns:
        A Promise that resolves to a Set of unique `backendNodeId`s corresponding
        to scrollable elements in the DOM.
    """
    # JS runs inside the right browsing context
    if target_frame:
        xpaths = await target_frame.evaluate("() => window.getScrollableElementXpaths()")
    else:
        xpaths = await stagehand_page.page.evaluate("() => window.getScrollableElementXpaths()")

    backend_ids = set()

    for xpath in xpaths:
        if not xpath:
            continue

        object_id = await resolve_object_id_for_xpath(stagehand_page, xpath, target_frame)

        if object_id:
            result = await stagehand_page.send_cdp('DOM.describeNode', {'objectId': object_id}, target_frame)
            node = result.get('node', {})
            if node.get('backendNodeId'):
                backend_ids.add(node['backendNodeId'])

    return backend_ids


async def resolve_object_id_for_xpath(
        page: StagehandPage,
        xpath: str,
        target_frame: Optional[Frame] = None
) -> Optional[str]:
    """
    Resolve an XPath to a Chrome-DevTools-Protocol (CDP) remote-object ID.

    Args:
        page: A StagehandPage (or Playwright.Page with .sendCDP)
        xpath: An absolute or relative XPath
        target_frame: Optional target frame for evaluation.

    Returns:
        The remote objectId for the matched node, or null
    """
    context_id = await get_frame_execution_context_id(page, target_frame)

    result = await page.send_cdp(
        'Runtime.evaluate',
        {
            'expression': f"""
                (() => {{
                    const res = document.evaluate(
                        {json.dumps(xpath)},
                        document,
                        null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE,
                        null
                    );
                    return res.singleNodeValue;
                }})();
            """,
            'returnByValue': False,
            **({'contextId': context_id} if context_id is not None else {}),
        },
        target_frame
    )
    if not result.get('result', {}).get('objectId'):
        raise StagehandElementNotFoundError([xpath])
    return result['result']['objectId']


async def get_frame_execution_context_id(
        stagehand_page: StagehandPage,
        frame: Optional[Frame] = None
) -> Optional[int]:
    """
    Returns a stable executionContextId for the given frame by creating (or reusing)
    an isolated world in that frame.
    """
    if not frame or frame == stagehand_page.page.main_frame:
        # Main frame (or no frame): use the default world.
        return None

    frame_id = await get_cdp_frame_id(stagehand_page, frame)
    result = await stagehand_page.send_cdp(
        'Page.createIsolatedWorld',
        {
            'frameId': frame_id,
            'worldName': WORLD_NAME,
            'grantUniversalAccess': True,
        },
        frame
    )

    return result.get('executionContextId')


async def filter_ax_tree_by_xpath(
        page: StagehandPage,
        full: List[AXNode],
        xpath: str,
        target_frame: Optional[Frame] = None
) -> List[AXNode]:
    """
    Filter an accessibility tree to include only the subtree under a specific XPath root.
    Resolves the DOM node for the XPath and performs a BFS over the AX node graph.

    Args:
        page: The StagehandPage instance for issuing CDP commands.
        full: The full list of AXNode entries to filter.
        xpath: The XPath expression locating the subtree root.
        target_frame: Optional Playwright.Frame context for CDP evaluation.

    Returns:
        A Promise resolving to an array of AXNode representing the filtered subtree.
    """
    # Resolve the backendNodeId for the element at the provided XPath
    object_id = await resolve_object_id_for_xpath(page, xpath, target_frame)
    # Describe the DOM node to retrieve its backendNodeId via CDP
    result = await page.send_cdp('DOM.describeNode', {'objectId': object_id}, target_frame)
    node = result.get('node', {})
    backend_node_id = node.get('backendNodeId')

    # Throw if unable to get a backendNodeId for the XPath target
    if not backend_node_id:
        raise StagehandDomProcessError(f'Unable to resolve backendNodeId for "{xpath}"')

    # Locate the corresponding AXNode in the full tree
    target = next((n for n in full if n.get('backendDOMNodeId') == backend_node_id), None)
    if not target:
        raise StagehandDomProcessError(f'Target node not found in accessibility tree')

    # Initialize BFS: collect the target node and its descendants
    keep = {target['nodeId']}
    queue = [target]
    while queue:
        cur = queue.pop(0)
        for child_id in cur.get('childIds', []):
            if child_id in keep:
                continue
            keep.add(child_id)
            child = next((n for n in full if n.get('nodeId') == child_id), None)
            if child:
                queue.append(child)

    # Return only nodes in the keep set, unsetting parentId for the new root
    return [
        {**n, 'parentId': None} if n.get('nodeId') == target['nodeId'] else n
        for n in full if n.get('nodeId') in keep
    ]


def decorate_roles(nodes: List[AXNode], scrollables: Set[int]) -> List[AccessibilityNode]:
    """
    Decorate AX nodes by marking scrollable elements in their role property.

    Args:
        nodes: Array of raw AXNode entries to decorate with scrollability.
        scrollables: Set of backendNodeId values representing scrollable elements.

    Returns:
        A new array of AccessibilityNode objects with updated roles indicating scrollable elements.
    """
    return [
        {
            'role': (
                f"scrollable, {n.get('role', {}).get('value', '')}"
                if n.get('role', {}).get('value') and n.get('role', {}).get('value') not in ['generic', 'none']
                else 'scrollable'
            ) if n.get('backendDOMNodeId') in scrollables else n.get('role', {}).get('value', ''),
            'name': n.get('name', {}).get('value'),
            'description': n.get('description', {}).get('value'),
            'value': n.get('value', {}).get('value'),
            'nodeId': n.get('nodeId'),
            'backendDOMNodeId': n.get('backendDOMNodeId'),
            'parentId': n.get('parentId'),
            'childIds': n.get('childIds'),
            'properties': n.get('properties'),
        }
        for n in nodes
    ]


async def get_frame_root_backend_node_id(
        sp: StagehandPage,
        frame: Optional[Frame] = None
) -> Optional[int]:
    """
    Get the backendNodeId of the iframe element that contains a given Playwright.Frame.

    Args:
        sp: The StagehandPage instance for issuing CDP commands.
        frame: The Playwright.Frame whose host iframe element to locate.

    Returns:
        A Promise resolving to the backendNodeId of the iframe element, or null if not applicable.
    """
    # Return null for top-level or undefined frames
    if not frame or frame == sp.page.main_frame:
        return None

    # Create a CDP session on the main page context
    cdp = await sp.page.context().new_cdp_session(sp.page)
    # Resolve the CDP frameId for the target iframe frame
    fid = await get_cdp_frame_id(sp, frame)
    if not fid:
        return None

    # Retrieve the DOM node that owns the frame via CDP
    result = await cdp.send('DOM.getFrameOwner', {'frameId': fid})
    return result.get('backendNodeId')


async def get_frame_root_xpath_with_shadow(frame: Optional[Frame]) -> str:
    """
    Compute the absolute XPath for the iframe element hosting a given Playwright.Frame.

    Args:
        frame: The Playwright.Frame whose iframe element to locate.

    Returns:
        A Promise resolving to the XPath of the iframe element, or "/" if no frame provided.
    """
    # Return root path when no frame context is provided
    if not frame:
        return '/'

    # Obtain the element handle of the iframe in the embedding document
    handle = await frame.frame_element()
    # Evaluate the element's absolute XPath within the page context
    return await handle.evaluate("""
        (node) => {
            function stepFor(el) {
                const tag = el.tagName.toLowerCase();
                let i = 1;
                for (let sib = el.previousElementSibling; sib; sib = sib.previousElementSibling) {
                    if (sib.tagName.toLowerCase() === tag) i++;
                }
                return `${tag}[${i}]`;
            }

            const segs = [];
            let el = node;

            while (el) {
                segs.unshift(stepFor(el));
                if (el.parentElement) {
                    el = el.parentElement;
                    continue;
                }

                // top of this tree: check if we're inside a shadow root
                const root = el.getRootNode(); // Document or ShadowRoot
                if (root.host) {
                    // Insert a shadow hop marker so the final path contains "//"
                    segs.unshift('');
                    el = root.host;
                    continue;
                }

                break;
            }

            // Leading '/' + join; empty tokens become "//" between segments
            return '/' + segs.join('/');
        }
    """)


async def get_frame_root_xpath(frame: Optional[Frame]) -> str:
    """
    Compute the absolute XPath for the iframe element hosting a given Playwright.Frame.

    Args:
        frame: The Playwright.Frame whose iframe element to locate.

    Returns:
        A Promise resolving to the XPath of the iframe element, or "/" if no frame provided.
    """
    # Return root path when no frame context is provided
    if not frame:
        return '/'

    # Obtain the element handle of the iframe in the embedding document
    handle = await frame.frame_element()
    # Evaluate the element's absolute XPath within the page context
    return await handle.evaluate("""
        (node) => {
            const pos = (el) => {
                let i = 1;
                for (let sib = el.previousElementSibling; sib; sib = sib.previousElementSibling)
                    if (sib.tagName === el.tagName) i += 1;
                return i;
            };
            const segs = [];
            for (let el = node; el; el = el.parentElement)
                segs.unshift(`${el.tagName.toLowerCase()}[${pos(el)}]`);
            return `/${segs.join('/')}`;
        }
    """)


async def resolve_frame_chain(
        sp: StagehandPage,
        abs_path: str  # must start with '/'
) -> Dict[str, Any]:
    """
    Resolve a chain of iframe frames from an absolute XPath, returning the frame sequence and inner XPath.

    This helper walks an XPath expression containing iframe steps (e.g., '/html/body/iframe[2]/...'),
    descending into each matching iframe element to build a frame chain, and returns the leftover
    XPath segment to evaluate within the context of the last iframe.

    Args:
        sp: The StagehandPage instance for evaluating XPath and locating frames.
        abs_path: An absolute XPath expression starting with '/', potentially including iframe steps.

    Returns:
        An object containing:
        frames: Array of Frame objects representing each iframe in the chain.
        rest: The remaining XPath string to evaluate inside the final iframe.

    Raises:
        Error if an iframe cannot be found or the final XPath cannot be resolved.
    """
    path = abs_path if abs_path.startswith('/') else '/' + abs_path
    ctx_frame = None  # current frame
    chain = []  # collected frames

    while True:
        # Does the whole path already resolve inside the current frame?
        try:
            await resolve_object_id_for_xpath(sp, path, ctx_frame)
            return {'frames': chain, 'rest': path}  # we're done
        except:
            # keep walking
            pass

        # Otherwise: accumulate steps until we include an <iframe> step
        steps = [s for s in path.split('/') if s]
        buf = []

        for i in range(len(steps)):
            buf.append(steps[i])

            if IFRAME_STEP_RE.match(steps[i]):
                # "/…/iframe[k]" found – descend into that frame
                selector = 'xpath=/' + '/'.join(buf)
                handle = (ctx_frame or sp.page.main_frame).locator(selector)
                frame = await handle.element_handle().then(lambda h: h.content_frame() if h else None)

                if not frame:
                    raise ContentFrameNotFoundError(selector)

                chain.append(frame)
                ctx_frame = frame
                path = '/' + '/'.join(steps[i + 1:])  # remainder
                break

            # Last step processed – but no iframe found → dead-end
            if i == len(steps) - 1:
                raise XPathResolutionError(abs_path)
