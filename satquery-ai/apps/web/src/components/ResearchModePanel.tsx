'use client';

import React, { useState } from 'react';
import { Cpu, Activity, BarChart3, Database, ShieldAlert, Sparkles } from 'lucide-react';

interface ResearchModePanelProps {
  opticalStats?: { mean_spectral: number[]; water_proxy: number };
  sarStats?: { mean_sigma0_db: number; min_sigma0_db: number; max_sigma0_db: number };
  gsdMeters?: number;
  crs?: string;
}

export function ResearchModePanel({
  opticalStats = { mean_spectral: [124.5, 142.1, 108.3], water_proxy: 0.084 },
  sarStats = { mean_sigma0_db: -16.4, min_sigma0_db: -24.8, max_sigma0_db: -4.2 },
  gsdMeters = 10.0,
  crs = 'EPSG:32643 (UTM Zone 43N)',
}: ResearchModePanelProps) {
  const [activeTab, setActiveTab] = useState<'spectral' | 'radar' | 'provenance'>('spectral');

  return (
    <div className="border border-neutral-800 rounded-xl p-5 bg-neutral-900/80 shadow-2xl space-y-4 font-mono">
      <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-purple-400" />
          <h3 className="font-semibold text-neutral-100 text-sm font-sans">Remote Sensing Research & Diagnostic Console</h3>
        </div>
        <span className="text-[10px] text-purple-300 bg-purple-500/10 border border-purple-500/30 px-2 py-0.5 rounded uppercase">
          Expert Mode Active
        </span>
      </div>

      {/* Mode Sub-tabs */}
      <div className="flex items-center gap-2 border-b border-neutral-800 pb-2">
        <button
          onClick={() => setActiveTab('spectral')}
          className={`px-3 py-1 text-xs rounded transition-colors ${
            activeTab === 'spectral'
              ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
              : 'text-neutral-400 hover:text-neutral-200'
          }`}
        >
          Spectral Radiometry (MSI)
        </button>
        <button
          onClick={() => setActiveTab('radar')}
          className={`px-3 py-1 text-xs rounded transition-colors ${
            activeTab === 'radar'
              ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
              : 'text-neutral-400 hover:text-neutral-200'
          }`}
        >
          SAR Backscatter (σ⁰ dB)
        </button>
        <button
          onClick={() => setActiveTab('provenance')}
          className={`px-3 py-1 text-xs rounded transition-colors ${
            activeTab === 'provenance'
              ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
              : 'text-neutral-400 hover:text-neutral-200'
          }`}
        >
          CRS & Spatial GSD
        </button>
      </div>

      {/* Tab 1: Spectral Radiometry */}
      {activeTab === 'spectral' && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="border border-neutral-800 rounded p-3 bg-neutral-950/60">
            <p className="text-[10px] text-neutral-500 uppercase">Red Mean (Band 4)</p>
            <p className="text-sm font-semibold text-neutral-200 mt-1">{opticalStats.mean_spectral[0]} DN</p>
          </div>
          <div className="border border-neutral-800 rounded p-3 bg-neutral-950/60">
            <p className="text-[10px] text-neutral-500 uppercase">Green Mean (Band 3)</p>
            <p className="text-sm font-semibold text-neutral-200 mt-1">{opticalStats.mean_spectral[1]} DN</p>
          </div>
          <div className="border border-neutral-800 rounded p-3 bg-neutral-950/60">
            <p className="text-[10px] text-neutral-500 uppercase">Blue Mean (Band 2)</p>
            <p className="text-sm font-semibold text-neutral-200 mt-1">{opticalStats.mean_spectral[2]} DN</p>
          </div>
        </div>
      )}

      {/* Tab 2: SAR Backscatter */}
      {activeTab === 'radar' && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="border border-neutral-800 rounded p-3 bg-neutral-950/60">
            <p className="text-[10px] text-neutral-500 uppercase">Mean Radar Backscatter</p>
            <p className="text-sm font-semibold text-cyan-300 mt-1">{sarStats.mean_sigma0_db} dB</p>
          </div>
          <div className="border border-neutral-800 rounded p-3 bg-neutral-950/60">
            <p className="text-[10px] text-neutral-500 uppercase">Min Backscatter (Specular)</p>
            <p className="text-sm font-semibold text-neutral-200 mt-1">{sarStats.min_sigma0_db} dB</p>
          </div>
          <div className="border border-neutral-800 rounded p-3 bg-neutral-950/60">
            <p className="text-[10px] text-neutral-500 uppercase">Max Backscatter (Double Bounce)</p>
            <p className="text-sm font-semibold text-amber-300 mt-1">{sarStats.max_sigma0_db} dB</p>
          </div>
        </div>
      )}

      {/* Tab 3: CRS & GSD */}
      {activeTab === 'provenance' && (
        <div className="space-y-2 text-xs">
          <div className="flex items-center justify-between border border-neutral-800 rounded p-2.5 bg-neutral-950/60">
            <span className="text-neutral-400">Projected Coordinate Reference System</span>
            <span className="text-neutral-200 font-semibold">{crs}</span>
          </div>
          <div className="flex items-center justify-between border border-neutral-800 rounded p-2.5 bg-neutral-950/60">
            <span className="text-neutral-400">Ground Sampling Distance (GSD)</span>
            <span className="text-cyan-300 font-semibold">{gsdMeters} m / pixel</span>
          </div>
        </div>
      )}
    </div>
  );
}
