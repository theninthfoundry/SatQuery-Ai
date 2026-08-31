'use client';

import React from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface ModelStatusProps {
  statusText?: string;
  isAllReady?: boolean;
  version?: string;
  isOfflineMode?: boolean;
  isRealNeuralWeights?: boolean;
}

export const ModelStatus: React.FC<ModelStatusProps> = () => {
  const ws = useWorkspace();

  return (
    <footer className="h-7 shrink-0 bg-transparent px-5 flex items-center justify-between text-[10px] font-mono text-[#6F6F6A] select-none">
      {/* Left: Tiny Calm Status Line */}
      <button
        onClick={() => ws.setIsSettingsOpen(true)}
        className="flex items-center gap-2 hover:text-[#111111] transition-colors"
        title="Open System Telemetry & Details"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
        <span>
          {ws.isRealWeights
            ? 'Live neural inference active · 3 assets · 10m GSD'
            : 'Offline demonstration mode · 3 assets synchronized · 10m GSD'}
        </span>
      </button>

      {/* Right: Quick Settings Link */}
      <button
        onClick={() => ws.setIsSettingsOpen(true)}
        className="hover:text-[#111111] transition-colors"
      >
        System details →
      </button>
    </footer>
  );
};
