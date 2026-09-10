'use client';

import React from 'react';
import { TemporalViewMode } from '../../context/WorkspaceContext';

export type { TemporalViewMode };

interface TemporalControllerProps {
  sliderPos: number;
  onSliderChange: (val: number) => void;
  temporalMode: TemporalViewMode;
  onSelectTemporalMode: (mode: TemporalViewMode) => void;
  dateT1?: string;
  dateT2?: string;
}

export const TemporalController: React.FC<TemporalControllerProps> = ({
  sliderPos,
  onSliderChange,
  temporalMode,
  onSelectTemporalMode,
  dateT1 = '14 MAR 2024',
  dateT2 = '19 MAR 2026',
}) => {
  return (
    <div className="h-10 shrink-0 bg-[#0A0A0A] border-t border-[#202020] px-5 flex items-center justify-between gap-6 select-none z-10 text-neutral-400 font-mono text-xs">
      {/* Precision Scientific Temporal Scrubber */}
      <div className="flex-1 flex items-center gap-3">
        {/* T1 Marker */}
        <button
          type="button"
          onClick={() => onSliderChange(0)}
          className="flex items-center gap-1.5 shrink-0 px-2 py-0.5 rounded hover:bg-neutral-800 transition-colors"
          title="View Full T1 Acquisition (100% T1)"
        >
          <span className="text-[10px] font-bold text-emerald-400 uppercase">T1</span>
          <span className="text-[11px] font-bold text-neutral-200">{dateT1}</span>
        </button>

        {/* Precision Hairline Slider Track */}
        <div className="flex-1 relative flex items-center px-1">
          <input
            type="range"
            min="0"
            max="100"
            value={sliderPos}
            onChange={(e) => onSliderChange(Number(e.target.value))}
            className="w-full accent-white cursor-ew-resize h-0.5 bg-neutral-700 appearance-none focus:outline-none"
          />
        </div>

        {/* T2 Marker */}
        <button
          type="button"
          onClick={() => onSliderChange(100)}
          className="flex items-center gap-1.5 shrink-0 px-2 py-0.5 rounded hover:bg-neutral-800 transition-colors"
          title="View Full T2 Acquisition (100% T2)"
        >
          <span className="text-[10px] font-bold text-blue-400 uppercase">T2</span>
          <span className="text-[11px] font-bold text-neutral-200">{dateT2}</span>
        </button>
      </div>

      {/* Mode Switcher: SWIPE · SIDE BY SIDE · DIFFERENCE */}
      <div className="flex items-center gap-0.5 bg-[#141414] p-0.5 rounded border border-neutral-800 text-[10px]">
        <button
          onClick={() => onSelectTemporalMode('Swipe')}
          className={`px-2 py-0.5 rounded transition-colors ${
            temporalMode === 'Swipe'
              ? 'bg-neutral-800 text-white font-bold'
              : 'text-neutral-500 hover:text-neutral-300'
          }`}
        >
          SWIPE
        </button>

        <button
          onClick={() => onSelectTemporalMode('Side by Side')}
          className={`px-2 py-0.5 rounded transition-colors ${
            temporalMode === 'Side by Side'
              ? 'bg-neutral-800 text-white font-bold'
              : 'text-neutral-500 hover:text-neutral-300'
          }`}
        >
          SPLIT
        </button>

        <button
          onClick={() => onSelectTemporalMode('Difference')}
          className={`px-2 py-0.5 rounded transition-colors ${
            temporalMode === 'Difference'
              ? 'bg-neutral-800 text-white font-bold'
              : 'text-neutral-500 hover:text-neutral-300'
          }`}
        >
          DIFF
        </button>
      </div>
    </div>
  );
};
