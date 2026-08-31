'use client';

import React from 'react';
import { X, Settings, Cpu, HardDrive, Zap, Shield, CheckCircle2, RefreshCw } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

export const SettingsModal: React.FC = () => {
  const {
    isSettingsOpen,
    setIsSettingsOpen,
    gpuUsage,
    isRealWeights,
    modelStatus,
    activateJudgeMode,
  } = useWorkspace();

  if (!isSettingsOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 select-none animate-in fade-in duration-150"
      onClick={() => setIsSettingsOpen(false)}
    >
      <div
        className="bg-white border border-[#E8E8E5] rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-panel max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#E8E8E5]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#0A0A0A] flex items-center justify-center text-white">
              <Settings className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#111111]">System & Telemetry Settings</h3>
              <p className="text-[11px] font-mono text-[#737373]">
                SatQuery AI v1.0.0 · ISRO Remote Sensing Workstation
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsSettingsOpen(false)}
            className="p-1 rounded-lg hover:bg-[#F3F3F0] text-[#777777] hover:text-[#111111] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Hardware & GPU Telemetry */}
        <div className="space-y-3">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#888888] block">
            HARDWARE & COMPUTE ENGINE
          </span>

          <div className="p-3.5 rounded-xl bg-[#F8F8F6] border border-[#E8E8E5] space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-[#111111] flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-[#555555]" />
                Target Compute Device
              </span>
              <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                NVIDIA RTX 4060 (8 GB)
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-[#111111] flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-amber-600" />
                VRAM Allocation
              </span>
              <span className="text-xs font-mono font-semibold text-[#333333]">{gpuUsage}</span>
            </div>

            <div className="w-full h-2 rounded-full bg-[#EAEAEA] overflow-hidden">
              <div className="h-full bg-emerald-600 rounded-full w-[58%]" />
            </div>
          </div>
        </div>

        {/* Model Status Registry */}
        <div className="space-y-3">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#888888] block">
            NEURAL SPECIALIST HEADS
          </span>

          <div className="space-y-2 font-mono text-xs">
            <div className="p-3 rounded-xl border border-[#E8E8E5] flex items-center justify-between bg-white">
              <div>
                <p className="font-bold text-[#111111]">GeoChat-7B (4-bit NF4)</p>
                <p className="text-[11px] text-[#737373]">{modelStatus.geochat}</p>
              </div>
              <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                ON-DEMAND
              </span>
            </div>

            <div className="p-3 rounded-xl border border-[#E8E8E5] flex items-center justify-between bg-white">
              <div>
                <p className="font-bold text-[#111111]">Siamese ChangeNet CNN</p>
                <p className="text-[11px] text-[#737373]">{modelStatus.changenet}</p>
              </div>
              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                ACTIVE
              </span>
            </div>

            <div className="p-3 rounded-xl border border-[#E8E8E5] flex items-center justify-between bg-white">
              <div>
                <p className="font-bold text-[#111111]">DOFA Multimodal Specialist</p>
                <p className="text-[11px] text-[#737373]">{modelStatus.dofa}</p>
              </div>
              <span className="text-[10px] font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                CORROBORATION
              </span>
            </div>
          </div>
        </div>

        {/* Quick Judge Mode Action */}
        <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200 flex items-center justify-between">
          <div className="space-y-0.5">
            <p className="text-xs font-bold text-emerald-950">Evaluator Judge Mode</p>
            <p className="text-[11px] text-emerald-800">
              Instantly reset state to canonical Mission 05 demonstration.
            </p>
          </div>
          <button
            onClick={() => {
              activateJudgeMode();
              setIsSettingsOpen(false);
            }}
            className="px-3 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold transition-colors shadow-sm"
          >
            Activate
          </button>
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-2 border-t border-[#E8E8E5]">
          <button
            onClick={() => setIsSettingsOpen(false)}
            className="px-4 py-2 rounded-xl bg-[#0A0A0A] text-white text-xs font-semibold hover:bg-black transition-colors"
          >
            Close Settings
          </button>
        </div>
      </div>
    </div>
  );
};
