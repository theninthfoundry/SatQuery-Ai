import React from 'react';
import { HealthResponse } from '../types';
import { Satellite, Cpu, Activity, ShieldCheck } from 'lucide-react';

interface HeaderProps {
  health: HealthResponse | null;
}

export const Header: React.FC<HeaderProps> = ({ health }) => {
  const isOnline = health?.status === 'ok';
  const hasGpu = !!health?.hardware?.gpu;
  const gpuName = health?.hardware?.gpu?.name || 'CPU Mode';
  const vramTotal = health?.hardware?.gpu?.total_vram_mb
    ? `${(health.hardware.gpu.total_vram_mb / 1024).toFixed(1)} GB`
    : 'N/A';

  return (
    <header className="border-b border-space-700/60 bg-space-900/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-satblue-500/10 border border-satblue-500/30 rounded-lg text-satblue-400">
            <Satellite className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold tracking-tight text-slate-100">
                SatQuery <span className="text-satblue-400">AI</span>
              </h1>
              <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-satblue-500/10 text-satblue-400 border border-satblue-500/20">
                Phase 0
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Interactive Vision-Language Assistant for Remote Sensing
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* API Status */}
          <div className="flex items-center space-x-1.5 text-xs font-mono px-2.5 py-1 rounded-md bg-space-800 border border-space-700">
            <div
              className={`w-2 h-2 rounded-full ${
                isOnline ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]' : 'bg-rose-500'
              }`}
            />
            <span className="text-slate-300">{isOnline ? 'API Connected' : 'API Disconnected'}</span>
          </div>

          {/* Hardware Status */}
          <div className="hidden md:flex items-center space-x-2 text-xs font-mono px-2.5 py-1 rounded-md bg-space-800 border border-space-700 text-slate-300">
            <Cpu className="w-3.5 h-3.5 text-satblue-400" />
            <span>{hasGpu ? `${gpuName} (${vramTotal})` : 'CPU Mode'}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
