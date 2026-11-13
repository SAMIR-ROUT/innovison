# Event Second Brain — Backend API

## What this is
This backend service manages sponsor profiles and tracks the full audit history of sponsorship commitment adjustments for the college event organizing team system "Event Second Brain – Agentic Workflow Automation & Context Engineering". It was engineered by Member 3 (Backend & Database) for NIT Rourkela Innov-a-thon 2.0 using FastAPI, PostgreSQL (hosted on Supabase), SQLAlchemy ORM, Pydantic v2 validation, and Alembic database migrations.

## Project structure
```text
backend/
├── app/
│   ├── __init__.py           # Package marker for the app module
│   ├── main.py               # FastAPI application, route declarations, CORS, OpenAPI metadata, and global error handlers
│   ├── database.py           # SQLAlchemy engine, session factory (SessionLocal), Base, and get_db() session dependency
│   ├── models.py             # SQLAlchemy ORM models: Sponsor and SponsorHistory
│   ├── schemas.py            # Pydantic v2 request/response schemas, field validators, and OpenAPI example payloads
│   └── auth.py               # API key authentication dependency (verify_api_key) protecting write endpoints
├── alembic/                  # Database migration configuration and version scripts
│   ├── env.py                # Alembic runtime environment connecting dynamically via DATABASE_URL
│   └── versions/             # Auto-generated database migration scripts
├── tests/                    # Automated test suite using pytest and FastAPI TestClient
│   ├── __init__.py           # Package marker for tests
│   ├── conftest.py           # Shared test fixtures (TestClient, API key, automatic DB cleanup)
│   └── test_api.py           # 17 automated end-to-end endpoint tests
├── seed.py                   # Standalone idempotent database seeding script with initial sample sponsors
├── alembic.ini               # Alembic migration tool settings
├── requirements.txt          # Pinned Python package dependencies
├── .env.example              # Template for required environment variables
├── .env                      # Local secret environment variables (ignored by Git)
└── README.md                 # Complete backend documentation and deployment guide
```

## Prerequisites
- Python 3.10 or higher
- A Supabase project (free tier works)
- Git

## Setup from scratch
1. Clone the repository and navigate to the `backend/` directory:
   ```bash
   git clone <repo-url>
   cd backend
   ```
2. Create and activate a Python virtual environment:
   - **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
3. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your real values:
   ```bash
   cp .env.example .env
   ```
   - `DATABASE_URL`: Your Supabase PostgreSQL URI from *Project Settings > Database > URI* (URL-encode special characters in the password like `%40` for `@`).
   - `API_KEY`: Secret string required in the `X-API-Key` header for write operations (generate with `python -c "import secrets; print(secrets.token_hex(32))"`).
   - `ALLOWED_ORIGINS`: Comma-separated allowed frontend origins for CORS (set to `*` for development).
5. Run Alembic migrations to set up the database schema in Supabase:
   ```bash
   alembic upgrade head
   ```
6. (Optional) Run the seed script to populate initial sample sponsors:
   ```bash
   python seed.py
   ```
7. Start the Uvicorn development server:
   ```bash
   uvicorn app.main:app --reload
   ```
8. Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser to confirm the interactive Swagger UI loads.

## Environment variables

| Variable | Example value | What it is |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://postgres:secret_pass@db.xyz.supabase.co:5432/postgres` | PostgreSQL connection URI for Supabase database |
| `API_KEY` | `4f3a8b2c9d1e0f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a` | Secret authentication token required for write endpoints (`POST`, `PATCH`) |
| `ALLOWED_ORIGINS` | `*` or `http://localhost:3000,http://127.0.0.1:3000` | Whitelisted origins permitted to make cross-origin browser requests |

## API endpoints

| Method | Endpoint | Auth required | What it does |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | No | Basic service uptime and health check |
| `GET` | `/health/db` | No | Verifies active database connection via `SELECT 1` |
| `POST` | `/sponsors` | Yes (`X-API-Key`) | Creates a new sponsor commitment record |
| `GET` | `/sponsors` | No | Retrieves all registered sponsors |
| `GET` | `/sponsors/{sponsor_id}` | No | Retrieves details of a specific sponsor by ID |
| `PATCH` | `/sponsors/{sponsor_id}` | Yes (`X-API-Key`) | Updates commitment and atomically logs a history entry |
| `GET` | `/sponsors/{sponsor_id}/history` | No | Retrieves chronological change history for a sponsor |

## Running tests
From the `backend/` directory with your virtual environment active, run:
```bash
pytest tests/ -v
```

## Demo day checklist
Verify these items before the judges arrive:
- [ ] `.env` is filled in with real Supabase credentials
- [ ] `alembic upgrade head` has been run on this machine
- [ ] `python seed.py` has been run (`sponsors` table has data)
- [ ] `uvicorn app.main:app --reload` starts without errors
- [ ] `http://localhost:8000/docs` loads in browser
- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] `GET /health/db` returns `{"status": "ok", "db": "connected"}`
- [ ] `GET /sponsors` returns at least 5 sponsors
- [ ] `POST /sponsors` with API key returns `201`
- [ ] `PATCH /sponsors/{id}` with API key logs a history row
- [ ] `pytest tests/ -v` shows all tests passing
- [ ] Frontend teammate has the base URL and API key
- [ ] AI agent teammate has the base URL and endpoint list

## Troubleshooting
1. **"connection refused" on startup** → Check `DATABASE_URL` in `.env`. Ensure your Supabase project is active, the database port is `5432`, and any special characters in the password (e.g., `@`) are URL-encoded (`%40`).
2. **"relation does not exist" error** → Run `alembic upgrade head` from `backend/` to apply database migrations.
3. **403 on POST or PATCH** → Check that the `X-API-Key` request header matches the `API_KEY` defined in `backend/.env`.
