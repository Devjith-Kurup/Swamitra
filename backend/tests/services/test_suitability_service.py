"""
Unit tests for SuitabilityScorer and CropKnowledgeDB.

All tests use in-memory mock data — no file I/O, no ML model.
The CropKnowledgeDB is constructed directly from a dict to keep tests hermetic.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.schemas.suitability import FarmConstraints
from app.services.suitability_service import (
    CropKnowledgeDB,
    SuitabilityScorer,
    SuitabilityService,
    WATER_CRITICAL_FACTOR,
    WATER_WARNING_FACTOR,
    DURATION_CRITICAL_FACTOR,
    DURATION_WARNING_FACTOR,
    PH_HARD_FACTOR,
    PH_SOFT_FACTOR,
    CLIMATE_OUT_FACTOR,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

RICE_META = {
    "crop": "rice",
    "duration_days": {"min": 90, "max": 180},
    "water_requirement": "very_high",
    "water_mm_season": 1200,
    "ideal_ph_min": 5.5,
    "ideal_ph_max": 7.0,
    "ph_min_hard": 4.0,
    "ph_max_hard": 8.5,
    "temperature_min": 20,
    "temperature_max": 38,
    "rainfall_min": 1000,
    "rainfall_max": 3000,
    "drought_tolerance": "low",
    "heat_tolerance": "medium",
    "irrigation_type": "both",
    "_data_quality": "prototype",
}

CHICKPEA_META = {
    "crop": "chickpea",
    "duration_days": {"min": 90, "max": 120},
    "water_requirement": "low",
    "water_mm_season": 300,
    "ideal_ph_min": 6.0,
    "ideal_ph_max": 8.0,
    "ph_min_hard": 5.5,
    "ph_max_hard": 9.0,
    "temperature_min": 10,
    "temperature_max": 30,
    "rainfall_min": 200,
    "rainfall_max": 700,
    "drought_tolerance": "high",
    "heat_tolerance": "low",
    "irrigation_type": "rainfed",
    "_data_quality": "prototype",
}

APPLE_META = {
    "crop": "apple",
    "duration_days": {"min": 150, "max": 180},
    "water_requirement": "medium",
    "water_mm_season": 700,
    "ideal_ph_min": 6.0,
    "ideal_ph_max": 7.0,
    "ph_min_hard": 5.0,
    "ph_max_hard": 8.0,
    "temperature_min": 5,
    "temperature_max": 25,
    "rainfall_min": 600,
    "rainfall_max": 1200,
    "drought_tolerance": "low",
    "heat_tolerance": "low",
    "irrigation_type": "irrigated",
    "_data_quality": "prototype",
}


@pytest.fixture
def scorer():
    return SuitabilityScorer()


def make_constraints(
    water_mm=1200,
    growing_days=120,
    irrigation=False,
    area_ha=1.0,
):
    return FarmConstraints(
        water_availability_mm=water_mm,
        growing_days_available=growing_days,
        farm_area_ha=area_ha,
        irrigation_available=irrigation,
    )


# ---------------------------------------------------------------------------
# CropKnowledgeDB tests
# ---------------------------------------------------------------------------

def test_crop_knowledge_db_lookup_known(tmp_path):
    """DB correctly indexes and returns a known crop by name."""
    import json
    db_file = tmp_path / "crops.json"
    db_file.write_text(json.dumps({
        "_schema_version": "1.0",
        "crops": [RICE_META, CHICKPEA_META]
    }))
    db = CropKnowledgeDB(db_path=str(db_file))

    result = db.get("rice")
    assert result is not None
    assert result["water_mm_season"] == 1200

    result2 = db.get("CHICKPEA")  # case-insensitive
    assert result2 is not None
    assert result2["crop"] == "chickpea"


def test_crop_knowledge_db_lookup_unknown(tmp_path):
    """DB returns None for a crop not in the database."""
    import json
    db_file = tmp_path / "crops.json"
    db_file.write_text(json.dumps({"_schema_version": "1.0", "crops": [RICE_META]}))
    db = CropKnowledgeDB(db_path=str(db_file))

    assert db.get("durian") is None


def test_crop_knowledge_db_schema_version(tmp_path):
    """DB correctly reads and exposes the schema version."""
    import json
    db_file = tmp_path / "crops.json"
    db_file.write_text(json.dumps({"_schema_version": "2.5", "crops": []}))
    db = CropKnowledgeDB(db_path=str(db_file))
    assert db.schema_version == "2.5"


# ---------------------------------------------------------------------------
# Water factor tests
# ---------------------------------------------------------------------------

def test_water_compatible_conditions(scorer):
    """When available water meets or exceeds crop need, factor = 1.0 and no limiting factor."""
    constraints = make_constraints(water_mm=1500)  # rice needs 1200
    factor, lf = scorer._water_factor(constraints, RICE_META)
    assert factor == 1.0
    assert lf is None


def test_water_warning_level(scorer):
    """Water at 82% of need (between warning ratio 70% and 100%) → warning LF."""
    # 82% of 1200 = 984 mm  → above WATER_WARNING_RATIO (0.70) but below 1.0
    constraints = make_constraints(water_mm=984)
    factor, lf = scorer._water_factor(constraints, RICE_META)
    assert factor == WATER_WARNING_FACTOR
    assert lf is not None
    assert lf.severity == "warning"
    assert lf.factor == "water"


def test_water_critical_level(scorer):
    """Water at 30% of need → critical LF and very low factor."""
    # 30% of 1200 = 360 mm
    constraints = make_constraints(water_mm=360)
    factor, lf = scorer._water_factor(constraints, RICE_META)
    assert factor == WATER_CRITICAL_FACTOR
    assert lf is not None
    assert lf.severity == "critical"


def test_water_extreme_shortage(scorer):
    """Near-zero water for a very-high water crop → critical."""
    constraints = make_constraints(water_mm=50)
    factor, lf = scorer._water_factor(constraints, RICE_META)
    assert factor == WATER_CRITICAL_FACTOR
    assert lf.severity == "critical"


def test_water_low_requirement_crop_passes_easily(scorer):
    """Chickpea (300 mm need) passes with 350 mm available."""
    constraints = make_constraints(water_mm=350)
    factor, lf = scorer._water_factor(constraints, CHICKPEA_META)
    assert factor == 1.0
    assert lf is None


# ---------------------------------------------------------------------------
# Duration factor tests
# ---------------------------------------------------------------------------

def test_duration_compatible(scorer):
    """Available days exceeds crop min → factor 1.0."""
    constraints = make_constraints(growing_days=150)  # rice min=90
    factor, lf = scorer._duration_factor(constraints, RICE_META)
    assert factor == 1.0
    assert lf is None


def test_duration_warning(scorer):
    """93% of min duration (above DURATION_WARNING_RATIO=90%) → warning factor."""
    # 93% of 150 (apple min) = 139 days
    constraints = make_constraints(growing_days=139)
    factor, lf = scorer._duration_factor(constraints, APPLE_META)
    assert factor == DURATION_WARNING_FACTOR
    assert lf is not None
    assert lf.severity == "warning"


def test_duration_critical_short(scorer):
    """30 days for a 150-day crop → critical penalty."""
    constraints = make_constraints(growing_days=30)
    factor, lf = scorer._duration_factor(constraints, APPLE_META)
    assert factor == DURATION_CRITICAL_FACTOR
    assert lf is not None
    assert lf.severity == "critical"
    assert "30" in lf.detail
    assert "150" in lf.detail


# ---------------------------------------------------------------------------
# pH factor tests
# ---------------------------------------------------------------------------

def test_ph_ideal_range(scorer):
    """pH within ideal band → factor 1.0, no LF."""
    factor, lf = scorer._ph_factor(6.5, RICE_META)  # ideal 5.5–7.0
    assert factor == 1.0
    assert lf is None


def test_ph_soft_mismatch_above_ideal(scorer):
    """pH 7.5 for rice (ideal max 7.0, hard max 8.5) → soft penalty."""
    factor, lf = scorer._ph_factor(7.5, RICE_META)
    assert factor == PH_SOFT_FACTOR
    assert lf is not None
    assert lf.severity == "warning"
    assert lf.factor == "ph"


def test_ph_hard_incompatible_too_acidic(scorer):
    """pH 3.5 for rice (hard min 4.0) → zero factor, critical LF."""
    factor, lf = scorer._ph_factor(3.5, RICE_META)
    assert factor == PH_HARD_FACTOR
    assert lf is not None
    assert lf.severity == "critical"
    assert lf.factor == "ph"


def test_ph_hard_incompatible_too_alkaline(scorer):
    """pH 9.0 for rice (hard max 8.5) → zero factor, critical LF."""
    factor, lf = scorer._ph_factor(9.0, RICE_META)
    assert factor == PH_HARD_FACTOR
    assert lf.severity == "critical"


def test_ph_within_hard_below_ideal(scorer):
    """pH 5.0 for rice (ideal min 5.5, hard min 4.0) → soft penalty."""
    factor, lf = scorer._ph_factor(5.0, RICE_META)
    assert factor == PH_SOFT_FACTOR
    assert lf.severity == "warning"


# ---------------------------------------------------------------------------
# Climate factor tests
# ---------------------------------------------------------------------------

def test_climate_compatible(scorer):
    """Temperature and rainfall within crop range → factor 1.0."""
    factor, lf = scorer._climate_factor(25.0, 1500.0, RICE_META)
    assert factor == 1.0
    assert lf is None


def test_climate_temperature_too_low(scorer):
    """Temperature below minimum → climate penalty."""
    factor, lf = scorer._climate_factor(10.0, 1500.0, RICE_META)  # rice min = 20
    assert factor == CLIMATE_OUT_FACTOR
    assert lf is not None
    assert lf.factor == "climate"
    assert "temperature" in lf.detail


def test_climate_temperature_too_high(scorer):
    """Temperature above maximum → climate penalty."""
    factor, lf = scorer._climate_factor(45.0, 1500.0, APPLE_META)  # apple max = 25
    assert factor == CLIMATE_OUT_FACTOR
    assert lf.factor == "climate"


def test_climate_rainfall_too_low(scorer):
    """Rainfall below crop minimum → climate penalty."""
    factor, lf = scorer._climate_factor(25.0, 200.0, RICE_META)  # rice min = 1000
    assert factor == CLIMATE_OUT_FACTOR
    assert lf is not None


def test_climate_unknown_skips_penalty(scorer):
    """None temperature and rainfall → no penalty applied."""
    factor, lf = scorer._climate_factor(None, None, RICE_META)
    assert factor == 1.0
    assert lf is None


# ---------------------------------------------------------------------------
# Full score() integration tests
# ---------------------------------------------------------------------------

def test_score_fully_compatible_conditions(scorer):
    """All factors 1.0 → suitability_score ≈ ml_score."""
    constraints = make_constraints(water_mm=2000, growing_days=150)
    result = scorer.score(
        crop_name="rice",
        ml_score=0.80,
        constraints=constraints,
        temperature=28.0,
        rainfall=1500.0,
        ph=6.2,
        crop_meta=RICE_META,
    )
    assert result.ml_score == pytest.approx(0.80, abs=1e-4)
    assert result.suitability_score == pytest.approx(0.80, abs=1e-4)
    assert len(result.limiting_factors) == 0


def test_score_low_water_reduces_suitability(scorer):
    """Low water availability produces a suitability score well below ML score."""
    constraints = make_constraints(water_mm=200, growing_days=150)  # 200/1200 = 16%
    result = scorer.score(
        crop_name="rice",
        ml_score=0.70,
        constraints=constraints,
        temperature=28.0,
        rainfall=1500.0,
        ph=6.2,
        crop_meta=RICE_META,
    )
    assert result.suitability_score < result.ml_score * 0.3
    assert any(lf.factor == "water" for lf in result.limiting_factors)
    assert any(lf.severity == "critical" for lf in result.limiting_factors)


def test_score_short_growing_duration_reduces_suitability(scorer):
    """30 growing days for a 150-day crop produces near-zero suitability."""
    constraints = make_constraints(water_mm=2000, growing_days=30)
    result = scorer.score(
        crop_name="apple",
        ml_score=0.60,
        constraints=constraints,
        temperature=15.0,
        rainfall=800.0,
        ph=6.5,
        crop_meta=APPLE_META,
    )
    assert result.suitability_score < 0.15
    assert any(lf.factor == "duration" for lf in result.limiting_factors)
    assert any(lf.severity == "critical" for lf in result.limiting_factors)


def test_score_incompatible_ph_zeroes_suitability(scorer):
    """pH outside hard limits produces near-zero suitability (hard incompatibility)."""
    constraints = make_constraints(water_mm=2000, growing_days=150)
    result = scorer.score(
        crop_name="rice",
        ml_score=0.75,
        constraints=constraints,
        temperature=28.0,
        rainfall=1500.0,
        ph=3.5,  # Below rice hard min of 4.0
        crop_meta=RICE_META,
    )
    # ph_factor=0.0 collapses entire score to 0.0
    assert result.suitability_score == pytest.approx(0.0, abs=1e-6)
    assert any(lf.factor == "ph" and lf.severity == "critical" for lf in result.limiting_factors)


def test_score_missing_crop_metadata(scorer):
    """Missing metadata passes ml_score through unchanged with a warning LF."""
    constraints = make_constraints()
    result = scorer.score(
        crop_name="durian",
        ml_score=0.42,
        constraints=constraints,
        temperature=28.0,
        rainfall=1500.0,
        ph=6.5,
        crop_meta=None,  # not in DB
    )
    assert result.suitability_score == pytest.approx(0.42, abs=1e-4)
    assert result.ml_score == pytest.approx(0.42, abs=1e-4)
    assert any(lf.factor == "missing_metadata" for lf in result.limiting_factors)


# ---------------------------------------------------------------------------
# Determinism test
# ---------------------------------------------------------------------------

def test_score_is_deterministic(scorer):
    """Same inputs always produce the exact same output."""
    constraints = make_constraints(water_mm=800, growing_days=100)
    kwargs = dict(
        crop_name="rice",
        ml_score=0.55,
        constraints=constraints,
        temperature=26.0,
        rainfall=900.0,
        ph=6.8,
        crop_meta=RICE_META,
    )
    result_a = scorer.score(**kwargs)
    result_b = scorer.score(**kwargs)
    assert result_a.suitability_score == result_b.suitability_score
    assert result_a.limiting_factors == result_b.limiting_factors


# ---------------------------------------------------------------------------
# SuitabilityService integration test (mocked ML model)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_suitability_service_returns_top_3(tmp_path):
    """SuitabilityService returns exactly 3 top recommendations sorted by suitability."""
    import json

    # Build a minimal crop DB with 3 crops
    db_file = tmp_path / "crops.json"
    db_file.write_text(json.dumps({
        "_schema_version": "1.0",
        "crops": [RICE_META, CHICKPEA_META, APPLE_META],
    }))
    db = CropKnowledgeDB(db_path=str(db_file))

    # Mock the crop service
    mock_crop_service = MagicMock()
    mock_crop_service.get_all_probabilities.return_value = {
        "rice":     0.60,
        "chickpea": 0.25,
        "apple":    0.15,
    }

    service = SuitabilityService(crop_service=mock_crop_service, db=db)

    constraints = make_constraints(water_mm=2000, growing_days=150)
    result = await service.recommend(
        nitrogen=90,
        phosphorus=42,
        potassium=43,
        ph=6.5,
        temperature=25.0,
        humidity=70.0,
        rainfall=1200.0,
        constraints=constraints,
    )

    assert len(result.top_recommendations) == 3
    assert len(result.all_candidates) == 3

    # Top candidate must have highest suitability score
    scores = [r.suitability_score for r in result.top_recommendations]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_suitability_service_low_water_reorders_ranking(tmp_path):
    """Low water should demote rice (high water need) and promote chickpea (low need)."""
    import json

    db_file = tmp_path / "crops.json"
    db_file.write_text(json.dumps({
        "_schema_version": "1.0",
        "crops": [RICE_META, CHICKPEA_META],
    }))
    db = CropKnowledgeDB(db_path=str(db_file))

    mock_crop_service = MagicMock()
    # Rice has higher ML score, but water is critically low for it
    mock_crop_service.get_all_probabilities.return_value = {
        "rice":     0.70,
        "chickpea": 0.30,
    }

    service = SuitabilityService(crop_service=mock_crop_service, db=db)

    # 500 mm available: critical for rice (needs 1200mm, ratio=41%), fine for chickpea (needs 300mm, ratio=166%)
    constraints = make_constraints(water_mm=500, growing_days=120)
    result = await service.recommend(
        nitrogen=90, phosphorus=42, potassium=43,
        ph=6.5, temperature=25.0, humidity=70.0, rainfall=500.0,
        constraints=constraints,
    )

    crops_by_rank = [r.crop for r in result.top_recommendations]
    # Chickpea should outrank rice despite lower ML score
    assert crops_by_rank.index("chickpea") < crops_by_rank.index("rice")
