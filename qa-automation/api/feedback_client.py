from typing import Any, Dict, List, Optional
import requests
from api.base_client import BaseApiClient

class FeedbackApiClient(BaseApiClient):
    """Client for Refinement & Feedback REST API endpoints."""

    def refine(
        self,
        session_id: str,
        filters: Dict[str, Any],
        rubric: Dict[str, Any],
        shown_profiles: List[Dict[str, Any]],
        feedback: str
    ) -> requests.Response:
        """POST /api/sessions/{id}/refine"""
        payload = {
            "filters": filters,
            "rubric": rubric,
            "shownProfiles": shown_profiles,
            "feedback": feedback
        }
        return self.post(f"sessions/{session_id}/refine", json=payload)
