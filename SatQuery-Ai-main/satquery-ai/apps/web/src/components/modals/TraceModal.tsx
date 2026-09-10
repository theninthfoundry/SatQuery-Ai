'use client';

import React from 'react';
import { X, GitCommit, Play, Pause, SkipForward, RotateCcw, Clock, CheckCircle2 } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

export const TraceModal: React.FC = () => {
  const {
    isTraceModalOpen,
    setIsTraceModalOpen,
    provenanceSteps,
    isTracePlaying,
    playbackTraceIndex,
    playTrace,
    pauseTrace,
    stepTraceForward,
    resetTrace,
  } = useWorkspace();

  if (!isTraceModalOpen) return null;

  const totalDuration = provenanceSteps.reduce((acc, s) => acc + s.durationMs, 0);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 select-none animate-in fade-in duration-150"
      onClick={() => setIsTraceModalOpen(false)}
    >
      <div
        className="bg-white border border-[#E8E8E5] rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-panel max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#E8E8E5] shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#0A0A0A] flex items-center justify-center text-white">
              <GitCommit className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#111111]">Computational Provenance Trace</h3>
              <p className="text-[11px] font-mono text-[#737373]">
                Total Computational Pipeline Latency: {totalDuration} ms ({provenanceSteps.length} discrete operations)
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsTraceModalOpen(false)}
            className="p-1 rounded-lg hover:bg-[#F3F3F0] text-[#777777] hover:text-[#111111] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Playback Controls Toolbar */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-[#F8F8F6] border border-[#E8E8E5] shrink-0">
          <div className="flex items-center gap-2">
            {isTracePlaying ? (
              <button
                onClick={pauseTrace}
                className="px-3 py-1.5 rounded-lg bg-[#0A0A0A] text-white text-xs font-semibold flex items-center gap-1.5 hover:bg-black transition-colors"
              >
                <Pause className="w-3.5 h-3.5" />
                <span>Pause</span>
              </button>
            ) : (
              <button
                onClick={playTrace}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold flex items-center gap-1.5 hover:bg-emerald-700 transition-colors shadow-sm"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Play Execution Replay</span>
              </button>
            )}

            <button
              onClick={stepTraceForward}
              className="p-1.5 rounded-lg bg-white border border-[#E8E8E5] hover:bg-[#F3F3F0] text-[#555555] hover:text-[#111111] transition-colors"
              title="Step Forward"
            >
              <SkipForward className="w-4 h-4" />
            </button>

            <button
              onClick={resetTrace}
              className="p-1.5 rounded-lg bg-white border border-[#E8E8E5] hover:bg-[#F3F3F0] text-[#555555] hover:text-[#111111] transition-colors"
              title="Reset Timeline"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          <span className="text-xs font-mono font-semibold text-[#666666]">
            Step {playbackTraceIndex + 1} of {provenanceSteps.length}
          </span>
        </div>

        {/* Interactive Steps Timeline */}
        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {provenanceSteps.map((step, idx) => {
            const isCompleted = idx <= playbackTraceIndex;
            const isCurrent = idx === playbackTraceIndex;

            return (
              <div
                key={step.id}
                className={`p-3.5 rounded-xl border transition-all ${
                  isCurrent
                    ? 'bg-emerald-50/60 border-emerald-300 ring-1 ring-emerald-400 shadow-sm'
                    : isCompleted
                    ? 'bg-white border-[#E8E8E5]'
                    : 'bg-[#FAFAF8] border-[#EDEDEA] opacity-40'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2.5">
                    <div
                      className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-mono font-bold shrink-0 mt-0.5 ${
                        isCurrent
                          ? 'bg-emerald-600 text-white'
                          : isCompleted
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-[#EAEAEA] text-[#888888]'
                      }`}
                    >
                      {idx + 1}
                    </div>

                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="text-[9px] font-mono font-bold uppercase tracking-wider text-[#888888]">
                          {step.stage}
                        </span>
                        <span className="text-[10px] font-mono text-[#999999]">({step.durationMs}ms)</span>
                      </div>
                      <p className="text-xs font-bold text-[#111111]">{step.label}</p>
                      <p className="text-[11px] text-[#666666] font-mono">{step.detail}</p>
                    </div>
                  </div>

                  <span className="text-[10px] font-mono text-[#999999] shrink-0">{step.timestamp}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-2 border-t border-[#E8E8E5] shrink-0">
          <button
            onClick={() => setIsTraceModalOpen(false)}
            className="px-4 py-2 rounded-xl bg-[#0A0A0A] text-white text-xs font-semibold hover:bg-black transition-colors"
          >
            Close Provenance Trace
          </button>
        </div>
      </div>
    </div>
  );
};
