import React, { useState } from 'react';
import {
  Sliders,
  Play,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
  Equal,
} from 'lucide-react';
import { useFarm } from '../context/FarmContext';
import { api, ApiError } from '../services/api';
import { RecommendationRequest, RecommendationResponse } from '../types/crop';
import { LimitingFactorBadge } from '../components/recommendations/LimitingFactorBadge';
import { TabId } from '../components/layout/Navbar';

interface SimulatorPageProps {
  onNavigate: (tab: TabId) => void;
  onSelectCrop: (cropName: string) => void;
}

export const SimulatorPage: React.FC<SimulatorPageProps> = ({ onNavigate, onSelectCrop }) => {
  const { profile, recommendations: baselineRecommendations } = useFarm();

  // Scenario variables (only variables supported by backend)
  const [scenarioWater, setScenarioWater] = useState<number>(profile?.water_availability_mm ?? 800);
  const [scenarioDuration, setScenarioDuration] = useState<number>(profile?.growing_days_available ?? 120);
  const [scenarioRainfall, setScenarioRainfall] = useState<number>(profile?.rainfall ?? 300);
  const [scenarioTemperature, setScenarioTemperature] = useState<number>(profile?.temperature ?? 26);
  const [scenarioPh, setScenarioPh] = useState<number>(profile?.ph ?? 6.5);
  const [scenarioIrrigation, setScenarioIrrigation] = useState<boolean>(profile?.irrigation_available ?? true);

  const [scenarioResult, setScenarioResult] = useState<RecommendationResponse | null>(null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simError, setSimError] = useState<string | null>(null);

  const runScenario = async () => {
    if (!profile) return;
    setIsSimulating(true);
    setSimError(null);

    try {
      const request: RecommendationRequest = {
        nitrogen: profile.nitrogen,
        phosphorus: profile.phosphorus,
        potassium: profile.potassium,
        ph: scenarioPh,
        temperature: scenarioTemperature,
        humidity: profile.humidity ?? 70,
        rainfall: scenarioRainfall,
        latitude: profile.latitude,
        longitude: profile.longitude,
        farm_constraints: {
          water_availability_mm: scenarioWater,
          growing_days_available: scenarioDuration,
          farm_area_ha: profile.farm_area_ha,
          irrigation_available: scenarioIrrigation,
        },
        include_yield: true,
        yield_state: profile.yield_state,
        yield_season: profile.yield_season,
        yield_soil_type: profile.yield_soil_type,
      };

      const result = await api.getCropRecommendations(request);
      setScenarioResult(result);
    } catch (err: unknown) {
      setSimError(err instanceof ApiError ? err.message : 'Scenario evaluation failed.');
    } finally {
      setIsSimulating(false);
    }
  };

  const resetToBaseline = () => {
    if (!profile) return;
    setScenarioWater(profile.water_availability_mm);
    setScenarioDuration(profile.growing_days_available);
    setScenarioRainfall(profile.rainfall ?? 300);
    setScenarioTemperature(profile.temperature ?? 26);
    setScenarioPh(profile.ph);
    setScenarioIrrigation(profile.irrigation_available);
    setScenarioResult(null);
    setSimError(null);
  };

  if (!profile || !baselineRecommendations) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center">
        <h2 className="text-xl font-bold text-slate-900">Setup Required for Scenario Simulation</h2>
        <p className="text-sm text-slate-600 mt-2">
          Configure and analyze your farm baseline profile before running what-if scenarios.
        </p>
        <button
          onClick={() => onNavigate('setup')}
          className="mt-6 px-5 py-2.5 rounded-xl bg-emerald-700 text-white text-xs font-bold hover:bg-emerald-800 transition-colors shadow-xs"
        >
          Configure Farm Baseline
        </button>
      </div>
    );
  }

  const baselineTop = baselineRecommendations.top_recommendations[0];
  const scenarioTop = scenarioResult ? scenarioResult.top_recommendations[0] : null;

  // Comparison metrics
  const suitabilityDelta = scenarioTop
    ? Math.round((scenarioTop.suitability_score - baselineTop.suitability_score) * 100)
    : 0;

  const yieldDelta =
    scenarioTop?.predicted_yield_per_ha && baselineTop.predicted_yield_per_ha
      ? Math.round((scenarioTop.predicted_yield_per_ha - baselineTop.predicted_yield_per_ha) * 100) / 100
      : null;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-16">
      {/* Page Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-800 text-xs font-bold uppercase tracking-wider">
          <Sliders className="w-3.5 h-3.5 text-emerald-700" />
          <span>Model-Based Scenario Analysis</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-black text-slate-900 mt-1 tracking-tight">
          What-If Farm & Climate Simulator
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Adjust water availability, season length, precipitation, and soil pH to see how suitability rankings and yield projections shift.
        </p>
      </div>

      {/* Prominent Scientific Disclaimer Banner */}
      <div className="p-4 rounded-2xl bg-amber-50/90 border border-amber-200 text-amber-950 text-xs space-y-1.5 shadow-xs">
        <div className="flex items-center gap-2 font-bold text-amber-900">
          <ShieldAlert className="w-4 h-4 text-amber-700" />
          <span>Methodology Notice: Model-Based Scenario Analysis</span>
        </div>
        <p className="text-amber-900/90 leading-relaxed">
          This simulator evaluates real SWAMITRA backend constraints and statistical ML models. It is <strong>not a scientifically exact biological crop-growth simulation</strong>. Variables like water availability and duration directly modulate farm suitability scores via deterministic agronomic thresholds; yield predictions reflect the statistical response of the Random Forest regressor.
        </p>
      </div>

      {/* Simulator Controls Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-emerald-700" />
            <span>Scenario Parameters</span>
          </h2>

          <button
            onClick={resetToBaseline}
            className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1 font-semibold"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset to Baseline</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Water Availability Slider */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <span>Water Availability (Rain + Irrigation):</span>
              <span className="font-bold text-emerald-800 text-sm">{scenarioWater} mm</span>
            </div>
            <input
              type="range"
              min="100"
              max="2500"
              step="50"
              value={scenarioWater}
              onChange={(e) => setScenarioWater(parseFloat(e.target.value))}
              className="w-full accent-emerald-700"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>Severe Drought (100mm)</span>
              <span>Baseline: {profile.water_availability_mm}mm</span>
              <span>Abundant (2500mm)</span>
            </div>
          </div>

          {/* Growing Duration Slider */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <span>Available Growing Days:</span>
              <span className="font-bold text-emerald-800 text-sm">{scenarioDuration} days</span>
            </div>
            <input
              type="range"
              min="45"
              max="240"
              step="5"
              value={scenarioDuration}
              onChange={(e) => setScenarioDuration(parseInt(e.target.value))}
              className="w-full accent-emerald-700"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>Short (45d)</span>
              <span>Baseline: {profile.growing_days_available}d</span>
              <span>Long (240d)</span>
            </div>
          </div>

          {/* Soil pH Slider */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <span>Soil pH Reaction:</span>
              <span className="font-bold text-emerald-800 text-sm">{scenarioPh.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="4.0"
              max="9.0"
              step="0.1"
              value={scenarioPh}
              onChange={(e) => setScenarioPh(parseFloat(e.target.value))}
              className="w-full accent-emerald-700"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>Acidic (4.0)</span>
              <span>Baseline: {profile.ph.toFixed(1)}</span>
              <span>Alkaline (9.0)</span>
            </div>
          </div>

          {/* Seasonal Rainfall */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <span>Seasonal Precipitation:</span>
              <span className="font-bold text-emerald-800 text-sm">{scenarioRainfall} mm</span>
            </div>
            <input
              type="range"
              min="50"
              max="2000"
              step="50"
              value={scenarioRainfall}
              onChange={(e) => setScenarioRainfall(parseFloat(e.target.value))}
              className="w-full accent-emerald-700"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>Dry (50mm)</span>
              <span>High Monsoon (2000mm)</span>
            </div>
          </div>

          {/* Temperature Slider */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <span>Mean Temperature:</span>
              <span className="font-bold text-emerald-800 text-sm">{scenarioTemperature}°C</span>
            </div>
            <input
              type="range"
              min="12"
              max="45"
              step="1"
              value={scenarioTemperature}
              onChange={(e) => setScenarioTemperature(parseFloat(e.target.value))}
              className="w-full accent-emerald-700"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>Cool (12°C)</span>
              <span>Hot (45°C)</span>
            </div>
          </div>

          {/* Irrigation Toggle */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200">
            <div>
              <div className="text-xs font-bold text-slate-800">Supplemental Irrigation</div>
              <div className="text-[10px] text-slate-500">Drip/Canal availability</div>
            </div>
            <input
              type="checkbox"
              checked={scenarioIrrigation}
              onChange={(e) => setScenarioIrrigation(e.target.checked)}
              className="w-4 h-4 text-emerald-700 rounded focus:ring-emerald-500"
            />
          </div>
        </div>

        <div className="flex items-center justify-end pt-2">
          <button
            type="button"
            onClick={runScenario}
            disabled={isSimulating}
            className="px-6 py-3 rounded-xl bg-emerald-700 text-white font-bold text-xs hover:bg-emerald-800 transition-colors shadow-sm flex items-center gap-2 disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-white" />
            <span>{isSimulating ? 'Evaluating Scenario...' : 'Execute Scenario Analysis'}</span>
          </button>
        </div>
      </div>

      {simError && <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">{simError}</div>}

      {/* Side-by-Side Comparison: CURRENT vs SCENARIO */}
      {scenarioResult && scenarioTop && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900">Scenario Evaluation Comparison</h2>
            <div className="text-xs text-slate-500">
              Primary crop: <strong>{baselineTop.crop}</strong> → <strong>{scenarioTop.crop}</strong>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* CURRENT BASELINE CARD */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Current Farm Baseline
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                  Actual Farm Setup
                </span>
              </div>

              <div>
                <h3 className="text-2xl font-black text-slate-900 capitalize">{baselineTop.crop}</h3>
                <p className="text-xs text-slate-500 mt-1 italic">"{baselineTop.explanation}"</p>
              </div>

              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase">Suitability</div>
                  <div className="text-2xl font-black text-slate-900 mt-0.5">
                    {Math.round(baselineTop.suitability_score * 100)}%
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase">Expected Yield</div>
                  <div className="text-2xl font-black text-slate-900 mt-0.5">
                    {baselineTop.predicted_yield_per_ha ? `${baselineTop.predicted_yield_per_ha.toFixed(1)}` : '—'}
                    <span className="text-xs font-normal text-slate-400"> q/ha</span>
                  </div>
                </div>
              </div>

              <div>
                <div className="text-xs font-semibold text-slate-600 mb-1">Active Limiting Constraints:</div>
                {baselineTop.limiting_factors.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {baselineTop.limiting_factors.map((f, i) => (
                      <LimitingFactorBadge key={i} factor={f} />
                    ))}
                  </div>
                ) : (
                  <span className="text-xs text-emerald-700">None</span>
                )}
              </div>
            </div>

            {/* SCENARIO CARD */}
            <div className="bg-white rounded-2xl border-2 border-emerald-600/70 p-6 shadow-md space-y-4 relative">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Simulated Scenario</span>
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                  What-If Projection
                </span>
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-2xl font-black text-emerald-950 capitalize">{scenarioTop.crop}</h3>
                  {scenarioTop.crop !== baselineTop.crop && (
                    <span className="text-xs font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800">
                      Crop Choice Shifted
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-1 italic">"{scenarioTop.explanation}"</p>
              </div>

              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200">
                  <div className="text-[10px] font-semibold text-emerald-800 uppercase">Suitability</div>
                  <div className="text-2xl font-black text-emerald-950 mt-0.5 flex items-center justify-center gap-1">
                    <span>{Math.round(scenarioTop.suitability_score * 100)}%</span>
                    {suitabilityDelta > 0 ? (
                      <span className="text-xs font-bold text-emerald-600 flex items-center">
                        <ArrowUpRight className="w-3 h-3" />+{suitabilityDelta}%
                      </span>
                    ) : suitabilityDelta < 0 ? (
                      <span className="text-xs font-bold text-rose-600 flex items-center">
                        <ArrowDownRight className="w-3 h-3" />{suitabilityDelta}%
                      </span>
                    ) : (
                      <span className="text-xs text-slate-400 flex items-center">
                        <Equal className="w-3 h-3" />0%
                      </span>
                    )}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200">
                  <div className="text-[10px] font-semibold text-emerald-800 uppercase">Expected Yield</div>
                  <div className="text-2xl font-black text-emerald-950 mt-0.5 flex items-center justify-center gap-1">
                    <span>{scenarioTop.predicted_yield_per_ha ? `${scenarioTop.predicted_yield_per_ha.toFixed(1)}` : '—'}</span>
                    {yieldDelta !== null && yieldDelta !== 0 && (
                      <span className={`text-xs font-bold ${yieldDelta > 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                        ({yieldDelta > 0 ? `+${yieldDelta}` : yieldDelta})
                      </span>
                    )}
                    <span className="text-xs font-normal text-emerald-700"> q/ha</span>
                  </div>
                </div>
              </div>

              <div>
                <div className="text-xs font-semibold text-slate-600 mb-1">Scenario Constraints:</div>
                {scenarioTop.limiting_factors.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {scenarioTop.limiting_factors.map((f, i) => (
                      <LimitingFactorBadge key={i} factor={f} />
                    ))}
                  </div>
                ) : (
                  <span className="text-xs text-emerald-700">None (Fully Compatible)</span>
                )}
              </div>
            </div>
          </div>

          {/* Top 3 Scenario Shift Table */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 mb-3">Top 3 Recommended Crops Under This Scenario</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {scenarioResult.top_recommendations.map((c, i) => (
                <div
                  key={c.crop}
                  onClick={() => {
                    onSelectCrop(c.crop);
                    onNavigate('details');
                  }}
                  className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between hover:bg-emerald-50/50 hover:border-emerald-200 cursor-pointer transition-all"
                >
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase">#{i + 1} Candidate</span>
                    <div className="font-bold text-sm capitalize text-slate-900">{c.crop}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-black text-emerald-700">
                      {Math.round(c.suitability_score * 100)}%
                    </div>
                    {c.predicted_yield_per_ha && (
                      <div className="text-[10px] text-slate-500">{c.predicted_yield_per_ha.toFixed(1)} q/ha</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
