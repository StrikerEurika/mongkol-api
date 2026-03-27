# Mongkol Sale System - Backend (FastAPI)

FastAPI backend for the Mongkol Sale System. Built to support dual-currency (USD/KHR), role-based access control, and robust sales tracking.

## Technical Stack

- **Framework**: FastAPI
- **Database Engine**: PostgreSQL with Async SQLAlchemy
- **Database Migrations**: Alembic
- **Package Manager**: `uv`

---

## Quick Start

### 1. Prerequisites
Ensure you have Python (>=3.14 recommended, though 3.10+ may work) and `uv` installed. 
You will also need a running instance of **PostgreSQL**.

### 2. Environment Variables
Create a `.env` file in the root of the `mongkol-api` directory:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mongkol
```

### 3. Install Dependencies
We use `uv` for fast dependency management. Sync your environment securely:
```bash
uv sync
```

### 4. Run Database Migrations
Create your database tables by running the Alembic migrations:
```bash
uv run alembic upgrade head
```

### 5. Start the Server
Start the FastAPI application in development mode with hot-reloading:
```bash
uv run uvicorn app.main:app --reload --port 8000
```
Once running, the interactive API documentation (Swagger UI) is automatically available at: **http://localhost:8000/docs**

---

## Mock Data Seeder

Seed deterministic dummy data (Products, Users, Sales, and Targets) to make local testing easier. 

### Running the Seeder
```bash
uv run python -m app.db.seed_mock_data --reset
```

### Available Configuration Flags:
- `--reset`: Safely cascade deletes existing sales, targets, products, and users before seeding new ones.
- `--staff`: Number of mock staff members to create (default `5`).
- `--sales`: Number of mock recent sales to generate (default `50`).
- `--months`: Number of past months to generate sales targets for (default `3`).

### Generated Entities:
- **Products**: Basic candle lineup (` Large Candle`, `Small Candle`, `Incense Sticks`, `Offering Set`) with default USD and KHR pricing.
- **Admin Account**: Email: `admin@example.com`
- **Staff Accounts**: Email: `staff1@example.com`, `staff2@example.com`, etc.

### AI models used
- **nvidia/nemotron-3-super-120b-a12b**: For code generation.