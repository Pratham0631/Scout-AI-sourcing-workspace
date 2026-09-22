from typing import Any, Dict, List
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from utils.logger import logger

class WorkspacePage(BasePage):
    """Page Object for the Workspace view (#workspace)."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.workspace = self.page.locator("#workspace")
        self.brief_text = self.page.locator("#briefText")
        self.new_search_btn = self.page.locator("#newSearch")

        # Filters
        self.skills_input = self.page.locator("#skillsInput")
        self.min_exp_input = self.page.locator("#minExp")
        self.max_exp_input = self.page.locator("#maxExp")
        self.location_input = self.page.locator("#locationInput")
        self.save_filters_btn = self.page.locator("#saveFilters")
        self.filtered_count = self.page.locator("#filteredCount")

        # Rubric
        self.rubric_container = self.page.locator("#rubric")
        self.save_rubric_btn = self.page.locator("#saveRubric")

        # Candidates & Results
        self.results_meta = self.page.locator("#resultsMeta")
        self.candidate_cards = self.page.locator("#candidates .candidate")
        self.empty_state = self.page.locator("#emptyState")
        self.change_banner = self.page.locator("#changeBanner")
        self.error_banner = self.page.locator("#errorBanner")

    def get_brief(self) -> str:
        return self.brief_text.inner_text().strip()

    def get_skills(self) -> str:
        return self.skills_input.input_value().strip()

    def set_skills(self, skills: str):
        logger.info(f"Setting skills filter: '{skills}'")
        self.skills_input.fill(skills)

    def get_experience_range(self) -> tuple[str, str]:
        return (self.min_exp_input.input_value().strip(), self.max_exp_input.input_value().strip())

    def set_experience_range(self, min_exp: str, max_exp: str):
        logger.info(f"Setting experience range: {min_exp} - {max_exp}")
        self.min_exp_input.fill(str(min_exp))
        self.max_exp_input.fill(str(max_exp))

    def get_location(self) -> str:
        return self.location_input.input_value().strip()

    def set_location(self, location: str):
        logger.info(f"Setting location filter: '{location}'")
        self.location_input.fill(location)

    def select_company_types(self, desired_types: List[str]):
        logger.info(f"Setting company types: {desired_types}")
        checkboxes = self.page.locator(".company-checks input")
        count = checkboxes.count()
        for i in range(count):
            cb = checkboxes.nth(i)
            val = cb.get_attribute("value")
            if val in desired_types and not cb.is_checked():
                cb.check()
            elif val not in desired_types and cb.is_checked():
                cb.uncheck()

    def apply_filters(self):
        logger.info("Clicking 'Apply' for objective filters")
        self.save_filters_btn.click()

    def apply_rubric(self):
        logger.info("Clicking 'Apply' for rubric")
        self.save_rubric_btn.click()

    def get_filtered_count(self) -> int:
        text = self.filtered_count.inner_text().strip()
        return int(text) if text.isdigit() else 0

    def get_candidate_count(self) -> int:
        return self.candidate_cards.count()

    def get_candidate_card_data(self, index: int = 0) -> Dict[str, Any]:
        card = self.candidate_cards.nth(index)
        name = card.locator("h3").inner_text().strip()
        title_company = card.locator(".identity p").inner_text().strip()
        score = card.locator(".score").inner_text().strip()
        facts = [f.inner_text().strip() for f in card.locator(".candidate-facts .fact").all()]
        explanation = card.locator(".explanation").inner_text().strip()
        evidence = [e.inner_text().strip() for e in card.locator(".evidence span").all()]

        return {
            "name": name,
            "title_company": title_company,
            "score": score,
            "facts": facts,
            "explanation": explanation,
            "evidence": evidence
        }

    def is_empty_state(self) -> bool:
        return self.empty_state.is_visible()

    def get_change_banner_text(self) -> str:
        if self.change_banner.is_visible():
            return self.change_banner.inner_text().strip()
        return ""
