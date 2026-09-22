import pytest
import uuid
from api.sourcing_client import SourcingApiClient
from utils.test_data import TestData

@pytest.mark.api
@pytest.mark.regression
class TestSourcingApi:
    """Tests for POST /api/sessions/{id}/edit and POST /api/sessions/{id}/freeze"""

    @pytest.fixture(scope="class")
    def live_session(self, sourcing_client: SourcingApiClient):
        """Creates a single active session for the test class to minimize LLM roundtrips."""
        search_res = sourcing_client.search(TestData.get_query("valid_rds"))
        if search_res.status_code == 200:
            return search_res.json()
        pytest.skip(f"Backend search not available (HTTP {search_res.status_code})")

    def test_edit_non_existent_session_returns_404(self, sourcing_client: SourcingApiClient):
        """Negative test: Editing an unknown session should return 404 Not Found."""
        random_id = str(uuid.uuid4())
        payload = TestData.get_edit_payload("valid_edits")
        response = sourcing_client.edit(random_id, payload["filters"], payload["rubric"])
        assert response.status_code == 404
        assert "Search session not found" in response.json().get("error", "")

    def test_freeze_non_existent_session_returns_404(self, sourcing_client: SourcingApiClient):
        """Negative test: Freezing an unknown session should return 404 Not Found."""
        random_id = str(uuid.uuid4())
        response = sourcing_client.freeze(random_id)
        assert response.status_code == 404
        assert "Search session not found" in response.json().get("error", "")

    def test_edit_validation_min_exp_greater_than_max(self, sourcing_client: SourcingApiClient, live_session):
        """Boundary/validation test: minYearsExperience > maxYearsExperience must return 400."""
        session_id = live_session["sessionId"]
        payload = TestData.get_edit_payload("invalid_experience_min_greater_than_max")
        res = sourcing_client.edit(session_id, payload["filters"], payload["rubric"])
        assert res.status_code == 400
        assert "Experience range is invalid" in res.json().get("error", "")

    def test_edit_validation_negative_experience(self, sourcing_client: SourcingApiClient, live_session):
        """Validation test: Negative experience must return 400."""
        session_id = live_session["sessionId"]
        payload = TestData.get_edit_payload("invalid_experience_negative")
        res = sourcing_client.edit(session_id, payload["filters"], payload["rubric"])
        assert res.status_code == 400
        assert "Invalid minimum experience" in res.json().get("error", "")

    def test_edit_validation_rubric_weights_must_sum_to_100(self, sourcing_client: SourcingApiClient, live_session):
        """Validation test: Rubric weights summing to != 100 must return 400."""
        session_id = live_session["sessionId"]
        payload = TestData.get_edit_payload("invalid_rubric_weight_sum")
        res = sourcing_client.edit(session_id, payload["filters"], payload["rubric"])
        assert res.status_code == 400
        assert "weights sum to 100" in res.json().get("error", "")

    def test_edit_validation_rubric_criteria_count(self, sourcing_client: SourcingApiClient, live_session):
        """Validation test: Rubric criteria count < 3 must return 400."""
        session_id = live_session["sessionId"]
        payload = TestData.get_edit_payload("invalid_rubric_criteria_count_too_low")
        res = sourcing_client.edit(session_id, payload["filters"], payload["rubric"])
        assert res.status_code == 400
        assert "Rubric must contain 3-6 criteria" in res.json().get("error", "")

    def test_edit_frozen_session_returns_409(self, sourcing_client: SourcingApiClient, live_session):
        """Conflict test: Modifying a frozen session must return 409 Conflict."""
        session_id = live_session["sessionId"]
        freeze_res = sourcing_client.freeze(session_id)
        assert freeze_res.status_code == 200
        assert freeze_res.json().get("status") == "frozen"

        payload = TestData.get_edit_payload("valid_edits")
        edit_res = sourcing_client.edit(session_id, payload["filters"], payload["rubric"])
        assert edit_res.status_code == 409
        assert "This search is frozen" in edit_res.json().get("error", "")
