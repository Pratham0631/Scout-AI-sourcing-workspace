import pytest
from playwright.sync_api import Page, expect
from pages.start_page import StartPage
from pages.workspace_page import WorkspacePage
from pages.feedback_panel import FeedbackPanel
from pages.freeze_modal import FreezeModal
from utils.test_data import TestData
from utils.db_validator import DatabaseValidator
from api.sourcing_client import SourcingApiClient

@pytest.mark.e2e
class TestSourcingEndToEnd:
    """
    End-to-End hybrid test combining API setup, UI automation, and Database validation.
    Demonstrates the complete user journey:
    Start Search -> Candidate Shortlist -> Database Integrity Check -> Voting & Feedback -> Refinement -> Freeze.
    """

    def test_complete_sourcing_refinement_and_freeze_journey(
        self, page: Page, stub_search_api, db_validator: DatabaseValidator, sourcing_client: SourcingApiClient
    ):
        stub_search_api()
        start_page = StartPage(page)
        workspace_page = WorkspacePage(page)
        feedback_panel = FeedbackPanel(page)
        freeze_modal = FreezeModal(page)

        # 1. Start on home page and submit sourcing brief
        start_page.navigate()
        brief = TestData.get_query("valid_rds")
        start_page.start_sourcing(brief)
        start_page.wait_for_workspace_displayed()

        # 2. Verify workspace loaded and objective filters rendered
        expect(workspace_page.workspace).to_be_visible()
        candidate_count = workspace_page.get_candidate_count()
        assert candidate_count > 0, "Top candidate matches should be displayed"

        # 3. Database Validation: Verify displayed candidates match candidate store records
        first_candidate = workspace_page.get_candidate_card_data(0)
        assert first_candidate["name"], "Candidate name must be present"
        
        # Verify candidate pool integrity in Database
        total_in_db = db_validator.count_candidates()
        assert total_in_db == 48, f"Database must contain all 48 profiles, found {total_in_db}"

        # 4. Feedback & Voting: Recruiter votes on candidates
        feedback_panel.vote_candidate(0, is_match=True)
        assert "is a strong match." in feedback_panel.get_feedback_text()

        # 5. Refinement: Recruiter submits additional feedback
        feedback_text = TestData.get_refine_feedback("valid_feedback")
        feedback_panel.refine(feedback_text)

        # Verify refinement diff banner appeared
        expect(workspace_page.change_banner).to_be_visible()
        assert "Search refined" in workspace_page.get_change_banner_text()

        # 6. Freeze Search: Recruiter locks the final shortlist
        freeze_modal.click_freeze()
        expect(freeze_modal.modal).to_be_visible()
        freeze_modal.confirm_done()

        # 7. Verify final frozen state
        assert freeze_modal.get_badge_text() == "FROZEN"
        assert freeze_modal.are_filters_disabled()
