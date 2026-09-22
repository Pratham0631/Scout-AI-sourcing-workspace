from playwright.sync_api import Page
from pages.base_page import BasePage
from utils.logger import logger

class LoginPage(BasePage):
    """
    Page Object demonstrating Authentication workflow automation.
    Handles login inputs, validation alerts, credential submission, and logout.
    """

    def __init__(self, page: Page):
        super().__init__(page)
        # Selectors using best practices (data-testid, label, semantic roles)
        self.username_input = self.page.locator("input[name='email'], #email, input[type='email']")
        self.password_input = self.page.locator("input[name='password'], #password, input[type='password']")
        self.login_button = self.page.locator("button[type='submit'], #loginBtn")
        self.error_banner = self.page.locator(".error-banner, .alert-danger, #loginError")
        self.user_badge = self.page.locator(".user-profile, #userBadge")
        self.logout_button = self.page.locator("#logoutBtn, button:has-text('Logout')")

    def login(self, username: str, password: str):
        logger.info(f"Submitting login for user: {username}")
        if self.username_input.is_visible():
            self.username_input.fill(username)
        if self.password_input.is_visible():
            self.password_input.fill(password)
        if self.login_button.is_visible():
            self.login_button.click()

    def get_error(self) -> str:
        if self.error_banner.is_visible():
            return self.error_banner.inner_text().strip()
        return ""

    def logout(self):
        logger.info("Logging out")
        if self.logout_button.is_visible():
            self.logout_button.click()
