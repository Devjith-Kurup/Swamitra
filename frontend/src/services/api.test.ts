import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api, ApiError } from './api';

describe('SWAMITRA API Client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('ApiError preserves status and message', () => {
    const error = new ApiError('Test error message', 400, { detail: 'Field invalid' });
    expect(error.message).toBe('Test error message');
    expect(error.status).toBe(400);
    expect(error.data).toEqual({ detail: 'Field invalid' });
  });

  it('checkHealth calls /health and returns response', async () => {
    const mockHealth = { status: 'ok' };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockHealth,
    } as Response);

    const result = await api.checkHealth();
    expect(result).toEqual({ status: 'ok' });
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/health'),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('getCurrentWeather passes latitude and longitude query params', async () => {
    const mockWeather = {
      location: { latitude: 18.52, longitude: 73.85 },
      current: {
        temperature_c: 26.5,
        humidity_percent: 70,
        rainfall_mm: 50,
        wind_speed_kph: 12,
        timestamp: '2026-09-22T00:00:00Z',
      },
      forecast: [],
      provider: 'mock-meteo',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockWeather,
    } as Response);

    const result = await api.getCurrentWeather(18.52, 73.85);
    expect(result.current.temperature_c).toBe(26.5);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('lat=18.52&lon=73.85'),
      expect.anything()
    );
  });

  it('getCropRecommendations sends POST with JSON payload', async () => {
    const mockRecommendation = {
      top_recommendations: [
        {
          crop: 'rice',
          ml_score: 0.85,
          suitability_score: 0.9,
          limiting_factors: [],
          explanation: 'Optimal farm match',
          predicted_yield_per_ha: 25.0,
          estimated_total_production: 50.0,
          yield_unit: 'quintal/hectare',
        },
      ],
      all_candidates: [],
      metadata: {
        weather_auto_filled: false,
        crop_db_version: '1.0',
        data_quality_note: 'Prototype note',
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockRecommendation,
    } as Response);

    const reqPayload = {
      nitrogen: 90,
      phosphorus: 42,
      potassium: 43,
      ph: 6.5,
      farm_constraints: {
        water_availability_mm: 1000,
        growing_days_available: 120,
        farm_area_ha: 2.0,
        irrigation_available: true,
      },
      include_yield: true,
      yield_state: 'Maharashtra',
      yield_season: 'Kharif',
      yield_soil_type: 'Black',
    };

    const result = await api.getCropRecommendations(reqPayload);
    expect(result.top_recommendations[0].crop).toBe('rice');
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/crops/recommend'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(reqPayload),
      })
    );
  });

  it('handles 503 service unavailable with friendly warming up message', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ detail: 'Model loading' }),
    } as Response);

    await expect(api.checkHealth()).rejects.toThrow(
      'AI model service is currently warming up or unavailable. Please retry in a few seconds.'
    );
  });

  it('handles Pydantic array validation errors gracefully', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({
        detail: [
          { loc: ['body', 'nitrogen'], msg: 'Input should be greater than or equal to 0' },
          { loc: ['body', 'ph'], msg: 'Input should be less than or equal to 9.5' },
        ],
      }),
    } as Response);

    await expect(
      api.getCropRecommendations({} as any)
    ).rejects.toThrow('nitrogen: Input should be greater than or equal to 0; ph: Input should be less than or equal to 9.5');
  });
});
