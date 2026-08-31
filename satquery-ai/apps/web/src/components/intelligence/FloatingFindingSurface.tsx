'use client';

import React from 'react';
import { ArrowRight, X, CheckCircle2 } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface FloatingFindingSurfaceProps {
  onInspectEvidence?: () => void;
}

export const FloatingFindingSurface: React.FC<FloatingFindingSurfaceProps> = ({
  onInspectEvidence,
}) => {
  const ws = useWorkspace();

  const handleInspect = () => {
    if (onInspectEvidence) {
      onInspectEvidence();
    } else {
      ws.toggleDrawer('evidence');
    }
  };

  // Minimized pill state
  if (ws.isFindingDismissed) {
    return (
      <div className="absolute bottom-6 right-6 z-30 animate-in fade-in slide-in-from-bottom-2 duration-300 select-none">
        <button
          onClick={() => ws.setIsFindingDismissed(false)}
          className="flex items-center gap-2.5 px-4 py-2.5 rounded-2xl bg-white/95 backdrop-blur-md border border-[#E6E6E1] shadow-xl hover:border-[#111111] transition-all group"
        >
          <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.6)]" />
          <span className="text-xs font-mono font-bold text-[#111111] uppercase">
            FINDING: {ws.totalAreaHa}
          </span>
          <span className="text-[11px] font-semibold text-[#6F6F6A] group-hover:text-[#111111] flex items-center gap-1 transition-colors">
            Inspect <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
          </span>
        </button>
      </div>
    );
  }

  return (
    <div className="absolute bottom-6 right-6 z-30 w-84 bg-white/95 backdrop-blur-md border border-[#E6E6E1] rounded-2xl shadow-2xl p-5 space-y-4 animate-in fade-in slide-in-from-bottom-3 duration-400 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#F0EFEA] pb-2.5">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.6)]" />
          <span className="text-[10px] font-mono font-bold tracking-wider text-[#6F6F6A] uppercase">
            SATQUERY FINDING
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
            {ws.evidenceScore}% Concordance
          </span>
          <button
            onClick={() => ws.setIsFindingDismissed(true)}
            className="p-1 rounded-lg text-[#888888] hover:text-[#111111] hover:bg-[#F0EFEA] transition-colors"
            title="Minimize Finding"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Finding Title & Concise Editorial Explanation */}
      <div className="space-y-1.5">
        <h3 className="text-base font-bold text-[#111111] tracking-tight uppercase leading-tight">
          {ws.findingTitle}
        </h3>
        <p className="text-xs text-[#555555] leading-relaxed line-clamp-3">
          {ws.synthesizedInsight}
        </p>
      </div>

      {/* Instrumentation Metric Display */}
      <div className="p-3.5 rounded-xl bg-[#FAF9F7] border border-[#E6E6E1] flex items-baseline justify-between font-mono">
        <div>
          <span className="text-[9px] text-[#888888] uppercase block">ANALYZED METRIC</span>
          <span className="text-2xl font-bold text-[#111111] tracking-tight">{ws.totalAreaHa}</span>
        </div>
        <div className="text-right">
          <span className="text-[9px] text-[#888888] uppercase block">SURFACE AREA</span>
          <span className="text-xs font-semibold text-[#555555]">{ws.totalAreaM2}</span>
        </div>
      </div>

      {/* Corroboration Stack Summary */}
      <div className="space-y-1.5 pt-0.5">
        <div className="grid grid-cols-2 gap-1.5 text-[10px] font-mono">
          <div className="flex items-center gap-1 p-1.5 rounded-lg bg-[#FAF9F7] border border-[#E6E6E1] text-[#333333]">
            <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
            <span>OPTICAL 88%</span>
          </div>
          <div className="flex items-center gap-1 p-1.5 rounded-lg bg-[#FAF9F7] border border-[#E6E6E1] text-[#333333]">
            <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
            <span>TEMPORAL 94%</span>
          </div>
          <div className="flex items-center gap-1 p-1.5 rounded-lg bg-[#FAF9F7] border border-[#E6E6E1] text-[#333333]">
            <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
            <span>SAR -14.5dB</span>
          </div>
          <div className="flex items-center gap-1 p-1.5 rounded-lg bg-[#FAF9F7] border border-[#E6E6E1] text-[#333333]">
            <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
            <span>REGISTRATION</span>
          </div>
        </div>

        <button
          onClick={handleInspect}
          className="w-full mt-2 flex items-center justify-between px-3.5 py-2.5 rounded-xl bg-[#111111] text-white hover:bg-black text-xs font-semibold shadow-sm transition-all group active:scale-[0.98]"
        >
          <span>Inspect evidence & provenance</span>
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </button>
      </div>
    </div>
  );
};
