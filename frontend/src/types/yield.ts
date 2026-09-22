export interface YieldPredictionRequest {
  state: string;
  crop: string;
  season: string;
  soil_type: string;
  area: number;
  rainfall: number;
  temperature: number;
  humidity: number;
  nitrogen: number;
  phosphorus: number;
  potassium: number;
}

export interface YieldPredictionResponse {
  crop: string;
  state: string;
  season: string;
  area_ha: number;
  predicted_yield_per_ha: number;
  yield_unit: string;
  estimated_total_production: number;
  production_unit: string;
  model: string;
  data_quality_note: string;
}

export interface YieldModelMetadata {
  model: string;
  model_loaded: boolean;
  valid_states: string[];
  valid_crops: string[];
  valid_seasons: string[];
  valid_soil_types: string[];
  feature_order: string[];
  output_unit: string;
  data_quality_note: string;
}
