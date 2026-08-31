'use client';

import React from 'react';
import { Calendar } from 'lucide-react';

export type TemporalViewMode = 'Swipe' | 'SideBySide' | 'Difference';

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
  dateT1 = 'Mar 14, 2024',
  dateT2 = 'Mar 19, 2026',
}) => {
  return (
    <div className="h-14 shrink-0 bg-white border-t border-[#E8E8E5] px-5 flex items-center justify-between gap-6 select-none z-10">
      {/* Left: Temporal Timeline Slider */}
      <div className="flex-1 flex items-center gap-4">
        {/* Calendar Icon */}
        <div className="w-8 h-8 rounded-lg bg-[#F8F8F6] border border-[#E8E8E5] flex items-center justify-center text-[#555555]">
          <Calendar className="w-4 h-4" />
        </div>

        {/* T1 Observation */}
        <div className="flex flex-col">
          <span className="text-xs font-semibold text-[#111111] font-mono leading-none">
            {dateT1}
          </span>
          <span className="text-[10px] text-[#0284C7] font-mono font-bold mt-0.5">
            T1
          </span>
        </div>

        {/* The Slider Track */}
        <div className="flex-1 relative flex items-center">
          <input
            type="range"
            min="0"
            max="100"
            value={sliderPos}
            onChange={(e) => onSliderChange(Number(e.target.value))}
            className="w-full accent-[#0A0A0A] cursor-ew-resize h-1.5 bg-[#E8E8E5] rounded-full appearance-none focus:outline-none"
          />
        </div>

        {/* T2 Observation */}
        <div className="flex flex-col text-right">
          <span className="text-xs font-semibold text-[#111111] font-mono leading-none">
            {dateT2}
          </span>
          <span className="text-[10px] text-emerald-600 font-mono font-bold mt-0.5">
            T2
          </span>
        </div>
      </div>

      {/* Right: Compare Modes (Swipe | Side-by-Side | Difference) */}
      <div className="flex items-center gap-1 bg-[#F3F3F0] p-1 rounded-xl border border-[#E8E8E5]">
        <button
          onClick={() => onSelectTemporalMode('Swipe')}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
            temporalMode === 'Swipe'
              ? 'bg-[#0A0A0A] text-white shadow-sm font-semibold'
              : 'text-[#666666] hover:text-[#111111]'
          }`}
        >
          Swipe
        </button>

        <button
          onClick={() => onSelectTemporalMode('SideBySide')}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
            temporalMode === 'SideBySide'
              ? 'bg-[#0A0A0A] text-white shadow-sm font-semibold'
              : 'text-[#666666] hover:text-[#111111]'
          }`}
        >
          Side by Side
        </button>

        <button
          onClick={() => onSelectTemporalMode('Difference')}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
            temporalMode === 'Difference'
              ? 'bg-[#0A0A0A] text-white shadow-sm font-semibold'
              : 'text-[#666666] hover:text-[#111111]'
          }`}
        >
          Difference
        </button>
      </div>
    </div>
  );
};
