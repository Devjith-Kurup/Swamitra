from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CropPredictionRequest(BaseModel):
    nitrogen: float = Field(..., description="Nitrogen content in soil (mg/kg)", ge=0, le=300)
    phosphorus: float = Field(..., description="Phosphorus content in soil (mg/kg)", ge=0, le=300)
    potassium: float = Field(..., description="Potassium content in soil (mg/kg)", ge=0, le=300)
    ph: float = Field(..., description="Soil pH value", ge=3.5, le=9.5)
    
    # Environmental variables can be optional if location is provided
    temperature: Optional[float] = Field(None, description="Temperature in Celsius", ge=5, le=50)
    humidity: Optional[float] = Field(None, description="Relative humidity in percentage", ge=10, le=100)
    rainfall: Optional[float] = Field(None, description="Rainfall in mm", ge=20, le=3000)
    
    # Location variables to auto-fill environmental variables
    latitude: Optional[float] = Field(None, description="Latitude for weather lookup", ge=-90, le=90)
    longitude: Optional[float] = Field(None, description="Longitude for weather lookup", ge=-180, le=180)

class CropRecommendationItem(BaseModel):
    crop: str = Field(..., description="Name of the recommended crop")
    score: float = Field(..., description="Confidence score or probability of the recommendation")

class CropPredictionResponse(BaseModel):
    predicted_crop: str = Field(..., description="The most highly recommended crop")
    recommendations: List[CropRecommendationItem] = Field(..., description="Top recommended crops with their confidence scores")
    model: str = Field(..., description="The identifier of the model used for prediction")
    features_used: Dict[str, Any] = Field(..., description="The input features used for the prediction")
