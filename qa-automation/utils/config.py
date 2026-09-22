import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env if present in project root or qa-automation folder
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
QA_DIR = Path(__file__).resolve().parent.parent

load_dotenv(ROOT_DIR / ".env")
load_dotenv(QA_DIR / ".env")

class Config:
    """Centralized configuration for QA Automation framework."""
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8080").rstrip("/")
    API_BASE_URL: str = os.getenv("API_BASE_URL", f"{BASE_URL}/api").rstrip("/")
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
    DEFAULT_TIMEOUT_MS: int = int(os.getenv("DEFAULT_TIMEOUT_MS", "45000"))
    DEFAULT_TIMEOUT_SEC: float = DEFAULT_TIMEOUT_MS / 1000.0
    BROWSER_NAME: str = os.getenv("BROWSER", "chromium")  # chromium, firefox, webkit
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")     # Optional external MySQL/PostgreSQL
    
    # Credentials for Mock Auth / Security demonstration
    TEST_USERNAME: str = os.getenv("TEST_USERNAME", "recruiter@flexiple.com")
    TEST_PASSWORD: str = os.getenv("TEST_PASSWORD", "RecruiterPass123!")
    INVALID_USERNAME: str = "invalid.user@flexiple.com"
    INVALID_PASSWORD: str = "WrongPassword999!"

    # Paths
    PROFILES_JSON_PATH: Path = ROOT_DIR / "src" / "main" / "resources" / "profiles.json"
    DATA_DIR: Path = QA_DIR / "data"
    REPORTS_DIR: Path = QA_DIR / "reports"
    SCREENSHOTS_DIR: Path = REPORTS_DIR / "screenshots"
