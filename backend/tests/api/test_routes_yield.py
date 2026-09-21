import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.schemas.yield_schema import (
    YieldModelMetadata,
    YieldPredictionResponse,
)
from app.services.yield_service import YieldService, get_yield_service

client = TestClient(app)


@pytest.fixture
def valid_yield_payload():
    return {
        "state": "Maharashtra",
        "crop": "Rice",
        "season": "Kharif",
        "soil_type": "Black",
        "area": 2.0,
        "rainfall": 1100.0,
        "temperature": 27.5,
        "humidity": 75.0,
        "nitrogen": 80.0,
        "phosphorus": 40.0,
        "potassium": 40.0,
    }


@pytest.fixture
def mock_yield_service():
    mock_service = MagicMock(spec=YieldService)

    mock_response = YieldPredictionResponse(
        crop="Rice",
        state="Maharashtra",
        season="Kharif",
        area_ha=2.0,
        predicted_yield_per_ha=25.4,
        yield_unit="quintal/hectare",
        estimated_total_production=50.8,
        production_unit="quintal",
        model="NIHAL670/Crop-yield",
    )

    mock_service.predict.return_value = mock_response

    mock_metadata = YieldModelMetadata(
        model="NIHAL670/Crop-yield",
        model_loaded=True,
        valid_states=["Haryana", "Maharashtra", "Punjab"],
        valid_crops=["Cotton", "Rice", "Wheat"],
        valid_seasons=["Kharif", "Rabi"],
        valid_soil_types=["Alluvial", "Black", "Clay"],
        feature_order=["State", "Crop", "Season", "Soil_Type", "Area", "Rainfall", "Temperature", "Humidity", "Nitrogen", "Phosphorus", "Potassium"],
        output_unit="quintal/hectare",
        data_quality_note="Data quality note disclaimer",
    )
    mock_service.get_metadata.return_value = mock_metadata

    app.dependency_overrides[get_yield_service] = lambda: mock_service
    yield mock_service
    app.dependency_overrides.clear()


def test_predict_yield_success(valid_yield_payload, mock_yield_service):
    response = client.post("/api/v1/yield/predict", json=valid_yield_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["crop"] == "Rice"
    assert data["state"] == "Maharashtra"
    assert data["predicted_yield_per_ha"] == 25.4
    assert data["estimated_total_production"] == 50.8
    assert data["yield_unit"] == "quintal/hectare"
    assert data["production_unit"] == "quintal"
    assert "data_quality_note" in data
    mock_yield_service.predict.assert_called_once()


def test_predict_yield_invalid_numeric_field(mock_yield_service):
    # Area <= 0 is invalid
    payload = {
        "state": "Maharashtra",
        "crop": "Rice",
        "season": "Kharif",
        "soil_type": "Black",
        "area": -1.0,
        "rainfall": 1100.0,
        "temperature": 27.5,
        "humidity": 75.0,
        "nitrogen": 80.0,
        "phosphorus": 40.0,
        "potassium": 40.0,
    }
    response = client.post("/api/v1/yield/predict", json=payload)
    assert response.status_code == 422
    mock_yield_service.predict.assert_not_called()


def test_predict_yield_unknown_categorical(valid_yield_payload, mock_yield_service):
    mock_yield_service.predict.side_effect = ValueError(
        "Unknown state: 'Atlantis'. Valid values are: ['Haryana', 'Maharashtra']"
    )

    valid_yield_payload["state"] = "Atlantis"
    response = client.post("/api/v1/yield/predict", json=valid_yield_payload)

    assert response.status_code == 400
    assert "Unknown state" in response.json()["detail"]


def test_predict_yield_service_unavailable(valid_yield_payload, mock_yield_service):
    mock_yield_service.predict.side_effect = RuntimeError("Yield prediction model is not loaded.")

    response = client.post("/api/v1/yield/predict", json=valid_yield_payload)

    assert response.status_code == 503
    assert "Yield prediction model is currently unavailable" in response.json()["detail"]


def test_predict_yield_internal_error(valid_yield_payload, mock_yield_service):
    mock_yield_service.predict.side_effect = Exception("Unexpected computation error")

    response = client.post("/api/v1/yield/predict", json=valid_yield_payload)

    assert response.status_code == 500
    assert "An unexpected error occurred" in response.json()["detail"]


def test_get_yield_metadata_success(mock_yield_service):
    response = client.get("/api/v1/yield/metadata")

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "NIHAL670/Crop-yield"
    assert data["model_loaded"] is True
    assert "Maharashtra" in data["valid_states"]
    assert "Rice" in data["valid_crops"]
    assert data["output_unit"] == "quintal/hectare"


def test_recommend_crops_with_yield_enrichment(mock_yield_service):
    # Test POST /api/v1/crops/recommend with include_yield=True
    from app.services.suitability_service import SuitabilityService, get_suitability_service
    from app.schemas.suitability import RecommendationResponse, CropSuitabilityResult, RecommendationMetadata

    mock_suitability = MagicMock(spec=SuitabilityService)

    mock_res = RecommendationResponse(
        top_recommendations=[
            CropSuitabilityResult(
                crop="rice",
                ml_score=0.9,
                suitability_score=0.85,
                limiting_factors=[],
                explanation="Highly suitable",
            )
        ],
        all_candidates=[],
        metadata=RecommendationMetadata(
            weather_auto_filled=False,
            crop_db_version="0.1.0-prototype",
        ),
    )

    async def mock_recommend(**kwargs):
        return mock_res

    mock_suitability.recommend = mock_recommend
    app.dependency_overrides[get_suitability_service] = lambda: mock_suitability
    app.dependency_overrides[get_yield_service] = lambda: mock_yield_service

    try:
        payload = {
            "nitrogen": 90,
            "phosphorus": 42,
            "potassium": 43,
            "ph": 6.5,
            "temperature": 25.0,
            "humidity": 80.0,
            "rainfall": 200.0,
            "farm_constraints": {
                "water_availability_mm": 1000.0,
                "growing_days_available": 120,
                "farm_area_ha": 2.5,
            },
            "include_yield": True,
            "yield_state": "Maharashtra",
            "yield_season": "Kharif",
            "yield_soil_type": "Black",
        }

        response = client.post("/api/v1/crops/recommend", json=payload)
        assert response.status_code == 200
        data = response.json()
        top_rec = data["top_recommendations"][0]
        assert top_rec["predicted_yield_per_ha"] == 25.4
        assert top_rec["estimated_total_production"] == 50.8
        assert top_rec["yield_unit"] == "quintal/hectare"
    finally:
        app.dependency_overrides.pop(get_suitability_service, None)


def test_recommend_crops_with_yield_missing_params(mock_yield_service):
    payload = {
        "nitrogen": 90,
        "phosphorus": 42,
        "potassium": 43,
        "ph": 6.5,
        "temperature": 25.0,
        "humidity": 80.0,
        "rainfall": 200.0,
        "farm_constraints": {
            "water_availability_mm": 1000.0,
            "growing_days_available": 120,
        },
        "include_yield": True,
        # Missing yield_state, yield_season, yield_soil_type
    }

    response = client.post("/api/v1/crops/recommend", json=payload)
    assert response.status_code == 400
    assert "requires yield_state, yield_season, and yield_soil_type" in response.json()["detail"]
