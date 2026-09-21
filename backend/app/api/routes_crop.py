from fastapi import APIRouter, Depends, HTTPException, status
import logging

from app.schemas.crop import CropPredictionRequest, CropPredictionResponse
from app.services.crop_service import CropService, get_crop_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/crops",
    tags=["crops"],
    responses={404: {"description": "Not found"}},
)

@router.post("/predict", response_model=CropPredictionResponse)
async def predict_crop(
    request: CropPredictionRequest,
    crop_service: CropService = Depends(get_crop_service)
):
    """
    Predicts the most suitable crop based on soil and climate conditions.
    """
    try:
        response = await crop_service.predict(request)
        return response
    except RuntimeError as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Crop recommendation model is currently unavailable."
        )
    except Exception as e:
        logger.error(f"Unexpected error during prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the request."
        )
