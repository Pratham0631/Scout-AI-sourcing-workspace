from typing import List
from playwright.sync_api import Page
from pages.base_page import BasePage
from utils.logger import logger

class FeedbackPanel(BasePage):
    """Page Object for the refinement and chat panel on the right side."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.chat_messages = self.page.locator("#chatMessages .chat-message")
        self.feedback_textarea = self.page.locator("#feedback")
        self.refine_button = self.page.locator("#refineBtn")
        self.quick_feedback_buttons = self.page.locator(".feedback-quick button")

    def vote_candidate(self, candidate_index: int, is_match: bool = True):
        vote_type = "is a strong match" if is_match else "not a match"
        logger.info(f"Voting on candidate {candidate_index}: '{vote_type}'")
        vote_btn = self.page.locator(f"[data-vote='{candidate_index}'][data-value='{vote_type}']")
        vote_btn.click()

    def enter_feedback(self, text: str):
        logger.info(f"Typing feedback: '{text}'")
        self.feedback_textarea.fill(text)

    def get_feedback_text(self) -> str:
        return self.feedback_textarea.input_value().strip()

    def click_refine(self):
        logger.info("Clicking 'Refine search' button")
        self.refine_button.click()

    def refine(self, feedback_text: str):
        self.enter_feedback(feedback_text)
        self.click_refine()

    def get_all_messages(self) -> List[str]:
        return [m.inner_text().strip() for m in self.chat_messages.all()]

    def get_latest_message(self) -> str:
        count = self.chat_messages.count()
        if count > 0:
            return self.chat_messages.nth(count - 1).inner_text().strip()
        return ""
