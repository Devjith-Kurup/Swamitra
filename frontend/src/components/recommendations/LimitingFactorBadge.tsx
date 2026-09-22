import React from 'react';
import { AlertCircle, AlertTriangle } from 'lucide-react';
import { LimitingFactor } from '../../types/crop';

interface LimitingFactorBadgeProps {
  factor: LimitingFactor;
}

export const LimitingFactorBadge: React.FC<LimitingFactorBadgeProps> = ({ factor }) => {
  const isCritical = factor.severity === 'critical';

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${
        isCritical
          ? 'bg-rose-50 text-rose-800 border-rose-200'
          : 'bg-amber-50 text-amber-800 border-amber-200'
      }`}
      title={factor.detail}
    >
      {isCritical ? (
        <AlertCircle className="w-3.5 h-3.5 text-rose-600 flex-shrink-0" />
      ) : (
        <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
      )}
      <span className="capitalize">{factor.factor}</span>
      <span className="text-[10px] opacity-75">({factor.severity})</span>
    </div>
  );
};
