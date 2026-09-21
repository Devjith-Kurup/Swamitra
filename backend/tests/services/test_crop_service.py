from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from app.schemas.crop import CropPredictionRequest
from app.services.crop_service import CropService, get_crop_service
from app.schemas.weather import WeatherResponse, CurrentWeather, Location
import app.services.crop_service as crop_service_module

@pytest.fixture
def mock_model():
    model = MagicMock()
    # Mock probabilities for 22 crops (model outputs 22 classes)
    mock_proba = [[0.0] * 22]
    mock_proba[0][0] = 0.8  # High probability for the first crop
    mock_proba[0][1] = 0.15 # Second crop
    mock_proba[0][2] = 0.05 # Third crop
    model.predict_proba.return_value = mock_proba
    return model

@pytest.fixture
def mock_label_encoder():
    encoder = MagicMock()
    # Mock 22 classes
    encoder.classes_ = [
        'apple', 'banana', 'blackgram', 'chickpea', 'coconut', 'coffee', 
        'cotton', 'grapes', 'jute', 'kidneybeans', 'lentil', 'maize', 
        'mango', 'mothbeans', 'mungbean', 'muskmelon', 'orange', 'papaya', 
        'pigeonpeas', 'pomegranate', 'rice', 'watermelon'
    ]
    return encoder

@pytest.fixture
def sample_request():
    return CropPredictionRequest(
        nitrogen=90,
        phosphorus=42,
        potassium=43,
        temperature=25.0,
        humidity=80.0,
        ph=6.5,
        rainfall=200.0
    )

def test_load_model_success(mock_model, mock_label_encoder):
    service = CropService()
    
    with patch('app.services.crop_service.hf_hub_download') as mock_download:
        with patch('app.services.crop_service.joblib.load') as mock_load:
            mock_download.side_effect = ['path_to_model', 'path_to_encoder']
            mock_load.side_effect = [mock_model, mock_label_encoder]
            
            service.load_model()
            
            assert service.model is not None
            assert service.label_encoder is not None
            assert mock_download.call_count == 2
            assert mock_load.call_count == 2

def test_load_model_failure():
    service = CropService()
    
    with patch('app.services.crop_service.hf_hub_download') as mock_download:
        mock_download.side_effect = Exception("Download failed")
        
        service.load_model()
        
        assert service.model is None
        assert service.label_encoder is None

@pytest.mark.asyncio
async def test_predict_success(mock_model, mock_label_encoder, sample_request):
    service = CropService()
    service.model = mock_model
    service.label_encoder = mock_label_encoder
    
    response = await service.predict(sample_request)
    
    assert response.predicted_crop == 'apple'
    assert len(response.recommendations) == 5
    assert response.recommendations[0].crop == 'apple'
    assert response.recommendations[0].score == 0.8
    assert response.recommendations[1].crop == 'banana'
    assert response.recommendations[1].score == 0.15
    assert response.model == "Sheshank2609/crop-recommendation-system"
    assert response.features_used == sample_request.model_dump()

@pytest.mark.asyncio
@patch("app.services.crop_service.get_weather_service")
async def test_predict_auto_fill_weather(mock_get_weather_service, mock_model, mock_label_encoder):
    service = CropService()
    service.model = mock_model
    service.label_encoder = mock_label_encoder
    
    # Request missing weather, but has lat/lon
    request = CropPredictionRequest(
        nitrogen=90, phosphorus=42, potassium=43, ph=6.5,
        latitude=18.52, longitude=73.85
    )
    
    mock_weather_service = AsyncMock()
    mock_weather = WeatherResponse(
        location=Location(latitude=18.52, longitude=73.85),
        current=CurrentWeather(temperature_c=25.0, humidity_percent=80.0, rainfall_mm=200.0, wind_speed_kph=10.0, timestamp="2023-10-25T00:00:00Z"),
        provider="mock"
    )
    mock_weather_service.get_weather.return_value = mock_weather
    mock_get_weather_service.return_value = mock_weather_service
    
    response = await service.predict(request)
    
    assert response.predicted_crop == 'apple'
    mock_weather_service.get_weather.assert_called_once_with(18.52, 73.85)

@pytest.mark.asyncio
async def test_predict_missing_weather_and_location(mock_model, mock_label_encoder):
    service = CropService()
    service.model = mock_model
    service.label_encoder = mock_label_encoder
    
    request = CropPredictionRequest(
        nitrogen=90, phosphorus=42, potassium=43, ph=6.5
    )
    
    with pytest.raises(ValueError):
        await service.predict(request)

@pytest.mark.asyncio
async def test_predict_model_not_loaded(sample_request):
    service = CropService()
    # model and label_encoder are None
    
    with pytest.raises(RuntimeError):
        await service.predict(sample_request)

def test_get_crop_service_singleton():
    # Reset singleton if already set by other tests or main app
    crop_service_module._crop_service_instance = None
    
    with patch.object(CropService, 'load_model') as mock_load:
        service1 = get_crop_service()
        service2 = get_crop_service()
        
        assert service1 is service2
        mock_load.assert_called_once()
