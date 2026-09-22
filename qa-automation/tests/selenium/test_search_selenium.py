import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.config import Config
from utils.test_data import TestData
from utils.logger import logger

class SeleniumStartPage:
    """Selenium Page Object Model demonstrating WebDriver locators and explicit waits."""

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

        # Locators using By strategy
        self.query_locator = (By.ID, "query")
        self.search_btn_locator = (By.ID, "searchBtn")
        self.example_pills_locator = (By.CSS_SELECTOR, "[data-example]")
        self.start_view_locator = (By.ID, "startView")

    def open(self):
        url = Config.BASE_URL
        logger.info(f"[Selenium] Navigating to {url}")
        self.driver.get(url)

    def enter_query(self, text: str):
        query_input = self.wait.until(EC.visibility_of_element_located(self.query_locator))
        query_input.clear()
        query_input.send_keys(text)

    def click_example(self, index: int = 0):
        elements = self.wait.until(EC.presence_of_all_elements_located(self.example_pills_locator))
        elements[index].click()

    def get_query_text(self) -> str:
        query_input = self.wait.until(EC.visibility_of_element_located(self.query_locator))
        return query_input.get_attribute("value")

    def click_start_sourcing(self):
        btn = self.wait.until(EC.element_to_be_clickable(self.search_btn_locator))
        btn.click()


@pytest.mark.selenium
class TestSearchSelenium:
    """
    Selenium WebDriver demonstration test suite.
    Demonstrates mastery of Selenium WebDriver, explicit waits (WebDriverWait / EC),
    By locators, and Page Object Model alongside the primary Playwright framework.
    """

    @pytest.fixture(scope="function")
    def driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1440,900")

        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            pytest.skip(f"Selenium ChromeDriver could not be initialized in this environment: {e}")

        yield driver
        driver.quit()

    def test_selenium_homepage_loads_and_pills_work(self, driver):
        """
        Validates page load, explicit wait for DOM elements, and example pill interaction via Selenium.
        """
        start_page = SeleniumStartPage(driver)
        start_page.open()

        # Verify page title
        assert "Scout — AI sourcing refinement" in driver.title

        # Click example pill and verify text populated
        start_page.click_example(0)
        query_value = start_page.get_query_text()
        assert len(query_value) > 0
        assert "RDS" in query_value or "PostgreSQL" in query_value
