# Flexiple Sourcing — Refinement Loop

A small full-stack implementation of the **Sourcing Refinement Loop** from the Flexiple engineering assessment.

The application intentionally focuses on one search session:

**free text → objective filters + subjective rubric → local filtering → LLM scoring/ranking → recruiter feedback → refinement → freeze**

The supplied 48-profile fictional talent pool is included in the repository and is loaded locally. No database, login, or persistence layer is used.

## 1. What the application does

1. A recruiter enters a natural-language sourcing brief.
2. The Java backend sends the brief to a real LLM API.
3. The LLM returns structured JSON containing:
   - objective filters: skills, experience, location, company background
   - a weighted subjective fit rubric
4. The backend validates the response.
5. Objective filtering happens locally against `profiles.json`.
6. The remaining profiles are sent to the LLM for scoring and ranking.
7. The UI shows the top five profiles with evidence-backed explanations.
8. The recruiter can:
   - vote on candidates
   - write natural-language feedback such as `1 is too junior, 2 and 4 are right`
   - directly edit filters and rubric
9. Refinement sends the current server-side state + reviewed profiles + recruiter feedback to the LLM.
10. The backend validates the new state, computes the new shortlist, and reports the changes.
11. The recruiter can freeze the search.
12. Freeze displays the final filters, rubric, and ranked shortlist.

## 2. Why this design

The assessment says to spend the majority of the time on the quality of the loop rather than building unrelated infrastructure.

So this project deliberately has:

- no authentication
- no database
- no multi-role system
- no cross-session persistence
- no fake LLM responses
- no simulated 98M-person database

Instead, the implementation concentrates on the four things the assessment evaluates most directly:

- a real end-to-end LLM loop
- trustworthy refinement state
- safe structured LLM output
- a polished recruiter-facing workflow

## 3. Tech stack

### Backend

- Java 17
- Spring Boot
- Maven
- Jackson
- Java `HttpClient` for the LLM API
- In-memory session state

### Frontend

- HTML
- CSS
- Vanilla JavaScript

There is intentionally no frontend build step. The Spring Boot application serves the frontend directly. This makes the evaluator setup a single-command run.

### LLM

The backend uses an OpenAI-compatible chat-completions API. The default configuration points to OpenRouter and a free Gemini model.

You can change:

- `OPENROUTER_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`

No key is hard-coded or sent to the browser.

## 4. Quick setup

### Requirements

- Java 17+
- Maven 3.9+
- An API key for an OpenAI-compatible LLM provider

### Step 1 — clone/open the repository

```bash
git clone <your-repository-url>
cd flexiple-sourcing
```

### Step 2 — configure the API key

Copy the example environment file:

```bash
cp .env.example .env
```

Set:

```bash
OPENROUTER_API_KEY=your_api_key_here
```

The application loads a local `.env` file on startup (if present) and otherwise reads these values from the process environment / system properties.

For the default provider you can also configure:

```bash
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=google/gemini-2.5-flash
```

If your provider uses a different OpenAI-compatible endpoint/model, change those two values.

> Do not commit `.env`.

### Step 3 — run

```bash
mvn spring-boot:run
```

Open:

```text
http://localhost:8080
```

That is it.

### Alternative: build a jar

```bash
mvn clean package
java -jar target/sourcing-refinement-loop-1.0.0.jar
```

Then open:

```text
http://localhost:8080
```

## 5. Project structure

```text
flexiple-sourcing/
├── data/
│   └── profiles.json
├── prompts/
│   ├── initial-search.txt
│   ├── refine-search.txt
│   └── score-profiles.txt
├── src/
│   ├── main/
│   │   ├── java/com/flexiple/sourcing/
│   │   │   ├── SourcingApplication.java
│   │   │   ├── SourcingController.java
│   │   │   ├── SourcingService.java
│   │   │   ├── LlmClient.java
│   │   │   ├── ProfileRepository.java
│   │   │   ├── SessionStore.java
│   │   │   ├── Models.java
│   │   │   └── ApiExceptionHandler.java
│   │   └── resources/
│   │       ├── static/
│   │       │   ├── index.html
│   │       │   ├── app.css
│   │       │   └── app.js
│   │       ├── prompts/
│   │       ├── profiles.json
│   │       └── application.properties
│   └── test/
│       └── java/com/flexiple/sourcing/
├── .env.example
├── .gitignore
├── pom.xml
└── README.md
```

## 6. Backend architecture

### `SourcingController`

Owns HTTP boundaries only.

Endpoints:

```text
POST /api/search
POST /api/sessions/{id}/refine
POST /api/sessions/{id}/edit
POST /api/sessions/{id}/freeze
GET  /api/health
```

The controller does not contain LLM or filtering logic.

### `SourcingService`

Contains the sourcing workflow:

```text
parse/validate LLM output
        ↓
objective filtering
        ↓
LLM scoring
        ↓
evidence validation
        ↓
rank top 5
```

For refinement:

```text
current server state
        +
recruiter feedback
        +
reviewed profiles
        ↓
LLM refinement
        ↓
validate new filters/rubric
        ↓
local filter
        ↓
LLM scoring
        ↓
new shortlist
```

### `ProfileRepository`

The 48 profiles are loaded once from the supplied JSON.

Filtering is deliberately local:

```text
skills
years
location
company background
```

For company background, the implementation considers both the current company and past companies. This lets a requirement such as "worked at startups" work against the supplied profile shape.

### `SessionStore`

Stores the current state in memory:

- filters
- rubric
- ranked results
- filtered count
- frozen state

This is enough for the assessment's single-session scope without introducing a database.

### `LlmClient`

The only class that talks to the external LLM.

It:

- reads the API key from an environment variable
- sets connection/request timeouts
- sends prompts server-side
- requests JSON output
- parses the returned JSON
- converts provider failures into user-safe errors

Keeping this boundary isolated makes it easy to replace OpenRouter with another OpenAI-compatible provider.

## 7. Structured output and validation

The LLM is not trusted blindly.

For filters, the backend validates:

- arrays are actually arrays
- experience is numeric
- experience is between 0 and 50
- min ≤ max
- company types belong to the supplied enum
- rubric has 3–6 criteria
- every criterion has name, description and weight
- rubric weights total exactly 100

For scores, the backend validates:

- every filtered profile is scored exactly once
- IDs belong to the filtered candidate set
- score is 0–100
- explanation exists
- evidence exists

Invalid output is rejected instead of being applied to the search state.

## 8. Evidence-backed explanations

One important assessment requirement is:

> Explanations for why a profile matched must cite actual fields from that profile.

The scoring prompt explicitly asks the LLM for evidence such as:

```text
years_experience: 6
skills: AWS RDS, PostgreSQL
current_company_type: startup
```

The server then checks that the evidence contains recognizable profile fields and concrete values from the candidate.

If evidence cannot be grounded to the actual candidate, the response is rejected.

This is intentionally stricter than simply trusting an LLM-generated paragraph.

## 9. Deliberate mismatches / near misses

The supplied dataset deliberately contains obvious matches, near misses and clear non-matches.

The product should not treat a hard-filter pass as an automatic perfect match.

The implementation handles this in two stages:

### Stage 1 — hard filter

Objective requirements remove obvious non-matches.

For example:

```text
AWS RDS
4–7 years
Bangalore
startup background
```

### Stage 2 — subjective scoring

The remaining candidates are ranked against the rubric.

Therefore someone can pass the hard filters but score lower because the profile does not demonstrate the depth or context described by the rubric.

This is important for the refinement loop because recruiter feedback can distinguish:

```text
"not qualified"
```

from:

```text
"qualified, but not the kind of person I want"
```

The refinement prompt is also instructed **not to turn one rejected candidate into a universal hard filter unless the recruiter feedback clearly implies an objective requirement**. That reduces overfitting after one feedback example.

## 10. Failure handling

The UI deliberately has states for:

### Loading

The recruiter sees a meaningful progress state rather than a blank screen.

### Empty results

If objective filtering returns zero profiles, the app does not make an LLM scoring call. The recruiter is told to loosen a filter or refine the request.

### Rate limit

HTTP 429 from the provider becomes a clear retryable message.

### Timeout/network failure

The backend returns a safe error and the UI keeps the current search state intact.

### Malformed LLM output

The backend validates structured output and rejects malformed responses.

Most importantly:

**a failed refinement does not replace the current valid state.**

The UI keeps the last successful filters, rubric and shortlist and offers Retry.

## 11. Direct editing

The assessment explicitly asks for filters and rubric to be editable.

The left panel exposes:

- skills
- minimum experience
- maximum experience
- location
- company types
- rubric criterion names
- descriptions
- weights

Pressing **Apply** sends the edited state to the backend.

The backend validates it and re-runs the local filter + LLM ranking pipeline.

## 12. Prompt design

Prompts live in:

```text
src/main/resources/prompts/
```

They are intentionally readable rather than hidden inside Java strings.

There are three separate responsibilities:

### `initial-search.txt`

Free text → filters + rubric.

### `score-profiles.txt`

Filtered profiles + rubric → scores + evidence-backed explanations.

### `refine-search.txt`

Current state + recruiter feedback + reviewed profiles → new filters + rubric + changes.

Separating these prompts makes the LLM contract easier to inspect and iterate on.

## 13. How to test the full flow

Use this example:

```text
RDS developers with 4-7 years of experience who have worked at startups, for a role based in Bangalore.
```

Then:

1. Click **Start sourcing**.
2. Wait for the LLM to produce filters/rubric.
3. Review the filters.
4. Review the top five candidates.
5. Click **Not a match** on one candidate.
6. Click **Strong match** on another.
7. Add natural-language feedback, for example:
   `1 is too junior, 2 and 4 are right. Prioritise deeper RDS ownership.`
8. Click **Refine search**.
9. Observe the "Search refined" explanation.
10. Verify the filters/rubric changed visibly.
11. Verify a new shortlist is generated.
12. Edit a filter directly and click **Apply**.
13. Freeze the search.
14. Review the final filters, rubric and ranked shortlist.

## 14. Tests

Run:

```bash
mvn test
```

The included tests verify that:

- all 48 supplied profiles load
- objective filters are applied locally
- filtered results satisfy the selected constraints

## 15. Coding practices used

The implementation keeps responsibilities separated:

- Controller = HTTP/API boundary
- Service = application/business workflow
- Repository = candidate data access/filtering
- LLM client = external API integration
- Session store = session state
- Models = API/domain data structures
- Exception handler = consistent API errors

Other choices:

- immutable Java records for request/response/domain DTOs
- constructor dependency injection
- validation before applying LLM state
- bounded LLM output
- explicit timeouts
- no API secrets in frontend code
- no business logic in the frontend
- no database for an explicitly non-persistent assignment
- prompts kept as repository files

## 16. What I prioritised

### Prioritised

1. **End-to-end loop**
   - Search
   - Filter
   - Score
   - Feedback
   - Refine
   - Freeze

2. **Trust**
   - structured output
   - server validation
   - evidence grounding
   - visible changes after refinement

3. **Failure states**
   - rate limit
   - timeout
   - malformed output
   - empty results
   - retry without losing the current valid state

4. **Recruiter UX**
   - current filters always visible
   - editable rubric
   - candidate-level feedback
   - natural-language feedback
   - clear frozen state

### Deliberately cut

I did not build:

- authentication
- candidate persistence
- recruiter accounts
- a real search/indexing layer
- the 98M-person talent map
- analytics
- notifications
- complex permissions
- multi-role workflows

Those would add infrastructure without improving the specific sourcing refinement loop being evaluated.

## 17. Assessment mapping

| Assessment requirement | Implementation |
|---|---|
| Free text → filters + rubric | `POST /api/search` + `initial-search.txt` |
| Real server-side LLM | `LlmClient` |
| API key from environment | `OPENROUTER_API_KEY` |
| Prompts in repository | `src/main/resources/prompts/` |
| Structured output | JSON contracts + Jackson validation |
| Local dataset filtering | `ProfileRepository` |
| LLM score/rank | `score-profiles.txt` |
| 4–5 profiles | Top 5 |
| Chat refinement | `/refine` + feedback composer |
| Per-profile yes/no | Candidate vote buttons |
| Explain changes | `changes` returned by refinement |
| Direct editing | `/edit` |
| Empty state | UI + no scoring call |
| LLM failure | API error handling + retry |
| Freeze | `/freeze` |
| Final filters/rubric/ranked list | Freeze modal |
| Deliberate near misses | Hard filter + subjective ranking + refinement |
| Single-session scope | In-memory `SessionStore` |

## 18. Loom walkthrough suggestion

Keep the walkthrough under 10–12 minutes.

Suggested sequence:

**0:00–1:00 — Product**

Explain the goal and show the initial search screen.

**1:00–3:00 — Initial search**

Enter:

```text
RDS developers with 4-7 years of experience who have worked at startups, for a role based in Bangalore.
```

Show the generated filters and rubric.

**3:00–5:00 — Shortlist**

Open candidate cards and point out the evidence tied to real profile fields.

**5:00–7:30 — Refinement**

Say something like:

```text
1 is too junior. 2 and 4 are strong matches.
Prioritise candidates with deeper RDS ownership.
```

Show the updated filters/rubric and the change explanation.

**7:30–9:00 — Direct edit**

Change one filter manually and apply it.

**9:00–10:00 — Failure/recovery**

Temporarily use an invalid/unavailable LLM configuration, show the friendly error, then restore the configuration and Retry.

**10:00–11:00 — Freeze**

Freeze the search and show the final shortlist, filters and rubric.

## 19. Important submission note

The assignment asks for a Loom walkthrough showing a failure/recovery moment. The application includes the recovery UI, but a genuine provider failure must be demonstrated during your recording by temporarily using an invalid API key/model or otherwise causing the configured provider to return an error.

The application never uses a fake/canned LLM response as a fallback.
