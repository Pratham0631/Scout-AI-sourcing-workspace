# Scout QA Automation Framework

A production-grade, multi-layer QA Automation Framework built for the **AI-Powered Talent Sourcing & Refinement Platform** ("Scout").

---

## 1. Project Overview & System Under Test (SUT)

**Scout** is a full-stack recruitment sourcing application powered by an LLM and local dataset filtering.
- **Backend**: Spring Boot 3.4 (Java 17, Maven) on port `8080`.
- **Frontend**: Served directly as static HTML5 / Vanilla CSS / Vanilla JS on `http://localhost:8080`.
- **Core Loop**: Natural Language Brief $\rightarrow$ LLM parsing to objective filters & fit rubric $\rightarrow$ Local in-memory filtering against 48 profiles $\rightarrow$ LLM subjective scoring with evidence grounding $\rightarrow$ Candidate feedback $\rightarrow$ LLM refinement $\rightarrow$ Session freeze.

The QA automation framework is completely decoupled from the production Java code, residing in `qa-automation/`. It acts as an external test harness verifying UI, REST APIs, and database consistency.

---

## 2. QA Architecture & Technology Stack

```text
                               ┌────────────────────────┐
                               │   Pytest Test Runner   │
                               └───────────┬────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │                                 │                                 │
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│ UI Tests (POM)   │             │   API Tests      │             │  E2E & DB Tests  │
│  • Playwright    │             │   • Requests     │             │  • Hybrid UI+API │
│  • Selenium (demo│             │   • Pydantic     │             │  • SQLite/SQL DB │
└────────┬─────────┘             └────────┬─────────┘             └────────┬─────────┘
         │                                │                                │
         ▼                                ▼                                ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│ Page Objects     │             │ API Client Layer │             │ DB Validator     │
│  • StartPage     │             │ • SourcingClient │             │ • Schema integrity│
│  • WorkspacePage │             │ • FeedbackClient │             │ • SQL assertions │
│  • FeedbackPanel │             │ • AuthClient     │             │                  │
│  • FreezeModal   │             └────────┬─────────┘             └──────────────────┘
│  • LoginPage     │                      │
└────────┬─────────┘                      │
         │                                │
         └────────────────┬───────────────┘
                          │
                          ▼
            [ Spring Boot SUT @ :8080 ]
```

### Primary Technologies
| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Test Runner** | **Pytest 8.x** | Test discovery, fixtures, parameterization, and CLI filtering via markers |
| **Primary UI Engine** | **Playwright for Python** | Fast, auto-waiting, reliable headless browser automation |
| **Secondary UI Engine**| **Selenium WebDriver** | Demonstrates cross-tool WebDriver expertise and explicit wait strategies |
| **API Client** | **Python Requests** | Fast, stateless HTTP calls for contract, positive, and negative testing |
| **Data Validation** | **SQLite / SQL** | Validates data integrity of candidate records against API filter counts |
| **Reporting** | **pytest-html** | Self-contained, visually rich HTML execution reports with screenshots |
| **CI/CD** | **GitHub Actions** | Automated build, healthcheck wait loop, smoke, and regression runs |
| **Containerization**| **Docker / Compose** | Reproducible execution across developer machines and build agents |

---

## 3. Directory Structure

```text
qa-automation/
├── api/
│   ├── base_client.py           # Requests wrapper: session, logging, timeouts
│   ├── sourcing_client.py       # Endpoints: /search, /edit, /freeze, /health
│   ├── feedback_client.py       # Endpoint: /sessions/{id}/refine
│   └── auth_client.py           # Auth contract: token generation, headers, validation
├── pages/
│   ├── base_page.py             # Playwright base POM: waits, clicks, screenshots
│   ├── start_page.py            # Start view: brief textarea, example pills, search button
│   ├── workspace_page.py        # Workspace: filters, rubric, candidate cards, empty state
│   ├── feedback_panel.py        # Refinement: chat stream, candidate voting, feedback composer
│   ├── freeze_modal.py          # Freeze workflow: modal, final snapshot, UI lock checks
│   └── login_page.py            # Authentication Page Object
├── utils/
│   ├── config.py                # Environment configurations (BASE_URL, HEADLESS, timeouts)
│   ├── logger.py                # Formatted logger with timestamps
│   ├── test_data.py             # Fixture loader for test_data.json and mock_responses.json
│   └── db_validator.py          # SQL-based candidate verification against profiles.json
├── data/
│   ├── test_data.json           # Valid/invalid briefs, edit payloads, boundary test cases
│   └── mock_responses.json      # Deterministic responses for offline/fast CI execution
├── tests/
│   ├── api/
│   │   ├── test_health_api.py   # GET /api/health smoke probe
│   │   ├── test_search_api.py   # POST /api/search (valid query, empty query 400)
│   │   ├── test_sourcing_api.py # POST /api/sessions/{id}/edit & freeze (400, 404, 409)
│   │   ├── test_feedback_api.py # POST /api/sessions/{id}/refine (400, 404, 409)
│   │   └── test_auth_api.py     # Auth contract: tokens, 401 Unauthorized, 403 Forbidden
│   ├── ui/
│   │   ├── test_candidate_search.py # Search submission, example pills, empty states
│   │   ├── test_sourcing.py         # Objective filters, rubric criteria, candidate evidence
│   │   ├── test_feedback.py         # Voting buttons, refinement loop, freeze modal
│   │   └── test_login.py            # Login form validation, error banners, logout
│   ├── e2e/
│   │   └── test_sourcing_e2e.py     # Full recruiter journey + database verification
│   └── selenium/
│       └── test_search_selenium.py  # Selenium WebDriver + WebDriverWait POM demo
├── conftest.py                  # Pytest fixtures, browser management, failure screenshot hooks
├── pytest.ini                   # Pytest configuration and registered markers
├── requirements.txt             # Pinned Python dependencies
├── Dockerfile                   # Standalone test runner container
├── docker-compose.test.yml      # Orchestrates application + test runner
└── README.md                    # Comprehensive documentation and interview guide
```

---

## 4. Setup & Installation

### Prerequisites
* Python 3.10+
* Java 17+ & Maven 3.9+ (to run the Spring Boot application)
* Google Chrome or Chromium (for UI automation)

### Step 1 — Install Python Dependencies
```bash
cd qa-automation
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2 — Install Playwright Browser Binaries
```bash
playwright install chromium
```

### Step 3 — Configure Environment Variables
Copy `.env.example` to `.env` (optional; default values target `http://localhost:8080`):
```bash
cp .env.example .env
```

---

## 5. Starting the Application Under Test (SUT)

In a separate terminal, from the root of the repository:
```bash
mvn spring-boot:run
```
Wait until the console displays:
```text
Started SourcingApplication in X.XXX seconds (process running for ...)
```
Verify readiness at `http://localhost:8080/api/health` (returns `ok`).

---

## 6. Running Tests

All commands can be executed from the `qa-automation/` folder:

### 1. Run Smoke Suite
Quick verification of critical paths (Health API, Home page, Search flow, Freeze):
```bash
pytest -m smoke
```

### 2. Run API Test Suite
Executes all REST API contract and validation tests using Python Requests:
```bash
pytest -m api
```

### 3. Run UI Test Suite
Executes all Playwright Page Object Model tests:
```bash
pytest -m ui
```

### 4. Run Full Regression Suite
Executes the comprehensive suite (API + UI + Boundary + Negative scenarios):
```bash
pytest -m regression
```

### 5. Run End-to-End Suite
Runs multi-step hybrid workflows with database assertions:
```bash
pytest -m e2e
```

### 6. Run Selenium Demonstration
Executes the clean Selenium WebDriver implementation:
```bash
pytest -m selenium
```

### 7. Run Everything with HTML Report Generation
```bash
pytest --html=reports/report.html --self-contained-html
```
The report will be generated at `qa-automation/reports/report.html`.

---

## 7. Key Engineering & Design Decisions

### Why Page Object Model (POM)?
1. **Separation of Concerns**: Test scripts describe **business behavior** ("Recruiter votes strong match on candidate 1 and refines search"); Page Objects encapsulate **technical implementation** (`#candidates [data-vote='0']`, `click()`).
2. **Single Point of Maintenance**: If a frontend ID or class name changes in `index.html`, only one locator in `pages/` needs updating, rather than dozens of tests.
3. **Reusability**: Actions like `start_sourcing()` or `vote_candidate()` are written once and reused across smoke, regression, and E2E suites.

### Why Playwright is Primary & Selenium is Secondary
1. **Auto-Waiting**: Playwright automatically waits for elements to be visible, enabled, and stable before interacting, virtually eliminating `ElementNotInteractableException` or `StaleElementReferenceException`.
2. **Network Interception (`page.route`)**: Allows deterministic stubbing of external LLM responses in CI environments, guaranteeing sub-second test runs without token costs or network flakiness.
3. **Built-in Tracing & Screenshots**: Zero-configuration full-page screenshots and video recording on failure.
4. **Selenium Inclusion**: A clean, explicit `WebDriverWait` test is included in `tests/selenium/` to demonstrate versatility and deep understanding of the standard W3C WebDriver specification.

### Dual Testing Strategy: Deterministic vs. Live
* **Deterministic Mode (Default in CI)**: Uses network stubs (`page.route`) and recorded contracts in `data/mock_responses.json`. Guarantees tests pass in 200ms without depending on external LLM provider uptime, rate limits, or API keys.
* **Live Mode**: When running against a live Spring Boot backend configured with an active `OPENROUTER_API_KEY`, API and E2E tests validate real server-side LLM orchestration.

---

## 8. Failure Artifacts & Debugging

When any Playwright test fails:
1. **Automatic Screenshot**: Captured automatically via the `pytest_runtest_makereport` hook in `conftest.py` and saved to `qa-automation/reports/screenshots/<test_name>_failure.png`.
2. **HTML Report**: Embedded directly in `reports/report.html` for instant inspection in CI/CD.
3. **Structured Logs**: Timestamped HTTP requests, responses, and locator interactions logged to the console.

---

## 9. CI/CD Pipeline (GitHub Actions)

Located at `.github/workflows/qa-tests.yml`:
1. **Checkout**: Pulls the repository code.
2. **Java 17 Setup**: Boots the Spring Boot application in the background (`mvn spring-boot:run &`).
3. **Health Probe**: Polls `http://localhost:8080/api/health` until HTTP 200 is returned.
4. **Python & Playwright Setup**: Caches pip dependencies and installs browser binaries.
5. **Execution**:
   - Runs `pytest -m smoke` for gatekeeping.
   - Runs `pytest -m regression` for thorough validation.
6. **Artifact Storage**: Automatically saves `report.html` and any failure screenshots with a 14-day retention window.

---

## 10. Containerized Execution (Docker)

To run the test suite inside an isolated Docker container:
```bash
cd qa-automation
docker build -t scout-qa .
docker run --network="host" -v $(pwd)/reports:/app/qa-automation/reports scout-qa
```
Or run the full stack via Docker Compose:
```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

---

## 11. Interview Guide: Defending the Framework

Below are concise, high-impact answers to common interview questions about this framework:

#### Q1: "How did you design your test automation framework?"
> *"I designed a layered, decoupled framework around Pytest. It separates concerns into four distinct layers: (1) **Tests** describing user and business scenarios, (2) **Page Objects** encapsulating Playwright locators and UI actions, (3) **API Clients** wrapping Python Requests for backend contract and validation testing, and (4) **Utilities** handling configuration, test data fixtures, and database validation. This structure adheres strictly to the Single Responsibility Principle and eliminates duplication."*

#### Q2: "How do you handle flaky tests in UI automation?"
> *"Flakiness is primarily caused by arbitrary sleeps, race conditions, and unstable selectors. In this framework, we eliminated arbitrary sleeps completely. We rely on Playwright’s built-in auto-waiting for actionability (visible, attached, stable). Where explicit conditions are needed, we use semantic locators (role, text, ID) rather than fragile XPaths. Furthermore, for non-deterministic third-party dependencies like LLM APIs, we use network route stubs during UI regression to isolate frontend behavior from backend latency."*

#### Q3: "Why did you choose Playwright over Selenium as the primary tool?"
> *"Playwright provides out-of-the-box auto-waiting, native network request interception (`page.route`), browser context isolation without needing multiple browser restarts, and superior execution speed through DevTools protocol / CDP connections. However, because enterprise codebases frequently maintain legacy or cross-browser Selenium suites, I also implemented a clean Selenium WebDriver module using explicit `WebDriverWait` and `ExpectedConditions` to prove competence in both ecosystems."*

#### Q4: "How do you test authentication in an application that doesn't have a login system?"
> *"In modern microservice architectures, individual domain services often don't handle authentication directly—an API Gateway or OAuth provider handles it. I structured our authentication tests as a contract validation layer (`AuthApiClient` and `LoginPage`) that validates Bearer token formatting, 401 Unauthorized handling, 403 Forbidden on tampered tokens, and form input validation. This ensures our test suite demonstrates complete auth coverage without unnecessarily polluting a stateless domain service."*

#### Q5: "How do you test an AI / LLM application without burning API credits or failing on non-deterministic outputs?"
> *"We employ a two-tiered testing pyramid: (1) **Deterministic Regression Testing**: We stub the LLM responses using pre-validated mock JSON contracts (`mock_responses.json`). This ensures that UI parsing, scoring card rendering, error handling, and filter changes are tested rapidly and reliably in CI without cost. (2) **Contract & Integration Testing**: We run targeted live API tests against the real Spring Boot backend to verify that our prompt formatting, Jackson JSON parsing, and profile evidence validation logic successfully parse real model completions."*
