import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.schemas.crop import CropPredictionResponse, CropRecommendationItem
from app.services.crop_service import get_crop_service, CropService

client = TestClient(app)

@pytest.fixture
def valid_payload():
    return {
        "nitrogen": 90,
        "phosphorus": 42,
        "potassium": 43,
        "temperature": 25.0,
        "humidity": 80.0,
        "ph": 6.5,
        "rainfall": 200.0
    }

@pytest.fixture
def mock_crop_service():
    mock_service = MagicMock(spec=CropService)
    
    # Setup mock response
    mock_response = CropPredictionResponse(
        predicted_crop="apple",
        recommendations=[
            CropRecommendationItem(crop="apple", score=0.8),
            CropRecommendationItem(crop="banana", score=0.15)
        ],
        model="mocked-model",
        features_used={"nitrogen": 90} # simplified
    )
    
    mock_service.predict.return_value = mock_response
    
    # Override dependency
    app.dependency_overrides[get_crop_service] = lambda: mock_service
    yield mock_service
    # Clean up
    app.dependency_overrides.clear()


def test_predict_crop_success(valid_payload, mock_crop_service):
    response = client.post("/api/v1/crops/predict", json=valid_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_crop"] == "apple"
    assert len(data["recommendations"]) == 2
    assert data["recommendations"][0]["crop"] == "apple"
    assert data["model"] == "mocked-model"
    mock_crop_service.predict.assert_called_once()

def test_predict_crop_validation_error(mock_crop_service):
    # Invalid nitrogen (above 300)
    invalid_payload = {
        "nitrogen": 400,
        "phosphorus": 42,
        "potassium": 43,
        "temperature": 25.0,
        "humidity": 80.0,
        "ph": 6.5,
        "rainfall": 200.0
    }
    
    response = client.post("/api/v1/crops/predict", json=invalid_payload)
    assert response.status_code == 422
    assert "nitrogen" in response.text
    mock_crop_service.predict.assert_not_called()

def test_predict_crop_missing_field(mock_crop_service):
    # Missing rainfall
    invalid_payload = {
        "nitrogen": 90,
        "phosphorus": 42,
        "potassium": 43,
        "temperature": 25.0,
        "humidity": 80.0,
        "ph": 6.5
    }
    
    # Mock the service to raise the ValueError as the real service would
    mock_crop_service.predict.side_effect = ValueError("Temperature, humidity, and rainfall must be provided if latitude and longitude are not specified.")
    
    response = client.post("/api/v1/crops/predict", json=invalid_payload)
    assert response.status_code == 400
    assert "must be provided" in response.text
    mock_crop_service.predict.assert_called_once()

def test_predict_crop_service_unavailable(valid_payload, mock_crop_service):
    mock_crop_service.predict.side_effect = RuntimeError("Model not loaded")
    
    response = client.post("/api/v1/crops/predict", json=valid_payload)
    
    assert response.status_code == 503
    assert response.json()["detail"] == "Crop recommendation model is currently unavailable."

def test_predict_crop_internal_error(valid_payload, mock_crop_service):
    mock_crop_service.predict.side_effect = Exception("Some weird error")
    
    response = client.post("/api/v1/crops/predict", json=valid_payload)
    
    assert response.status_code == 500
    assert response.json()["detail"] == "An unexpected error occurred while processing the request."
