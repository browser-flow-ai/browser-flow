"""
Deep locator utilities
"""

import re
import asyncio
from typing import Any, List, Optional, Union, Dict
from playwright.async_api import Page, Locator, FrameLocator

# Error type definitions
class StagehandShadowRootMissingError(Exception):
    def __init__(self, detail: str = ""):
        super().__init__(f"Shadow root not found{': ' + detail if detail else ''}")
        self.name = "StagehandShadowRootMissingError"

class StagehandShadowSegmentEmptyError(Exception):
    def __init__(self):
        super().__init__('Empty selector segment after shadow-DOM hop ("//")')
        self.name = "StagehandShadowSegmentEmptyError"

class StagehandShadowSegmentNotFoundError(Exception):
    def __init__(self, segment: str, hint: str = ""):
        super().__init__(f"Shadow segment not found: {segment}{' (' + hint + ')' if hint else ''}")
        self.name = "StagehandShadowSegmentNotFoundError"

# Constants
IFRAME_STEP_RE = re.compile(r'^iframe(\[[^\]]+])?$', re.IGNORECASE)

def step_to_css(step: str) -> str:
    """Convert step to CSS selector"""
    m = re.match(r'^([a-zA-Z*][\w-]*)(?:\[(\d+)])?$', step)
    if not m:
        return step
    tag, idx_raw = m.groups()
    idx = int(idx_raw) if idx_raw else None
    if tag == "*":
        return f"*:nth-child({idx})" if idx else "*"
    return f"{tag}:nth-of-type({idx})" if idx else tag

def build_direct(steps: List[str]) -> str:
    """Build direct CSS selector"""
    return " > ".join(step_to_css(step) for step in steps)

def build_desc(steps: List[str]) -> str:
    """Build descendant CSS selector"""
    return " ".join(step_to_css(step) for step in steps)

async def resolve_shadow_segment(
    host_loc: Locator,
    shadow_steps: List[str],
    attr: str = "data-__stagehand-id",
    timeout: int = 1500,
) -> Locator:
    """Resolve one contiguous shadow segment and return a stable Locator"""
    direct = build_direct(shadow_steps)
    desc = build_desc(shadow_steps)

    async def evaluate_shadow():
        return await host_loc.evaluate("""
            (host, {direct, desc, attr, timeout}) => {
                const backdoor = window.__stagehand__;
                
                const root = host.shadowRoot ?? backdoor?.getClosedRoot?.(host);
                if (!root) return { id: null, noRoot: true };

                const tryFind = () =>
                    root.querySelector(direct) ??
                    root.querySelector(desc);

                return new Promise((resolve) => {
                    const mark = (el) => {
                        let v = el.getAttribute(attr);
                        if (!v) {
                            v = "sh_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
                            el.setAttribute(attr, v);
                        }
                        return { id: v, noRoot: false };
                    };

                    const first = tryFind();
                    if (first) return resolve(mark(first));

                    const start = Date.now();
                    const tick = () => {
                        const el = tryFind();
                        if (el) return resolve(mark(el));
                        if (Date.now() - start >= timeout)
                            return resolve({ id: null, noRoot: false });
                        setTimeout(tick, 50);
                    };
                    tick();
                });
            }
        """, {"direct": direct, "desc": desc, "attr": attr, "timeout": timeout})

    result = await evaluate_shadow()
    
    if result.get("noRoot"):
        raise StagehandShadowRootMissingError(f"segment='{'/'.join(shadow_steps)}'")
    
    if not result.get("id"):
        raise StagehandShadowSegmentNotFoundError("/".join(shadow_steps))
    
    return host_loc.locator(f"stagehand={result['id']}")

async def deep_locator_with_shadow(
    root: Union[Page, FrameLocator],
    xpath: str,
) -> Locator:
    """Create a deep locator that can pierce shadow DOM and iframes"""
    # 1 ─ prepend with slash if not already included
    if not xpath.startswith("/"):
        xpath = "/" + xpath
    tokens = xpath.split("/")  # keep "" from "//"

    ctx: Union[Page, FrameLocator, Locator] = root
    buffer: List[str] = []
    element_scoped = False

    def xp() -> str:
        return "xpath=./" if element_scoped else "xpath=/"

    def flush_into_frame():
        nonlocal ctx, buffer, element_scoped
        if not buffer:
            return
        ctx = ctx.frame_locator(xp() + "/".join(buffer))
        buffer = []
        element_scoped = False

    def flush_into_locator():
        nonlocal ctx, buffer, element_scoped
        if not buffer:
            return
        ctx = ctx.locator(xp() + "/".join(buffer))
        buffer = []
        element_scoped = True

    i = 1
    while i < len(tokens):
        step = tokens[i]

        # Shadow hop: "//"
        if step == "":
            flush_into_locator()

            # collect full shadow segment until next hop/iframe/end
            seg: List[str] = []
            j = i + 1
            while j < len(tokens):
                t = tokens[j]
                if t == "" or IFRAME_STEP_RE.match(t):
                    break
                seg.append(t)
                j += 1
            
            if not seg:
                raise StagehandShadowSegmentEmptyError()

            # resolve inside the shadow root
            ctx = await resolve_shadow_segment(ctx, seg)
            element_scoped = True

            i = j - 1
            i += 1
            continue

        # Normal DOM step
        buffer.append(step)

        # iframe hop → descend into frame
        if IFRAME_STEP_RE.match(step):
            flush_into_frame()

        i += 1

    if not buffer:
        # If we're already element-scoped, we already have the final Locator.
        if element_scoped:
            return ctx
        
        # Otherwise (page/frame scoped), return the root element of the current doc.
        return ctx.locator("xpath=/")

    # Otherwise, resolve the remaining buffered steps.
    return ctx.locator(xp() + "/".join(buffer))

def deep_locator(root: Union[Page, FrameLocator], xpath: str) -> Locator:
    """Create a deep locator that can pierce iframes"""
    # 1 ─ prepend with slash if not already included
    if not xpath.startswith("/"):
        xpath = "/" + xpath

    # 2 ─ split into steps, accumulate until we hit an iframe step
    steps = [s for s in xpath.split("/") if s]  # tokens
    ctx: Union[Page, FrameLocator] = root
    buffer: List[str] = []

    def flush_into_frame():
        nonlocal ctx, buffer
        if not buffer:
            return
        selector = "xpath=/" + "/".join(buffer)
        ctx = ctx.frame_locator(selector)
        buffer = []

    for step in steps:
        buffer.append(step)
        if IFRAME_STEP_RE.match(step):
            # we've included the <iframe> element in buffer ⇒ descend
            flush_into_frame()

    # 3 ─ whatever is left in buffer addresses the target *inside* the last ctx
    final_selector = "xpath=/" + "/".join(buffer)
    return ctx.locator(final_selector)
