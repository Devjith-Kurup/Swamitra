# Swamitra

AI-powered agricultural decision-support system that combines soil, climate, water, satellite data, and machine learning to recommend crops, optimize farm management, and simulate farming scenarios.

This repository is the project foundation. ML training, satellite pipelines, the AI agent, and the frontend are reserved as independent packages and are not implemented yet.

## Architecture

Modules are separated so they can evolve independently:

| Path | Responsibility |
|------|----------------|
| `backend/` | FastAPI API, configuration, logging, schemas, services, simulator |
| `agent/` | Prompts, tools, and workflows for the decision-support agent |
| `ml/` | Model notebooks, training, and evaluation |
| `satellite/` | Imagery preprocessing and zoning |
| `data/` | Crop reference data plus raw/processed datasets (datasets are gitignored) |
| `frontend/` | Web client (not initialized) |
| `docs/` | Project documentation |

The backend is PostgreSQL-compatible via `DATABASE_URL`. Secrets and API keys belong only in environment variables (see `.env.example`). Do not commit model weights, datasets, or `.env` files.

## Requirements

- Python 3.12
- Optional: Docker and Docker Compose (API + PostgreSQL)

## Local setup

1. Copy environment placeholders and replace them with local values:

   ```powershell
   copy .env.example .env
   ```

2. Create a virtual environment and install backend dependencies:

   ```powershell
   cd backend
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Run the API:

   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

4. Check health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) should return `{"status":"ok"}`.

5. Run tests:

   ```powershell
   pytest
   ```

## Docker

From the repository root, after creating a `.env` from `.env.example`:

```powershell
docker compose up --build
```

PostgreSQL is provided as the `db` service. The backend container reads `DATABASE_URL` pointing at that service. The `/health` endpoint does not require a live database.

## License

MIT. See [LICENSE](LICENSE).
