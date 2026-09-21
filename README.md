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

## API Endpoints

### 1. Crop Recommendation (Raw ML)
`POST /api/v1/crops/predict`

Predicts the most suitable crop based on soil and climate conditions using Hugging Face model `Sheshank2609/crop-recommendation-system`.

**Request Body:**
```json
{
  "nitrogen": 90,
  "phosphorus": 42,
  "potassium": 43,
  "ph": 6.5,
  "temperature": 25.0,
  "humidity": 80.0,
  "rainfall": 200.0
}
```

### 2. Farm-Aware Crop Recommendation
`POST /api/v1/crops/recommend`

Evaluates crop candidates using the ML model and passes predictions through SWAMITRA's deterministic `SuitabilityService` to account for:
- Available water (rainfall + irrigation) vs. crop water requirement
- Available growing duration vs. crop duration days
- Soil pH compatibility
- Climate limits (temperature, rainfall)

Supports optional automated weather lookup via `latitude` and `longitude`, as well as optional yield estimation via `include_yield=true`.

**Request Body (with Yield Enrichment):**
```json
{
  "nitrogen": 90,
  "phosphorus": 42,
  "potassium": 43,
  "ph": 6.5,
  "temperature": 25.0,
  "humidity": 80.0,
  "rainfall": 200.0,
  "farm_constraints": {
    "water_availability_mm": 1000.0,
    "growing_days_available": 120,
    "farm_area_ha": 2.5
  },
  "include_yield": true,
  "yield_state": "Maharashtra",
  "yield_season": "Kharif",
  "yield_soil_type": "Black"
}
```

### 3. Weather Service
`GET /api/v1/weather/current?lat=18.52&lon=73.85`
`GET /api/v1/weather/forecast?lat=18.52&lon=73.85&days=7`

Retrieves normalized environmental and weather data using configurable providers (Open-Meteo, OpenWeatherMap, WeatherAPI).

### 4. Crop Yield Prediction (ML)
`POST /api/v1/yield/predict`

Predicts crop yield (quintal/hectare) and estimated total production using Hugging Face model `NIHAL670/Crop-yield`.

**Request Body:**
```json
{
  "state": "Maharashtra",
  "crop": "Rice",
  "season": "Kharif",
  "soil_type": "Black",
  "area": 2.0,
  "rainfall": 1100.0,
  "temperature": 27.5,
  "humidity": 75.0,
  "nitrogen": 80.0,
  "phosphorus": 40.0,
  "potassium": 40.0
}
```

**Response:**
```json
{
  "crop": "Rice",
  "state": "Maharashtra",
  "season": "Kharif",
  "area_ha": 2.0,
  "predicted_yield_per_ha": 25.4,
  "yield_unit": "quintal/hectare",
  "estimated_total_production": 50.8,
  "production_unit": "quintal",
  "model": "NIHAL670/Crop-yield",
  "data_quality_note": "IMPORTANT: Nitrogen, Phosphorus, Potassium, Humidity, and Soil_Type were synthetically generated..."
}
```

`GET /api/v1/yield/metadata`

Returns lists of valid states, crops, seasons, and soil types recognised by the yield prediction model's categorical encoders.

---

## Machine Learning Models

SWAMITRA uses exactly two ML models:
1. **Crop Recommendation**: `Sheshank2609/crop-recommendation-system` (Random Forest Classifier)
2. **Crop Yield Prediction**: `NIHAL670/Crop-yield` (Random Forest Regressor)

See [docs/ml-models.md](docs/ml-models.md) for full technical documentation, feature schemas, training caveats, and serving lifecycle details.

## Docker

From the repository root, after creating a `.env` from `.env.example`:

```powershell
docker compose up --build
```

PostgreSQL is provided as the `db` service. The backend container reads `DATABASE_URL` pointing at that service. The `/health` endpoint does not require a live database.

## License

MIT. See [LICENSE](LICENSE).
