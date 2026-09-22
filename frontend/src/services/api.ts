/**
 * Centralized API client for SWAMITRA.
 * Connects directly to the FastAPI backend.
 * Handles timeouts, network failures, and detailed backend error extraction.
 */

import {
  CropPredictionResponse,
  RecommendationRequest,
  RecommendationResponse,
} from '../types/crop';
import { WeatherResponse } from '../types/weather';
import {
  YieldModelMetadata,
  YieldPredictionRequest,
  YieldPredictionResponse,
} from '../types/yield';

// Use VITE_API_BASE_URL if set; otherwise use relative path (proxied by Vite dev server)
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export class ApiError extends Error {
  status?: number;
  data?: unknown;

  constructor(message: string, status?: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}, timeoutMs = 25000): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const defaultHeaders: Record<string, string> = {
    'Accept': 'application/json',
  };

  if (options.body && typeof options.body === 'string') {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMessage = `Server error (${response.status})`;
      let errorData: unknown = null;

      try {
        const json = await response.json();
        errorData = json;
        if (json.detail) {
          if (typeof json.detail === 'string') {
            errorMessage = json.detail;
          } else if (Array.isArray(json.detail)) {
            // Pydantic validation error array
            errorMessage = json.detail.map((d: { msg?: string; loc?: string[] }) => {
              const field = d.loc ? d.loc.filter(l => l !== 'body').join('.') : '';
              return field ? `${field}: ${d.msg}` : (d.msg || 'Validation error');
            }).join('; ');
          }
        }
      } catch {
        const text = await response.text().catch(() => '');
        if (text) errorMessage = text;
      }

      if (response.status === 503) {
        errorMessage = 'AI model service is currently warming up or unavailable. Please retry in a few seconds.';
      } else if (response.status === 502) {
        errorMessage = 'Weather provider service error. Check location coordinates or try again later.';
      }

      throw new ApiError(errorMessage, response.status, errorData);
    }

    return (await response.json()) as T;
  } catch (error: unknown) {
    clearTimeout(timeoutId);

    if (error instanceof ApiError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('Request timed out. The backend server took too long to respond.');
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError('Unable to reach the SWAMITRA backend. Please ensure the server is running at ' + (API_BASE_URL || 'http://127.0.0.1:8000'));
    }

    throw new ApiError(error instanceof Error ? error.message : 'An unexpected network error occurred.');
  }
}

export const api = {
  /**
   * Health check endpoint
   */
  async checkHealth(): Promise<{ status: string }> {
    return request<{ status: string }>('/health', { method: 'GET' }, 5000);
  },

  /**
   * Current weather lookup from coordinates
   */
  async getCurrentWeather(latitude: number, longitude: number): Promise<WeatherResponse> {
    const params = new URLSearchParams({
      lat: latitude.toString(),
      lon: longitude.toString(),
    });
    return request<WeatherResponse>(`/api/v1/weather/current?${params.toString()}`);
  },

  /**
   * Multi-day weather forecast lookup
   */
  async getWeatherForecast(latitude: number, longitude: number, days = 7): Promise<WeatherResponse> {
    const params = new URLSearchParams({
      lat: latitude.toString(),
      lon: longitude.toString(),
      days: days.toString(),
    });
    return request<WeatherResponse>(`/api/v1/weather/forecast?${params.toString()}`);
  },

  /**
   * Farm-aware crop recommendation with optional yield enrichment
   */
  async getCropRecommendations(data: RecommendationRequest): Promise<RecommendationResponse> {
    return request<RecommendationResponse>('/api/v1/crops/recommend', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Raw ML crop prediction (top 5 by confidence)
   */
  async predictCropRaw(data: {
    nitrogen: number;
    phosphorus: number;
    potassium: number;
    ph: number;
    temperature?: number | null;
    humidity?: number | null;
    rainfall?: number | null;
    latitude?: number | null;
    longitude?: number | null;
  }): Promise<CropPredictionResponse> {
    return request<CropPredictionResponse>('/api/v1/crops/predict', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Standalone crop yield prediction
   */
  async predictYield(data: YieldPredictionRequest): Promise<YieldPredictionResponse> {
    return request<YieldPredictionResponse>('/api/v1/yield/predict', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Yield model metadata (valid states, crops, seasons, soil types)
   */
  async getYieldMetadata(): Promise<YieldModelMetadata> {
    return request<YieldModelMetadata>('/api/v1/yield/metadata');
  },
};
