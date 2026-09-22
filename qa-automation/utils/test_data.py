import json
from pathlib import Path
from typing import Any, Dict
from utils.config import Config

class TestData:
    """Helper for reading test fixtures and mock responses."""
    _test_data: Dict[str, Any] = {}
    _mock_data: Dict[str, Any] = {}

    @classmethod
    def _load(cls):
        if not cls._test_data:
            test_file = Config.DATA_DIR / "test_data.json"
            if test_file.exists():
                with open(test_file, "r", encoding="utf-8") as f:
                    cls._test_data = json.load(f)

        if not cls._mock_data:
            mock_file = Config.DATA_DIR / "mock_responses.json"
            if mock_file.exists():
                with open(mock_file, "r", encoding="utf-8") as f:
                    cls._mock_data = json.load(f)

    @classmethod
    def get_query(cls, key: str = "valid_rds") -> str:
        cls._load()
        return cls._test_data.get("search_queries", {}).get(key, "")

    @classmethod
    def get_edit_payload(cls, key: str = "valid_edits") -> Dict[str, Any]:
        cls._load()
        return cls._test_data.get("edit_payloads", {}).get(key, {})

    @classmethod
    def get_refine_feedback(cls, key: str = "valid_feedback") -> str:
        cls._load()
        return cls._test_data.get("refine_payloads", {}).get(key, "")

    @classmethod
    def get_auth_credentials(cls, key: str = "valid") -> Dict[str, str]:
        cls._load()
        return cls._test_data.get("auth_credentials", {}).get(key, {})

    @classmethod
    def get_mock_response(cls, key: str) -> Dict[str, Any]:
        cls._load()
        return cls._mock_data.get(key, {})
