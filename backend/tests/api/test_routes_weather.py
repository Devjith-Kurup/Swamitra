import pytest
import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.services.weather_service import get_weather_service

client = TestClient(app)

@pytest.fixture
def mock_open_meteo_response():
    return {
        "current": {
            "temperature_2m": 25.5,
            "relative_humidity_2m": 60.0,
            "precipitation": 0.0,
            "wind_speed_10m": 12.0
        },
        "daily": {
            "time": ["2023-10-25"],
            "temperature_2m_max": [30.0],
            "temperature_2m_min": [20.0],
            "precipitation_sum": [0.0]
        }
    }

@patch("httpx.AsyncClient.get")
def test_get_current_weather_success(mock_get, mock_open_meteo_response):
    # Setup mock
    mock_response = MagicMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = mock_open_meteo_response
    mock_get.return_value = mock_response

    # Clear cache before test
    from app.services.weather_service import weather_cache
    weather_cache.clear()

    response = client.get("/api/v1/weather/current?lat=18.52&lon=73.85")
    
    assert response.status_code == 200
    data = response.json()
    assert data["location"]["latitude"] == 18.52
    assert data["location"]["longitude"] == 73.85
    assert data["current"]["temperature_c"] == 25.5
    assert data["provider"] == "open-meteo"
    assert len(data["forecast"]) == 1
    assert data["forecast"][0]["max_temperature_c"] == 30.0

@patch("httpx.AsyncClient.get")
def test_get_current_weather_api_failure(mock_get):
    mock_fail = httpx.HTTPStatusError("Error", request=MagicMock(), response=MagicMock())
    mock_get.side_effect = mock_fail
    
    # Clear cache before test
    from app.services.weather_service import weather_cache
    weather_cache.clear()

    response = client.get("/api/v1/weather/current?lat=18.52&lon=73.85")
    
    # Due to tenacity retries, this takes a moment. Then it raises the error.
    assert response.status_code == 502
    assert response.json()["detail"] == "Failed to retrieve weather data from the provider."

def test_get_current_weather_validation_error():
    # Missing parameters
    response = client.get("/api/v1/weather/current")
    assert response.status_code == 422
    
    # Out of bounds lat
    response = client.get("/api/v1/weather/current?lat=100&lon=73.85")
    assert response.status_code == 422
