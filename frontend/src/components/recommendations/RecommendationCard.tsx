import React from 'react';
import { CheckCircle2, TrendingUp, Scale, ArrowRight } from 'lucide-react';
import { CropSuitabilityResult } from '../../types/crop';
import { LimitingFactorBadge } from './LimitingFactorBadge';
import { getCropImageUrl } from '../../utils/cropImages';

interface RecommendationCardProps {
  cropResult: CropSuitabilityResult;
  rank: number;
  onSelectCrop?: (cropName: string) => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  cropResult,
  rank,
  onSelectCrop,
}) => {
  const suitabilityPct = Math.round(cropResult.suitability_score * 100);
  const mlScorePct = Math.round(cropResult.ml_score * 100);

  const getRankBadgeStyle = (r: number) => {
    switch (r) {
      case 1:
        return 'bg-amber-100 text-amber-900 border-amber-300 font-extrabold';
      case 2:
        return 'bg-slate-200 text-slate-800 border-slate-300 font-bold';
      case 3:
        return 'bg-amber-50 text-amber-800 border-amber-200 font-semibold';
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  return (
    <div className="glass-card hover:-translate-y-1 transition-all duration-300 p-5 flex flex-col justify-between h-full">
      <div>
        {/* Crop Image Header */}
        <div className="relative h-36 w-full mb-4 rounded-xl overflow-hidden shadow-sm">
          <img 
            src={getCropImageUrl(cropResult.crop)} 
            alt={cropResult.crop}
            className="w-full h-full object-cover transition-transform duration-700 hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 via-slate-900/20 to-transparent"></div>
          <div className="absolute bottom-3 left-3 flex items-center gap-2">
            <span
              className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs border shadow-sm ${getRankBadgeStyle(
                rank
              )}`}
            >
              #{rank}
            </span>
            <div>
              <h3 className="text-xl font-black text-white capitalize tracking-tight drop-shadow-md">
                {cropResult.crop}
              </h3>
            </div>
          </div>
          <div className="absolute top-3 right-3">
            <div className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-md bg-white/90 text-emerald-800 shadow-sm backdrop-blur-sm">
              {suitabilityPct >= 80 ? 'Excellent Match' : suitabilityPct >= 60 ? 'Good Match' : 'Fair Match'}
            </div>
          </div>
        </div>



        {/* Expected Yield section (if available from backend) */}
        {cropResult.predicted_yield_per_ha !== undefined && cropResult.predicted_yield_per_ha !== null && (
          <div className="mt-4 p-3 rounded-xl bg-emerald-50/70 border border-emerald-200 flex items-center justify-between">
            <div>
              <div className="text-xs font-medium text-emerald-800 uppercase tracking-wider">Expected Yield</div>
              <div className="text-lg font-bold text-emerald-950">
                {cropResult.predicted_yield_per_ha.toFixed(2)}{' '}
                <span className="text-xs font-normal text-emerald-700">{cropResult.yield_unit || 'quintal/ha'}</span>
              </div>
            </div>
            {cropResult.estimated_total_production !== undefined && cropResult.estimated_total_production !== null && (
              <div className="text-right">
                <div className="text-xs font-medium text-emerald-800 uppercase tracking-wider">Est. Production</div>
                <div className="text-lg font-bold text-emerald-950">
                  {cropResult.estimated_total_production.toFixed(1)}{' '}
                  <span className="text-xs font-normal text-emerald-700">quintal</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Limiting Factors */}
        <div className="mt-4">
          <div className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
            Things to watch out for
          </div>
          {cropResult.limiting_factors.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {cropResult.limiting_factors.map((factor, idx) => (
                <LimitingFactorBadge key={idx} factor={factor} />
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-emerald-700 font-medium">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Looks good! No major issues.</span>
            </div>
          )}
        </div>

        {/* Explanation */}
        <p className="mt-3 text-xs text-slate-600 leading-relaxed italic bg-slate-50/50 p-2.5 rounded-lg border border-slate-100">
          "{cropResult.explanation}"
        </p>
      </div>

      {/* Card Footer Button */}
      {onSelectCrop && (
        <button
          onClick={() => onSelectCrop(cropResult.crop)}
          className="mt-5 w-full flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-slate-900 text-white text-xs font-semibold hover:bg-emerald-800 transition-colors shadow-xs"
        >
          <span>See Details</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};
