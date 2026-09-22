from typing import Any, Dict, Optional
import requests
from api.base_client import BaseApiClient

class SourcingApiClient(BaseApiClient):
    """Client for Sourcing REST API endpoints."""

    def health(self) -> requests.Response:
        """GET /api/health"""
        return self.get("health")

    def search(self, query: str) -> requests.Response:
        """POST /api/search"""
        payload = {"query": query}
        return self.post("search", json=payload)

    def edit(self, session_id: str, filters: Dict[str, Any], rubric: Dict[str, Any]) -> requests.Response:
        """POST /api/sessions/{id}/edit"""
        payload = {"filters": filters, "rubric": rubric}
        return self.post(f"sessions/{session_id}/edit", json=payload)

    def freeze(self, session_id: str) -> requests.Response:
        """POST /api/sessions/{id}/freeze"""
        return self.post(f"sessions/{session_id}/freeze")
