import React from 'react';
import { ShieldAlert, Cpu } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-slate-200 mt-auto py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-emerald-700" />
            <span>
              <strong>SWAMITRA Dual-ML Engine:</strong> Crop Recommendation (<code>Sheshank2609</code>) + Yield Regressor (<code>NIHAL670</code>)
            </span>
          </div>

          <div className="flex items-center gap-1.5 text-slate-600 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-lg">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-700 flex-shrink-0" />
            <span>Agronomic advice based on prototype knowledge base; regional field testing required for production decisions.</span>
          </div>

          <p className="text-slate-400">
            &copy; {new Date().getFullYear()} SWAMITRA AI. Open-source agricultural decision support.
          </p>
        </div>
      </div>
    </footer>
  );
};
