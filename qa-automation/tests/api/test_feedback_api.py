import pytest
import uuid
from api.sourcing_client import SourcingApiClient
from api.feedback_client import FeedbackApiClient
from utils.test_data import TestData

@pytest.mark.api
@pytest.mark.regression
class TestFeedbackApi:
    """Tests for POST /api/sessions/{id}/refine"""

    @pytest.fixture(scope="class")
    def live_session(self, sourcing_client: SourcingApiClient):
        """Creates an active session for the feedback test class."""
        search_res = sourcing_client.search(TestData.get_query("valid_rds"))
        if search_res.status_code == 200:
            return search_res.json()
        pytest.skip(f"Backend search not available (HTTP {search_res.status_code})")

    def test_refine_non_existent_session_returns_404(self, feedback_client: FeedbackApiClient):
        """Negative test: Refining a non-existent session should return 404 Not Found."""
        random_id = str(uuid.uuid4())
        response = feedback_client.refine(
            session_id=random_id,
            filters={"skills": ["Python"]},
            rubric={"criteria": [{"name": "C1", "description": "D1", "weight": 100}]},
            shown_profiles=[{"profile": {"id": "p001"}}],
            feedback="Prioritize senior engineers"
        )
        assert response.status_code == 404
        assert "Search session not found" in response.json().get("error", "")

    def test_refine_missing_feedback_returns_400(
        self, feedback_client: FeedbackApiClient, live_session
    ):
        """Negative test: Missing or empty feedback must return 400 Bad Request."""
        session_id = live_session["sessionId"]
        response = feedback_client.refine(
            session_id=session_id,
            filters=live_session["filters"],
            rubric=live_session["rubric"],
            shown_profiles=live_session["results"],
            feedback=""
        )
        assert response.status_code == 400
        assert "provide recruiter feedback" in response.json().get("error", "")

    def test_refine_missing_shown_profiles_returns_400(
        self, feedback_client: FeedbackApiClient, live_session
    ):
        """Negative test: Empty shownProfiles array must return 400 Bad Request."""
        session_id = live_session["sessionId"]
        response = feedback_client.refine(
            session_id=session_id,
            filters=live_session["filters"],
            rubric=live_session["rubric"],
            shown_profiles=[],
            feedback="Focus more on AWS RDS"
        )
        assert response.status_code == 400
        assert "No reviewed profiles were supplied" in response.json().get("error", "")

    def test_refine_frozen_session_returns_409(
        self, sourcing_client: SourcingApiClient, feedback_client: FeedbackApiClient, live_session
    ):
        """Conflict test: Cannot refine a frozen search session."""
        session_id = live_session["sessionId"]
        sourcing_client.freeze(session_id)

        res = feedback_client.refine(
            session_id=session_id,
            filters=live_session["filters"],
            rubric=live_session["rubric"],
            shown_profiles=live_session["results"],
            feedback="Want even more experience"
        )
        assert res.status_code == 409
        assert "This search is frozen" in res.json().get("error", "")
