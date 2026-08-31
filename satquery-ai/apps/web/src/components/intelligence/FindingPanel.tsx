'use client';

import React from 'react';
import { ArrowRight, CheckCircle2, MessageSquare } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface FindingPanelProps {
  onInspectEvidence?: () => void;
}

export const FindingPanel: React.FC<FindingPanelProps> = ({ onInspectEvidence }) => {
  const ws = useWorkspace();

  const handleInspect = () => {
    if (onInspectEvidence) {
      onInspectEvidence();
    } else {
      ws.toggleDrawer('evidence');
    }
  };

  return (
    <aside className="w-80 shrink-0 bg-white border-l border-[#E6E6E1] flex flex-col justify-between p-5 select-none overflow-y-auto z-10 space-y-5">
      {/* Top Finding Section */}
      <div className="space-y-4">
        {/* User Question Context Callout */}
        <div className="p-3 rounded-xl bg-[#FAF9F7] border border-[#E6E6E1] space-y-1">
          <div className="flex items-center gap-1.5 text-[9px] font-mono font-bold tracking-wider text-[#888888] uppercase">
            <MessageSquare className="w-3 h-3 text-[#6F6F6A]" />
            <span>YOU ASKED</span>
          </div>
          <p className="text-xs font-semibold text-[#111111] line-clamp-3 leading-snug">
            "{ws.lastAskedQuery}"
          </p>
        </div>

        {/* Finding Status Tag */}
        <div className="flex items-center justify-between border-b border-[#F0EFEA] pb-2.5">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.6)]" />
            <span className="text-[10px] font-mono font-bold tracking-wider text-[#6F6F6A] uppercase">
              SATQUERY FINDING
            </span>
          </div>
          <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
            {ws.evidenceScore}% Concordance
          </span>
        </div>

        {/* Dynamic Finding Title & Synthesized Answer */}
        <div className="space-y-2">
          <h2 className="text-sm font-bold text-[#111111] uppercase tracking-wide leading-tight">
            {ws.findingTitle}
          </h2>
          <p className="text-xs text-[#555555] leading-relaxed">
            {ws.synthesizedInsight}
          </p>
        </div>

        {/* Metric Area Instrumentation Blocks */}
        <div className="p-4 rounded-2xl bg-[#FAF9F7] border border-[#E6E6E1] space-y-2.5 font-mono">
          <div className="flex items-baseline justify-between">
            <div>
              <span className="text-[9px] text-[#888888] uppercase block">ANALYZED METRIC</span>
              <span className="text-2xl font-bold text-[#111111] tracking-tight">{ws.totalAreaHa}</span>
            </div>
            <div className="text-right">
              <span className="text-[9px] text-[#888888] uppercase block">SURFACE M²</span>
              <span className="text-xs font-semibold text-[#555555]">{ws.totalAreaM2}</span>
            </div>
          </div>

          <div className="pt-2 border-t border-[#E6E6E1] flex items-center justify-between text-[11px] text-[#6F6F6A]">
            <span>Spatial Impact:</span>
            <span className="font-bold text-[#111111]">12.4% of AOI</span>
          </div>
        </div>

        {/* Multi-Modal Corroboration Stack */}
        <div className="space-y-2">
          <span className="text-[10px] font-mono font-bold tracking-wider text-[#888888] uppercase block">
            CORROBORATION SOURCES
          </span>

          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex items-center justify-between p-2.5 rounded-xl border border-[#E6E6E1] bg-white">
              <span className="text-[#333333] font-semibold text-[11px]">TEMPORAL CHANGENET</span>
              <span className="text-emerald-700 font-bold flex items-center gap-1 text-[11px]">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> 94%
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl border border-[#E6E6E1] bg-white">
              <span className="text-[#333333] font-semibold text-[11px]">OPTICAL REFLECTANCE</span>
              <span className="text-emerald-700 font-bold flex items-center gap-1 text-[11px]">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> 88%
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl border border-[#E6E6E1] bg-white">
              <span className="text-[#333333] font-semibold text-[11px]">SAR RADAR BACKSCATTER</span>
              <span className="text-emerald-700 font-bold flex items-center gap-1 text-[11px]">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> 91%
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl border border-[#E6E6E1] bg-white">
              <span className="text-[#333333] font-semibold text-[11px]">SPATIAL REGISTRATION</span>
              <span className="text-emerald-700 font-bold flex items-center gap-1 text-[11px]">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> 96%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Primary CTA Button */}
      <div className="pt-2">
        <button
          onClick={handleInspect}
          className="w-full flex items-center justify-between px-4 py-3 rounded-xl bg-[#111111] text-white hover:bg-black text-xs font-semibold shadow-md transition-all group active:scale-[0.98]"
        >
          <span>Inspect evidence & provenance</span>
          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
    </aside>
  );
};
