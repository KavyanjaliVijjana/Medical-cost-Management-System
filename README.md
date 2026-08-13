# Medical Cost Trend Forecasting and Cost-Containment Advisor

Healthcare financial and operational analytics for early visibility into medical cost pressure. The project is intentionally built in phases; this repository currently contains **Phase 2: Data Ingestion**.

## Current scope

- FastAPI backend with a health endpoint and SQLite initialization.
- SQLAlchemy foundation and an idempotently seeded demo user.
- React, Vite, TypeScript, and Tailwind frontend shell.
- Simple demo-user login and frontend health-status indicator.
- CSV validation, preview, confirmation-based processing, and canonical SQLite storage.
- A deterministic, clearly labeled **Synthetic Demo Dataset** for hackathon demonstrations.

Analytics, forecasting, alerts, recommendations, scenarios, reports, and AI capabilities are not implemented yet.

## Prerequisites

- Python 3.11+
- Node.js 20+

## Run locally

### Backend

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

The first startup creates `backend/medical_cost.db` and seeds `demo@medicalcost.local`.

Verify API health at [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health). Interactive API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

### Frontend

In another terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) and select **Continue as demo user**.

Open **Data upload** to validate a CSV or select **Load Demo Dataset**. Required CSV headers are `date`, `department`, `patient_count`, and `total_cost`. Records are written to SQLite only after selecting **Confirm processing**.

## Configuration

Root `.env.example` documents the available backend and frontend settings. For local use, copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to `frontend/.env`.

## Architecture

- `backend/app/api`: HTTP routes only.
- `backend/app/services`: reserved deterministic business-service boundaries for future phases.
- `backend/app/db`: SQLAlchemy configuration, ORM models, and initialization.
- `frontend/src/api`: typed backend client.
- `frontend/src/components` and `frontend/src/pages`: application shell and page-level UI.

The application is a modular monolith. Future AI capability, if added after the deterministic MVP, will call established services rather than access the database or duplicate logic.
