import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.schemas.weather import WeatherResponse
from app.services.weather_service import WeatherService, get_weather_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/weather",
    tags=["weather"],
    responses={404: {"description": "Not found"}},
)

@router.get("/current", response_model=WeatherResponse)
async def get_current_weather(
    lat: float = Query(..., description="Latitude", ge=-90, le=90),
    lon: float = Query(..., description="Longitude", ge=-180, le=180),
    weather_service: WeatherService = Depends(get_weather_service)
):
    """
    Retrieves current weather and short-term forecast for the given location.
    """
    try:
        response = await weather_service.get_weather(lat, lon)
        return response
    except httpx.HTTPError as e:
        logger.error(f"Weather provider error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve weather data from the provider."
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching weather: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching weather data."
        )

@router.get("/forecast", response_model=WeatherResponse)
async def get_forecast_weather(
    lat: float = Query(..., description="Latitude", ge=-90, le=90),
    lon: float = Query(..., description="Longitude", ge=-180, le=180),
    weather_service: WeatherService = Depends(get_weather_service)
):
    """
    Retrieves the weather forecast for the given location.
    Currently, the underlying provider fetches both current and forecast data together.
    """
    # The get_weather method returns both current and forecast.
    return await get_current_weather(lat, lon, weather_service)
