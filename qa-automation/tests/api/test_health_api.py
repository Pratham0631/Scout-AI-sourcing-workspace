import pytest
from api.sourcing_client import SourcingApiClient

@pytest.mark.smoke
@pytest.mark.api
def test_health_check_returns_200(sourcing_client: SourcingApiClient):
    """
    Smoke test: Validates that the Spring Boot service is healthy and reachable.
    Target: GET /api/health
    """
    response = sourcing_client.health()
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    assert response.text == "ok" or "ok" in response.text
