import pytest
from playwright.sync_api import Page, expect
from pages.start_page import StartPage
from pages.workspace_page import WorkspacePage
from utils.test_data import TestData

@pytest.mark.ui
@pytest.mark.regression
class TestCandidateSearchUi:
    """UI test scenarios for initial candidate sourcing workflow."""

    @pytest.mark.smoke
    def test_homepage_loads_correctly(self, page: Page):
        """Smoke test: Verify home view loads with brand, headline, and query input."""
        start_page = StartPage(page)
        start_page.navigate()

        expect(page).to_have_title("Scout — AI sourcing refinement")
        expect(start_page.query_input).to_be_visible()
        expect(start_page.search_button).to_be_visible()
        expect(start_page.example_buttons.first).to_be_visible()

    def test_example_pill_populates_query_textarea(self, page: Page):
        """Positive test: Clicking an example suggestion pill populates the query input."""
        start_page = StartPage(page)
        start_page.navigate()

        start_page.click_example(0)
        query_val = start_page.get_query_text()
        assert len(query_val) > 10, "Example text should populate the brief input"
        assert "RDS" in query_val or "PostgreSQL" in query_val

    def test_empty_brief_submission_prevented(self, page: Page):
        """Negative test: Clicking 'Start sourcing' on an empty input does not transition views."""
        start_page = StartPage(page)
        start_page.navigate()

        start_page.enter_query("")
        start_page.click_start_sourcing()

        # Workspace should remain hidden
        expect(start_page.workspace_view).to_be_hidden()
        expect(start_page.start_view).to_be_visible()

    @pytest.mark.smoke
    def test_start_sourcing_transitions_to_workspace(self, page: Page, stub_search_api):
        """
        Positive test: Submitting a valid brief transitions the UI to the workspace view
        and displays the brief text in the left panel.
        """
        stub_search_api()
        start_page = StartPage(page)
        workspace_page = WorkspacePage(page)

        start_page.navigate()
        brief = TestData.get_query("valid_rds")
        start_page.start_sourcing(brief)

        start_page.wait_for_workspace_displayed()
        expect(workspace_page.workspace).to_be_visible()
        assert brief in workspace_page.get_brief()

    def test_empty_results_state_display(self, page: Page, stub_search_api):
        """
        Validation test: When objective filters match 0 candidates, the empty results state is shown.
        """
        stub_search_api(TestData.get_mock_response("search_empty"))
        start_page = StartPage(page)
        workspace_page = WorkspacePage(page)

        start_page.navigate()
        start_page.start_sourcing("Rare skill in Antarctica")
        start_page.wait_for_workspace_displayed()

        assert workspace_page.is_empty_state()
        assert workspace_page.get_filtered_count() == 0
