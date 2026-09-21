import logging
import httpx
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from cachetools import TTLCache, cached

from app.core.config import settings
from app.schemas.weather import WeatherResponse, CurrentWeather, DailyForecast, Location

logger = logging.getLogger(__name__)

# Cache weather responses for 30 minutes. Key is rounded lat/lon.
weather_cache = TTLCache(maxsize=1000, ttl=1800)

class WeatherProvider(ABC):
    @abstractmethod
    async def get_weather(self, lat: float, lon: float) -> WeatherResponse:
        """Fetch current weather and forecast for the given coordinates."""
        pass

class OpenMeteoProvider(WeatherProvider):
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    async def _fetch_data(self, lat: float, lon: float) -> dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()

    async def get_weather(self, lat: float, lon: float) -> WeatherResponse:
        data = await self._fetch_data(lat, lon)
        
        current_data = data.get("current", {})
        daily_data = data.get("daily", {})

        current_weather = CurrentWeather(
            temperature_c=current_data.get("temperature_2m", 0.0),
            humidity_percent=current_data.get("relative_humidity_2m", 0.0),
            rainfall_mm=current_data.get("precipitation", 0.0),
            wind_speed_kph=current_data.get("wind_speed_10m", 0.0),
            timestamp=datetime.now(timezone.utc)
        )

        forecast = []
        if daily_data and "time" in daily_data:
            for i in range(len(daily_data["time"])):
                forecast.append(
                    DailyForecast(
                        date=daily_data["time"][i],
                        max_temperature_c=daily_data["temperature_2m_max"][i],
                        min_temperature_c=daily_data["temperature_2m_min"][i],
                        rainfall_mm=daily_data["precipitation_sum"][i]
                    )
                )

        return WeatherResponse(
            location=Location(latitude=lat, longitude=lon),
            current=current_weather,
            forecast=forecast,
            provider="open-meteo"
        )


class WeatherService:
    def __init__(self, provider_name: str = "open-meteo", api_key: Optional[str] = None):
        self.provider_name = provider_name
        self.api_key = api_key
        self.provider = self._init_provider()

    def _init_provider(self) -> WeatherProvider:
        if self.provider_name.lower() == "open-meteo":
            return OpenMeteoProvider()
        else:
            logger.warning(f"Unknown provider '{self.provider_name}'. Falling back to Open-Meteo.")
            return OpenMeteoProvider()

    # We cache based on rounded lat/lon to avoid duplicate calls for nearby points
    # Since we can't easily memoize an async method with TTLCache decorators out-of-the-box in all python versions,
    # we can use a custom wrapper or just cache the result manually in a dictionary.
    
    async def get_weather(self, lat: float, lon: float) -> WeatherResponse:
        # Round to 2 decimal places (approx 1.1 km resolution) for caching
        cache_key = (round(lat, 2), round(lon, 2))
        
        if cache_key in weather_cache:
            logger.debug(f"Cache hit for weather at {cache_key}")
            return weather_cache[cache_key]
            
        logger.info(f"Fetching weather from {self.provider_name} for lat: {lat}, lon: {lon}")
        response = await self.provider.get_weather(lat, lon)
        
        weather_cache[cache_key] = response
        return response

def get_weather_service() -> WeatherService:
    return WeatherService(
        provider_name=settings.weather_provider,
        api_key=settings.weather_api_key
    )
