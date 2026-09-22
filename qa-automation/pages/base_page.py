from pathlib import Path
from typing import Optional
from playwright.sync_api import Page, Locator, expect
from utils.config import Config
from utils.logger import logger

class BasePage:
    """Base Page Object containing common interactions and robust waiting strategies."""

    def __init__(self, page: Page):
        self.page = page

    def navigate(self, path: str = ""):
        url = f"{Config.BASE_URL}/{path.lstrip('/')}"
        logger.info(f"Navigating to {url}")
        self.page.goto(url, wait_until="domcontentloaded")

    def take_screenshot(self, name: str) -> Path:
        Config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        path = Config.SCREENSHOTS_DIR / f"{name}.png"
        self.page.screenshot(path=str(path), full_page=True)
        logger.info(f"Screenshot saved: {path}")
        return path

    def wait_for_visible(self, selector: str, timeout_ms: int = Config.DEFAULT_TIMEOUT_MS) -> Locator:
        loc = self.page.locator(selector)
        loc.wait_for(state="visible", timeout=timeout_ms)
        return loc

    def wait_for_hidden(self, selector: str, timeout_ms: int = Config.DEFAULT_TIMEOUT_MS):
        loc = self.page.locator(selector)
        loc.wait_for(state="hidden", timeout=timeout_ms)

    def is_visible(self, selector: str) -> bool:
        return self.page.locator(selector).is_visible()

    def get_text(self, selector: str) -> str:
        return self.page.locator(selector).inner_text().strip()

    def fill(self, selector: str, text: str):
        loc = self.page.locator(selector)
        loc.fill(text)

    def click(self, selector: str):
        loc = self.page.locator(selector)
        loc.click()
