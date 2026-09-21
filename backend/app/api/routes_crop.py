from fastapi import APIRouter, Depends, HTTPException, status
import logging

from app.schemas.crop import CropPredictionRequest, CropPredictionResponse
from app.schemas.suitability import RecommendationRequest, RecommendationResponse
from app.services.crop_service import CropService, get_crop_service
from app.services.suitability_service import SuitabilityService, get_suitability_service
from app.services.weather_service import get_weather_service
from app.services.yield_service import YieldService, get_yield_service
from app.schemas.yield_schema import YieldPredictionRequest

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
    Returns raw ML scores (top 5). Use /recommend for farm-constraint-aware scoring.
    """
    try:
        response = await crop_service.predict(request)
        return response
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=503, detail="Crop recommendation model is currently unavailable.")
    except Exception as e:
        logger.error(f"Unexpected error during prediction: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the request.")


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend_crops(
    request: RecommendationRequest,
    suitability_service: SuitabilityService = Depends(get_suitability_service),
    yield_service: YieldService = Depends(get_yield_service),
):
    """
    Farm-aware crop recommendation.

    Runs the ML model for all crops, then applies a deterministic suitability
    scoring engine that accounts for:
    - Available water (mm/season)
    - Available growing days
    - Soil pH compatibility
    - Climate compatibility (temperature, rainfall)

    Returns top 3 recommendations with ML scores, suitability scores,
    limiting factors, and plain-language explanations.

    **Optional yield enrichment**: Set `include_yield=true` and provide
    `yield_state`, `yield_season`, and `yield_soil_type` to additionally
    attach yield predictions (quintal/hectare) to each of the top 3 crops.
    Existing responses are unaffected when `include_yield` is omitted or false.
    """
    temperature = request.temperature
    humidity = request.humidity
    rainfall = request.rainfall
    weather_auto_filled = False

    # Auto-fill climate from weather service if location provided and values missing
    if None in (temperature, humidity, rainfall):
        if request.latitude is not None and request.longitude is not None:
            try:
                weather_service = get_weather_service()
                weather = await weather_service.get_weather(request.latitude, request.longitude)
                temperature = temperature if temperature is not None else weather.current.temperature_c
                humidity    = humidity    if humidity    is not None else weather.current.humidity_percent
                rainfall    = rainfall    if rainfall    is not None else weather.current.rainfall_mm
                weather_auto_filled = True
                logger.info(
                    f"Auto-filled weather for /recommend: "
                    f"temp={temperature}, humidity={humidity}, rainfall={rainfall}"
                )
            except Exception as e:
                logger.error(f"Weather fetch failed: {e}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Could not retrieve weather data for the provided location: {e}",
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Temperature, humidity, and rainfall must be provided explicitly "
                    "if latitude and longitude are not specified."
                ),
            )

    # Validate yield enrichment parameters upfront if requested
    if request.include_yield:
        if not (request.yield_state and request.yield_season and request.yield_soil_type):
            raise HTTPException(
                status_code=400,
                detail=(
                    "include_yield=true requires yield_state, yield_season, "
                    "and yield_soil_type to be provided."
                ),
            )

    try:
        response = await suitability_service.recommend(
            nitrogen=request.nitrogen,
            phosphorus=request.phosphorus,
            potassium=request.potassium,
            ph=request.ph,
            temperature=temperature,
            humidity=humidity,
            rainfall=rainfall,
            constraints=request.farm_constraints,
            weather_auto_filled=weather_auto_filled,
        )
    except RuntimeError as e:
        logger.error(f"Suitability scoring failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Crop recommendation model is currently unavailable.",
        )
    except Exception as e:
        logger.error(f"Unexpected error during recommendation: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the recommendation.",
        )

    # Optional yield enrichment — only if explicitly requested
    if request.include_yield:
        if not yield_service.is_loaded:
            logger.warning("Yield model unavailable; skipping yield enrichment.")
        else:
            area = request.farm_constraints.farm_area_ha or 1.0
            for rec in response.top_recommendations:
                try:
                    yield_req = YieldPredictionRequest(
                        state=request.yield_state,
                        crop=rec.crop,
                        season=request.yield_season,
                        soil_type=request.yield_soil_type,
                        area=area,
                        rainfall=rainfall or 0.0,
                        temperature=temperature or 25.0,
                        humidity=humidity or 60.0,
                        nitrogen=request.nitrogen,
                        phosphorus=request.phosphorus,
                        potassium=request.potassium,
                    )
                    yield_result = yield_service.predict(yield_req)
                    rec.predicted_yield_per_ha = yield_result.predicted_yield_per_ha
                    rec.estimated_total_production = yield_result.estimated_total_production
                    rec.yield_unit = yield_result.yield_unit
                except ValueError as e:
                    # Unknown crop/state/season in yield model — attach None, log warning
                    logger.warning(
                        f"Yield prediction skipped for '{rec.crop}': {e}"
                    )
                except Exception as e:
                    logger.error(f"Unexpected error in yield enrichment for '{rec.crop}': {e}")

    return response
