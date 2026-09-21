from unittest.mock import patch, MagicMock
import numpy as np
import pytest

from app.schemas.yield_schema import YieldPredictionRequest
from app.services.yield_service import YieldService, get_yield_service, FEATURE_ORDER
import app.services.yield_service as yield_service_module


@pytest.fixture
def mock_regressor():
    model = MagicMock()
    model.predict.return_value = np.array([24.5])
    return model


@pytest.fixture
def mock_encoders():
    le_state = MagicMock()
    le_state.classes_ = np.array(["Haryana", "Maharashtra", "Punjab", "Tamil Nadu"])
    le_state.transform.side_effect = lambda vals: [1 if vals[0].lower() == "maharashtra" else 0]

    le_crop = MagicMock()
    le_crop.classes_ = np.array(["Cotton", "Maize", "Rice", "Wheat"])
    le_crop.transform.side_effect = lambda vals: [2 if vals[0].lower() == "rice" else 0]

    le_season = MagicMock()
    le_season.classes_ = np.array(["Kharif", "Rabi", "Whole Year"])
    le_season.transform.side_effect = lambda vals: [0 if vals[0].lower() == "kharif" else 1]

    le_soil = MagicMock()
    le_soil.classes_ = np.array(["Alluvial", "Black", "Clay", "Laterite", "Red"])
    le_soil.transform.side_effect = lambda vals: [1 if vals[0].lower() == "black" else 0]

    return {
        "state": le_state,
        "crop": le_crop,
        "season": le_season,
        "soil": le_soil,
    }


@pytest.fixture
def sample_yield_request():
    return YieldPredictionRequest(
        state="Maharashtra",
        crop="Rice",
        season="Kharif",
        soil_type="Black",
        area=2.5,
        rainfall=1200.0,
        temperature=28.0,
        humidity=75.0,
        nitrogen=80.0,
        phosphorus=40.0,
        potassium=40.0,
    )


def test_load_model_success(mock_regressor, mock_encoders):
    service = YieldService()

    with patch("app.services.yield_service.hf_hub_download") as mock_download:
        with patch("app.services.yield_service.joblib.load") as mock_load:
            mock_download.side_effect = [
                "path_model", "path_le_state", "path_le_crop",
                "path_le_season", "path_le_soil"
            ]
            mock_load.side_effect = [
                mock_regressor,
                mock_encoders["state"],
                mock_encoders["crop"],
                mock_encoders["season"],
                mock_encoders["soil"],
            ]

            service.load_model()

            assert service.is_loaded is True
            assert service.model is not None
            assert service.le_state is not None
            assert service.le_crop is not None
            assert service.le_season is not None
            assert service.le_soil is not None
            assert mock_download.call_count == 5
            assert mock_load.call_count == 5


def test_load_model_failure():
    service = YieldService()

    with patch("app.services.yield_service.hf_hub_download") as mock_download:
        mock_download.side_effect = Exception("HF Hub connection error")

        service.load_model()

        assert service.is_loaded is False
        assert service.model is None
        assert service.le_state is None
        assert service.le_crop is None
        assert service.le_season is None
        assert service.le_soil is None


def test_predict_success(mock_regressor, mock_encoders, sample_yield_request):
    service = YieldService()
    service.model = mock_regressor
    service.le_state = mock_encoders["state"]
    service.le_crop = mock_encoders["crop"]
    service.le_season = mock_encoders["season"]
    service.le_soil = mock_encoders["soil"]

    response = service.predict(sample_yield_request)

    assert response.crop == "Rice"
    assert response.state == "Maharashtra"
    assert response.season == "Kharif"
    assert response.area_ha == 2.5
    assert response.predicted_yield_per_ha == 24.5
    assert response.estimated_total_production == round(24.5 * 2.5, 4)
    assert response.yield_unit == "quintal/hectare"
    assert response.production_unit == "quintal"
    assert response.model == "NIHAL670/Crop-yield"
    assert "synthetically generated" in response.data_quality_note


def test_predict_case_insensitive(mock_regressor, mock_encoders):
    service = YieldService()
    service.model = mock_regressor
    service.le_state = mock_encoders["state"]
    service.le_crop = mock_encoders["crop"]
    service.le_season = mock_encoders["season"]
    service.le_soil = mock_encoders["soil"]

    req = YieldPredictionRequest(
        state="maharashtra",
        crop="rice",
        season="kharif",
        soil_type="black",
        area=1.0,
        rainfall=1000.0,
        temperature=25.0,
        humidity=70.0,
        nitrogen=60.0,
        phosphorus=30.0,
        potassium=30.0,
    )

    response = service.predict(req)
    assert response.predicted_yield_per_ha == 24.5


def test_predict_unknown_state(mock_regressor, mock_encoders, sample_yield_request):
    service = YieldService()
    service.model = mock_regressor
    service.le_state = mock_encoders["state"]
    service.le_crop = mock_encoders["crop"]
    service.le_season = mock_encoders["season"]
    service.le_soil = mock_encoders["soil"]

    sample_yield_request.state = "Atlantis"

    with pytest.raises(ValueError) as exc_info:
        service.predict(sample_yield_request)
    assert "Unknown state" in str(exc_info.value)


def test_predict_unknown_crop(mock_regressor, mock_encoders, sample_yield_request):
    service = YieldService()
    service.model = mock_regressor
    service.le_state = mock_encoders["state"]
    service.le_crop = mock_encoders["crop"]
    service.le_season = mock_encoders["season"]
    service.le_soil = mock_encoders["soil"]

    sample_yield_request.crop = "Dragonfruit"

    with pytest.raises(ValueError) as exc_info:
        service.predict(sample_yield_request)
    assert "Unknown crop" in str(exc_info.value)


def test_predict_unknown_season(mock_regressor, mock_encoders, sample_yield_request):
    service = YieldService()
    service.model = mock_regressor
    service.le_state = mock_encoders["state"]
    service.le_crop = mock_encoders["crop"]
    service.le_season = mock_encoders["season"]
    service.le_soil = mock_encoders["soil"]

    sample_yield_request.season = "Monsoon_Autumn"

    with pytest.raises(ValueError) as exc_info:
        service.predict(sample_yield_request)
    assert "Unknown season" in str(exc_info.value)


def test_predict_unknown_soil_type(mock_regressor, mock_encoders, sample_yield_request):
    service = YieldService()
    service.model = mock_regressor
    service.le_state = mock_encoders["state"]
    service.le_crop = mock_encoders["crop"]
    service.le_season = mock_encoders["season"]
    service.le_soil = mock_encoders["soil"]

    sample_yield_request.soil_type = "VolcanicAsh"

    with pytest.raises(ValueError) as exc_info:
        service.predict(sample_yield_request)
    assert "Unknown soil_type" in str(exc_info.value)


def test_predict_model_not_loaded(sample_yield_request):
    service = YieldService()
    assert service.is_loaded is False

    with pytest.raises(RuntimeError) as exc_info:
        service.predict(sample_yield_request)
    assert "Yield prediction model is not loaded" in str(exc_info.value)


def test_predict_negative_clamping(mock_encoders, sample_yield_request):
    service = YieldService()
    neg_model = MagicMock()
    neg_model.predict.return_value = np.array([-12.5])
    service.model = neg_model
    service.le_state = mock_encoders["state"]
    service.le_crop = mock_encoders["crop"]
    service.le_season = mock_encoders["season"]
    service.le_soil = mock_encoders["soil"]

    response = service.predict(sample_yield_request)
    assert response.predicted_yield_per_ha == 0.0
    assert response.estimated_total_production == 0.0


def test_get_metadata(mock_encoders):
    service = YieldService()
    service.model = MagicMock()
    service.le_state = mock_encoders["state"]
    service.le_crop = mock_encoders["crop"]
    service.le_season = mock_encoders["season"]
    service.le_soil = mock_encoders["soil"]

    meta = service.get_metadata()
    assert meta.model_loaded is True
    assert "Maharashtra" in meta.valid_states
    assert "Rice" in meta.valid_crops
    assert "Kharif" in meta.valid_seasons
    assert "Black" in meta.valid_soil_types
    assert meta.feature_order == FEATURE_ORDER


def test_get_metadata_when_not_loaded():
    service = YieldService()
    meta = service.get_metadata()
    assert meta.model_loaded is False
    assert meta.valid_states == []
    assert meta.valid_crops == []


def test_get_yield_service_singleton():
    yield_service_module._yield_service_instance = None

    with patch.object(YieldService, "load_model") as mock_load:
        s1 = get_yield_service()
        s2 = get_yield_service()
        assert s1 is s2
        mock_load.assert_called_once()
