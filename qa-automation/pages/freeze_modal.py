from playwright.sync_api import Page
from pages.base_page import BasePage
from utils.logger import logger

class FreezeModal(BasePage):
    """Page Object for the Freeze Search workflow and modal."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.freeze_button = self.page.locator("#freezeBtn")
        self.modal = self.page.locator("#freezeModal")
        self.frozen_summary = self.page.locator("#frozenSummary")
        self.close_button = self.page.locator("#closeModal")
        self.done_button = self.page.locator("#doneBtn")
        self.session_badge = self.page.locator("#sessionBadge")

    def click_freeze(self):
        logger.info("Clicking 'Freeze search' button")
        self.freeze_button.click()

    def is_modal_visible(self) -> bool:
        return self.modal.is_visible()

    def get_summary_text(self) -> str:
        return self.frozen_summary.inner_text().strip()

    def close_modal(self):
        logger.info("Closing freeze modal")
        self.close_button.click()

    def confirm_done(self):
        logger.info("Clicking 'Done' in freeze modal")
        self.done_button.click()

    def get_badge_text(self) -> str:
        return self.session_badge.inner_text().strip()

    def are_filters_disabled(self) -> bool:
        skills_disabled = self.page.locator("#skillsInput").is_disabled()
        min_exp_disabled = self.page.locator("#minExp").is_disabled()
        refine_disabled = self.page.locator("#refineBtn").is_disabled()
        return skills_disabled and min_exp_disabled and refine_disabled
