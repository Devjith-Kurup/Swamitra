import { RecommendationResponse } from './crop';
import { WeatherResponse } from './weather';

export interface FarmLocationPreset {
  name: string;
  state: string;
  latitude: number;
  longitude: number;
  typicalSeason: string;
  typicalSoil: string;
}

export interface FarmProfile {
  name: string;
  locationName: string;
  latitude: number;
  longitude: number;
  farm_area_ha: number;
  
  // Soil
  nitrogen: number;
  phosphorus: number;
  potassium: number;
  ph: number;
  
  // Climate (optional manual overrides)
  temperature?: number | null;
  humidity?: number | null;
  rainfall?: number | null;
  
  // Farm Constraints
  water_availability_mm: number;
  growing_days_available: number;
  irrigation_available: boolean;
  
  // Yield Model Categoricals
  yield_state: string;
  yield_season: string;
  yield_soil_type: string;
}

export interface FarmState {
  profile: FarmProfile | null;
  isConfigured: boolean;
  weather: WeatherResponse | null;
  recommendations: RecommendationResponse | null;
  isLoading: boolean;
  loadingMessage: string;
  error: string | null;
}
