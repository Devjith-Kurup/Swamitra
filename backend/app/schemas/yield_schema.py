"""
Pydantic schemas for the Crop Yield Prediction endpoint.

Model: NIHAL670/Crop-yield (Random Forest Regressor)
Source: https://huggingface.co/NIHAL670/Crop-yield

IMPORTANT — Training data quality note (documented from train_model.py):
The features Nitrogen, Phosphorus, Potassium, Humidity, and Soil_Type were
synthetically generated with np.random.randint / np.random.choice during training
if they were absent from the source CSV. These features therefore carry no meaningful
predictive signal in the trained model. Real predictive weight lies primarily in
State, Crop, Season, Area, and Rainfall. This is documented in every API response.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Valid categorical values
# These are informational — the actual validation is done against the live
# label encoder classes loaded from the HF model at runtime.
# ---------------------------------------------------------------------------

_KNOWN_SOIL_TYPES = ["Alluvial", "Black", "Clay", "Laterite", "Red"]


class YieldPredictionRequest(BaseModel):
    """
    Input features for crop yield prediction.

    Feature order matches the exact training schema from NIHAL670/Crop-yield:
    State, Crop, Season, Soil_Type, Area, Rainfall, Temperature,
    Humidity, Nitrogen, Phosphorus, Potassium

    Units:
      - area: hectares
      - rainfall: mm (seasonal total)
      - temperature: °C (mean)
      - humidity: % relative humidity
      - nitrogen / phosphorus / potassium: mg/kg soil

    NOTE: Nitrogen, Phosphorus, Potassium, Humidity, and Soil_Type were
    synthetically generated during model training and carry no real predictive
    signal. They are accepted for API completeness but will not meaningfully
    influence the prediction.
    """

    # Categorical features — validated against label encoder classes at runtime
    state: str = Field(
        ...,
        description=(
            "Indian state name as recognised by the model's label encoder. "
            "Run GET /api/v1/yield/metadata for the full list of valid values."
        ),
    )
    crop: str = Field(
        ...,
        description=(
            "Crop name as recognised by the model's label encoder. "
            "Run GET /api/v1/yield/metadata for the full list of valid values."
        ),
    )
    season: str = Field(
        ...,
        description=(
            "Growing season as recognised by the model's label encoder "
            "(e.g. 'Kharif', 'Rabi', 'Whole Year'). "
            "Run GET /api/v1/yield/metadata for the full list of valid values."
        ),
    )
    soil_type: str = Field(
        ...,
        description=(
            f"Soil type. Known values: {_KNOWN_SOIL_TYPES}. "
            "NOTE: Soil_Type was synthetically generated during model training "
            "and does not carry real predictive weight."
        ),
    )

    # Numeric features
    area: float = Field(
        ...,
        description="Cultivated area in hectares.",
        gt=0,
        le=1_000_000,
    )
    rainfall: float = Field(
        ...,
        description="Seasonal rainfall in mm.",
        ge=0,
        le=5000,
    )
    temperature: float = Field(
        ...,
        description="Mean temperature during growing season (°C).",
        ge=-10,
        le=60,
    )
    humidity: float = Field(
        ...,
        description=(
            "Relative humidity (%). "
            "NOTE: Humidity was synthetically generated during model training "
            "and does not carry real predictive weight."
        ),
        ge=0,
        le=100,
    )
    nitrogen: float = Field(
        ...,
        description=(
            "Soil nitrogen content (mg/kg). "
            "NOTE: Nitrogen was synthetically generated during model training "
            "and does not carry real predictive weight."
        ),
        ge=0,
        le=500,
    )
    phosphorus: float = Field(
        ...,
        description=(
            "Soil phosphorus content (mg/kg). "
            "NOTE: Phosphorus was synthetically generated during model training "
            "and does not carry real predictive weight."
        ),
        ge=0,
        le=300,
    )
    potassium: float = Field(
        ...,
        description=(
            "Soil potassium content (mg/kg). "
            "NOTE: Potassium was synthetically generated during model training "
            "and does not carry real predictive weight."
        ),
        ge=0,
        le=300,
    )


class YieldPredictionResponse(BaseModel):
    """Output of POST /api/v1/yield/predict."""

    crop: str = Field(..., description="Crop name as provided in the request.")
    state: str = Field(..., description="State as provided in the request.")
    season: str = Field(..., description="Season as provided in the request.")
    area_ha: float = Field(..., description="Area in hectares as provided in the request.")

    predicted_yield_per_ha: float = Field(
        ...,
        description="Model-predicted crop yield per hectare.",
    )
    yield_unit: str = Field(
        default="quintal/hectare",
        description="Unit of the predicted yield value.",
    )
    estimated_total_production: float = Field(
        ...,
        description=(
            "Estimated total production = predicted_yield_per_ha × area_ha. "
            "Unit: quintal."
        ),
    )
    production_unit: str = Field(
        default="quintal",
        description="Unit of the estimated total production.",
    )
    model: str = Field(
        default="NIHAL670/Crop-yield",
        description="Hugging Face model identifier used for this prediction.",
    )
    data_quality_note: str = Field(
        default=(
            "IMPORTANT: Nitrogen, Phosphorus, Potassium, Humidity, and Soil_Type "
            "were synthetically generated (random values) during model training. "
            "These features carry no meaningful predictive weight. "
            "The model's primary signals are State, Crop, Season, Area, and Rainfall. "
            "This is a third-party model trained on India-wide historical data; "
            "predictions should not be treated as guaranteed agricultural outcomes."
        ),
        description="Data quality and limitation notice for this model.",
    )


class YieldModelMetadata(BaseModel):
    """Response for GET /api/v1/yield/metadata — lists valid categorical values."""

    model: str
    model_loaded: bool
    valid_states: list
    valid_crops: list
    valid_seasons: list
    valid_soil_types: list
    feature_order: list
    output_unit: str
    data_quality_note: str
