import React from 'react';
import { CropSuitabilityResult } from '../../types/crop';

interface CropComparisonTableProps {
  candidates: CropSuitabilityResult[];
  onSelectCrop: (cropName: string) => void;
}

export const CropComparisonTable: React.FC<CropComparisonTableProps> = ({
  candidates,
  onSelectCrop,
}) => {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-slate-900">All 22 Crop Candidates Ranked</h3>
          <p className="text-xs text-slate-500">Evaluated across machine learning affinity and farm constraints</p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
            <tr>
              <th className="py-3 px-4">Rank</th>
              <th className="py-3 px-4">Crop Name</th>
              <th className="py-3 px-4">Suitability Score</th>
              <th className="py-3 px-4">Raw ML Score</th>
              <th className="py-3 px-4">Expected Yield</th>
              <th className="py-3 px-4">Limiting Constraints</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
            {candidates.map((cand, index) => {
              const suitabilityPct = Math.round(cand.suitability_score * 100);
              const mlPct = Math.round(cand.ml_score * 100);
              const isTop3 = index < 3;

              return (
                <tr
                  key={cand.crop}
                  className={`hover:bg-slate-50/80 transition-colors ${
                    isTop3 ? 'bg-emerald-50/30' : ''
                  }`}
                >
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center justify-center w-6 h-6 rounded-md text-xs font-bold ${
                        index === 0
                          ? 'bg-amber-100 text-amber-800'
                          : isTop3
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'text-slate-500'
                      }`}
                    >
                      #{index + 1}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-bold text-slate-900 capitalize text-sm">
                    {cand.crop}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            suitabilityPct >= 70
                              ? 'bg-emerald-600'
                              : suitabilityPct >= 40
                              ? 'bg-amber-500'
                              : 'bg-rose-500'
                          }`}
                          style={{ width: `${suitabilityPct}%` }}
                        />
                      </div>
                      <span className="font-bold">{suitabilityPct}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-slate-600">
                    <span>{mlPct}%</span>
                  </td>
                  <td className="py-3 px-4">
                    {cand.predicted_yield_per_ha !== undefined && cand.predicted_yield_per_ha !== null ? (
                      <span className="font-semibold text-emerald-800">
                        {cand.predicted_yield_per_ha.toFixed(2)} q/ha
                      </span>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    {cand.limiting_factors.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {cand.limiting_factors.map((f, i) => (
                          <span
                            key={i}
                            className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                              f.severity === 'critical'
                                ? 'bg-rose-100 text-rose-800'
                                : 'bg-amber-100 text-amber-800'
                            }`}
                            title={f.detail}
                          >
                            {f.factor}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-emerald-700 font-medium">None (Optimal)</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => onSelectCrop(cand.crop)}
                      className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 underline"
                    >
                      Details
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
