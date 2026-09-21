# Machine Learning Models in SWAMITRA

SWAMITRA intentionally uses **two ML models** from Hugging Face for machine learning inference:
1. **Crop Recommendation Model**: `Sheshank2609/crop-recommendation-system`
2. **Crop Yield Prediction Model**: `NIHAL670/Crop-yield`

All agronomic reasoning, farm constraints (water availability, growing duration, soil pH compatibility, climate thresholds), and risk penalties are managed deterministically by the rule-based `SuitabilityService`.

---

## 1. Crop Recommendation Model

- **Repository**: [`Sheshank2609/crop-recommendation-system`](https://huggingface.co/Sheshank2609/crop-recommendation-system)
- **Model Type**: Random Forest Classifier (`scikit-learn`)
- **Artifacts**: `model.pkl` (classifier), `label_encoder.pkl` (22 classes)
- **Service**: `app.services.crop_service.CropService`
- **Endpoints**:
  - `POST /api/v1/crops/predict` (raw ML scores, top 5)
  - `POST /api/v1/crops/recommend` (farm-aware suitability scoring engine)

### Input Features
The model expects 7 environmental and soil features:
1. `nitrogen` (N) — soil nitrogen content in mg/kg
2. `phosphorus` (P) — soil phosphorus content in mg/kg
3. `potassium` (K) — soil potassium content in mg/kg
4. `temperature` — average temperature in °C
5. `humidity` — relative humidity in %
6. `ph` — soil pH (3.5 – 9.5)
7. `rainfall` — seasonal rainfall in mm

### Target Classes (22 Crops)
`apple`, `banana`, `blackgram`, `chickpea`, `coconut`, `coffee`, `cotton`, `grapes`, `jute`, `kidneybeans`, `lentil`, `maize`, `mango`, `mothbeans`, `mungbean`, `muskmelon`, `orange`, `papaya`, `pigeonpeas`, `pomegranate`, `rice`, `watermelon`.

### Strengths & Limitations
- **Strengths**: Fast inference; models multi-dimensional soil-nutrient and climate affinities well.
- **Limitations**: The raw model has no concept of farm water infrastructure, actual growing days available before frost or seasonal deadlines, farm size, or farmer resource constraints.
- **Remedy in SWAMITRA**: Raw ML probabilities are fed into `SuitabilityService`, which validates candidate crops against `data/crops/crops.json` and applies deterministic penalties for water deficits, duration mismatches, and pH/climate stress.

---

## 2. Crop Yield Prediction Model

- **Repository**: [`NIHAL670/Crop-yield`](https://huggingface.co/NIHAL670/Crop-yield)
- **Model Type**: Random Forest Regressor (`scikit-learn`)
- **Artifacts**:
  - `model.pkl` — trained regressor
  - `le_state.pkl` — LabelEncoder for State
  - `le_crop.pkl` — LabelEncoder for Crop
  - `le_season.pkl` — LabelEncoder for Season
  - `le_soil.pkl` — LabelEncoder for Soil_Type
- **Training Data**: `india_crop_yield_20000_rows.csv` (India-wide historical agricultural data)
- **Service**: `app.services.yield_service.YieldService`
- **Endpoints**:
  - `POST /api/v1/yield/predict` (standalone yield prediction)
  - `GET /api/v1/yield/metadata` (lists valid states, crops, seasons, soil types)
  - `POST /api/v1/crops/recommend` (optional yield enrichment via `include_yield=true`)

### Feature Schema & Order
Inference requires exactly 11 features in the following order:

| Index | Feature | Type | Unit / Description |
|-------|---------|------|--------------------|
| 0 | `State` | Categorical | Encoded via `le_state.pkl` |
| 1 | `Crop` | Categorical | Encoded via `le_crop.pkl` |
| 2 | `Season` | Categorical | Encoded via `le_season.pkl` (e.g. `Kharif`, `Rabi`, `Whole Year`) |
| 3 | `Soil_Type` | Categorical | Encoded via `le_soil.pkl` (`Alluvial`, `Black`, `Clay`, `Laterite`, `Red`) |
| 4 | `Area` | Numeric | Cultivated area in hectares |
| 5 | `Rainfall` | Numeric | Seasonal rainfall in mm |
| 6 | `Temperature` | Numeric | Mean temperature in °C |
| 7 | `Humidity` | Numeric | Relative humidity in % |
| 8 | `Nitrogen` | Numeric | Soil nitrogen (mg/kg) |
| 9 | `Phosphorus` | Numeric | Soil phosphorus (mg/kg) |
| 10 | `Potassium` | Numeric | Soil potassium (mg/kg) |

### Output
- `predicted_yield_per_ha`: Model prediction in **quintal/hectare** ($\text{Yield} = \frac{\text{Production}}{\text{Area}}$)
- `estimated_total_production`: $\text{predicted\_yield\_per\_ha} \times \text{area\_ha}$ in **quintal**

### Critical Limitation & Data Quality Transparency
> [!WARNING]
> Inspection of the upstream training script (`train_model.py`) reveals that **Nitrogen, Phosphorus, Potassium, Humidity, and Soil_Type were synthetically generated** using `np.random` during dataset preprocessing if not present in the source CSV.
>
> Consequently:
> - These 5 features carry **random noise** and have negligible predictive weight.
> - The model's real predictive signal comes from **State, Crop, Season, Area, and Rainfall**.
> - Every API response includes a prominent `data_quality_note` disclosing this limitation to farmers and application developers.
> - Yield estimates must be treated as indicative references, not guaranteed harvest commitments.

---

## 3. Serving & Lifecycle Architecture

1. **Lazy Loading & Preloading**: Both models are implemented as thread-safe singletons (`get_crop_service()` and `get_yield_service()`). They are preloaded at startup via FastAPI's `lifespan` handler to eliminate first-request latency.
2. **Local Caching**: Weights and encoders are fetched via Hugging Face Hub (`hf_hub_download`), which maintains a persistent local cache.
3. **Graceful Fallbacks**: If model loading fails, endpoints return a `503 Service Unavailable` with descriptive errors rather than crashing the process.
4. **Input Validation**: Categorical variables are validated against the actual label encoders (`classes_`) using case-insensitive matching; invalid categories return a clear `400 Bad Request` enumerating valid options.
