import React from 'react';
import {
  MapPin,
  Thermometer,
  Droplets,
  CloudRain,
  Wind,
  Layers,
  Waves,
  ArrowRight,
  TrendingUp,
  Scale,
  Sparkles,
  ShieldAlert,
} from 'lucide-react';
import { useFarm, LOCATION_PRESETS } from '../context/FarmContext';
import { MetricCard } from '../components/common/MetricCard';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { TabId } from '../components/layout/Navbar';

interface DashboardPageProps {
  onNavigate: (tab: TabId) => void;
  onSelectCrop: (cropName: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate, onSelectCrop }) => {
  const { profile, weather, recommendations, isConfigured, isLoading, loadingMessage, analyzeFarm, saveProfile } = useFarm();

  const handleApplyPreset = async (presetIndex: number) => {
    const preset = LOCATION_PRESETS[presetIndex];
    const newProfile = {
      name: `${preset.name} Farm`,
      locationName: preset.name,
      latitude: preset.latitude,
      longitude: preset.longitude,
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
      yield_state: preset.state,
      yield_season: preset.typicalSeason,
      yield_soil_type: preset.typicalSoil,
    };
    saveProfile(newProfile);
    await analyzeFarm(newProfile);
  };

  if (isLoading) {
    return <LoadingSpinner message={loadingMessage || 'Fetching farm telemetry & models...'} fullScreen />;
  }

  // Empty State: No farm configured
  if (!isConfigured || !profile) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6">
        <div className="bg-white rounded-3xl border border-slate-200 p-8 sm:p-12 shadow-sm text-center">
          <div className="w-16 h-16 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center mx-auto shadow-inner">
            <Sparkles className="w-8 h-8" />
          </div>

          <h2 className="mt-6 text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Welcome to SWAMITRA
          </h2>
          <p className="mt-3 text-sm sm:text-base text-slate-600 max-w-xl mx-auto leading-relaxed">
            AI-powered agricultural decision-support system. Configure your farm location, soil chemistry, and resource constraints to receive ML-powered crop recommendations and yield forecasts.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => onNavigate('setup')}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-emerald-700 text-white font-semibold text-sm hover:bg-emerald-800 transition-colors shadow-sm flex items-center justify-center gap-2"
            >
              <span>Set Up Your Farm Profile</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Quick preset selector for instant testing */}
          <div className="mt-12 pt-8 border-t border-slate-100">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">
              Or load an Indian agricultural hub preset:
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 max-w-2xl mx-auto">
              {LOCATION_PRESETS.map((p, idx) => (
                <button
                  key={p.name}
                  onClick={() => handleApplyPreset(idx)}
                  className="px-3 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-left hover:border-emerald-500 hover:bg-emerald-50/50 transition-all text-xs"
                >
                  <div className="font-bold text-slate-800">{p.name}</div>
                  <div className="text-[11px] text-slate-500">{p.state} • {p.typicalSoil}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  const topCrop = recommendations?.top_recommendations?.[0];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Farm Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-emerald-800 text-xs font-semibold uppercase tracking-wider">
            <MapPin className="w-4 h-4 text-emerald-700" />
            <span>Active Farm Profile</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 mt-1 tracking-tight">
            {profile.name || profile.locationName}
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {profile.locationName} ({profile.latitude.toFixed(4)}°N, {profile.longitude.toFixed(4)}°E) •{' '}
            <strong>{profile.farm_area_ha} hectares</strong> • {profile.yield_state} ({profile.yield_season} Season)
          </p>
        </div>

        <div className="flex items-center gap-2.5 w-full md:w-auto">
          <button
            onClick={() => onNavigate('setup')}
            className="flex-1 md:flex-none px-4 py-2 rounded-xl border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition-colors"
          >
            Edit Farm Setup
          </button>
          <button
            onClick={() => analyzeFarm()}
            className="flex-1 md:flex-none px-4 py-2 rounded-xl bg-emerald-700 text-white text-xs font-semibold hover:bg-emerald-800 transition-colors shadow-xs"
          >
            Re-Analyze Farm
          </button>
        </div>
      </div>

      {/* Primary Recommendation Highlight Banner */}
      {topCrop && (
        <div className="bg-gradient-to-r from-emerald-900 to-emerald-950 text-white rounded-3xl p-6 sm:p-8 shadow-sm relative overflow-hidden">
          <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-800/80 text-emerald-200 text-xs font-semibold border border-emerald-700/50">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Primary Recommendation</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-black mt-2 capitalize tracking-tight">
                {topCrop.crop}
              </h2>
              <p className="text-emerald-100/90 text-sm mt-2 leading-relaxed">
                {topCrop.explanation}
              </p>

              <div className="mt-4 flex flex-wrap items-center gap-4 text-xs font-medium">
                <div className="flex items-center gap-1.5">
                  <Scale className="w-4 h-4 text-emerald-400" />
                  <span>Suitability Score:</span>
                  <strong className="text-white text-base">{Math.round(topCrop.suitability_score * 100)}%</strong>
                </div>
                <div className="flex items-center gap-1.5 text-emerald-200">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  <span>ML Probability:</span>
                  <strong className="text-white">{Math.round(topCrop.ml_score * 100)}%</strong>
                </div>
                {topCrop.predicted_yield_per_ha && (
                  <div className="flex items-center gap-1.5 text-emerald-200">
                    <span>Expected Yield:</span>
                    <strong className="text-white text-base">{topCrop.predicted_yield_per_ha.toFixed(2)} quintal/ha</strong>
                  </div>
                )}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row lg:flex-col gap-2.5 w-full lg:w-auto">
              <button
                onClick={() => onNavigate('recommendations')}
                className="px-5 py-3 rounded-xl bg-white text-emerald-950 font-bold text-xs hover:bg-emerald-50 transition-colors shadow-sm text-center"
              >
                View Top 3 Recommendations
              </button>
              <button
                onClick={() => {
                  onSelectCrop(topCrop.crop);
                  onNavigate('details');
                }}
                className="px-5 py-3 rounded-xl bg-emerald-800/80 border border-emerald-700 text-white font-semibold text-xs hover:bg-emerald-800 transition-colors text-center"
              >
                Deep-Dive Agronomic Analysis
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Grid: Live Weather Telemetry */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <Thermometer className="w-4 h-4 text-emerald-700" />
            <span>Environmental & Weather Telemetry</span>
          </h3>
          {weather && (
            <span className="text-xs text-slate-500">
              Provider: <strong>{weather.provider}</strong> • {new Date(weather.current.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
          <MetricCard
            label="Temperature"
            value={weather?.current ? weather.current.temperature_c.toFixed(1) : (profile.temperature ?? '—')}
            unit="°C"
            subtext={weather ? 'Live sensor/forecast feed' : 'Farm baseline'}
            icon={<Thermometer className="w-5 h-5" />}
          />
          <MetricCard
            label="Relative Humidity"
            value={weather?.current ? weather.current.humidity_percent.toFixed(0) : (profile.humidity ?? '—')}
            unit="%"
            subtext="Atmospheric moisture"
            icon={<Droplets className="w-5 h-5 text-sky-600" />}
          />
          <MetricCard
            label="Seasonal Rainfall"
            value={weather?.current ? weather.current.rainfall_mm.toFixed(0) : (profile.rainfall ?? '—')}
            unit="mm"
            subtext="Available precipitation"
            icon={<CloudRain className="w-5 h-5 text-indigo-600" />}
          />
          <MetricCard
            label="Wind Speed"
            value={weather?.current ? weather.current.wind_speed_kph.toFixed(1) : '—'}
            unit="km/h"
            subtext="Surface velocity"
            icon={<Wind className="w-5 h-5 text-teal-600" />}
          />
        </div>
      </div>

      {/* Grid: Soil Chemistry & Farm Constraints */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Soil Summary */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 mb-4">
            <Layers className="w-4 h-4 text-emerald-700" />
            <span>Soil Macronutrients & Reaction</span>
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <div className="text-[11px] font-semibold text-slate-500 uppercase">Nitrogen (N)</div>
              <div className="text-xl font-bold text-slate-900 mt-1">{profile.nitrogen}</div>
              <div className="text-[10px] text-slate-400">mg/kg</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <div className="text-[11px] font-semibold text-slate-500 uppercase">Phosphorus (P)</div>
              <div className="text-xl font-bold text-slate-900 mt-1">{profile.phosphorus}</div>
              <div className="text-[10px] text-slate-400">mg/kg</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <div className="text-[11px] font-semibold text-slate-500 uppercase">Potassium (K)</div>
              <div className="text-xl font-bold text-slate-900 mt-1">{profile.potassium}</div>
              <div className="text-[10px] text-slate-400">mg/kg</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <div className="text-[11px] font-semibold text-slate-500 uppercase">Soil pH</div>
              <div className="text-xl font-bold text-emerald-800 mt-1">{profile.ph.toFixed(1)}</div>
              <div className="text-[10px] text-slate-400">
                {profile.ph < 6.0 ? 'Acidic' : profile.ph > 7.5 ? 'Alkaline' : 'Neutral'}
              </div>
            </div>
          </div>

          <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-600 flex items-center justify-between">
            <span>Configured Soil Class:</span>
            <span className="font-bold text-slate-900">{profile.yield_soil_type} Soil</span>
          </div>
        </div>

        {/* Farm Constraints & Water */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 mb-4">
            <Waves className="w-4 h-4 text-emerald-700" />
            <span>Water & Season Resource Window</span>
          </h3>

          <div className="grid grid-cols-2 gap-3 text-center">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <div className="text-[11px] font-semibold text-slate-500 uppercase">Total Water Available</div>
              <div className="text-xl font-bold text-emerald-800 mt-1">{profile.water_availability_mm}</div>
              <div className="text-[10px] text-slate-400">mm / season</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <div className="text-[11px] font-semibold text-slate-500 uppercase">Growing Window</div>
              <div className="text-xl font-bold text-slate-900 mt-1">{profile.growing_days_available}</div>
              <div className="text-[10px] text-slate-400">days available</div>
            </div>
          </div>

          <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-600 flex items-center justify-between">
            <span>Supplemental Irrigation Infrastructure:</span>
            <span className={`font-bold ${profile.irrigation_available ? 'text-emerald-700' : 'text-slate-500'}`}>
              {profile.irrigation_available ? 'Equipped (Active)' : 'Rainfed Only'}
            </span>
          </div>
        </div>
      </div>

      {/* Model Transparency Disclaimer Card */}
      <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-900 text-xs flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold">Agronomic Decision-Support Notice</p>
          <p className="text-amber-800">
            Suitability calculations enforce deterministic penalties for water, duration, and pH limits using prototype reference ranges from <code>crops.json</code>. Yield predictions are generated by the <code>NIHAL670/Crop-yield</code> Random Forest model, where Nitrogen, Phosphorus, Potassium, Humidity, and Soil_Type were synthetically generated during training and primary predictive signals derive from State, Crop, Season, Area, and Rainfall.
          </p>
        </div>
      </div>
    </div>
  );
};
