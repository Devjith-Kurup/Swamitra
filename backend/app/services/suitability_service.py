"""
Suitability Service — deterministic, explainable crop re-ranking.

Architecture:
  CropKnowledgeDB  →  loads data/crops/crops.json at startup
  SuitabilityScorer →  stateless; computes per-factor multipliers
  SuitabilityService → orchestrates ML + scoring + sorting

Scoring model (multiplicative):
  suitability_score = ml_score
                      × water_factor        (0.0–1.0)
                      × duration_factor     (0.0–1.0)
                      × ph_factor           (0.0–1.0)
                      × climate_factor      (0.0–1.0)

All thresholds are named module-level constants for auditability.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Tuple

from app.schemas.suitability import (
    CropSuitabilityResult,
    FarmConstraints,
    LimitingFactor,
    RecommendationMetadata,
    RecommendationResponse,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring constants — change here, not buried in logic
# ---------------------------------------------------------------------------

# Water factor thresholds
WATER_CRITICAL_RATIO = 0.40   # Below 40% of crop need → critical penalty
WATER_WARNING_RATIO  = 0.70   # Below 70% → warning penalty
WATER_CRITICAL_FACTOR = 0.10
WATER_WARNING_FACTOR  = 0.50

# Duration factor thresholds
DURATION_CRITICAL_RATIO = 0.70  # < 70% of crop min duration → critical
DURATION_WARNING_RATIO  = 0.90  # < 90% of crop min duration → warning
DURATION_CRITICAL_FACTOR = 0.10
DURATION_WARNING_FACTOR  = 0.60

# pH factor — hard incompatibility uses ph_min_hard / ph_max_hard from DB
PH_HARD_FACTOR  = 0.0          # Outside hard limits → zero
PH_IDEAL_FACTOR = 1.0          # Within ideal band
PH_SOFT_FACTOR  = 0.75         # Outside ideal, but within hard limits

# Climate factor — based on temperature being within [temperature_min, temperature_max]
CLIMATE_OUT_FACTOR = 0.70      # Temperature or rainfall out of viable range
CLIMATE_OK_FACTOR  = 1.0

# Path to knowledge base (relative to repo root, resolved at load time)
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
CROP_DB_PATH = os.path.join(_REPO_ROOT, "data", "crops", "crops.json")


# ---------------------------------------------------------------------------
# Crop Knowledge Database
# ---------------------------------------------------------------------------

class CropKnowledgeDB:
    """
    Loads and indexes crops.json.  Provides O(1) lookup by crop name.
    The underlying JSON is PROTOTYPE data — see _data_quality field.
    """

    def __init__(self, db_path: str = CROP_DB_PATH):
        self._db_path = db_path
        self._index: Dict[str, dict] = {}
        self._schema_version = "unknown"
        self._load()

    def _load(self) -> None:
        try:
            with open(self._db_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._schema_version = raw.get("_schema_version", "unknown")
            for record in raw.get("crops", []):
                name = record.get("crop", "").lower().strip()
                if name:
                    self._index[name] = record
            logger.info(
                f"CropKnowledgeDB loaded {len(self._index)} crops "
                f"(schema v{self._schema_version}) from {self._db_path}"
            )
        except FileNotFoundError:
            logger.error(f"Crop knowledge DB not found at: {self._db_path}")
        except Exception as e:
            logger.error(f"Failed to load crop knowledge DB: {e}")

    def get(self, crop_name: str) -> Optional[dict]:
        """Returns the crop record or None if not found."""
        return self._index.get(crop_name.lower().strip())

    @property
    def schema_version(self) -> str:
        return self._schema_version


# ---------------------------------------------------------------------------
# Suitability Scorer — pure / stateless
# ---------------------------------------------------------------------------

class SuitabilityScorer:
    """
    Computes a suitability score for one (crop, ml_score, constraints) triple.
    All methods are deterministic and side-effect free.
    """

    def score(
        self,
        crop_name: str,
        ml_score: float,
        constraints: FarmConstraints,
        temperature: Optional[float],
        rainfall: Optional[float],
        ph: float,
        crop_meta: Optional[dict],
    ) -> CropSuitabilityResult:
        """
        Entry point. Returns a fully populated CropSuitabilityResult.
        If crop_meta is None, suitability_score passes through as ml_score.
        """
        if crop_meta is None:
            return CropSuitabilityResult(
                crop=crop_name,
                ml_score=ml_score,
                suitability_score=round(ml_score, 6),
                limiting_factors=[
                    LimitingFactor(
                        factor="missing_metadata",
                        severity="warning",
                        detail=f"No agronomic profile found for '{crop_name}' in the knowledge base. "
                               "Suitability score equals raw ML score — farm constraints not applied.",
                    )
                ],
                explanation=(
                    f"ML model gives {ml_score:.1%} probability for {crop_name}. "
                    "No farm-constraint adjustment applied (missing crop metadata)."
                ),
            )

        limiting_factors: List[LimitingFactor] = []

        w_factor, w_lf = self._water_factor(constraints, crop_meta)
        d_factor, d_lf = self._duration_factor(constraints, crop_meta)
        p_factor, p_lf = self._ph_factor(ph, crop_meta)
        c_factor, c_lf = self._climate_factor(temperature, rainfall, crop_meta)

        if w_lf:
            limiting_factors.append(w_lf)
        if d_lf:
            limiting_factors.append(d_lf)
        if p_lf:
            limiting_factors.append(p_lf)
        if c_lf:
            limiting_factors.append(c_lf)

        composite = ml_score * w_factor * d_factor * p_factor * c_factor
        suitability_score = round(max(0.0, min(1.0, composite)), 6)

        explanation = self._build_explanation(
            crop_name, ml_score, suitability_score, limiting_factors,
            w_factor, d_factor, p_factor, c_factor
        )

        return CropSuitabilityResult(
            crop=crop_name,
            ml_score=round(ml_score, 6),
            suitability_score=suitability_score,
            limiting_factors=limiting_factors,
            explanation=explanation,
        )

    # ------------------------------------------------------------------
    # Factor calculators
    # ------------------------------------------------------------------

    def _water_factor(
        self, constraints: FarmConstraints, crop_meta: dict
    ) -> Tuple[float, Optional[LimitingFactor]]:
        """
        Compares available water to crop's seasonal water requirement.
        Returns (factor, optional LimitingFactor).
        """
        water_needed = crop_meta.get("water_mm_season")
        if not water_needed:
            return 1.0, None

        available = constraints.water_availability_mm
        # If irrigation is available, allow a small boost (10%) to model access to supplemental water
        if constraints.irrigation_available and crop_meta.get("irrigation_type") in ("irrigated", "both"):
            available = available * 1.10

        ratio = available / water_needed if water_needed > 0 else 1.0

        if ratio >= 1.0:
            return CLIMATE_OK_FACTOR, None
        elif ratio >= WATER_WARNING_RATIO:
            lf = LimitingFactor(
                factor="water",
                severity="warning",
                detail=(
                    f"Water available ({constraints.water_availability_mm:.0f} mm) is "
                    f"{ratio:.0%} of the crop's typical seasonal need ({water_needed} mm). "
                    "Mild deficit expected."
                ),
            )
            return WATER_WARNING_FACTOR, lf
        elif ratio >= WATER_CRITICAL_RATIO:
            lf = LimitingFactor(
                factor="water",
                severity="critical",
                detail=(
                    f"Water available ({constraints.water_availability_mm:.0f} mm) is only "
                    f"{ratio:.0%} of the crop's typical need ({water_needed} mm). "
                    "Severe water deficit — significant yield loss or crop failure likely."
                ),
            )
            return WATER_CRITICAL_FACTOR, lf
        else:
            lf = LimitingFactor(
                factor="water",
                severity="critical",
                detail=(
                    f"Water available ({constraints.water_availability_mm:.0f} mm) is critically "
                    f"insufficient for {crop_meta['crop']} (needs ~{water_needed} mm). "
                    "Crop failure very likely."
                ),
            )
            return WATER_CRITICAL_FACTOR, lf

    def _duration_factor(
        self, constraints: FarmConstraints, crop_meta: dict
    ) -> Tuple[float, Optional[LimitingFactor]]:
        """
        Compares available growing days to the crop's minimum duration.
        """
        duration_range = crop_meta.get("duration_days", {})
        min_duration = duration_range.get("min") if isinstance(duration_range, dict) else None
        if not min_duration:
            return 1.0, None

        available = constraints.growing_days_available
        ratio = available / min_duration

        if ratio >= 1.0:
            return 1.0, None
        elif ratio >= DURATION_WARNING_RATIO:
            lf = LimitingFactor(
                factor="duration",
                severity="warning",
                detail=(
                    f"Growing window ({available} days) is slightly shorter than the crop's "
                    f"minimum typical duration ({min_duration} days). "
                    "Early-maturing varieties may still work."
                ),
            )
            return DURATION_WARNING_FACTOR, lf
        else:
            lf = LimitingFactor(
                factor="duration",
                severity="critical",
                detail=(
                    f"Growing window ({available} days) is too short for {crop_meta['crop']} "
                    f"(minimum ~{min_duration} days). Crop cannot reach maturity in this window."
                ),
            )
            return DURATION_CRITICAL_FACTOR, lf

    def _ph_factor(
        self, ph: float, crop_meta: dict
    ) -> Tuple[float, Optional[LimitingFactor]]:
        """
        Checks soil pH against the crop's ideal and hard limits.
        Hard incompatibility (outside ph_min_hard/ph_max_hard) → factor = 0.
        Outside ideal band but within hard limits → soft penalty.
        """
        ph_min_hard = crop_meta.get("ph_min_hard")
        ph_max_hard = crop_meta.get("ph_max_hard")
        ph_min_ideal = crop_meta.get("ideal_ph_min")
        ph_max_ideal = crop_meta.get("ideal_ph_max")

        # Hard incompatibility check
        if ph_min_hard is not None and ph < ph_min_hard:
            return PH_HARD_FACTOR, LimitingFactor(
                factor="ph",
                severity="critical",
                detail=(
                    f"Soil pH ({ph:.1f}) is below the absolute minimum for {crop_meta['crop']} "
                    f"(hard limit: {ph_min_hard}). Crop is not viable at this acidity level."
                ),
            )
        if ph_max_hard is not None and ph > ph_max_hard:
            return PH_HARD_FACTOR, LimitingFactor(
                factor="ph",
                severity="critical",
                detail=(
                    f"Soil pH ({ph:.1f}) exceeds the absolute maximum for {crop_meta['crop']} "
                    f"(hard limit: {ph_max_hard}). Crop is not viable at this alkalinity level."
                ),
            )

        # Soft mismatch (outside ideal, within hard limits)
        outside_ideal = (
            (ph_min_ideal is not None and ph < ph_min_ideal) or
            (ph_max_ideal is not None and ph > ph_max_ideal)
        )
        if outside_ideal:
            return PH_SOFT_FACTOR, LimitingFactor(
                factor="ph",
                severity="warning",
                detail=(
                    f"Soil pH ({ph:.1f}) is outside the ideal range for {crop_meta['crop']} "
                    f"({ph_min_ideal}–{ph_max_ideal}). Yield may be reduced; amendment possible."
                ),
            )

        return PH_IDEAL_FACTOR, None

    def _climate_factor(
        self,
        temperature: Optional[float],
        rainfall: Optional[float],
        crop_meta: dict,
    ) -> Tuple[float, Optional[LimitingFactor]]:
        """
        Checks temperature and rainfall against the crop's viable ranges.
        Applied only when the values are known. Unknown → no penalty.
        """
        if temperature is None and rainfall is None:
            return CLIMATE_OK_FACTOR, None

        issues = []

        t_min = crop_meta.get("temperature_min")
        t_max = crop_meta.get("temperature_max")
        if temperature is not None and t_min is not None and t_max is not None:
            if temperature < t_min:
                issues.append(
                    f"temperature ({temperature:.1f}°C) below crop minimum ({t_min}°C)"
                )
            elif temperature > t_max:
                issues.append(
                    f"temperature ({temperature:.1f}°C) above crop maximum ({t_max}°C)"
                )

        r_min = crop_meta.get("rainfall_min")
        r_max = crop_meta.get("rainfall_max")
        if rainfall is not None and r_min is not None and r_max is not None:
            if rainfall < r_min:
                issues.append(
                    f"seasonal rainfall ({rainfall:.0f} mm) below crop minimum ({r_min} mm)"
                )
            elif rainfall > r_max:
                issues.append(
                    f"seasonal rainfall ({rainfall:.0f} mm) above crop maximum ({r_max} mm)"
                )

        if issues:
            return CLIMATE_OUT_FACTOR, LimitingFactor(
                factor="climate",
                severity="warning",
                detail=f"Climate mismatch for {crop_meta['crop']}: {'; '.join(issues)}.",
            )

        return CLIMATE_OK_FACTOR, None

    # ------------------------------------------------------------------
    # Explanation builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_explanation(
        crop_name: str,
        ml_score: float,
        suitability_score: float,
        limiting_factors: List[LimitingFactor],
        w_factor: float,
        d_factor: float,
        p_factor: float,
        c_factor: float,
    ) -> str:
        if not limiting_factors:
            return (
                f"{crop_name.capitalize()} is well-suited to the given farm conditions. "
                f"ML probability: {ml_score:.1%}. No limiting factors detected."
            )

        factor_lines = [f"  • {lf.detail}" for lf in limiting_factors]
        severity = "critical" if any(lf.severity == "critical" for lf in limiting_factors) else "warning"
        adj = "significantly reduced" if suitability_score < 0.3 else "reduced"

        return (
            f"{crop_name.capitalize()}: ML probability {ml_score:.1%}, "
            f"farm suitability {suitability_score:.1%} ({adj} from raw ML score). "
            f"Factor multipliers — water: {w_factor:.2f}, duration: {d_factor:.2f}, "
            f"pH: {p_factor:.2f}, climate: {c_factor:.2f}. "
            f"Limiting factors ({severity}):\n" + "\n".join(factor_lines)
        )


# ---------------------------------------------------------------------------
# Suitability Service — orchestration layer
# ---------------------------------------------------------------------------

class SuitabilityService:
    """
    Orchestrates ML inference + agronomic re-ranking.

    Designed to be instantiated once and reused (singleton pattern).
    crop_service must already have its model loaded.
    """

    def __init__(self, crop_service, db: Optional[CropKnowledgeDB] = None):
        self._crop_service = crop_service
        self._db = db or CropKnowledgeDB()
        self._scorer = SuitabilityScorer()

    async def recommend(
        self,
        *,
        # Soil
        nitrogen: float,
        phosphorus: float,
        potassium: float,
        ph: float,
        # Climate (may be auto-filled)
        temperature: Optional[float],
        humidity: Optional[float],
        rainfall: Optional[float],
        # Farm constraints
        constraints: FarmConstraints,
        # Weather auto-fill flag (informational)
        weather_auto_filled: bool = False,
    ) -> RecommendationResponse:
        """
        Main entry point. Returns full RecommendationResponse.
        """
        features_dict = {
            "N": nitrogen,
            "P": phosphorus,
            "K": potassium,
            "temperature": temperature or 25.0,  # fallback prevents ML crash; scored as None
            "humidity": humidity or 60.0,
            "ph": ph,
            "rainfall": rainfall or 800.0,
        }

        # Get probabilities for all crops from the ML model
        all_probs: Dict[str, float] = self._crop_service.get_all_probabilities(features_dict)

        # Score each candidate
        results: List[CropSuitabilityResult] = []
        for crop_name, ml_score in all_probs.items():
            crop_meta = self._db.get(crop_name)
            result = self._scorer.score(
                crop_name=crop_name,
                ml_score=ml_score,
                constraints=constraints,
                temperature=temperature,
                rainfall=rainfall,
                ph=ph,
                crop_meta=crop_meta,
            )
            results.append(result)

        # Sort by suitability_score descending, ML score as tiebreaker
        results.sort(key=lambda r: (r.suitability_score, r.ml_score), reverse=True)

        metadata = RecommendationMetadata(
            weather_auto_filled=weather_auto_filled,
            crop_db_version=self._db.schema_version,
        )

        return RecommendationResponse(
            top_recommendations=results[:3],
            all_candidates=results,
            metadata=metadata,
        )


# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------

_suitability_service_instance: Optional[SuitabilityService] = None


def get_suitability_service() -> SuitabilityService:
    """Returns the singleton SuitabilityService, initializing it on first call."""
    global _suitability_service_instance
    if _suitability_service_instance is None:
        # Import here to avoid circular imports
        from app.services.crop_service import get_crop_service
        _suitability_service_instance = SuitabilityService(
            crop_service=get_crop_service()
        )
    return _suitability_service_instance
