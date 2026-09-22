import pytest
from api.auth_client import AuthApiClient
from utils.config import Config
from utils.test_data import TestData

@pytest.mark.api
@pytest.mark.auth
class TestAuthApi:
    """Authentication and Authorization contract tests."""

    def test_auth_valid_credentials(self, auth_client: AuthApiClient):
        """Positive test: Valid login credentials should return 200 with active session token."""
        creds = TestData.get_auth_credentials("valid")
        response = auth_client.login(creds["email"], creds["password"])
        assert response["status_code"] == 200
        assert response["token"] is not None
        assert response["token"].startswith("mock-jwt-token")
        assert response["user"]["email"] == Config.TEST_USERNAME

    def test_auth_invalid_password(self, auth_client: AuthApiClient):
        """Negative test: Invalid password returns 401 Unauthorized."""
        creds = TestData.get_auth_credentials("invalid_password")
        response = auth_client.login(creds["email"], creds["password"])
        assert response["status_code"] == 401
        assert "Invalid email or password" in response["error"]

    def test_auth_empty_credentials(self, auth_client: AuthApiClient):
        """Negative test: Empty credentials return 400 Bad Request."""
        creds = TestData.get_auth_credentials("empty_fields")
        response = auth_client.login(creds["email"], creds["password"])
        assert response["status_code"] == 400
        assert "required" in response["error"]

    def test_auth_token_validation_positive(self, auth_client: AuthApiClient):
        """Positive test: Token verification passes with an active valid token."""
        auth_client.login(Config.TEST_USERNAME, Config.TEST_PASSWORD)
        validation = auth_client.validate_token()
        assert validation["status_code"] == 200
        assert validation["valid"] is True

    def test_auth_token_missing_returns_401(self, auth_client: AuthApiClient):
        """Negative test: Unauthenticated request without token returns 401."""
        auth_client.clear_auth_token()
        validation = auth_client.validate_token("")
        assert validation["status_code"] == 401
        assert validation["valid"] is False

    def test_auth_token_tampered_returns_403(self, auth_client: AuthApiClient):
        """Negative test: Tampered / malformed token returns 403 Forbidden."""
        validation = auth_client.validate_token("tampered-invalid-jwt-payload")
        assert validation["status_code"] == 403
        assert validation["valid"] is False

    def test_auth_logout_clears_token(self, auth_client: AuthApiClient):
        """Positive test: Logout successfully invalidates and clears the token."""
        auth_client.login(Config.TEST_USERNAME, Config.TEST_PASSWORD)
        res = auth_client.logout()
        assert res["status_code"] == 200
        # Subsequent check without token should fail
        assert auth_client.validate_token()["valid"] is False
