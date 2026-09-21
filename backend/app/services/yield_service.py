"""
YieldService — Crop Yield Prediction using NIHAL670/Crop-yield.

Architecture follows the same singleton/lazy-load pattern as CropService.

Model: NIHAL670/Crop-yield
  - model.pkl         : Random Forest Regressor (sklearn)
  - le_state.pkl      : LabelEncoder for State
  - le_crop.pkl       : LabelEncoder for Crop
  - le_season.pkl     : LabelEncoder for Season
  - le_soil.pkl       : LabelEncoder for Soil_Type

Feature order (must match training exactly):
  [State, Crop, Season, Soil_Type, Area, Rainfall, Temperature,
   Humidity, Nitrogen, Phosphorus, Potassium]

Output:
  Yield = Production / Area  →  quintal / hectare

IMPORTANT — training data caveat:
  Nitrogen, Phosphorus, Potassium, Humidity, and Soil_Type were
  synthetically generated during training (np.random). They are
  accepted inputs but carry no real predictive weight in the model.
  See docs/ml-models.md for full details.
"""

import logging
import numpy as np
from typing import Dict, List, Optional

import joblib
from huggingface_hub import hf_hub_download

from app.schemas.yield_schema import (
    YieldModelMetadata,
    YieldPredictionRequest,
    YieldPredictionResponse,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL_REPO_ID = "NIHAL670/Crop-yield"

# Exact feature order as used in train_model.py
FEATURE_ORDER = [
    "State",
    "Crop",
    "Season",
    "Soil_Type",
    "Area",
    "Rainfall",
    "Temperature",
    "Humidity",
    "Nitrogen",
    "Phosphorus",
    "Potassium",
]

OUTPUT_UNIT = "quintal/hectare"

DATA_QUALITY_NOTE = (
    "IMPORTANT: Nitrogen, Phosphorus, Potassium, Humidity, and Soil_Type "
    "were synthetically generated (random values) during model training. "
    "These features carry no meaningful predictive weight. "
    "The model's primary signals are State, Crop, Season, Area, and Rainfall. "
    "This is a third-party model trained on India-wide historical data; "
    "predictions should not be treated as guaranteed agricultural outcomes."
)


# ---------------------------------------------------------------------------
# YieldService
# ---------------------------------------------------------------------------

class YieldService:
    """
    Wraps the NIHAL670/Crop-yield Random Forest Regressor.

    - Downloads model files from Hugging Face Hub on first load.
    - Caches locally (Hugging Face Hub handles cache).
    - Validates categorical inputs against the real label encoder classes.
    - Never silently substitutes missing values.
    """

    def __init__(self) -> None:
        self.model_id: str = MODEL_REPO_ID
        self.model = None
        self.le_state = None
        self.le_crop = None
        self.le_season = None
        self.le_soil = None

    def load_model(self) -> None:
        """
        Downloads and loads model.pkl + 4 label encoders from Hugging Face Hub.
        Called once at application startup. Logs clearly on failure.
        """
        try:
            logger.info(f"Loading yield model: {self.model_id}")
            model_path = hf_hub_download(repo_id=self.model_id, filename="model.pkl")
            le_state_path = hf_hub_download(repo_id=self.model_id, filename="le_state.pkl")
            le_crop_path = hf_hub_download(repo_id=self.model_id, filename="le_crop.pkl")
            le_season_path = hf_hub_download(repo_id=self.model_id, filename="le_season.pkl")
            le_soil_path = hf_hub_download(repo_id=self.model_id, filename="le_soil.pkl")

            self.model = joblib.load(model_path)
            self.le_state = joblib.load(le_state_path)
            self.le_crop = joblib.load(le_crop_path)
            self.le_season = joblib.load(le_season_path)
            self.le_soil = joblib.load(le_soil_path)

            logger.info(
                f"Yield model loaded successfully. "
                f"States: {len(self.le_state.classes_)}, "
                f"Crops: {len(self.le_crop.classes_)}, "
                f"Seasons: {len(self.le_season.classes_)}, "
                f"Soil types: {len(self.le_soil.classes_)}"
            )
        except Exception as e:
            logger.error(f"Failed to load yield model: {e}")
            self.model = None
            self.le_state = None
            self.le_crop = None
            self.le_season = None
            self.le_soil = None

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def _validate_categorical(self, field_name: str, value: str, encoder) -> int:
        """
        Validates a categorical value against the label encoder's known classes.
        Raises ValueError with a clear message listing valid options if unknown.
        """
        classes: List[str] = list(encoder.classes_)
        # Case-insensitive lookup
        match = next((c for c in classes if c.lower() == value.lower()), None)
        if match is None:
            raise ValueError(
                f"Unknown {field_name}: '{value}'. "
                f"Valid values are: {sorted(classes)}"
            )
        return int(encoder.transform([match])[0])

    def predict(self, request: YieldPredictionRequest) -> YieldPredictionResponse:
        """
        Validates inputs, encodes categoricals, runs inference.

        Raises:
            RuntimeError: if model is not loaded.
            ValueError: if a categorical field value is not known to the encoder.
        """
        if not self.is_loaded:
            raise RuntimeError(
                "Yield prediction model is not loaded or failed to initialise."
            )

        # Validate and encode all categorical fields
        state_enc = self._validate_categorical("state", request.state, self.le_state)
        crop_enc = self._validate_categorical("crop", request.crop, self.le_crop)
        season_enc = self._validate_categorical("season", request.season, self.le_season)
        soil_enc = self._validate_categorical("soil_type", request.soil_type, self.le_soil)

        # Build feature array in exact training order
        features = np.array([[
            state_enc,
            crop_enc,
            season_enc,
            soil_enc,
            request.area,
            request.rainfall,
            request.temperature,
            request.humidity,
            request.nitrogen,
            request.phosphorus,
            request.potassium,
        ]])

        logger.debug(
            f"Yield prediction input: state={request.state}({state_enc}), "
            f"crop={request.crop}({crop_enc}), season={request.season}({season_enc}), "
            f"soil={request.soil_type}({soil_enc}), area={request.area}"
        )

        raw_prediction = self.model.predict(features)
        yield_per_ha = float(raw_prediction[0])

        # Guard against physically impossible negative predictions
        yield_per_ha = max(0.0, yield_per_ha)
        estimated_production = round(yield_per_ha * request.area, 4)

        logger.info(
            f"Yield predicted: {yield_per_ha:.4f} quintal/ha "
            f"for {request.crop} in {request.state}"
        )

        return YieldPredictionResponse(
            crop=request.crop,
            state=request.state,
            season=request.season,
            area_ha=request.area,
            predicted_yield_per_ha=round(yield_per_ha, 4),
            estimated_total_production=estimated_production,
        )

    def get_metadata(self) -> YieldModelMetadata:
        """Returns model metadata and valid categorical values for API discovery."""
        return YieldModelMetadata(
            model=self.model_id,
            model_loaded=self.is_loaded,
            valid_states=sorted(self.le_state.classes_.tolist()) if self.le_state else [],
            valid_crops=sorted(self.le_crop.classes_.tolist()) if self.le_crop else [],
            valid_seasons=sorted(self.le_season.classes_.tolist()) if self.le_season else [],
            valid_soil_types=sorted(self.le_soil.classes_.tolist()) if self.le_soil else [],
            feature_order=FEATURE_ORDER,
            output_unit=OUTPUT_UNIT,
            data_quality_note=DATA_QUALITY_NOTE,
        )


# ---------------------------------------------------------------------------
# Dependency injection — singleton
# ---------------------------------------------------------------------------

_yield_service_instance: Optional[YieldService] = None


def get_yield_service() -> YieldService:
    """Returns the singleton YieldService, loading the model on first call."""
    global _yield_service_instance
    if _yield_service_instance is None:
        _yield_service_instance = YieldService()
        _yield_service_instance.load_model()
    return _yield_service_instance
