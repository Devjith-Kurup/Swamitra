import React, { createContext, useContext, useEffect, useState } from 'react';
import { RecommendationRequest, RecommendationResponse } from '../types/crop';
import { FarmLocationPreset, FarmProfile } from '../types/farm';
import { WeatherResponse } from '../types/weather';
import { YieldModelMetadata } from '../types/yield';
import { api, ApiError } from '../services/api';

export const LOCATION_PRESETS: FarmLocationPreset[] = [
  {
    name: 'Pune / Haveli',
    state: 'Maharashtra',
    latitude: 18.5204,
    longitude: 73.8567,
    typicalSeason: 'Kharif',
    typicalSoil: 'Black',
  },
  {
    name: 'Ludhiana / Malwa',
    state: 'Punjab',
    latitude: 30.9010,
    longitude: 75.8573,
    typicalSeason: 'Rabi',
    typicalSoil: 'Alluvial',
  },
  {
    name: 'Karnal / Central Basin',
    state: 'Haryana',
    latitude: 29.6857,
    longitude: 76.9905,
    typicalSeason: 'Kharif',
    typicalSoil: 'Alluvial',
  },
  {
    name: 'Coimbatore / Kongu',
    state: 'Tamil Nadu',
    latitude: 11.0168,
    longitude: 76.9558,
    typicalSeason: 'Kharif',
    typicalSoil: 'Red',
  },
  {
    name: 'Guntur / Krishna Delta',
    state: 'Andhra Pradesh',
    latitude: 16.3067,
    longitude: 80.4365,
    typicalSeason: 'Kharif',
    typicalSoil: 'Black',
  },
  {
    name: 'Bhopal / Malwa Plateau',
    state: 'Madhya Pradesh',
    latitude: 23.2599,
    longitude: 77.4126,
    typicalSeason: 'Rabi',
    typicalSoil: 'Black',
  },
];

interface FarmContextType {
  profile: FarmProfile | null;
  isConfigured: boolean;
  weather: WeatherResponse | null;
  recommendations: RecommendationResponse | null;
  yieldMetadata: YieldModelMetadata | null;
  isLoading: boolean;
  loadingMessage: string;
  error: string | null;
  backendOnline: boolean;
  checkBackendHealth: () => Promise<boolean>;
  saveProfile: (profile: FarmProfile) => void;
  fetchWeatherForCoords: (lat: number, lon: number) => Promise<WeatherResponse | null>;
  analyzeFarm: (customProfile?: FarmProfile) => Promise<RecommendationResponse | null>;
  clearFarm: () => void;
  clearError: () => void;
}

const FarmContext = createContext<FarmContextType | undefined>(undefined);

const STORAGE_KEY_PROFILE = 'swamitra_farm_profile';
const STORAGE_KEY_RESULTS = 'swamitra_farm_recommendations';

export const FarmProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [profile, setProfile] = useState<FarmProfile | null>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_PROFILE);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_RESULTS);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [weather, setWeather] = useState<WeatherResponse | null>(null);
  const [yieldMetadata, setYieldMetadata] = useState<YieldModelMetadata | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingMessage, setLoadingMessage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean>(true);

  // Check backend health and fetch yield metadata on mount
  const checkBackendHealth = async (): Promise<boolean> => {
    try {
      const health = await api.checkHealth();
      const online = health.status === 'ok';
      setBackendOnline(online);
      return online;
    } catch {
      setBackendOnline(false);
      return false;
    }
  };

  useEffect(() => {
    checkBackendHealth();
    api.getYieldMetadata()
      .then(setYieldMetadata)
      .catch((err) => console.warn('Yield metadata fetch skipped or failed:', err));
  }, []);

  // Fetch weather automatically when profile with coordinates exists
  useEffect(() => {
    if (profile && profile.latitude && profile.longitude) {
      fetchWeatherForCoords(profile.latitude, profile.longitude);
    }
  }, [profile?.latitude, profile?.longitude]);

  const saveProfile = (newProfile: FarmProfile) => {
    setProfile(newProfile);
    try {
      localStorage.setItem(STORAGE_KEY_PROFILE, JSON.stringify(newProfile));
    } catch (e) {
      console.error('Failed to persist profile:', e);
    }
  };

  const fetchWeatherForCoords = async (lat: number, lon: number): Promise<WeatherResponse | null> => {
    try {
      const data = await api.getCurrentWeather(lat, lon);
      setWeather(data);
      return data;
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : 'Could not fetch weather data';
      console.warn('Weather fetch note:', msg);
      return null;
    }
  };

  const analyzeFarm = async (customProfile?: FarmProfile): Promise<RecommendationResponse | null> => {
    const targetProfile = customProfile || profile;
    if (!targetProfile) {
      setError('Please complete Farm Setup before analyzing.');
      return null;
    }

    setIsLoading(true);
    setLoadingMessage('Running farm suitability & yield models...');
    setError(null);

    try {
      const request: RecommendationRequest = {
        nitrogen: targetProfile.nitrogen,
        phosphorus: targetProfile.phosphorus,
        potassium: targetProfile.potassium,
        ph: targetProfile.ph,
        temperature: targetProfile.temperature ?? null,
        humidity: targetProfile.humidity ?? null,
        rainfall: targetProfile.rainfall ?? null,
        latitude: targetProfile.latitude,
        longitude: targetProfile.longitude,
        farm_constraints: {
          water_availability_mm: targetProfile.water_availability_mm,
          growing_days_available: targetProfile.growing_days_available,
          farm_area_ha: targetProfile.farm_area_ha,
          irrigation_available: targetProfile.irrigation_available,
        },
        include_yield: true,
        yield_state: targetProfile.yield_state,
        yield_season: targetProfile.yield_season,
        yield_soil_type: targetProfile.yield_soil_type,
      };

      const result = await api.getCropRecommendations(request);
      setRecommendations(result);
      try {
        localStorage.setItem(STORAGE_KEY_RESULTS, JSON.stringify(result));
      } catch (e) {
        console.error('Failed to persist results:', e);
      }
      return result;
    } catch (err: unknown) {
      const errorMsg = err instanceof ApiError ? err.message : 'Failed to analyze farm recommendations.';
      setError(errorMsg);
      return null;
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  const clearFarm = () => {
    setProfile(null);
    setRecommendations(null);
    setWeather(null);
    localStorage.removeItem(STORAGE_KEY_PROFILE);
    localStorage.removeItem(STORAGE_KEY_RESULTS);
  };

  const clearError = () => setError(null);

  return (
    <FarmContext.Provider
      value={{
        profile,
        isConfigured: profile !== null,
        weather,
        recommendations,
        yieldMetadata,
        isLoading,
        loadingMessage,
        error,
        backendOnline,
        checkBackendHealth,
        saveProfile,
        fetchWeatherForCoords,
        analyzeFarm,
        clearFarm,
        clearError,
      }}
    >
      {children}
    </FarmContext.Provider>
  );
};

export const useFarm = (): FarmContextType => {
  const context = useContext(FarmContext);
  if (!context) {
    throw new Error('useFarm must be used within a FarmProvider');
  }
  return context;
};
