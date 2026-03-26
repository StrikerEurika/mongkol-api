# Mongkol Sale System - Backend (FastAPI)

FastAPI backend for the Mongkol Sale System using async SQLAlchemy and PostgreSQL.

What's included:

- FastAPI app (app/main.py)
- Async SQLAlchemy models and DB (app/models/_, app/db/_)
- Routers for auth, admin, and sales (app/routers/\*)
- Requirements (requirements.txt)

Quick start (assuming Python 3.10+):

1. Create a venv and activate it:

```bash
python -m venv .venv
source .venv/Scripts/activate # on Windows PowerShell/CMD: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
uvicorn app.main:app --reload --port 8000
```

API docs will be available at http://localhost:8000/docs

## Mock Data Seeder

Seed deterministic mock data for API testing.

Tables are created automatically if missing.

Run:

```bash
# From backend folder, with venv activated
python -m app.db.seed_mock_data --reset --staff 5 --sales 50 --months 3
```

Flags:

- `--reset`: clears existing users, targets, and sales
- `--staff`: number of staff users to create (default 5)
- `--sales`: number of sales to create (default 50)
- `--months`: number of past months for targets (default 3)

Notes:

- Uses `DATABASE_URL` from `.env` (defaults to PostgreSQL).
- Admin user: `admin@example.com`. Staff users: `staff{n}@example.com`.
