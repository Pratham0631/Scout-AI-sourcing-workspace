import requests
from typing import Any, Dict, Optional
from utils.config import Config
from utils.logger import logger

class BaseApiClient:
    """Reusable REST API client wrapper around Python Requests."""

    def __init__(self, base_url: str = Config.API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def set_auth_token(self, token: str):
        """Sets Bearer authorization header."""
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def clear_auth_token(self):
        """Clears authorization header."""
        self.session.headers.pop("Authorization", None)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.info(f"HTTP GET: {url}")
        response = self.session.get(url, params=params, timeout=Config.DEFAULT_TIMEOUT_SEC, **kwargs)
        logger.info(f"Response: {response.status_code}")
        return response

    def post(self, endpoint: str, json: Optional[Any] = None, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.info(f"HTTP POST: {url}")
        response = self.session.post(url, json=json, timeout=Config.DEFAULT_TIMEOUT_SEC, **kwargs)
        logger.info(f"Response: {response.status_code}")
        return response
