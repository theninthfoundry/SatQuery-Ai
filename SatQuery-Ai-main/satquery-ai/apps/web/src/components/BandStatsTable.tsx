import React from 'react';
import { BandStatistics } from '../types';
import { Layers } from 'lucide-react';

interface BandStatsTableProps {
  bands: BandStatistics[];
}

export const BandStatsTable: React.FC<BandStatsTableProps> = ({ bands }) => {
  if (!bands || bands.length === 0) return null;

  return (
    <div className="space-y-2">
      <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
        <Layers className="w-3.5 h-3.5 text-satblue-400" />
        <span>Band Radiometry & Statistics ({bands.length} {bands.length === 1 ? 'Band' : 'Bands'})</span>
      </div>

      <div className="overflow-x-auto border border-space-700/80 rounded-lg bg-space-950/60">
        <table className="min-w-full divide-y divide-space-700/60 text-xs font-mono">
          <thead>
            <tr className="bg-space-900/80 text-slate-400 text-left">
              <th className="px-3 py-2 font-medium">Band</th>
              <th className="px-3 py-2 font-medium">Dtype</th>
              <th className="px-3 py-2 font-medium">Min</th>
              <th className="px-3 py-2 font-medium">Max</th>
              <th className="px-3 py-2 font-medium">Mean</th>
              <th className="px-3 py-2 font-medium">Std Dev</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-space-800 text-slate-300">
            {bands.map((b) => (
              <tr key={b.band_index} className="hover:bg-space-800/40 transition-colors">
                <td className="px-3 py-1.5 font-semibold text-satblue-400">Band {b.band_index}</td>
                <td className="px-3 py-1.5 text-slate-400">{b.dtype}</td>
                <td className="px-3 py-1.5">{b.min}</td>
                <td className="px-3 py-1.5">{b.max}</td>
                <td className="px-3 py-1.5">{b.mean}</td>
                <td className="px-3 py-1.5 text-slate-400">{b.std ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
