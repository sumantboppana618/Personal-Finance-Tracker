# Personal Finance Tracker

## Project Overview

**Personal Finance Tracker** is an AI-powered web application designed to help users manage their personal finances in a simple and intelligent way. The app allows users to record income and expenses, organize transactions into categories, track monthly spending, and receive AI-generated financial insights. It is intended for students, young professionals, and anyone who wants a clearer view of their spending habits and better budgeting support.

---

## Week 11 Milestone Status

- [x] Project proposal added to the repository `README.md`
- [x] Public GitHub repository created with a project board and initial issues
- [x] Database provisioned and connection tested through `/db-health`
- [x] App skeleton running locally with a working `/health` endpoint
- [x] Dockerfile created and tested for container builds
- [x] Feature branches created for each team ownership area

---

## Week 12 Milestone Status

- [x] Core transaction routes implemented (create, read, update, delete, filter)
- [x] MongoDB read/write implemented with mock-friendly fallback for tests/CI
- [x] AI spending insight endpoint (`/ai/spending-insights`) working end-to-end
- [x] Unit test suite expanded to 11 tests covering routes and logic
- [x] GitHub Actions CI added (lint, tests, Docker build, container smoke test)
- [x] Docker image builds cleanly; container health endpoint verified in CI

---

## Local Setup & Secrets

- **Environment variables** (add to `.env` or export before running):
  - `MONGO_URI`: Atlas connection string (e.g., `mongodb+srv://user:pass@personalfinancetracker...`)
  - `MONGO_DB_NAME`: optional; defaults to `finance_tracker`
  - `GEMINI_KEY`: Gemini API key powering `/ai/spending-insights`
  - `USE_MOCK_DB`: set to `1` to run locally without a real MongoDB (tests/CI use this)

- **Commands**
  - `pip install -r requirements.txt`
  - `python app.py`
  - `& "$HOME\AppData\Roaming\Python\Python314\Scripts\pytest.exe" -q`
  - `& "$HOME\AppData\Roaming\Python\Python314\Scripts\flake8.exe" . --jobs 1`

These steps mirror the CI job so your local dev environment runs the same checks as every push/PR to `main`.

## Features

### Core Features

- Add income and expense transactions
- View transaction history
- Categorise transactions such as food, transport, rent, shopping, salary, and bills
- Edit and delete transactions
- View total income, total expenses, and balance
- View monthly spending summaries
- Filter transactions by type, category, or date

### AI-Powered Features via Gemini

- **AI Spending Analysis:** Analyses the user's recent transactions and explains spending patterns
- **AI Budget Advice:** Suggests budget adjustments based on transaction history
- **AI Saving Tips:** Gives personalised money-saving recommendations based on overspending categories

---

## Tech Stack

### Backend: Python + Flask
Chosen because it is simple, lightweight, and matches the tools already used in earlier coursework.

### Frontend: HTML, CSS, JavaScript
Chosen to keep the project manageable within 3 weeks and allow fast iteration.

### Database: MongoDB Atlas
Chosen because it is cloud-hosted, easy to connect to, and suitable for storing transaction data.

### AI Integration: Google Gemini API
Required for the AI-powered features and recommended in the project guidelines.

### Containerization: Docker
Required to package the application consistently and run it locally and in deployment.

### CI/CD: GitHub Actions
Required by the course to automate testing, Docker builds, and deployment.

### Deployment: Render
Suggested in the project guide and works well with Docker and GitHub Actions.

---

## Team Members and Roles

### Member 1 - Backend & Database Lead
- Build Flask routes and application logic
- Set up MongoDB Atlas connection
- Implement CRUD operations for transactions
- Maintain API structure and data validation

### Member 2 - Frontend & UI Lead
- Build dashboard UI
- Create forms for adding and editing transactions
- Design transaction list and summary views
- Improve usability and responsiveness

### Member 3 - AI & DevOps Lead
- Integrate Gemini API
- Build AI analysis and recommendation endpoints
- Create Dockerfile and container setup
- Prepare GitHub Actions workflows and deployment setup

---

## Shared Team Responsibilities

- All members create and work from feature branches
- All tasks tracked through GitHub Issues and project board
- All changes merged through pull requests
- Every member reviews teammates' PRs and leaves meaningful comments
- All members contribute commits and weekly progress updates

---

## High-Level 3-Week Timeline

### Week 11 - Foundation & Proposal
- Finalise project proposal
- Set up a public GitHub repository and project board
- Create issues and feature branches
- Set up MongoDB Atlas and test the connection
- Build Flask app skeleton with health-check endpoint
- Create and test Dockerfile

### Week 12 - Core Development & CI
- Implement transaction CRUD features
- Build dashboard and transaction interface
- Implement one AI-powered feature end-to-end
- Add unit tests for routes and application logic
- Set up GitHub Actions CI pipeline

### Week 13 - Deployment & Presentation Prep
- Deploy the application to Render
- Configure CD pipeline from GitHub Actions
- Test AI features on live deployment
- Update README with setup instructions and live URL
- Prepare slides and rehearse live demo

---

## Contributors

| Member | Role | GitHub |
|--------|------|--------|
| Sumant | AI & DevOps Lead | @sumantboppana618 |
| Ibrahim | Frontend & UI Lead | @ibrahimgit05 |
| Moataz | Backend & Database Lead | @moataz-r |
