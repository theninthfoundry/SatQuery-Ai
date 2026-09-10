import React from 'react';
import { CRSInfo } from '../types';
import { Globe, Compass, AlertTriangle } from 'lucide-react';

interface CRSBadgeProps {
  crs: CRSInfo;
}

export const CRSBadge: React.FC<CRSBadgeProps> = ({ crs }) => {
  if (!crs.present) {
    return (
      <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-mono bg-amber-500/10 text-amber-300 border border-amber-500/20">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
        <span>No CRS (Non-Georeferenced)</span>
      </div>
    );
  }

  const isProjected = crs.type === 'projected';

  return (
    <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-md text-xs font-mono bg-space-800 border border-space-700">
      {isProjected ? (
        <Compass className="w-3.5 h-3.5 text-satblue-400" />
      ) : (
        <Globe className="w-3.5 h-3.5 text-emerald-400" />
      )}
      <span className="font-semibold text-slate-200">
        {crs.epsg ? `EPSG:${crs.epsg}` : crs.name || 'Custom CRS'}
      </span>
      <span
        className={`px-1.5 py-0.2 rounded text-[10px] uppercase font-bold ${
          isProjected
            ? 'bg-satblue-500/10 text-satblue-400 border border-satblue-500/20'
            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
        }`}
      >
        {crs.type}
      </span>
    </div>
  );
};
