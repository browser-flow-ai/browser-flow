"""
Browser utility functions
"""
import os
import shutil
import tempfile
import json
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, BrowserContext, Browser, Playwright
from browser_wrapper.browser_types.types import BrowserResult, PlaywrightBrowser, PlaywrightBrowserContext
from browser_common.browser_logging import get_logger
logger = get_logger("browser_wrapper.browser", enable_file_logging=False)
async def get_browser(headless: bool = False) -> BrowserResult:
    """Get browser instance with configuration"""
    # Create temporary directory for user data
    tmp_dir_path = Path(tempfile.gettempdir()) / "stagehand"
    tmp_dir_path.mkdir(exist_ok=True)
    
    # Create unique context directory
    tmp_dir = tempfile.mkdtemp(prefix="ctx_", dir=str(tmp_dir_path))
    user_dir = Path(tmp_dir) / "userdir" / "Default"
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # Set default preferences
    default_preferences = {
        "plugins": {
            "always_open_pdf_externally": True,
        }
    }
    
    preferences_file = user_dir / "Preferences"
    with open(preferences_file, "w") as f:
        json.dump(default_preferences, f)
    
    user_data_dir = str(user_dir.parent)
    
    # Create downloads directory
    downloads_path = Path.cwd() / "downloads"
    downloads_path.mkdir(exist_ok=True)
    
    # Launch browser
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        accept_downloads=True,
        headless=headless,
        viewport={"width": 1024, "height": 768},
        locale="en-US",
        timezone_id="America/New_York",
        device_scale_factor=1,
        args=["--disable-blink-features=AutomationControlled"],
        bypass_csp=True,
        proxy=None,
        geolocation=None,
        has_touch=True,
        ignore_https_errors=True,
        permissions=None,
        chromium_sandbox=False,
        devtools=False,
        env=None,
        executable_path=None,
        handle_sighup=True,
        handle_sigint=True,
        handle_sigterm=True,
        ignore_default_args=None,
    )
    
    # Apply stealth scripts
    await apply_stealth_scripts(browser)
    
    return {
        "browser": browser.browser,
        "context": browser,
        "context_path": user_data_dir,
    }

async def apply_stealth_scripts(context: BrowserContext) -> None:
    """Apply stealth scripts to avoid detection"""
    await context.add_init_script("""
        // Override the navigator.webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });

        // Mock languages and plugins to mimic a real browser
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });

        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });

        // Remove Playwright-specific properties
        delete window.__playwright;
        delete window.__pw_manual;
        delete window.__PW_inspect;

        // Redefine the headless property
        Object.defineProperty(navigator, 'headless', {
            get: () => false,
        });

        // Override the permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) =>
            parameters.name === 'notifications'
                ? Promise.resolve({
                    state: Notification.permission,
                })
                : originalQuery(parameters);
    """)

async def cleanup_browser_resources(
    browser: Optional[Browser],
    context: Optional[BrowserContext],
    playwright: Optional[Playwright],
    temp_user_data_dir: Optional[Path],
):
    """
    Clean up browser resources.

    Args:
        browser: The browser instance (if any)
        context: The browser context
        playwright: The Playwright instance
        temp_user_data_dir: Temporary user data directory to remove (if any)
        logger: The logger instance
    """
    if context:
        try:
            logger.debug("Closing browser context...")
            await context.close()
        except Exception as e:
            logger.error(f"Error closing context: {str(e)}")
    if browser:
        try:
            logger.debug("Closing browser...")
            await browser.close()
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")

    # Clean up temporary user data directory if created
    if temp_user_data_dir:
        try:
            logger.debug(
                f"Removing temporary user data directory: {temp_user_data_dir}"
            )
            shutil.rmtree(temp_user_data_dir)
        except Exception as e:
            logger.error(
                f"Error removing temporary directory {temp_user_data_dir}: {str(e)}"
            )

    if playwright:
        try:
            logger.debug("Stopping Playwright...")
            await playwright.stop()
        except Exception as e:
            logger.error(f"Error stopping Playwright: {str(e)}")
