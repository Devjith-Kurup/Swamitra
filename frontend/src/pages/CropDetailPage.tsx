import React, { useState } from 'react';
import {
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  Calculator,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useFarm } from '../context/FarmContext';
import { TabId } from '../components/layout/Navbar';
import { LimitingFactorBadge } from '../components/recommendations/LimitingFactorBadge';

interface CropDetailPageProps {
  selectedCrop: string;
  onSelectCrop: (cropName: string) => void;
  onNavigate: (tab: TabId) => void;
}

export const CropDetailPage: React.FC<CropDetailPageProps> = ({
  selectedCrop,
  onSelectCrop,
  onNavigate,
}) => {
  const { recommendations, profile } = useFarm();
  const [simulatedArea, setSimulatedArea] = useState<number>(profile?.farm_area_ha || 2.5);

  const allCrops = recommendations?.all_candidates || [];
  const currentCropResult = allCrops.find(
    (c) => c.crop.toLowerCase() === selectedCrop.toLowerCase()
  ) || recommendations?.top_recommendations?.[0] || allCrops[0];

  if (!currentCropResult) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center">
        <h2 className="text-xl font-bold text-slate-900">No Crop Data Available</h2>
        <p className="text-sm text-slate-600 mt-2">
          Run farm analysis first to view detailed agronomic breakdowns.
        </p>
        <button
          onClick={() => onNavigate('setup')}
          className="mt-6 px-5 py-2.5 rounded-xl bg-emerald-700 text-white text-xs font-bold hover:bg-emerald-800 transition-colors"
        >
          Go to Farm Setup
        </button>
      </div>
    );
  }

  const suitabilityPct = Math.round(currentCropResult.suitability_score * 100);
  const mlScorePct = Math.round(currentCropResult.ml_score * 100);

  // Scaled production calculation
  const yieldPerHa = currentCropResult.predicted_yield_per_ha ?? 0;
  const scaledProduction = Math.round(yieldPerHa * simulatedArea * 10) / 10;

  // Chart data: Normalizing macronutrients for comparative visualization
  const soilChartData = profile ? [
    {
      parameter: 'Nitrogen',
      Farm: profile.nitrogen,
      BaselineRef: 100,
      unit: 'mg/kg',
    },
    {
      parameter: 'Phosphorus',
      Farm: profile.phosphorus,
      BaselineRef: 50,
      unit: 'mg/kg',
    },
    {
      parameter: 'Potassium',
      Farm: profile.potassium,
      BaselineRef: 50,
      unit: 'mg/kg',
    },
    {
      parameter: 'pH (x10)',
      Farm: profile.ph * 10,
      BaselineRef: 65,
      unit: 'pH x10',
    },
  ] : [];

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-16">
      {/* Top Bar with Back & Dropdown Selector */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <button
          onClick={() => onNavigate('recommendations')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Recommendations</span>
        </button>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <label className="text-xs font-semibold text-slate-500 whitespace-nowrap">Switch Crop:</label>
          <select
            value={currentCropResult.crop}
            onChange={(e) => onSelectCrop(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 capitalize"
          >
            {allCrops.map((c) => (
              <option key={c.crop} value={c.crop}>
                {c.crop} ({Math.round(c.suitability_score * 100)}% Match)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Hero Header Card */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold uppercase tracking-wider">
              Agronomic Evaluation
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-slate-900 capitalize tracking-tight mt-2">
              {currentCropResult.crop}
            </h1>
            <p className="text-sm text-slate-600 mt-2 max-w-2xl leading-relaxed italic bg-slate-50 p-3 rounded-xl border border-slate-100">
              "{currentCropResult.explanation}"
            </p>
          </div>

          <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-2xl border border-slate-200/80">
            <div className="text-center px-3 border-r border-slate-200">
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Suitability</div>
              <div className="text-3xl font-black text-emerald-700">{suitabilityPct}%</div>
              <div className="text-[10px] text-slate-400">Farm-Adjusted</div>
            </div>
            <div className="text-center px-3">
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Raw ML Score</div>
              <div className="text-3xl font-black text-slate-800">{mlScorePct}%</div>
              <div className="text-[10px] text-slate-400">Model Probability</div>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Limiting Factors & Yield Scaler */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Limiting Factors Deep-Dive */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <AlertCircle className="w-4 h-4 text-emerald-700" />
            <span>Limiting Constraints & Penalties</span>
          </h2>

          {currentCropResult.limiting_factors.length > 0 ? (
            <div className="space-y-3">
              {currentCropResult.limiting_factors.map((f, i) => (
                <div
                  key={i}
                  className={`p-3.5 rounded-xl border ${
                    f.severity === 'critical'
                      ? 'bg-rose-50/60 border-rose-200 text-rose-950'
                      : 'bg-amber-50/60 border-amber-200 text-amber-950'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs capitalize flex items-center gap-1.5">
                      <LimitingFactorBadge factor={f} />
                    </span>
                  </div>
                  <p className="text-xs mt-1.5 leading-relaxed">{f.detail}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 text-center text-emerald-800 bg-emerald-50/50 rounded-xl border border-emerald-100">
              <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
              <div className="font-bold text-sm">No Limiting Constraints Detected</div>
              <p className="text-xs text-emerald-700 mt-1">
                This crop matches your water availability, growing duration, soil pH, and climate conditions without penalty.
              </p>
            </div>
          )}
        </div>

        {/* Expected Yield & Production Calculator */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <Calculator className="w-4 h-4 text-emerald-700" />
            <span>Yield & Production Scaling</span>
          </h2>

          {yieldPerHa > 0 ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-100">
                  <div className="text-[11px] font-semibold text-emerald-800 uppercase">Predicted Yield</div>
                  <div className="text-2xl font-black text-emerald-950 mt-1">
                    {yieldPerHa.toFixed(2)}
                  </div>
                  <div className="text-[10px] text-emerald-700">quintal / hectare</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase">Est. Total Harvest</div>
                  <div className="text-2xl font-black text-slate-900 mt-1">
                    {scaledProduction.toFixed(1)}
                  </div>
                  <div className="text-[10px] text-slate-500">quintal total</div>
                </div>
              </div>

              {/* Area Interactive Slider */}
              <div className="pt-2">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-700 mb-1.5">
                  <span>Simulate Cultivated Land Area:</span>
                  <span className="font-black text-emerald-800 text-sm">{simulatedArea} ha</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="20"
                  step="0.5"
                  value={simulatedArea}
                  onChange={(e) => setSimulatedArea(parseFloat(e.target.value))}
                  className="w-full accent-emerald-700"
                />
                <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                  <span>0.5 ha</span>
                  <span>10 ha</span>
                  <span>20 ha</span>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-[11px] text-slate-500 space-y-1">
                <div>• Formula: Estimated Production = Yield × Area</div>
                <div>• Model: <code>NIHAL670/Crop-yield</code> Random Forest Regressor</div>
              </div>
            </div>
          ) : (
            <div className="p-6 text-center text-slate-500 bg-slate-50 rounded-xl">
              Yield model predictions not populated for this candidate.
            </div>
          )}
        </div>
      </div>

      {/* Chart: Macronutrient Baseline vs Farm Inputs */}
      {soilChartData.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">Farm Soil Parameters vs General Agronomic Reference</h2>
            <p className="text-xs text-slate-500">
              Visualizing how your farm's nitrogen, phosphorus, potassium, and pH compare to nominal agricultural references
            </p>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={soilChartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="parameter" tick={{ fontSize: 12, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 12, fill: '#64748b' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderColor: '#e2e8f0',
                    borderRadius: '0.75rem',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="Farm" fill="#047857" name="Your Farm Measurement" radius={[4, 4, 0, 0]} />
                <Bar dataKey="BaselineRef" fill="#94a3b8" name="General Agronomic Nominal" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};
