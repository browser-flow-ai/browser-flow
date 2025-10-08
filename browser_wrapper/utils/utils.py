"""
General utility functions
"""

from playwright.async_api import CDPSession, Page


async def clear_overlays(page: Page) -> None:
    """Remove existing stagehandObserve attributes"""
    await page.evaluate("""
        () => {
            const elements = document.querySelectorAll('[stagehandObserve="true"]');
            elements.forEach((el) => {
                const parent = el.parentNode;
                while (el.firstChild) {
                    parent?.insertBefore(el.firstChild, el);
                }
                parent?.removeChild(el);
            });
        }
    """)

async def get_current_root_frame_id(session: CDPSession) -> str:
    """Get current root frame ID from CDP session"""
    response = await session.send("Page.getFrameTree")
    return response["frameTree"]["frame"]["id"]
