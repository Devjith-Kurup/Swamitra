from fastapi import APIRouter, Depends, HTTPException
import logging

from app.schemas.yield_schema import (
    YieldModelMetadata,
    YieldPredictionRequest,
    YieldPredictionResponse,
)
from app.services.yield_service import YieldService, get_yield_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/yield",
    tags=["yield"],
    responses={404: {"description": "Not found"}},
)


@router.post("/predict", response_model=YieldPredictionResponse)
def predict_yield(
    request: YieldPredictionRequest,
    yield_service: YieldService = Depends(get_yield_service),
):
    """
    Predicts crop yield for the given inputs using the NIHAL670/Crop-yield
    Random Forest Regressor model.

    **Important data quality note** (returned in every response):
    Nitrogen, Phosphorus, Potassium, Humidity, and Soil_Type were synthetically
    generated during model training and carry no real predictive weight.
    The model's primary predictive signals are State, Crop, Season, Area, and Rainfall.

    Returns:
    - `predicted_yield_per_ha` — model output in **quintal/hectare**
    - `estimated_total_production` — yield_per_ha × area in **quintal**
    - `data_quality_note` — limitation disclosure

    For valid categorical values, call `GET /api/v1/yield/metadata`.
    """
    try:
        return yield_service.predict(request)
    except ValueError as e:
        logger.warning(f"Invalid yield prediction input: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Yield model unavailable: {e}")
        raise HTTPException(
            status_code=503,
            detail="Yield prediction model is currently unavailable.",
        )
    except Exception as e:
        logger.error(f"Unexpected error during yield prediction: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during yield prediction.",
        )


@router.get("/metadata", response_model=YieldModelMetadata)
def get_yield_metadata(
    yield_service: YieldService = Depends(get_yield_service),
):
    """
    Returns the valid categorical values for the yield prediction model
    (states, crops, seasons, soil types), along with model metadata and
    the data quality disclaimer.

    Use this endpoint to discover which values are accepted by `POST /predict`.
    """
    return yield_service.get_metadata()
