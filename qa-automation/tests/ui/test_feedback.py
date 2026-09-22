import pytest
from playwright.sync_api import Page, expect
from pages.start_page import StartPage
from pages.workspace_page import WorkspacePage
from pages.feedback_panel import FeedbackPanel
from pages.freeze_modal import FreezeModal
from utils.test_data import TestData

@pytest.mark.ui
@pytest.mark.regression
class TestFeedbackAndRefinementUi:
    """UI test scenarios for candidate voting, natural-language refinement, and freeze."""

    def _setup_workspace(self, page: Page, stub_search_api):
        stub_search_api()
        start_page = StartPage(page)
        start_page.navigate()
        start_page.start_sourcing(TestData.get_query("valid_rds"))
        start_page.wait_for_workspace_displayed()
        return WorkspacePage(page), FeedbackPanel(page), FreezeModal(page)

    def test_candidate_voting_updates_feedback_composer(self, page: Page, stub_search_api):
        """
        Positive test: Clicking 'Strong match' on candidate 1 updates the feedback textarea
        with '1 (<Candidate Name>) is a strong match.'.
        """
        workspace, feedback_panel, _ = self._setup_workspace(page, stub_search_api)

        feedback_panel.vote_candidate(0, is_match=True)
        text = feedback_panel.get_feedback_text()
        assert "1 (" in text
        assert "is a strong match." in text

    def test_candidate_voting_not_a_match(self, page: Page, stub_search_api):
        """Positive test: Clicking 'Not a match' appends 'not a match' to feedback."""
        workspace, feedback_panel, _ = self._setup_workspace(page, stub_search_api)

        feedback_panel.vote_candidate(0, is_match=False)
        text = feedback_panel.get_feedback_text()
        assert "1 (" in text
        assert "not a match." in text

    def test_refine_search_renders_changes_banner(self, page: Page, stub_search_api):
        """
        Refinement workflow: Submitting feedback calls the refinement loop,
        updates the UI, and displays the Search Refined change banner.
        """
        workspace, feedback_panel, _ = self._setup_workspace(page, stub_search_api)

        feedback_text = TestData.get_refine_feedback("valid_feedback")
        feedback_panel.refine(feedback_text)

        # Wait for refinement response to render change banner
        expect(workspace.change_banner).to_be_visible()
        banner_text = workspace.get_change_banner_text()
        assert "Search refined" in banner_text
        assert "Experience" in banner_text

    @pytest.mark.smoke
    def test_freeze_search_locks_workspace_and_shows_modal(self, page: Page, stub_search_api):
        """
        Freeze workflow: Clicking Freeze locks all inputs, updates badge to 'FROZEN',
        and presents the final shortlist modal snapshot.
        """
        workspace, _, freeze_modal = self._setup_workspace(page, stub_search_api)

        freeze_modal.click_freeze()

        # Modal is displayed
        expect(freeze_modal.modal).to_be_visible()
        summary = freeze_modal.get_summary_text()
        assert "FINAL FILTERS" in summary
        assert "FINAL RUBRIC" in summary
        assert "RANKED SHORTLIST" in summary

        # Dismiss modal
        freeze_modal.confirm_done()
        expect(freeze_modal.modal).to_be_hidden()

        # Verify badge and inputs locked
        assert freeze_modal.get_badge_text() == "FROZEN"
        assert freeze_modal.are_filters_disabled()
