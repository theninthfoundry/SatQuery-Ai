import React, { useState } from 'react';
import { EvidenceObject, ExecutionStep } from '../types';
import { ShieldCheck, Cpu, Clock, CheckCircle2, ChevronDown, ChevronUp, Layers, ListOrdered } from 'lucide-react';

interface EvidenceCardProps {
  evidence: EvidenceObject;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ evidence }) => {
  const [traceOpen, setTraceOpen] = useState(true);
  const conf = evidence.confidence;
  const overallPercent = Math.round(conf.overall * 100);

  return (
    <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 space-y-4 shadow-lg">
      <div className="flex items-center justify-between pb-3 border-b border-space-800">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-bold text-slate-100">Verifiable Evidence & Audit Trail</h3>
        </div>
        <span className="text-xs font-mono text-slate-400">ID: {evidence.id}</span>
      </div>

      {/* Claim / Grounded Result */}
      <div className="bg-space-950/70 p-3.5 rounded-lg border border-space-800">
        <span className="text-[10px] font-mono text-satblue-400 uppercase font-bold block mb-1">
          Grounded Claim
        </span>
        <p className="text-xs text-slate-200 font-medium leading-relaxed">{evidence.claim}</p>
      </div>

      {/* Confidence Breakdown Panel */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-slate-300 font-semibold">Computed Confidence</span>
          <span
            className={`font-bold ${
              overallPercent >= 80
                ? 'text-emerald-400'
                : overallPercent >= 60
                ? 'text-amber-400'
                : 'text-rose-400'
            }`}
          >
            {overallPercent}%
          </span>
        </div>

        <div className="w-full bg-space-800 h-2 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              overallPercent >= 80
                ? 'bg-emerald-500'
                : overallPercent >= 60
                ? 'bg-amber-500'
                : 'bg-rose-500'
            }`}
            style={{ width: `${overallPercent}%` }}
          />
        </div>

        {/* Signals */}
        <div className="grid grid-cols-2 gap-2 pt-1 text-[11px] font-mono">
          <div className="bg-space-950/50 p-2 rounded border border-space-800 flex justify-between">
            <span className="text-slate-400">Model Certainty:</span>
            <span className="text-slate-200 font-bold">{Math.round(conf.model_score * 100)}%</span>
          </div>
          <div className="bg-space-950/50 p-2 rounded border border-space-800 flex justify-between">
            <span className="text-slate-400">GSD Suitability:</span>
            <span className="text-slate-200 font-bold">{Math.round(conf.resolution_score * 100)}%</span>
          </div>
        </div>
      </div>

      {/* Observable Execution Trace */}
      <div className="pt-2">
        <button
          onClick={() => setTraceOpen(!traceOpen)}
          className="flex items-center justify-between w-full text-xs font-semibold text-slate-300 hover:text-slate-100 py-1"
        >
          <div className="flex items-center space-x-2">
            <ListOrdered className="w-3.5 h-3.5 text-satblue-400" />
            <span>Execution Trace ({evidence.execution_steps.length} Steps)</span>
          </div>
          {traceOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {traceOpen && (
          <div className="mt-2 space-y-1.5 font-mono text-[11px]">
            {evidence.execution_steps.map((step, idx) => (
              <div
                key={idx}
                className="flex items-start space-x-2.5 bg-space-950/60 p-2.5 rounded-lg border border-space-800/80"
              >
                <span className="text-satblue-400 font-bold flex-shrink-0">#{step.step_number}</span>
                <div className="flex-1 space-y-0.5">
                  <div className="flex items-center justify-between text-slate-200">
                    <span className="font-semibold">{step.tool}</span>
                    <span className="text-[10px] text-slate-400">{step.duration_ms} ms</span>
                  </div>
                  <p className="text-slate-400 text-[10px]">{step.description}</p>
                </div>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
