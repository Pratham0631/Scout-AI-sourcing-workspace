from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from utils.logger import logger

class StartPage(BasePage):
    """Page Object for the Start Sourcing view (#startView)."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.query_input = self.page.locator("#query")
        self.search_button = self.page.locator("#searchBtn")
        self.start_view = self.page.locator("#startView")
        self.workspace_view = self.page.locator("#workspace")
        self.example_buttons = self.page.locator("[data-example]")
        self.loading_indicator = self.page.locator("#startLoading")
        self.global_loading = self.page.locator("#globalLoading")
        self.error_banner = self.page.locator("#startError")
        self.retry_button = self.page.locator("#startRetryBtn")

    def enter_query(self, query: str):
        logger.info(f"Entering recruiter brief: '{query[:40]}...'")
        self.query_input.fill(query)

    def get_query_text(self) -> str:
        return self.query_input.input_value()

    def click_example(self, index: int = 0):
        logger.info(f"Clicking example query pill at index {index}")
        self.example_buttons.nth(index).click()

    def click_start_sourcing(self):
        logger.info("Clicking 'Start sourcing' button")
        self.search_button.click()

    def start_sourcing(self, query: str):
        self.enter_query(query)
        self.click_start_sourcing()

    def wait_for_loading_finish(self, timeout_ms: int = 30000):
        """Waits for loading overlays to disappear."""
        if self.global_loading.is_visible():
            self.global_loading.wait_for(state="hidden", timeout=timeout_ms)

    def wait_for_workspace_displayed(self, timeout_ms: int = 30000):
        self.workspace_view.wait_for(state="visible", timeout=timeout_ms)

    def get_error_message(self) -> str:
        if self.error_banner.is_visible():
            return self.error_banner.inner_text().strip()
        return ""
