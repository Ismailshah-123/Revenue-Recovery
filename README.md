# Revenue Recovery AI

**An AI-assisted sales operations MVP for identifying follow-up gaps and potential revenue opportunities in customer conversations.**

The application brings together email ingestion, follow-up detection, AI-assisted analysis, workspace management, and a dashboard so teams can review conversations that may need attention.

[![Backend Tests](https://github.com/Ismailshah-123/Revenue-Recovery/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/Ismailshah-123/Revenue-Recovery/actions/workflows/backend-tests.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-D71F00)

**Project stage:** MVP. Gmail, AI-provider, and billing features require their respective credentials and configuration. Review the production checklist before using live customer or financial data.

## Contents

- [What the application does](#what-the-application-does)
- [Architecture](#architecture)
- [Repository structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [First-time setup](#first-time-setup)
- [Backend setup](#backend-setup)
- [Backend environment variables](#backend-environment-variables)
- [Frontend setup](#frontend-setup)
- [Run the application locally](#run-the-application-locally)
- [How the login and workspace flow works](#how-the-login-and-workspace-flow-works)
- [Gmail integration](#gmail-integration)
- [AI configuration](#ai-configuration)
- [Stripe and billing](#stripe-and-billing)
- [Database](#database)
- [API documentation](#api-documentation)
- [Running tests](#running-tests)
- [Docker](#docker)
- [Production checklist](#production-checklist)
- [Troubleshooting](#troubleshooting)
- [Security and secrets](#security-and-secrets)
- [Git and GitHub workflow](#git-and-github-workflow)
- [License](#license)

---

## What the application does

The current MVP is designed around a simple revenue recovery workflow:

1. A user creates a workspace.
2. The first user is created as the workspace administrator.
3. Customer email threads can be stored through the API and can be ingested from Gmail when a valid Gmail OAuth token is available.
4. Follow-up detection checks whether an email appears to need attention.
5. AI analysis can estimate a potential value, classify sentiment and urgency, explain the revenue signal, and suggest a next action.
6. The dashboard surfaces email activity, recovery opportunities, and analytics.
7. Optional Stripe billing can enforce plan limits when `MVP_MODE=false`.
8. Background scheduling is enabled when the application is not running in MVP mode.

When no AI API key is configured, the backend uses a deterministic fallback insight instead of failing the request. That makes local development and automated tests possible without an external AI provider.

---

## Architecture

```text
Browser
   |
   | HTTP
   v
Streamlit Frontend :8501
   |
   | REST + JWT
   v
FastAPI Backend :8000
   |
   +---------------------+
   |                     |
   v                     v
SQLAlchemy + DB      External Services
                      |   |   |
                      |   |   +--> Stripe (optional)
                      |   +------> OpenAI (optional)
                      +----------> Gmail (optional)
```

### Main technologies

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI + Uvicorn |
| Database | SQLAlchemy async engine |
| Local database | SQLite + `aiosqlite` |
| Production database | PostgreSQL + `asyncpg` |
| Authentication | JWT via `python-jose` |
| Password hashing | `passlib` + bcrypt |
| Email integration | Gmail API |
| AI | OpenAI API |
| Billing | Stripe |
| Scheduling | APScheduler |
| Testing | Pytest + pytest-asyncio + HTTPX |
| CI | GitHub Actions |

---

## Repository structure

```text
revenue-recovery-mvp/
|
+-- backend/
|   +-- app/
|   |   +-- core/                 # Security and JWT helpers
|   |   +-- routers/              # Auth, billing, email API routes
|   |   +-- services/             # AI, Gmail, email, follow-up logic
|   |   +-- tasks/                # Background scheduler
|   |   +-- config.py             # Centralized environment configuration
|   |   +-- crud.py               # Database CRUD operations
|   |   +-- database.py           # Async SQLAlchemy engine/session
|   |   +-- main.py               # FastAPI application entrypoint
|   |   +-- models.py             # SQLAlchemy models
|   |   +-- schemas.py             # Pydantic schemas
|   |   +-- deps.py               # Dependencies and plan limits
|   |
|   +-- tests/                    # Backend test suite
|   +-- .env.example              # Safe environment template
|   +-- requirements.txt           # Runtime dependencies
|   +-- requirements-dev.txt       # Test/dev dependencies
|   +-- setup_db.py                # Optional manual database initializer
|   +-- run_scheduler.py           # Scheduler entrypoint
|   +-- Dockerfile
|   +-- pytest.ini
|
+-- frontend/
|   +-- components/               # Reusable Streamlit UI components
|   +-- pages/                    # Streamlit page modules
|   +-- views/                    # Dashboard and application views
|   +-- utils/                    # API, auth, session, helper utilities
|   +-- .streamlit/
|   |   +-- secrets.toml.example
|   +-- app.py                    # Streamlit entrypoint
|   +-- requirements.txt
|   +-- Dockerfile
|
+-- .github/
|   +-- workflows/
|       +-- backend-tests.yml     # GitHub Actions backend CI
|
+-- .gitignore
+-- README.md
```

---

## Prerequisites

Install the following before starting:

- Python 3.11 or newer
- Git
- VS Code recommended
- A modern web browser
- Internet access for package installation and optional external services

For the exact dependency versions used by this project, prefer the project requirement files over installing packages manually one by one.

Check your tools:

```powershell
python --version
git --version
```

On Windows, the Python launcher can also be checked with:

```powershell
py --version
```

---

## First-time setup

### 1. Open the project root

Always open the folder containing both `backend` and `frontend`:

```text
C:\Users\<your-user>\Desktop\saas project\revenue-recovery-mvp
```

Do not open only `backend` or only `frontend` when configuring the Git repository.

### 2. Create or use the Git repository

From the project root:

```powershell
cd "C:\Users\<your-user>\Desktop\saas project\revenue-recovery-mvp"
git status
```

The project root should contain a `.git` directory and should report a branch such as `main`.

### 3. Create the backend virtual environment

Windows PowerShell:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation because of execution policy, you can either use Command Prompt or activate through the batch file:

```powershell
.\venv\Scripts\activate.bat
```

macOS/Linux:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 4. Install backend dependencies

With the backend virtual environment active:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 5. Create the backend `.env`

From the `backend` folder:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Then edit:

```text
backend/.env
```

The `backend/.env` file is local-only and must not be committed.

### 6. Create the frontend virtual environment

Open a second terminal at the project root:

Windows:

```powershell
cd "C:\Users\<your-user>\Desktop\saas project\revenue-recovery-mvp\frontend"
python -m venv venv_frontend
.\venv_frontend\Scripts\Activate.ps1
```

macOS/Linux:

```bash
cd frontend
python3 -m venv venv_frontend
source venv_frontend/bin/activate
```

Install frontend dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 7. Create Streamlit secrets

From the `frontend` folder:

```powershell
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

macOS/Linux:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

The default local value is:

```toml
BACKEND_URL = "http://127.0.0.1:8000"
```

Do not commit `frontend/.streamlit/secrets.toml`.

---

## Backend environment variables

The backend reads configuration from `backend/.env` using Pydantic Settings.

A complete local `.env` can look like this:

```env
# Application
ENVIRONMENT=development
DEBUG=true
FRONTEND_URL=http://localhost:8501

# Security
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Database
DATABASE_URL=sqlite:///./app.db

# Gmail - optional
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=
GMAIL_USER=

# AI - optional
AI_API_KEY=

# MVP mode
MVP_MODE=true

# Feature limits
MAX_EMAIL_THREADS=20
MAX_AI_CALLS=50

# Stripe - only needed for live billing
STRIPE_API_KEY=
STRIPE_WEBHOOK_SECRET=
```

### Recommended development values

For local development, keep:

```env
ENVIRONMENT=development
DEBUG=true
MVP_MODE=true
DATABASE_URL=sqlite:///./app.db
```

### Generate a secure `SECRET_KEY`

Do not use the placeholder value in a real deployment.

Run this from the backend virtual environment:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated result into:

```env
SECRET_KEY=YOUR_GENERATED_VALUE
```

### What each variable does

| Variable | Required | Development guidance |
|---|---:|---|
| `ENVIRONMENT` | Yes | `development` locally, `production` for deployment |
| `DEBUG` | Yes | `true` locally, `false` in production |
| `FRONTEND_URL` | Yes | `http://localhost:8501` locally |
| `SECRET_KEY` | Yes | Long random secret, never commit |
| `ALGORITHM` | Yes | Keep `HS256` unless the auth implementation is intentionally changed |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Default `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | Default `30` |
| `DATABASE_URL` | Yes | SQLite locally; PostgreSQL for production |
| `GMAIL_CLIENT_ID` | No | Gmail integration configuration |
| `GMAIL_CLIENT_SECRET` | No | Gmail integration configuration |
| `GMAIL_REFRESH_TOKEN` | No | Reserved for Gmail configuration |
| `GMAIL_USER` | No | Gmail account identifier/configuration |
| `AI_API_KEY` | No | Leave blank to use the built-in fallback AI insight |
| `MVP_MODE` | Yes | `true` for local MVP; `false` for billing enforcement and scheduler |
| `MAX_EMAIL_THREADS` | No | Default `20` |
| `MAX_AI_CALLS` | No | Default `50` |
| `STRIPE_API_KEY` | No | Needed when live Stripe billing is enabled |
| `STRIPE_WEBHOOK_SECRET` | No | Needed for validating Stripe webhooks |

### Important: `MVP_MODE`

`MVP_MODE=true` is the easiest local configuration.

In MVP mode:

- Billing enforcement is disabled.
- The checkout endpoint returns a local MVP stub URL.
- The background scheduler is disabled.
- Feature usage checks do not block requests.
- AI can still work through the external provider when `AI_API_KEY` is configured.
- The application can run without Stripe credentials.

For a production billing flow, set:

```env
MVP_MODE=false
```

and configure the required Stripe values and plan price IDs in the application configuration.

---

## Frontend setup

The Streamlit application reads the backend address from:

```text
frontend/.streamlit/secrets.toml
```

For local development:

```toml
BACKEND_URL = "http://127.0.0.1:8000"
```

If your backend runs on another host or port, change this value. For example:

```toml
BACKEND_URL = "http://192.168.1.25:8000"
```

Do not place backend API keys, JWT secrets, Gmail credentials, or Stripe secrets in Streamlit secrets. The frontend only needs the backend URL for the current architecture.

---

## Run the application locally

The cleanest development workflow uses two terminals.

### Terminal 1: FastAPI backend

```powershell
cd "C:\Users\<your-user>\Desktop\saas project\revenue-recovery-mvp\backend"
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Or:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Expected backend URLs:

```text
API:       http://127.0.0.1:8000
Health:    http://127.0.0.1:8000/health
Swagger:   http://127.0.0.1:8000/docs
ReDoc:     http://127.0.0.1:8000/redoc
OpenAPI:   http://127.0.0.1:8000/openapi.json
```

### Terminal 2: Streamlit frontend

```powershell
cd "C:\Users\<your-user>\Desktop\saas project\revenue-recovery-mvp\frontend"
.\venv_frontend\Scripts\Activate.ps1
streamlit run app.py
```

Expected frontend URL:

```text
http://localhost:8501
```

### Verify the backend before opening the frontend

In PowerShell:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health | Select-Object -ExpandProperty Content
```

You should receive JSON containing:

```json
{"status":"ok"}
```

Then open:

```text
http://localhost:8501
```

---

## First login / signup

The frontend starts on the authentication screen.

### Create a workspace

Use the `Create Workspace` tab and enter:

- Company name
- Work email
- Password

The backend creates:

1. A workspace
2. A default subscription record
3. The first user as `admin`
4. An access token and refresh token

### Login

Use the same email and password in the `Login` tab.

The frontend stores the session token in Streamlit session state and uses the JWT as a Bearer token when making backend API requests.

---

## How the login and workspace flow works

The authentication endpoints are:

```text
POST /api/auth/signup
POST /api/auth/login
POST /api/auth/refresh
GET  /api/auth/me
```

A typical signup request is:

```json
{
  "email": "founder@example.com",
  "password": "correct-horse-battery-staple",
  "company": "Acme Revenue Co"
}
```

A typical login request is:

```json
{
  "email": "founder@example.com",
  "password": "correct-horse-battery-staple"
}
```

The API returns a token pair. The frontend then calls `/api/auth/me` to load the current user, workspace, role, and plan.

---

## Gmail integration

Gmail integration is optional for local development.

### Current implementation behavior

The current Gmail ingestion service reads a locally stored OAuth token from:

```text
backend/token.pickle
```

The code resolves that file relative to the backend package, so the Gmail service can find it regardless of whether Uvicorn or pytest was launched from the backend directory or another working directory.

The repository intentionally does **not** commit this token.

### Important distinction about the Gmail environment variables

The following configuration values exist in `backend/.env.example` and `app/config.py`:

```env
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=
GMAIL_USER=
```

They are available as centralized application settings, but the current `email_sync.py` implementation obtains Gmail credentials from `backend/token.pickle`. In other words, filling the four `GMAIL_*` values alone does not currently generate or install the OAuth token.

### What you need for a real Gmail connection

You need a valid Gmail OAuth credential/token file compatible with the code in `email_sync.py` and saved as:

```text
backend/token.pickle
```

The current repository does not include an interactive Gmail OAuth bootstrap script. Do not copy a real production token into Git, GitHub, a ZIP archive shared publicly, or a public issue.

### What happens without a token

If `backend/token.pickle` does not exist, the Gmail service logs a warning and returns an empty thread list instead of crashing the application. That lets the rest of the MVP continue running in a no-inbox-connected state.

---

## AI configuration

AI analysis is optional.

### With AI enabled

Set:

```env
AI_API_KEY=your-provider-api-key
```

The current implementation uses the OpenAI client and the model configured in `backend/app/services/ai_reasoning.py`.

### Without AI enabled

Leave this blank:

```env
AI_API_KEY=
```

The application then uses its built-in fallback reasoning path. This is useful for:

- Local UI development
- Backend tests
- Offline development
- Avoiding external API costs during setup

The fallback still returns a structured insight instead of causing the request to fail.

### AI analysis flow

For an email thread:

```text
Email snippet
    |
    v
Follow-up detector
    |
    +----> needs_followup + confidence
    |
    v
AI reasoning service
    |
    +----> summary
    +----> sentiment
    +----> urgency
    +----> revenue signal
    +----> detected value
    +----> reasoning
    +----> suggested action
    +----> confidence score
```

---

## Stripe and billing

Stripe is optional while the application is in MVP mode.

### Local development

Keep:

```env
MVP_MODE=true
STRIPE_API_KEY=
STRIPE_WEBHOOK_SECRET=
```

The checkout endpoint returns a stub response rather than creating a live Stripe checkout session.

### Live billing mode

Set:

```env
MVP_MODE=false
STRIPE_API_KEY=sk_live_or_test_key
STRIPE_WEBHOOK_SECRET=whsec_...
```

The billing router supports:

```text
GET  /api/billing/plan
POST /api/billing/create-checkout
POST /api/billing/webhook
```

### Plan price IDs

The project defines starter, growth, and pro plan settings in `backend/app/config.py`. Before live billing, make sure each plan has a valid Stripe `price_id` configured for the environment you are using.

### Stripe webhook

The webhook endpoint validates the `stripe-signature` header using:

```env
STRIPE_WEBHOOK_SECRET=...
```

Do not disable signature validation in production.

---

## Database

### Local SQLite

The default local configuration is:

```env
DATABASE_URL=sqlite:///./app.db
```

The backend normalizes the URL for SQLAlchemy's asynchronous SQLite driver.

When the FastAPI application starts, its lifespan handler automatically runs the SQLAlchemy metadata creation step, so a fresh local database is created without a separate migration command.

### Optional manual initialization

If you want to initialize the schema manually:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python setup_db.py
```

You should see:

```text
Database initialized
```

### PostgreSQL

For production, use a PostgreSQL connection string such as:

```env
DATABASE_URL=postgresql://username:password@host:5432/revenue_recovery
```

The backend converts a standard PostgreSQL URL to the asynchronous `asyncpg` SQLAlchemy driver automatically.

Use a managed PostgreSQL service in production and keep the credentials in the deployment platform's secret manager rather than committing them to the repository.

---

## API documentation

Once the backend is running, FastAPI exposes interactive documentation.

### Swagger UI

```text
http://127.0.0.1:8000/docs
```

### ReDoc

```text
http://127.0.0.1:8000/redoc
```

### OpenAPI JSON

```text
http://127.0.0.1:8000/openapi.json
```

### Main route groups

| Area | Base path |
|---|---|
| Health | `/health` |
| Root | `/` |
| Authentication | `/api/auth` |
| Billing | `/api/billing` |
| Emails | `/emails` |

### Example health request

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### Example signup request with curl

```bash
curl -X POST "http://127.0.0.1:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"founder@example.com","password":"correct-horse-battery-staple","company":"Acme Revenue Co"}'
```

---

## Running tests

Backend tests are located in:

```text
backend/tests/
```

### Recommended command

From the backend directory with the backend environment active:

```powershell
pytest -v
```

### Run compilation checks

```powershell
python -m compileall -q app tests run_scheduler.py setup_db.py
```

### Run both checks

```powershell
python -m compileall -q app tests run_scheduler.py setup_db.py
pytest -v
```

The repository includes GitHub Actions CI that installs backend dependencies, checks compilation, and runs the backend tests on pushes and pull requests affecting the backend.

### Test database behavior

The test suite uses an isolated temporary SQLite database. The tests do not require your development `app.db`, Gmail token, OpenAI key, or Stripe account.

That means you should be able to run the backend tests with:

```env
AI_API_KEY=
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=
GMAIL_USER=
MVP_MODE=true
```

---

## Docker

Both backend and frontend have separate Dockerfiles.

### Backend image

From `backend`:

```bash
docker build -t revenue-recovery-backend .
docker run --rm -p 8000:8000 --env-file .env revenue-recovery-backend
```

### Frontend image

From `frontend`:

```bash
docker build -t revenue-recovery-frontend .
docker run --rm -p 8501:8501 revenue-recovery-frontend
```

For the frontend container to communicate with a backend container, do not use `127.0.0.1` as the backend address unless both services are inside the same network and that address resolves to the correct service. Use the backend service/container hostname or a reachable network address.

### Example Docker network

```bash
docker network create revenue-recovery

docker run -d --name revenue-backend --network revenue-recovery -p 8000:8000 --env-file backend/.env revenue-recovery-backend
```

Then configure the frontend secret for the backend container hostname:

```toml
BACKEND_URL = "http://revenue-backend:8000"
```

Start the frontend on the same network:

```bash
docker run --rm --network revenue-recovery -p 8501:8501 revenue-recovery-frontend
```

---

## Production checklist

Before deploying publicly, review all of the following:

### Environment

```env
ENVIRONMENT=production
DEBUG=false
MVP_MODE=false
```

Use a strong unique secret:

```env
SECRET_KEY=<long-random-value>
```

Use PostgreSQL instead of a local SQLite file:

```env
DATABASE_URL=postgresql://...
```

### Security

- Never commit `.env` files.
- Never commit `credentials.json`.
- Never commit `token.pickle`.
- Never commit local database files.
- Never commit Stripe secret keys.
- Never commit AI provider keys.
- Never expose JWT secrets to the frontend.
- Restrict CORS to the real frontend origin.
- Keep `DEBUG=false` in production.
- Use HTTPS for public deployments.
- Rotate leaked credentials immediately.

### Billing

- Configure real Stripe price IDs.
- Configure `STRIPE_API_KEY`.
- Configure `STRIPE_WEBHOOK_SECRET`.
- Test webhook delivery and signature validation.
- Verify subscription state transitions.

### Gmail

- Use a controlled production OAuth flow.
- Store OAuth credentials in a secure secret store.
- Avoid storing long-lived credentials in source control or shared archives.

### Infrastructure

- Put FastAPI behind a production reverse proxy or managed platform.
- Use a managed PostgreSQL database.
- Configure application logging and monitoring.
- Configure backups for production data.
- Use process supervision or the platform's native service manager.

---

## Troubleshooting

### `ModuleNotFoundError` after starting the backend

Make sure the correct backend virtual environment is active:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Then verify:

```powershell
python -c "import fastapi, sqlalchemy, aiosqlite; print('backend dependencies OK')"
```

### `ModuleNotFoundError` when starting Streamlit

Activate the frontend environment:

```powershell
cd frontend
.\venv_frontend\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Verify Streamlit:

```powershell
streamlit --version
```

### Backend starts but frontend says it cannot connect

Check the API directly:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

If that works, check:

```text
frontend/.streamlit/secrets.toml
```

and make sure it contains:

```toml
BACKEND_URL = "http://127.0.0.1:8000"
```

### CORS error

Check that `FRONTEND_URL` exactly matches the browser origin used by Streamlit:

```env
FRONTEND_URL=http://localhost:8501
```

If you use `http://127.0.0.1:8501` instead, configure that exact origin instead.

### Backend fails at startup with a settings validation error

The most common missing required values are:

```env
SECRET_KEY=...
DATABASE_URL=...
```

Make sure `backend/.env` exists and contains both.

### AI analysis works but does not call the external model

Check:

```env
AI_API_KEY=...
```

If the key is blank, the fallback insight path is expected behavior.

### Gmail returns no emails

Check that:

```text
backend/token.pickle
```

exists and is a valid credential object. The current Gmail sync code returns an empty list rather than crashing when the token is missing or the Gmail call fails.

### Git shows thousands of files from `backend/venv`

Your virtual environment should never be committed.

From the project root:

```powershell
git reset
git check-ignore -v backend\venv\Scripts\python.exe
git check-ignore -v frontend\venv_frontend\Scripts\python.exe
```

Both commands should report a matching `.gitignore` rule.

Then:

```powershell
git add .
git status
```

### Git shows `LF will be replaced by CRLF`

This is a Windows line-ending warning, not an application runtime error. It is normally safe for a Windows development environment. The important check is that ignored directories such as `venv` are not being staged.

---

## Security and secrets

The following files should remain local-only:

```text
backend/.env
backend/credentials.json
backend/token.pickle
backend/*.db
backend/*.log
frontend/.streamlit/secrets.toml
backend/venv/
frontend/venv_frontend/
```

Safe templates that can be committed:

```text
backend/.env.example
frontend/.streamlit/secrets.toml.example
```

### If a secret was accidentally committed

Removing a secret from the latest working tree is not sufficient if it already exists in Git history. Rotate the compromised credential first, then clean the Git history using an appropriate repository-history tool and verify that the secret is revoked.

---

## Git and GitHub workflow

From the repository root:

```powershell
cd "C:\Users\<your-user>\Desktop\saas project\revenue-recovery-mvp"
```

Check the repository:

```powershell
git status
git remote -v
git branch --show-current
```

If the remote is the target repository, you should see:

```text
https://github.com/Ismailshah-123/Revenue-Recovery.git
```

### First commit

After verifying `git status` does not contain secrets or virtual environments:

```powershell
git add .
git status
git commit -m "Prepare Revenue Recovery SaaS"
git push -u origin main
```

### Normal update workflow

```powershell
git add .
git commit -m "Update Revenue Recovery"
git push
```

### Important Git rule

Do not use:

```powershell
git add -f .
```

to force ignored files into the repository. That can accidentally publish secrets, credentials, local databases, or virtual environments.

---

## Development recommendations

For the current MVP, the simplest local configuration is:

```env
ENVIRONMENT=development
DEBUG=true
MVP_MODE=true
DATABASE_URL=sqlite:///./app.db
AI_API_KEY=
```

Then start:

```text
FastAPI     -> http://127.0.0.1:8000
Swagger     -> http://127.0.0.1:8000/docs
Streamlit   -> http://localhost:8501
```

This setup avoids requiring Gmail, OpenAI, Stripe, or PostgreSQL just to run the application locally.

---

## Current project status

The backend contains automated tests and GitHub Actions CI. The local test environment is intentionally isolated from live external services, and the AI service contains a fallback path when an external AI API key is not configured.

For a production launch, the next engineering steps should focus on a formal Gmail OAuth onboarding flow, database migrations, production secret management, hardened deployment configuration, and expanded end-to-end frontend/API tests.

---

## License

This project currently does not include a separate license file in the repository. Add a `LICENSE` file before publicly distributing the software under a specific open-source license.

---

## Author

**Ismail Shah**

Revenue Recovery AI — full-stack SaaS MVP for finding and analyzing potential missed revenue opportunities in customer conversations.
