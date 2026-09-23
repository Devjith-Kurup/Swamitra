import React, { useState } from 'react';
import {
  MapPin,
  Compass,
  Layers,
  Waves,
  CloudSun,
  Save,
  RotateCcw,
  Sparkles,
  Check,
} from 'lucide-react';
import { useFarm, LOCATION_PRESETS } from '../context/FarmContext';
import { FarmProfile } from '../types/farm';
import { TabId } from '../components/layout/Navbar';
import { ErrorAlert } from '../components/common/ErrorAlert';

interface FarmSetupPageProps {
  onNavigate: (tab: TabId) => void;
}

export const FarmSetupPage: React.FC<FarmSetupPageProps> = ({ onNavigate }) => {
  const { profile, saveProfile, analyzeFarm, fetchWeatherForCoords, yieldMetadata, error, clearError } = useFarm();

  const [formData, setFormData] = useState<FarmProfile>(() => {
    if (profile) return profile;
    const defaultPreset = LOCATION_PRESETS[0];
    return {
      name: `${defaultPreset.name} Farm`,
      locationName: defaultPreset.name,
      latitude: defaultPreset.latitude,
      longitude: defaultPreset.longitude,
      farm_area_ha: 2.5,
      nitrogen: 90,
      phosphorus: 42,
      potassium: 43,
      ph: 6.5,
      temperature: null,
      humidity: null,
      rainfall: null,
      water_availability_mm: 900,
      growing_days_available: 120,
      irrigation_available: true,
      yield_state: defaultPreset.state,
      yield_season: defaultPreset.typicalSeason,
      yield_soil_type: defaultPreset.typicalSoil,
    };
  });

  const [isFetchingWeather, setIsFetchingWeather] = useState(false);
  const [weatherFetchSuccess, setWeatherFetchSuccess] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Fallback valid options if metadata hasn't loaded yet
  const states = yieldMetadata?.valid_states || [
    'Andhra Pradesh', 'Gujarat', 'Haryana', 'Karnataka', 'Madhya Pradesh', 'Maharashtra', 'Punjab', 'Rajasthan', 'Tamil Nadu', 'Uttar Pradesh', 'West Bengal'
  ];
  const seasons = yieldMetadata?.valid_seasons || ['Autumn', 'Kharif', 'Rabi', 'Summer', 'Winter', 'Whole Year'];
  const soilTypes = yieldMetadata?.valid_soil_types || ['Alluvial', 'Black', 'Clay', 'Laterite', 'Red'];

  const validate = (): boolean => {
    const errs: Record<string, string> = {};

    if (formData.latitude < -90 || formData.latitude > 90) {
      errs.latitude = 'Latitude must be between -90 and 90';
    }
    if (formData.longitude < -180 || formData.longitude > 180) {
      errs.longitude = 'Longitude must be between -180 and 180';
    }
    if (formData.farm_area_ha <= 0 || formData.farm_area_ha > 10000) {
      errs.farm_area_ha = 'Area must be between 0.01 and 10,000 hectares';
    }
    if (formData.nitrogen < 0 || formData.nitrogen > 300) {
      errs.nitrogen = 'Nitrogen must be between 0 and 300 mg/kg';
    }
    if (formData.phosphorus < 0 || formData.phosphorus > 300) {
      errs.phosphorus = 'Phosphorus must be between 0 and 300 mg/kg';
    }
    if (formData.potassium < 0 || formData.potassium > 300) {
      errs.potassium = 'Potassium must be between 0 and 300 mg/kg';
    }
    if (formData.ph < 3.5 || formData.ph > 9.5) {
      errs.ph = 'Soil pH must be between 3.5 and 9.5';
    }
    if (formData.water_availability_mm < 0 || formData.water_availability_mm > 5000) {
      errs.water_availability_mm = 'Water availability must be between 0 and 5000 mm';
    }
    if (formData.growing_days_available < 1 || formData.growing_days_available > 365) {
      errs.growing_days_available = 'Growing days must be between 1 and 365 days';
    }

    setValidationErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handlePresetSelect = (presetIndex: number) => {
    const preset = LOCATION_PRESETS[presetIndex];
    setFormData((prev) => ({
      ...prev,
      name: `${preset.name} Farm`,
      locationName: preset.name,
      latitude: preset.latitude,
      longitude: preset.longitude,
      yield_state: preset.state,
      yield_season: preset.typicalSeason,
      yield_soil_type: preset.typicalSoil,
    }));
  };

  const handleFetchWeather = async () => {
    setIsFetchingWeather(true);
    setWeatherFetchSuccess(false);
    try {
      const weather = await fetchWeatherForCoords(formData.latitude, formData.longitude);
      if (weather?.current) {
        setFormData((prev) => ({
          ...prev,
          temperature: Math.round(weather.current.temperature_c * 10) / 10,
          humidity: Math.round(weather.current.humidity_percent),
          rainfall: Math.round(weather.current.rainfall_mm),
        }));
        setWeatherFetchSuccess(true);
        setTimeout(() => setWeatherFetchSuccess(false), 4000);
      }
    } finally {
      setIsFetchingWeather(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    saveProfile(formData);
    const result = await analyzeFarm(formData);
    if (result) {
      onNavigate('recommendations');
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">Farm Setup</h1>
        <p className="text-sm text-slate-600 mt-1">
          Tell us about your farm. You can pick a quick preset below or fill in your details manually.
        </p>
      </div>

      {error && <ErrorAlert message={error} onDismiss={clearError} />}

      {/* Preset Hub Selector */}
      <div className="glass-card p-5 animate-fade-in-up">
        <div className="flex items-center gap-2 text-sm font-bold text-slate-700 mb-3">
          <Sparkles className="w-5 h-5 text-emerald-700" />
          <span>Quick Setup: Choose a region close to you</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {LOCATION_PRESETS.map((p, idx) => (
            <button
              key={p.name}
              type="button"
              onClick={() => handlePresetSelect(idx)}
              className={`p-2.5 rounded-xl border text-left text-xs transition-all ${
                formData.locationName === p.name
                  ? 'border-emerald-600 bg-emerald-50 text-emerald-950 font-bold'
                  : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
              }`}
            >
              <div className="truncate font-semibold">{p.name.split('/')[0].trim()}</div>
              <div className="text-[10px] text-slate-500 truncate">{p.state}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="glass-card p-6 space-y-4 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <MapPin className="w-5 h-5 text-emerald-700" />
              <span>Basic Farm Information</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Farm Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                placeholder="e.g. My Farm"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Farm Size (Hectares)</label>
              <input
                type="number"
                step="0.1"
                min="0.01"
                max="10000"
                value={formData.farm_area_ha}
                onChange={(e) => setFormData({ ...formData, farm_area_ha: parseFloat(e.target.value) || 0 })}
                className={`w-full px-3 py-2 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
                  validationErrors.farm_area_ha ? 'border-rose-500' : 'border-slate-200'
                }`}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">State</label>
              <select
                value={formData.yield_state}
                onChange={(e) => setFormData({ ...formData, yield_state: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
                required
              >
                {states.map((st) => (
                  <option key={st} value={st}>{st}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Growing Season</label>
              <select
                value={formData.yield_season}
                onChange={(e) => setFormData({ ...formData, yield_season: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
                required
              >
                {seasons.map((sn) => (
                  <option key={sn} value={sn}>{sn}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Soil Type</label>
              <select
                value={formData.yield_soil_type}
                onChange={(e) => setFormData({ ...formData, yield_soil_type: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
                required
              >
                {soilTypes.map((st) => (
                  <option key={st} value={st}>{st}</option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-3 pt-6">
              <input
                type="checkbox"
                id="irrigation"
                checked={formData.irrigation_available}
                onChange={(e) => setFormData({ ...formData, irrigation_available: e.target.checked })}
                className="w-5 h-5 rounded text-emerald-700 focus:ring-emerald-500 border-slate-300"
              />
              <label htmlFor="irrigation" className="text-sm font-bold text-slate-800 cursor-pointer">
                I have irrigation (Drip, Canal, or Borewell)
              </label>
            </div>
          </div>
        </div>

        {/* Advanced Settings (Hidden by default) */}
        <details className="glass-card group animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          <summary className="p-6 font-bold text-slate-700 cursor-pointer flex items-center justify-between outline-none">
            <span className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-emerald-700" />
              Advanced Soil & Weather Settings (Optional)
            </span>
            <span className="text-xs text-slate-400 group-open:hidden">Click to expand</span>
          </summary>
          
          <div className="px-6 pb-6 space-y-6 border-t border-slate-100 pt-4">
            
            {/* Auto Weather */}
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div>
                <div className="font-bold text-sm text-slate-800">Auto-detect weather</div>
                <div className="text-xs text-slate-500">Fetch live weather data based on the coordinates below.</div>
              </div>
              <button
                type="button"
                onClick={handleFetchWeather}
                disabled={isFetchingWeather}
                className="text-xs font-bold px-4 py-2 rounded-lg bg-emerald-100 text-emerald-800 hover:bg-emerald-200 transition-colors flex items-center gap-2"
              >
                <CloudSun className="w-4 h-4" />
                <span>{isFetchingWeather ? 'Fetching...' : 'Get Live Weather'}</span>
                {weatherFetchSuccess && <Check className="w-4 h-4 text-emerald-600" />}
              </button>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Latitude (°N)</label>
                <input
                  type="number"
                  step="0.0001"
                  value={formData.latitude}
                  onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) || 0 })}
                  className={`w-full px-3 py-2 rounded-xl border text-sm ${validationErrors.latitude ? 'border-rose-500' : 'border-slate-200'}`}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Longitude (°E)</label>
                <input
                  type="number"
                  step="0.0001"
                  value={formData.longitude}
                  onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) || 0 })}
                  className={`w-full px-3 py-2 rounded-xl border text-sm ${validationErrors.longitude ? 'border-rose-500' : 'border-slate-200'}`}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Nitrogen (N)</label>
                <input
                  type="number"
                  value={formData.nitrogen}
                  onChange={(e) => setFormData({ ...formData, nitrogen: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Phosphorus (P)</label>
                <input
                  type="number"
                  value={formData.phosphorus}
                  onChange={(e) => setFormData({ ...formData, phosphorus: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Potassium (K)</label>
                <input
                  type="number"
                  value={formData.potassium}
                  onChange={(e) => setFormData({ ...formData, potassium: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Soil pH</label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.ph}
                  onChange={(e) => setFormData({ ...formData, ph: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Water Available (mm)</label>
                <input
                  type="number"
                  value={formData.water_availability_mm}
                  onChange={(e) => setFormData({ ...formData, water_availability_mm: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Growing Window (days)</label>
                <input
                  type="number"
                  value={formData.growing_days_available}
                  onChange={(e) => setFormData({ ...formData, growing_days_available: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm"
                />
              </div>
            </div>
          </div>
        </details>

        {/* Submit Bar */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={() => handlePresetSelect(0)}
            className="px-4 py-2.5 rounded-xl border border-slate-200 text-slate-600 text-xs font-semibold hover:bg-slate-50 transition-colors flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset to Default</span>
          </button>

          <button
            type="submit"
            className="px-6 py-3 rounded-xl bg-emerald-700 text-white text-xs font-bold hover:bg-emerald-800 transition-colors shadow-sm flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            <span>Save Profile & Analyze Recommendations</span>
          </button>
        </div>
      </form>
    </div>
  );
};
