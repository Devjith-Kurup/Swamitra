import pytest
import httpx
from unittest.mock import patch, AsyncMock
from app.services.weather_service import WeatherService, OpenMeteoProvider, weather_cache

@pytest.fixture
def mock_open_meteo_response():
    return {
        "current": {
            "temperature_2m": 25.5,
            "relative_humidity_2m": 60,
            "precipitation": 1.2,
            "wind_speed_10m": 15.0
        },
        "daily": {
            "time": ["2023-10-25", "2023-10-26"],
            "temperature_2m_max": [30.0, 31.0],
            "temperature_2m_min": [20.0, 21.0],
            "precipitation_sum": [5.0, 0.0]
        }
    }

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_weather_success(mock_get, mock_open_meteo_response):
    weather_cache.clear()
    
    mock_response = AsyncMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = mock_open_meteo_response
    mock_get.return_value = mock_response

    service = WeatherService(provider_name="open-meteo")
    weather = await service.get_weather(18.52, 73.85)

    assert weather.provider == "open-meteo"
    assert weather.location.latitude == 18.52
    assert weather.current.temperature_c == 25.5
    assert weather.current.rainfall_mm == 1.2
    assert len(weather.forecast) == 2
    assert weather.forecast[0].max_temperature_c == 30.0

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_weather_caching(mock_get, mock_open_meteo_response):
    weather_cache.clear()
    
    mock_response = AsyncMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = mock_open_meteo_response
    mock_get.return_value = mock_response

    service = WeatherService(provider_name="open-meteo")
    
    # First call
    await service.get_weather(18.52, 73.85)
    
    # Second call (should hit cache)
    await service.get_weather(18.524, 73.851)  # slightly different, but rounds to same 2 decimal places

    # Mock should only be called once because of cache
    assert mock_get.call_count == 1

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_weather_retry_logic(mock_get, mock_open_meteo_response):
    weather_cache.clear()
    
    # First call fails, second call succeeds
    mock_fail = httpx.HTTPStatusError("Error", request=AsyncMock(), response=AsyncMock())
    
    mock_success = AsyncMock()
    mock_success.raise_for_status = lambda: None
    mock_success.json.return_value = mock_open_meteo_response
    
    mock_get.side_effect = [mock_fail, mock_success]

    service = WeatherService(provider_name="open-meteo")
    
    weather = await service.get_weather(19.0, 72.0)
    
    assert weather.current.temperature_c == 25.5
    assert mock_get.call_count == 2
