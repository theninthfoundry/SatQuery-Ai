'use client';

import { ArrowRight, X, CheckCircle2 } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

export const FindingCard: React.FC = () => {
  const ws = useWorkspace();

  // If dismissed, show a compact minimized pill so user can easily re-open
  if (ws.isFindingDismissed) {
    return (
      <div className="absolute bottom-6 right-6 z-30 animate-in fade-in slide-in-from-bottom-2 duration-300 select-none">
        <button
          onClick={() => ws.setIsFindingDismissed(false)}
          className="flex items-center gap-2.5 px-4 py-2.5 rounded-2xl bg-white/95 backdrop-blur-md border border-[#E6E6E1] shadow-lg hover:border-[#111111] transition-all group"
        >
          <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.5)]" />
          <span className="text-xs font-mono font-bold text-[#111111]">
            FINDING: {ws.totalAreaHa} CHANGED
          </span>
          <span className="text-[11px] font-semibold text-[#6F6F6A] group-hover:text-[#111111] flex items-center gap-1 transition-colors">
            Inspect <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
          </span>
        </button>
      </div>
    );
  }

  return (
    <div className="absolute bottom-6 right-6 z-30 w-80 bg-white/95 backdrop-blur-md border border-[#E6E6E1] rounded-2xl shadow-xl p-5 space-y-4 animate-in fade-in slide-in-from-bottom-3 duration-400 select-none">
      {/* Header with dismiss button */}
      <div className="flex items-center justify-between border-b border-[#F0EFEA] pb-2.5">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.6)]" />
          <span className="text-[10px] font-mono font-bold tracking-wider text-[#6F6F6A] uppercase">
            FINDING
          </span>
        </div>
        <button
          onClick={() => ws.setIsFindingDismissed(true)}
          className="p-1 rounded-lg text-[#888888] hover:text-[#111111] hover:bg-[#F0EFEA] transition-colors"
          title="Minimize Finding Card"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Main Finding Text & Area Metrics */}
      <div className="space-y-1.5">
        <h3 className="text-sm font-bold text-[#111111] leading-snug">
          {ws.selectedMissionId === 'mission_05_compound'
            ? 'Built-up area increased'
            : ws.selectedMissionId === 'mission_01_vqa'
            ? 'Dominant land cover classified'
            : ws.selectedMissionId === 'mission_02_grounding'
            ? 'Water body channel localized'
            : ws.selectedMissionId === 'mission_03_temporal'
            ? 'Altered surface area detected'
            : 'Radar & optical concordance verified'}
        </h3>
        <p className="text-xs text-[#6F6F6A] leading-relaxed line-clamp-2">
          {ws.synthesizedInsight}
        </p>
      </div>

      {/* Large Metric Display */}
      <div className="p-3 rounded-xl bg-[#FAF9F7] border border-[#E6E6E1] flex items-baseline justify-between font-mono">
        <div>
          <span className="text-[9px] text-[#888888] uppercase block">CHANGED AREA</span>
          <span className="text-lg font-bold text-[#111111] tracking-tight">{ws.totalAreaHa}</span>
        </div>
        <div className="text-right">
          <span className="text-[9px] text-[#888888] uppercase block">METRIC M²</span>
          <span className="text-xs font-semibold text-[#555555]">{ws.totalAreaM2}</span>
        </div>
      </div>

      {/* Corroboration Badge & Action */}
      <div className="space-y-3 pt-0.5">
        <div className="flex items-center gap-1.5 text-[11px] font-mono text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
          <span>Optical + SAR corroborated ({ws.evidenceScore}%)</span>
        </div>

        <button
          onClick={() => ws.toggleDrawer('evidence')}
          className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl bg-[#111111] text-white hover:bg-black text-xs font-semibold shadow-sm transition-all group active:scale-[0.98]"
        >
          <span>Inspect evidence & why</span>
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </button>
      </div>
    </div>
  );
};
