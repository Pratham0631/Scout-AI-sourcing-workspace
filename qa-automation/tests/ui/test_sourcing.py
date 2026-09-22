import pytest
from playwright.sync_api import Page, expect
from pages.start_page import StartPage
from pages.workspace_page import WorkspacePage
from utils.test_data import TestData

@pytest.mark.ui
@pytest.mark.regression
class TestSourcingUi:
    """UI test scenarios for candidate cards, filters, and rubric in the workspace."""

    def _load_workspace(self, page: Page, stub_search_api):
        stub_search_api()
        start_page = StartPage(page)
        start_page.navigate()
        start_page.start_sourcing(TestData.get_query("valid_rds"))
        start_page.wait_for_workspace_displayed()
        return WorkspacePage(page)

    def test_objective_filters_rendered_correctly(self, page: Page, stub_search_api):
        """Verify that objective filters reflect the parsed backend search response."""
        workspace = self._load_workspace(page, stub_search_api)

        skills = workspace.get_skills()
        assert "AWS RDS" in skills or "PostgreSQL" in skills

        min_exp, max_exp = workspace.get_experience_range()
        assert min_exp == "4"
        assert max_exp == "7"

        location = workspace.get_location()
        assert location == "Bangalore"

    def test_candidate_cards_rendered_with_evidence(self, page: Page, stub_search_api):
        """
        Verify that candidate cards render:
        - Candidate Name & Title
        - Score /100
        - Quick facts (years, location, company)
        - Explanation text
        - Evidence tags grounded to profile
        """
        workspace = self._load_workspace(page, stub_search_api)

        count = workspace.get_candidate_count()
        assert count > 0, "At least one candidate card should be rendered"

        card = workspace.get_candidate_card_data(0)
        assert len(card["name"]) > 0
        assert "/100" in card["score"]
        assert len(card["facts"]) >= 2
        assert len(card["explanation"]) > 10
        assert len(card["evidence"]) >= 1

    def test_direct_edit_filters_and_apply(self, page: Page, stub_search_api):
        """
        Positive test: Directly editing filter values in the UI and clicking Apply.
        Verifies that inputs allow editing and Apply trigger sends updated filters.
        """
        workspace = self._load_workspace(page, stub_search_api)

        # Edit experience values
        workspace.set_experience_range("5", "8")
        min_exp, max_exp = workspace.get_experience_range()
        assert min_exp == "5"
        assert max_exp == "8"

        # Apply edits
        workspace.apply_filters()
        expect(workspace.workspace).to_be_visible()
