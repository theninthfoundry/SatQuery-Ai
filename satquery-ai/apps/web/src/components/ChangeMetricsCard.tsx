import React from 'react';
import { ChangeAnalysisResult } from '../types';
import { Layers, Activity, MapPin, TrendingUp, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface ChangeMetricsCardProps {
  result: ChangeAnalysisResult;
}

export const ChangeMetricsCard: React.FC<ChangeMetricsCardProps> = ({ result }) => {
  return (
    <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 space-y-4 shadow-lg">
      <div className="flex items-center justify-between pb-3 border-b border-space-800">
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-4 h-4 text-rose-400" />
          <h3 className="text-sm font-bold text-slate-100">Quantified Change Analysis</h3>
        </div>
        <div>
          {result.is_trained ? (
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="w-3 h-3" />
              <span>Trained Checkpoint</span>
            </span>
          ) : (
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/20">
              <AlertTriangle className="w-3 h-3 text-amber-400" />
              <span>Siamese Architecture Active</span>
            </span>
          )}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-space-950/60 p-3 rounded-lg border border-space-800">
          <span className="text-[11px] text-slate-400 font-mono block mb-1">Surface Change</span>
          <span className="text-base font-bold font-mono text-rose-400">
            {result.change_percent}%
          </span>
        </div>

        <div className="bg-space-950/60 p-3 rounded-lg border border-space-800">
          <span className="text-[11px] text-slate-400 font-mono block mb-1">Total Area Changed</span>
          <span className="text-base font-bold font-mono text-slate-200">
            {result.total_area_m2.toLocaleString()} m²
          </span>
        </div>

        <div className="bg-space-950/60 p-3 rounded-lg border border-space-800">
          <span className="text-[11px] text-slate-400 font-mono block mb-1">Ground Area (Hectares)</span>
          <span className="text-base font-bold font-mono text-emerald-400">
            {result.total_area_ha} ha
          </span>
        </div>

        <div className="bg-space-950/60 p-3 rounded-lg border border-space-800">
          <span className="text-[11px] text-slate-400 font-mono block mb-1">Distinct Clusters</span>
          <span className="text-base font-bold font-mono text-satblue-400">
            {result.cluster_count} {result.cluster_count === 1 ? 'Cluster' : 'Clusters'}
          </span>
        </div>
      </div>
    </div>
  );
};
