'use client';

import React from 'react';
import { CheckCircle2, Sparkles } from 'lucide-react';

interface MissionSummaryProps {
  status?: string;
  insightText?: string;
}

export const MissionSummary: React.FC<MissionSummaryProps> = ({
  status = 'Completed',
  insightText = 'Temporal change analysis detected 12.4% surface alteration across 25,600 m². Change is concentrated in 2 major clusters.',
}) => {
  return (
    <div className="space-y-3 select-none">
      {/* Header & Status Badge */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-mono font-bold tracking-wider text-[#737373] uppercase">
          MISSION SUMMARY
        </span>
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          {status}
        </span>
      </div>

      {/* Synthesized Insight Block */}
      <div className="space-y-1">
        <span className="text-[10px] font-mono font-bold tracking-wider text-[#888888] uppercase block">
          SYNTHESIZED INSIGHT
        </span>
        <p className="text-xs text-[#222222] leading-relaxed font-sans font-normal">
          {insightText}
        </p>
      </div>
    </div>
  );
};
