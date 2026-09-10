'use client';

import React, { useState } from 'react';
import { Target, ChevronDown, MoreHorizontal, Compass } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface TopHeaderProps {
  onOpenSystemHub: () => void;
  onOpenAOIModal: () => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  onOpenSystemHub,
  onOpenAOIModal,
}) => {
  const ws = useWorkspace();
  const currentMission = ws.currentMission;

  const dateRangeStr =
    currentMission.dateT1 && currentMission.dateT2
      ? `${currentMission.dateT1.slice(0, 4)} → ${currentMission.dateT2.slice(0, 4)}`
      : '2024 → 2026';

  return (
    <header className="h-10 shrink-0 bg-[#0A0A0A] border-b border-white/10 px-5 flex items-center justify-between z-30 select-none text-white font-mono text-xs">
      {/* 1. Left: Brand & Micro Scientific Title */}
      <div className="flex items-center gap-2.5">
        <div className="w-5 h-5 rounded bg-white flex items-center justify-center text-black shadow-xs">
          <Target className="w-3.5 h-3.5 stroke-[2.5]" />
        </div>
        <span className="font-bold tracking-tight text-white text-xs">
          SATQUERY AI
        </span>
        <span className="hidden md:inline text-[9px] text-neutral-500 uppercase tracking-widest pl-1 border-l border-white/10">
          Scientific Earth Observatory
        </span>
      </div>

      {/* 2. Center: Study, Location, and Observation Temporal Range */}
      <div className="flex items-center gap-2">
        <button
          onClick={onOpenAOIModal}
          className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-neutral-900/90 hover:bg-neutral-800 border border-white/10 text-neutral-300 hover:text-white transition-colors"
          title="Click to change Study AOI or upload custom boundaries"
        >
          <span className="text-neutral-500 text-[10px]">Study:</span>
          <span className="font-bold text-neutral-100">{currentMission.location.split(' (')[0]}</span>
          <span className="text-neutral-500">/</span>
          <span className="text-emerald-400 font-bold">{dateRangeStr}</span>
          <ChevronDown className="w-3 h-3 text-neutral-500" />
        </button>
      </div>

      {/* 3. Right: Truth Status Indicator & System Hub Menu */}
      <div className="flex items-center gap-3">
        {/* Status indicator */}
        <div className="flex items-center gap-1.5 text-[10px] text-neutral-300">
          {ws.isAnalyzing ? (
            <>
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-amber-300 font-bold">ANALYZING</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
              <span className="text-neutral-300 font-bold">● Ready</span>
            </>
          )}
        </div>

        {/* System & Verification Menu Button */}
        <button
          id="btn-system-hub"
          onClick={onOpenSystemHub}
          className="p-1.5 rounded-md bg-neutral-900 hover:bg-neutral-800 border border-white/10 hover:border-white/20 text-neutral-400 hover:text-white transition-colors"
          title="System Registry, Model Verification & Replay (Shortcut: Esc closes)"
        >
          <MoreHorizontal className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
