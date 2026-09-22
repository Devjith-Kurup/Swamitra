export interface FarmConstraints {
  water_availability_mm: number;
  growing_days_available: number;
  farm_area_ha?: number | null;
  irrigation_available: boolean;
}

export interface RecommendationRequest {
  nitrogen: number;
  phosphorus: number;
  potassium: number;
  ph: number;
  temperature?: number | null;
  humidity?: number | null;
  rainfall?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  farm_constraints: FarmConstraints;
  include_yield?: boolean;
  yield_state?: string | null;
  yield_season?: string | null;
  yield_soil_type?: string | null;
}

export interface LimitingFactor {
  factor: string;
  severity: "warning" | "critical";
  detail: string;
}

export interface CropSuitabilityResult {
  crop: string;
  ml_score: number;
  suitability_score: number;
  limiting_factors: LimitingFactor[];
  explanation: string;
  predicted_yield_per_ha?: number | null;
  estimated_total_production?: number | null;
  yield_unit?: string | null;
}

export interface RecommendationMetadata {
  weather_auto_filled: boolean;
  crop_db_version: string;
  data_quality_note: string;
}

export interface RecommendationResponse {
  top_recommendations: CropSuitabilityResult[];
  all_candidates: CropSuitabilityResult[];
  metadata: RecommendationMetadata;
}

export interface CropRecommendationItem {
  crop: string;
  score: number;
}

export interface CropPredictionResponse {
  predicted_crop: string;
  recommendations: CropRecommendationItem[];
  model: string;
  features_used: Record<string, unknown>;
}
