from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class FarmConstraints(BaseModel):
    """Constraints representing the farm's physical and resource limitations."""
    water_availability_mm: float = Field(
        ...,
        description="Total water available for the season (mm). Includes rainfall + irrigation.",
        ge=0,
        le=5000
    )
    growing_days_available: int = Field(
        ...,
        description="Number of days in the available growing window before the next constraint (e.g. frost, market deadline).",
        ge=1,
        le=365
    )
    farm_area_ha: Optional[float] = Field(
        None,
        description="Farm area in hectares. Currently informational; reserved for future yield estimation.",
        ge=0.01,
        le=10000
    )
    irrigation_available: bool = Field(
        False,
        description="Whether supplemental irrigation infrastructure is available."
    )


class RecommendationRequest(BaseModel):
    """
    Full input for the farm-aware crop recommendation endpoint.
    Combines soil parameters, optional climate override, farm constraints, and optional location.
    """
    # --- Soil inputs (required) ---
    nitrogen: float = Field(..., description="Nitrogen content in soil (mg/kg)", ge=0, le=300)
    phosphorus: float = Field(..., description="Phosphorus content in soil (mg/kg)", ge=0, le=300)
    potassium: float = Field(..., description="Potassium content in soil (mg/kg)", ge=0, le=300)
    ph: float = Field(..., description="Soil pH value", ge=3.5, le=9.5)

    # --- Climate inputs (optional if location is provided) ---
    temperature: Optional[float] = Field(None, description="Mean temperature in Celsius", ge=5, le=50)
    humidity: Optional[float] = Field(None, description="Relative humidity (%)", ge=10, le=100)
    rainfall: Optional[float] = Field(None, description="Seasonal rainfall in mm", ge=0, le=3000)

    # --- Location for auto-fetching climate (optional) ---
    latitude: Optional[float] = Field(None, description="Latitude for weather lookup", ge=-90, le=90)
    longitude: Optional[float] = Field(None, description="Longitude for weather lookup", ge=-180, le=180)

    # --- Farm constraints (required for suitability scoring) ---
    farm_constraints: FarmConstraints


class LimitingFactor(BaseModel):
    """A single named constraint that reduced the suitability score for a crop."""
    factor: str = Field(..., description="Machine-readable factor name (e.g. 'water', 'duration', 'ph', 'temperature')")
    severity: Literal["warning", "critical"] = Field(
        ...,
        description="'critical' means a hard incompatibility (score zeroed or near-zero); 'warning' is a soft penalty."
    )
    detail: str = Field(..., description="Human-readable explanation of this specific limiting factor.")


class CropSuitabilityResult(BaseModel):
    """Suitability assessment for a single crop candidate."""
    crop: str = Field(..., description="Crop name (matches ML model label)")
    ml_score: float = Field(..., description="Raw ML probability from the crop recommendation model (0–1)", ge=0, le=1)
    suitability_score: float = Field(..., description="Farm-adjusted suitability score (0–1)", ge=0, le=1)
    limiting_factors: List[LimitingFactor] = Field(
        default_factory=list,
        description="Ordered list of factors that reduced the suitability score. Empty = fully compatible."
    )
    explanation: str = Field(..., description="Plain-language summary of the suitability assessment.")


class RecommendationMetadata(BaseModel):
    """Contextual information about what drove the recommendation."""
    weather_auto_filled: bool = Field(False, description="True if climate values were fetched from the weather service.")
    crop_db_version: str = Field(..., description="Schema version of the crops.json knowledge base used.")
    data_quality_note: str = Field(
        "Crop knowledge values are PROTOTYPE reference estimates. Do not use for production agronomic decisions without verified regional data.",
        description="Data quality disclaimer for the crop knowledge base."
    )


class RecommendationResponse(BaseModel):
    """
    Output of POST /api/v1/crops/recommend.
    Contains the top 3 farm-aware recommendations and full candidate list.
    """
    top_recommendations: List[CropSuitabilityResult] = Field(
        ...,
        description="Top 3 crops ranked by suitability score, descending."
    )
    all_candidates: List[CropSuitabilityResult] = Field(
        ...,
        description="Full ranked list of all candidates scored by the ML model (22 crops)."
    )
    metadata: RecommendationMetadata
