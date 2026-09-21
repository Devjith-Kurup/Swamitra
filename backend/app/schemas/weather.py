from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class Location(BaseModel):
    latitude: float = Field(..., description="Latitude of the location", ge=-90, le=90)
    longitude: float = Field(..., description="Longitude of the location", ge=-180, le=180)

class CurrentWeather(BaseModel):
    temperature_c: float = Field(..., description="Current temperature in Celsius")
    humidity_percent: float = Field(..., description="Current relative humidity in percentage")
    rainfall_mm: float = Field(..., description="Rainfall in mm for the current period")
    wind_speed_kph: float = Field(..., description="Wind speed in km/h")
    timestamp: datetime = Field(..., description="Timestamp of the weather reading")

class DailyForecast(BaseModel):
    date: str = Field(..., description="Date of the forecast (YYYY-MM-DD)")
    max_temperature_c: float = Field(..., description="Maximum temperature in Celsius")
    min_temperature_c: float = Field(..., description="Minimum temperature in Celsius")
    rainfall_mm: float = Field(..., description="Predicted total rainfall in mm")

class WeatherResponse(BaseModel):
    location: Location
    current: CurrentWeather
    forecast: List[DailyForecast] = Field(default_factory=list, description="Daily forecast for upcoming days")
    provider: str = Field(..., description="The weather data provider used")
