import React, { useState } from 'react';
import { Sparkles, ShieldAlert, RotateCcw, AlertTriangle } from 'lucide-react';
import { useFarm } from '../context/FarmContext';
import { RecommendationCard } from '../components/recommendations/RecommendationCard';
import { CropComparisonTable } from '../components/recommendations/CropComparisonTable';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { TabId } from '../components/layout/Navbar';

interface RecommendationsPageProps {
  onNavigate: (tab: TabId) => void;
  onSelectCrop: (cropName: string) => void;
}

export const RecommendationsPage: React.FC<RecommendationsPageProps> = ({
  onNavigate,
  onSelectCrop,
}) => {
  const { recommendations, profile, isLoading, loadingMessage, analyzeFarm } = useFarm();
  const [searchTerm, setSearchTerm] = useState('');

  if (isLoading) {
    return <LoadingSpinner message={loadingMessage || 'Evaluating farm suitability & predicting yield...'} fullScreen />;
  }

  if (!recommendations || recommendations.top_recommendations.length === 0) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center">
        <div className="w-16 h-16 rounded-2xl bg-amber-100 text-amber-800 flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900">No Recommendations Available</h2>
        <p className="text-sm text-slate-600 mt-2 max-w-md mx-auto">
          {profile
            ? 'Your farm profile is saved, but has not yet been analyzed against the crop recommendation models.'
            : 'Please set up your farm profile first to generate farm-aware crop recommendations.'}
        </p>
        <div className="mt-6 flex justify-center gap-3">
          {profile ? (
            <button
              onClick={() => analyzeFarm()}
              className="px-5 py-2.5 rounded-xl bg-emerald-700 text-white text-xs font-bold hover:bg-emerald-800 transition-colors shadow-xs"
            >
              Analyze Farm Now
            </button>
          ) : (
            <button
              onClick={() => onNavigate('setup')}
              className="px-5 py-2.5 rounded-xl bg-emerald-700 text-white text-xs font-bold hover:bg-emerald-800 transition-colors shadow-xs"
            >
              Go to Farm Setup
            </button>
          )}
        </div>
      </div>
    );
  }

  const { top_recommendations, all_candidates, metadata } = recommendations;

  const filteredCandidates = all_candidates.filter((c) =>
    c.crop.toLowerCase().includes(searchTerm.toLowerCase().trim())
  );

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-800 uppercase tracking-wider">
            <Sparkles className="w-4 h-4 text-emerald-700" />
            <span>Your Results</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 mt-1 tracking-tight">
            Best Crops for Your Farm
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Evaluated for <strong>{profile?.name || profile?.locationName}</strong> ({profile?.farm_area_ha} ha) •{' '}
            {profile?.yield_state} ({profile?.yield_season})
          </p>
        </div>

        <button
          onClick={() => analyzeFarm()}
          className="px-4 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition-colors flex items-center gap-1.5 shadow-xs"
        >
          <RotateCcw className="w-3.5 h-3.5 text-emerald-700" />
          <span>Re-Evaluate</span>
        </button>
      </div>



      {/* Top 3 Recommendation Cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Top 3 Recommended Crops</h2>
            <p className="text-xs text-slate-500">
              The absolute best choices for your region and resources.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          {top_recommendations.map((rec, index) => (
            <RecommendationCard
              key={rec.crop}
              cropResult={rec}
              rank={index + 1}
              onSelectCrop={(cropName) => {
                onSelectCrop(cropName);
                onNavigate('details');
              }}
            />
          ))}
        </div>
      </div>

      {/* All Candidates Comparison Table */}
      <div className="space-y-3 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900">All Other Crops</h2>
            <p className="text-xs text-slate-500">
              Search and compare other crops
            </p>
          </div>

          <div className="w-full sm:w-64">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search crop candidate..."
              className="w-full px-3 py-1.5 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>

        <CropComparisonTable
          candidates={filteredCandidates}
          onSelectCrop={(cropName) => {
            onSelectCrop(cropName);
            onNavigate('details');
          }}
        />
      </div>
    </div>
  );
};
