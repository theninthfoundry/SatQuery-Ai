'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Layers, Sparkles, Clock, Compass, ShieldCheck, Play } from 'lucide-react';
import { useWorkspace, ProvenanceStep } from '../../context/WorkspaceContext';

interface WhyThisAnswerProps {
  explanation?: string;
  regionsDetectedCount?: number;
  spatialConsistency?: string;
  executionSteps?: ProvenanceStep[];
}

export const WhyThisAnswer: React.FC<WhyThisAnswerProps> = ({
  explanation: propExplanation,
  regionsDetectedCount: propRegionsCount,
  spatialConsistency: propSpatialConsistency,
  executionSteps: propSteps,
}) => {
  const ws = useWorkspace();
  const [isOpen, setIsOpen] = useState(true);
  const [showTrace, setShowTrace] = useState(false);

  const explanation = propExplanation || ws.synthesizedInsight;
  const regionsDetectedCount =
    propRegionsCount !== undefined ? propRegionsCount : ws.clusters.length;
  const spatialConsistency =
    propSpatialConsistency || `${ws.evidenceScore}% Cross-Modal Concordance`;
  const executionSteps = propSteps || ws.provenanceSteps;

  return (
    <div className="rounded-xl border border-[#E8E8E5] bg-white overflow-hidden shadow-subtle select-none">
      {/* Accordion Toggle Header */}
      <button
        onClick={() => setIsOpen((v) => !v)}
        className="w-full px-3.5 py-2.5 flex items-center justify-between hover:bg-[#F8F8F6] transition-colors"
      >
        <span className="text-[10px] font-mono font-bold tracking-wider text-[#737373] uppercase">
          SCIENTIFIC PROVENANCE & REASONING
        </span>
        {isOpen ? (
          <ChevronUp className="w-3.5 h-3.5 text-[#888888]" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-[#888888]" />
        )}
      </button>

      {/* Expanded Explanation Body */}
      {isOpen && (
        <div className="px-3.5 pb-3.5 pt-1 space-y-3 border-t border-[#F3F3F0]">
          <p className="text-xs text-[#444444] leading-relaxed font-sans">
            {explanation}
          </p>

          {/* Scientific Audit Badges */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#F8F8F6] border border-[#E8E8E5] text-[11px] font-mono text-[#555555]">
              <Layers className="w-3 h-3 text-[#777777]" />
              <span>{regionsDetectedCount} clusters detected</span>
            </div>

            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#F8F8F6] border border-[#E8E8E5] text-[11px] font-mono text-emerald-700 font-medium">
              <Sparkles className="w-3 h-3 text-emerald-600" />
              <span>{spatialConsistency}</span>
            </div>

            <button
              onClick={() => ws.setIsTraceModalOpen(true)}
              className="text-[11px] font-mono text-emerald-700 hover:text-emerald-800 underline ml-auto flex items-center gap-1 font-semibold"
              title="Open Interactive Trace Replay Modal (T)"
            >
              <Play className="w-3 h-3 text-emerald-600 fill-emerald-600" />
              <span>Trace Replay</span>
            </button>
          </div>

          {/* Quick Toggle for Inline Trace */}
          <div className="pt-1">
            <button
              onClick={() => setShowTrace((v) => !v)}
              className="text-[10px] font-mono text-[#888888] hover:text-[#444444] flex items-center gap-1"
            >
              <Clock className="w-3 h-3" />
              <span>{showTrace ? 'Hide Inline Operations' : 'Show Inline Operations'}</span>
            </button>
          </div>

          {/* Inline Calculation Provenance Trace */}
          {showTrace && (
            <div className="mt-2 pt-2 border-t border-[#F0F0EC] space-y-1.5 font-mono text-[10px]">
              <span className="text-[#888888] font-bold block mb-1 uppercase tracking-wider">
                COMPUTATIONAL PROVENANCE CHAIN:
              </span>
              {executionSteps.map((s, idx) => (
                <div key={idx} className="flex items-start gap-2 p-1.5 rounded bg-[#F8F8F6] border border-[#EDEDEA]">
                  <span className="text-[#999999] shrink-0">{s.timestamp}</span>
                  <div className="space-y-0.5">
                    <span className="font-bold text-[#222222] block">{s.label}</span>
                    <span className="text-[#666666] block">{s.detail}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
