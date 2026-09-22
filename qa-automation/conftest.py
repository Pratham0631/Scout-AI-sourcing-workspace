import os
import pytest
from pathlib import Path
from typing import Generator
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from utils.config import Config
from utils.logger import logger
from utils.test_data import TestData
from utils.db_validator import DatabaseValidator
from api.sourcing_client import SourcingApiClient
from api.feedback_client import FeedbackApiClient
from api.auth_client import AuthApiClient

@pytest.fixture(scope="session")
def playwright_instance():
    """Session-level Playwright instance."""
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session")
def browser(playwright_instance) -> Generator[Browser, None, None]:
    """Session-level Browser fixture."""
    browser_type = getattr(playwright_instance, Config.BROWSER_NAME)
    browser = browser_type.launch(headless=Config.HEADLESS)
    logger.info(f"Launched {Config.BROWSER_NAME} (Headless: {Config.HEADLESS})")
    yield browser
    browser.close()

@pytest.fixture(scope="function")
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """Function-level browser context ensuring test isolation."""
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        record_video_dir=str(Config.REPORTS_DIR / "videos") if os.getenv("RECORD_VIDEO") else None
    )
    yield ctx
    ctx.close()

@pytest.fixture(scope="function")
def page(context: BrowserContext, request) -> Generator[Page, None, None]:
    """Function-level Page fixture with automatic failure screenshot capture."""
    p = context.new_page()
    yield p

    # Capture failure screenshot if test failed
    failed = getattr(request.node, "rep_call", None) and request.node.rep_call.failed
    if failed:
        Config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = Config.SCREENSHOTS_DIR / f"{request.node.name}_failure.png"
        try:
            p.screenshot(path=str(screenshot_path), full_page=True)
            logger.error(f"Test failed! Screenshot captured at: {screenshot_path}")
        except Exception as e:
            logger.warning(f"Could not take failure screenshot: {e}")
    p.close()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Captures test result report for screenshot hook and HTML reporting."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

@pytest.fixture(scope="session")
def sourcing_client() -> SourcingApiClient:
    """Session-level Sourcing API client."""
    return SourcingApiClient()

@pytest.fixture(scope="session")
def feedback_client() -> FeedbackApiClient:
    """Session-level Feedback API client."""
    return FeedbackApiClient()

@pytest.fixture(scope="session")
def auth_client() -> AuthApiClient:
    """Session-level Authentication API client."""
    return AuthApiClient()

@pytest.fixture(scope="session")
def db_validator() -> Generator[DatabaseValidator, None, None]:
    """Session-level Database validation utility."""
    db = DatabaseValidator()
    yield db
    db.close()

@pytest.fixture
def stub_search_api(page: Page):
    """
    Playwright route interceptor providing deterministic mock responses.
    Prevents flaky LLM rate limits, reduces cost, and ensures instant execution in CI.
    """
    def _apply_stub(custom_data=None):
        mock_data = custom_data or TestData.get_mock_response("search_success")
        page.route("**/api/search", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            json=mock_data
        ))
        page.route("**/api/sessions/*/refine", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            json=TestData.get_mock_response("refine_success")
        ))
        page.route("**/api/sessions/*/freeze", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            json=TestData.get_mock_response("freeze_success")
        ))
    return _apply_stub
