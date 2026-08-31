'use client';

import React from 'react';
import { X, GitCommit, Play, Pause, SkipForward, RotateCcw, CheckCircle2 } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface TraceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const TraceDrawer: React.FC<TraceDrawerProps> = ({ isOpen, onClose }) => {
  const ws = useWorkspace();
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-[440px] bg-white border-l border-[#E6E6E1] shadow-2xl flex flex-col transition-transform duration-300 animate-in slide-in-from-right select-none">
      {/* Header */}
      <div className="h-14 px-5 border-b border-[#E6E6E1] flex items-center justify-between bg-[#FAF9F7]">
        <div className="flex items-center gap-2">
          <GitCommit className="w-4 h-4 text-[#111111]" />
          <h2 className="text-xs font-bold tracking-tight text-[#111111] uppercase font-mono">
            Observable Provenance Trace
          </h2>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-[#6F6F6A] hover:text-[#111111] hover:bg-[#EAEAE5] transition-colors"
          aria-label="Close Trace Drawer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Timeline Controls */}
      <div className="px-5 py-3 border-b border-[#E6E6E1] bg-white flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={ws.isTracePlaying ? ws.pauseTrace : ws.playTrace}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#111111] text-white hover:bg-black text-xs font-semibold transition-all shadow-sm"
          >
            {ws.isTracePlaying ? (
              <>
                <Pause className="w-3.5 h-3.5" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Replay Trace</span>
              </>
            )}
          </button>
          <button
            onClick={ws.stepTraceForward}
            className="p-1.5 rounded-lg border border-[#E6E6E1] hover:bg-[#FAF9F7] text-[#6F6F6A] hover:text-[#111111]"
            title="Step Forward"
          >
            <SkipForward className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={ws.resetTrace}
            className="p-1.5 rounded-lg border border-[#E6E6E1] hover:bg-[#FAF9F7] text-[#6F6F6A] hover:text-[#111111]"
            title="Reset Trace"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>

        <span className="text-[11px] font-mono text-[#6F6F6A]">
          Step {ws.playbackTraceIndex + 1} / {ws.provenanceSteps.length}
        </span>
      </div>

      {/* Steps List */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {ws.provenanceSteps.map((step, idx) => {
          const isReached = idx <= ws.playbackTraceIndex;
          const isCurrent = idx === ws.playbackTraceIndex;

          return (
            <div
              key={step.id}
              className={`p-3.5 rounded-xl border transition-all ${
                isCurrent
                  ? 'bg-white border-[#111111] shadow-sm ring-1 ring-black/5'
                  : isReached
                  ? 'bg-[#FAF9F7] border-[#E6E6E1]'
                  : 'bg-white/50 border-[#F0EFEA] opacity-40'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono font-bold text-[#888888]">
                    {String(idx + 1).padStart(2, '0')}
                  </span>
                  <span className="text-xs font-bold text-[#111111]">{step.label}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] font-mono text-[#888888]">{step.durationMs}ms</span>
                  {isReached && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
                </div>
              </div>

              <p className="text-[11px] font-mono text-[#6F6F6A] mt-1.5 leading-relaxed">
                {step.detail}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
