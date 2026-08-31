'use client';

import React from 'react';
import { X, ShieldCheck, Layers, Sparkles, Check, Database, Activity } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

export const EvidenceModal: React.FC = () => {
  const {
    isEvidenceModalOpen,
    setIsEvidenceModalOpen,
    activeEvidenceDetail,
    evidenceLayers,
    selectEvidenceLayer,
    evidenceScore,
  } = useWorkspace();

  if (!isEvidenceModalOpen || !activeEvidenceDetail) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 select-none animate-in fade-in duration-150"
      onClick={() => setIsEvidenceModalOpen(false)}
    >
      <div
        className="bg-white border border-[#E8E8E5] rounded-2xl max-w-xl w-full p-6 space-y-5 shadow-panel max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#E8E8E5]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#111111]">{activeEvidenceDetail.title}</h3>
              <p className="text-[11px] font-mono text-emerald-700">
                Composite Evidence Score: {evidenceScore}% (Platt-Scaled)
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsEvidenceModalOpen(false)}
            className="p-1 rounded-lg hover:bg-[#F3F3F0] text-[#777777] hover:text-[#111111] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Evidence Category Selector Pill Tabs */}
        <div className="flex flex-wrap gap-1.5 p-1 bg-[#F8F8F6] rounded-xl border border-[#E8E8E5]">
          {evidenceLayers.map((layer) => {
            const isSelected = activeEvidenceDetail.id === layer.id;
            return (
              <button
                key={layer.id}
                onClick={() => selectEvidenceLayer(layer.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
                  isSelected
                    ? 'bg-white text-[#111111] shadow-sm font-bold border border-[#E0E0DC]'
                    : 'text-[#666666] hover:text-[#111111]'
                }`}
              >
                {layer.category} ({Math.round(layer.score * 100)}%)
              </button>
            );
          })}
        </div>

        {/* Detail Cards */}
        <div className="space-y-3 font-sans text-xs">
          <div className="p-3.5 rounded-xl bg-[#F8F8F6] border border-[#E8E8E5] space-y-1.5">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#888888]">
              Methodology & Mathematical Formulation
            </span>
            <p className="text-[#333333] leading-relaxed font-mono text-[11px]">
              {activeEvidenceDetail.methodology}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl border border-[#E8E8E5] bg-white space-y-1">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#888888]">
                Data Source
              </span>
              <p className="text-xs font-semibold text-[#111111] flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-[#555555]" />
                {activeEvidenceDetail.source}
              </p>
            </div>

            <div className="p-3 rounded-xl border border-[#E8E8E5] bg-white space-y-1">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#888888]">
                Contribution Weight
              </span>
              <p className="text-xs font-semibold text-[#111111] flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-emerald-600" />
                {Math.round(activeEvidenceDetail.weight * 100)}% of Composite Score
              </p>
            </div>
          </div>

          <div className="p-3 rounded-xl border border-emerald-100 bg-emerald-50/50 flex items-center justify-between text-emerald-900">
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-600 stroke-[2.5]" />
              <span className="font-semibold text-xs">Spatial & Sensor Concordance Verified</span>
            </div>
            <span className="font-mono text-xs font-bold text-emerald-700">
              {Math.round(activeEvidenceDetail.score * 100)}%
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-2">
          <button
            onClick={() => setIsEvidenceModalOpen(false)}
            className="px-4 py-2 rounded-xl bg-[#0A0A0A] text-white text-xs font-semibold hover:bg-black transition-colors"
          >
            Close Evidence Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
