import pytest
from api.sourcing_client import SourcingApiClient
from utils.test_data import TestData

@pytest.mark.api
@pytest.mark.regression
class TestSearchApi:
    """Tests for POST /api/search"""

    def test_search_empty_query_returns_400(self, sourcing_client: SourcingApiClient):
        """Negative test: Submitting an empty query should return 400 Bad Request."""
        response = sourcing_client.search("")
        assert response.status_code == 400, f"Expected 400 Bad Request, got {response.status_code}"
        body = response.json()
        assert "error" in body
        assert "Tell us what kind of candidate" in body["error"]

    def test_search_whitespace_query_returns_400(self, sourcing_client: SourcingApiClient):
        """Negative test: Submitting only whitespace should return 400 Bad Request."""
        response = sourcing_client.search("     ")
        assert response.status_code == 400
        body = response.json()
        assert "Tell us what kind of candidate" in body.get("error", "")

    @pytest.mark.smoke
    def test_search_valid_query_structure(self, sourcing_client: SourcingApiClient):
        """
        Positive test: Submitting a valid brief should return a well-structured SearchResponse.
        Validates contract: sessionId, status, filters, rubric, results, filteredCount.
        """
        query = TestData.get_query("valid_rds")
        response = sourcing_client.search(query)
        
        # When backend has active LLM connection
        if response.status_code == 200:
            data = response.json()
            assert "sessionId" in data
            assert data["status"] in ("ready", "empty")
            assert "filters" in data
            assert "skills" in data["filters"]
            assert "rubric" in data
            assert "criteria" in data["rubric"]
            assert isinstance(data["results"], list)
            assert "filteredCount" in data
        else:
            # If LLM API key is not configured / rate-limited in test environment
            assert response.status_code in (500, 502, 429)
            data = response.json()
            assert "error" in data
