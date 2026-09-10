'use client';

import { Check, CheckCircle2 } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface AgentExecutionProps {
  currentStepIndex: number;
}

export const AgentExecution: React.FC<AgentExecutionProps> = ({ currentStepIndex }) => {
  const ws = useWorkspace();

  return (
    <div className="w-full max-w-4xl mx-auto p-4 rounded-2xl bg-white border border-[#E6E6E1] shadow-xl space-y-3.5 select-none animate-in fade-in slide-in-from-bottom-2 duration-200">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#F0EFEA] pb-2.5">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
          <span className="text-[10px] font-mono font-bold tracking-wider text-[#111111] uppercase">
            AUTONOMOUS AGENT ORCHESTRATION
          </span>
        </div>
        <span className="text-[10px] font-mono text-[#6F6F6A]">
          Observable SIH26167 Execution Trace
        </span>
      </div>

      {/* Structured Observable Execution Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs font-mono">
        {/* Box 1: Query & Task */}
        <div className="p-3 rounded-xl bg-[#FAF9F7] border border-[#E6E6E1] space-y-1">
          <span className="text-[9px] text-[#888888] uppercase block font-bold">TASK CLASSIFICATION</span>
          <p className="font-bold text-[#111111] truncate">
            {ws.selectedMissionId === 'mission_05_compound'
              ? 'Compound Multimodal'
              : ws.selectedMissionId === 'mission_01_vqa'
              ? 'Terrain RS-VQA'
              : ws.selectedMissionId === 'mission_02_grounding'
              ? 'Visual Grounding'
              : ws.selectedMissionId === 'mission_03_temporal'
              ? 'Bi-Temporal Change'
              : 'Optical + SAR Corroboration'}
          </p>
          <span className="text-[10px] text-emerald-700 font-semibold flex items-center gap-1">
            <Check className="w-3 h-3 stroke-[2.5]" /> Intent Routed
          </span>
        </div>

        {/* Box 2: Co-Registered Inputs */}
        <div className="p-3 rounded-xl bg-[#FAF9F7] border border-[#E6E6E1] space-y-1">
          <span className="text-[9px] text-[#888888] uppercase block font-bold">INPUT OBSERVATIONS</span>
          <div className="space-y-0.5 text-[10px] text-[#444444]">
            <p className="flex items-center gap-1">
              <Check className="w-3 h-3 text-emerald-600" /> Optical T1 (2024)
            </p>
            <p className="flex items-center gap-1">
              <Check className="w-3 h-3 text-emerald-600" /> Optical T2 (2026)
            </p>
            <p className="flex items-center gap-1">
              <Check className="w-3 h-3 text-emerald-600" /> Sentinel-1 SAR C-band
            </p>
          </div>
        </div>

        {/* Box 3: Specialist Tools Selected */}
        <div className="p-3 rounded-xl bg-[#FAF9F7] border border-[#E6E6E1] space-y-1">
          <span className="text-[9px] text-[#888888] uppercase block font-bold">TOOLS SELECTED</span>
          <div className="space-y-0.5 text-[10px] text-[#444444]">
            <p className="flex items-center gap-1">
              <Check className="w-3 h-3 text-emerald-600" /> Temporal ChangeNet
            </p>
            <p className="flex items-center gap-1">
              <Check className="w-3 h-3 text-emerald-600" /> SAR -14.5 dB Corroboration
            </p>
            <p className="flex items-center gap-1">
              <Check className="w-3 h-3 text-emerald-600" /> Geospatial Area Engine
            </p>
          </div>
        </div>

        {/* Box 4: Current Execution Status */}
        <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 space-y-1 flex flex-col justify-between">
          <div>
            <span className="text-[9px] text-emerald-800 uppercase block font-bold">PIPELINE STATUS</span>
            <p className="text-xs font-bold text-emerald-900 mt-0.5">
              {currentStepIndex >= 4 ? 'Finding Synthesized' : 'Executing Specialists...'}
            </p>
          </div>
          <span className="text-[10px] text-emerald-700 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> 10m Metric Calibration
          </span>
        </div>
      </div>
    </div>
  );
};
