# Production-grade Playwright + Python QA Test Runner Container
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app/qa-automation

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test framework
COPY . .

ENV BASE_URL=http://localhost:8080
ENV HEADLESS=true

# Default entrypoint runs the smoke tests and produces an HTML report
ENTRYPOINT ["pytest"]
CMD ["-m", "smoke", "--html=reports/report.html", "--self-contained-html"]
