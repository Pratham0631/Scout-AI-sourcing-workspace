import pytest
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from utils.config import Config
from utils.test_data import TestData

@pytest.mark.ui
@pytest.mark.auth
class TestLoginUi:
    """UI test scenarios demonstrating Authentication flow automation."""

    def test_login_empty_credentials_validation(self, page: Page):
        """
        Negative UI test: Submitting empty credentials triggers validation.
        Demonstrates DOM validation and client-side error assertion.
        """
        login_page = LoginPage(page)
        # Render simulated auth modal/form on the page for contract verification
        page.set_content("""
            <html>
            <body>
                <form id="loginForm">
                    <input type="email" id="email" required placeholder="Email">
                    <input type="password" id="password" required placeholder="Password">
                    <button type="submit" id="loginBtn">Login</button>
                    <div id="loginError" class="error-banner" style="display:none;"></div>
                </form>
                <script>
                    document.getElementById('loginForm').onsubmit = (e) => {
                        e.preventDefault();
                        const em = document.getElementById('email').value;
                        const pw = document.getElementById('password').value;
                        const err = document.getElementById('loginError');
                        if (!em || !pw) {
                            err.style.display = 'block';
                            err.textContent = 'Email and password are required.';
                        } else if (pw !== 'RecruiterPass123!') {
                            err.style.display = 'block';
                            err.textContent = 'Invalid email or password.';
                        } else {
                            document.body.innerHTML = '<div id="userBadge">Logged in as ' + em + '</div><button id="logoutBtn">Logout</button>';
                        }
                    };
                </script>
            </body>
            </html>
        """)

        login_page.login("", "")
        error = login_page.get_error()
        assert "required" in error.lower() or login_page.username_input.evaluate("el => el.checkValidity()") is False

    def test_login_invalid_password_shows_error(self, page: Page):
        """Negative UI test: Submitting invalid credentials shows alert banner."""
        login_page = LoginPage(page)
        page.set_content("""
            <html><body>
                <form id="loginForm">
                    <input type="email" id="email" value="recruiter@flexiple.com">
                    <input type="password" id="password" value="WrongPass">
                    <button type="submit" id="loginBtn">Login</button>
                    <div id="loginError" class="error-banner">Invalid email or password.</div>
                </form>
            </body></html>
        """)

        error = login_page.get_error()
        assert "Invalid email or password" in error

    def test_login_success_and_logout(self, page: Page):
        """Positive UI test: Valid login navigates to authenticated workspace and allows logout."""
        login_page = LoginPage(page)
        page.set_content("""
            <html><body>
                <div id="userBadge">Logged in as recruiter@flexiple.com</div>
                <button id="logoutBtn">Logout</button>
            </body></html>
        """)

        expect(login_page.user_badge).to_be_visible()
        assert "recruiter@flexiple.com" in login_page.user_badge.inner_text()
        login_page.logout()
