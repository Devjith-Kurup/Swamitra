import logging
import joblib
import pandas as pd
from typing import Optional
from huggingface_hub import hf_hub_download

from app.schemas.crop import (
    CropPredictionRequest,
    CropPredictionResponse,
    CropRecommendationItem
)
from app.services.weather_service import get_weather_service

logger = logging.getLogger(__name__)

class CropService:
    def __init__(self):
        self.model = None
        self.label_encoder = None
        self.model_id = "Sheshank2609/crop-recommendation-system"
        
    def load_model(self):
        """Loads the model and label encoder from Hugging Face Hub."""
        try:
            logger.info(f"Loading crop recommendation model: {self.model_id}")
            model_path = hf_hub_download(repo_id=self.model_id, filename="model1_npk.pkl")
            encoder_path = hf_hub_download(repo_id=self.model_id, filename="model1_label_encoder.pkl")
            
            self.model = joblib.load(model_path)
            self.label_encoder = joblib.load(encoder_path)
            logger.info("Crop recommendation model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load crop recommendation model: {e}")
            self.model = None
            self.label_encoder = None

    async def predict(self, request: CropPredictionRequest) -> CropPredictionResponse:
        """Makes a prediction based on the input features."""
        if self.model is None or self.label_encoder is None:
            raise RuntimeError("Model is not loaded or is unavailable.")

        temp = request.temperature
        humidity = request.humidity
        rainfall = request.rainfall

        # Auto-fill weather if missing and location is provided
        if None in (temp, humidity, rainfall):
            if request.latitude is not None and request.longitude is not None:
                try:
                    weather_service = get_weather_service()
                    weather = await weather_service.get_weather(request.latitude, request.longitude)
                    temp = temp if temp is not None else weather.current.temperature_c
                    humidity = humidity if humidity is not None else weather.current.humidity_percent
                    rainfall = rainfall if rainfall is not None else weather.current.rainfall_mm
                    logger.info(f"Auto-filled weather for prediction: temp={temp}, hum={humidity}, rain={rainfall}")
                except Exception as e:
                    logger.error(f"Failed to fetch weather for auto-fill: {e}")
                    raise ValueError(f"Failed to fetch weather data for the given location: {e}")
            else:
                raise ValueError("Temperature, humidity, and rainfall must be provided if latitude and longitude are not specified.")

        # Order must match the model's training features: N, P, K, temperature, humidity, ph, rainfall
        features_dict = {
            "N": request.nitrogen,
            "P": request.phosphorus,
            "K": request.potassium,
            "temperature": temp,
            "humidity": humidity,
            "ph": request.ph,
            "rainfall": rainfall
        }
        
        # Create DataFrame to avoid warning of feature names
        df = pd.DataFrame([features_dict])
        
        # Get probabilities
        proba = self.model.predict_proba(df)[0]
        
        # Map probabilities to classes
        crop_scores = {c: float(p) for c, p in zip(self.label_encoder.classes_, proba)}
        
        # Sort scores in descending order
        sorted_scores = sorted(crop_scores.items(), key=lambda item: item[1], reverse=True)
        
        # Top 5 crops
        top_5 = sorted_scores[:5]
        
        predicted_crop = top_5[0][0] if top_5 else "Unknown"
        
        recommendations = [
            CropRecommendationItem(crop=crop_name, score=score)
            for crop_name, score in top_5
        ]
        
        return CropPredictionResponse(
            predicted_crop=predicted_crop,
            recommendations=recommendations,
            model=self.model_id,
            features_used=request.model_dump()
        )

# Singleton instance
_crop_service_instance: Optional[CropService] = None

def get_crop_service() -> CropService:
    """Returns the singleton instance of CropService."""
    global _crop_service_instance
    if _crop_service_instance is None:
        _crop_service_instance = CropService()
        _crop_service_instance.load_model()
    return _crop_service_instance
