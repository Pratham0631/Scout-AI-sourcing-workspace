import time
from typing import Any, Dict, Optional
import requests
from api.base_client import BaseApiClient
from utils.config import Config

class AuthApiClient(BaseApiClient):
    """
    Client for Authentication & Authorization testing.
    Validates token generation, credential verification, and authorization contracts.
    """

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Simulates authenticating a user.
        Returns a mock JWT payload or error structure to test auth contracts.
        """
        if not email or not password:
            return {
                "status_code": 400,
                "error": "Email and password are required.",
                "token": None
            }

        if email == Config.TEST_USERNAME and password == Config.TEST_PASSWORD:
            mock_token = f"mock-jwt-token-{int(time.time())}"
            self.set_auth_token(mock_token)
            return {
                "status_code": 200,
                "token": mock_token,
                "user": {"email": email, "role": "recruiter"},
                "expires_in": 3600
            }

        return {
            "status_code": 401,
            "error": "Invalid email or password.",
            "token": None
        }

    def validate_token(self, token: Optional[str] = None) -> Dict[str, Any]:
        """Validates token presence and format."""
        active_token = token or self.session.headers.get("Authorization", "").replace("Bearer ", "")
        if not active_token:
            return {"status_code": 401, "valid": False, "error": "Missing authorization token"}
        if not active_token.startswith("mock-jwt-token"):
            return {"status_code": 403, "valid": False, "error": "Invalid or expired token"}
        return {"status_code": 200, "valid": True, "user": Config.TEST_USERNAME}

    def logout(self) -> Dict[str, Any]:
        """Clears auth state and invalidates session token."""
        self.clear_auth_token()
        return {"status_code": 200, "message": "Successfully logged out."}
