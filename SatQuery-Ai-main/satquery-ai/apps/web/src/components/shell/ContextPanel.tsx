'use client';

import React from 'react';
import {
  Plus,
  Check,
  MapPin,
  Layers,
  Circle,
  FileImage,
  Radio,
  Sparkles,
} from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface ContextPanelProps {
  activeStep?: string;
  onSelectStep?: (stepKey: string) => void;
  activeDatasetIndex?: number;
  onSelectDataset?: (index: number) => void;
  onAddDataset?: () => void;
  scenarioName?: string;
  scenarioAoiArea?: string;
}

const WORKFLOW_STEPS = [
  { key: 'assets', label: 'Scene Assets', n: '01' },
  { key: 'query', label: 'Agent Query', n: '02' },
  { key: 'perception', label: 'Perception Panel', n: '03' },
  { key: 'evidence', label: 'Evidence & Areas', n: '04' },
  { key: 'audit', label: 'Audit & Provenance', n: '05' },
];

export const ContextPanel: React.FC<ContextPanelProps> = ({
  activeStep: propActiveStep,
  onSelectStep: propOnSelectStep,
  activeDatasetIndex: propActiveDatasetIndex,
  onSelectDataset: propOnSelectDataset,
  onAddDataset: propOnAddDataset,
  scenarioName: propScenarioName,
  scenarioAoiArea: propScenarioAoiArea,
}) => {
  const ws = useWorkspace();

  const activeStep = propActiveStep || ws.activeWorkflowStep;
  const onSelectStep = propOnSelectStep || ws.setActiveWorkflowStep;
  const activeDatasetIndex =
    propActiveDatasetIndex !== undefined ? propActiveDatasetIndex : ws.activeDatasetIndex;
  const onSelectDataset =
    propOnSelectDataset ||
    ((idx: number) => {
      ws.setActiveDatasetIndex(idx);
      if (idx === 0 || idx === 1) ws.setActiveLens('True Color');
      else if (idx === 2) ws.setActiveLens('SAR');
    });
  const onAddDataset = propOnAddDataset || (() => ws.setActiveTab('diagnostics'));
  const scenarioName = propScenarioName || ws.currentMission.name;
  const scenarioAoiArea = propScenarioAoiArea || ws.currentMission.areaAoi;

  return (
    <aside className="w-64 shrink-0 bg-white border-r border-[#E8E8E5] flex flex-col justify-between overflow-y-auto z-10 select-none">
      {/* Top: Scene Assets & Pipeline Steps */}
      <div className="p-4 space-y-4">
        {/* Header with + Add action */}
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-mono font-bold tracking-wider text-[#737373] uppercase">
            SCENE ASSETS
          </span>
          <button
            onClick={onAddDataset}
            className="p-1 rounded-md hover:bg-[#F3F3F0] text-[#555555] hover:text-[#111111] transition-colors"
            title="Upload / Ingest Scene Asset"
          >
            <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
          </button>
        </div>

        {/* Pipeline Step List */}
        <nav className="space-y-1">
          {WORKFLOW_STEPS.map((s) => {
            const isActive = activeStep === s.key;
            return (
              <button
                key={s.key}
                onClick={() => {
                  onSelectStep(s.key);
                  if (s.key === 'audit') ws.setIsTraceModalOpen(true);
                  if (s.key === 'evidence') ws.setIsEvidenceModalOpen(true);
                }}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs transition-all ${
                  isActive
                    ? 'bg-[#F3F3F0] text-[#111111] font-semibold'
                    : 'text-[#666666] hover:text-[#111111] hover:bg-[#F8F8F6]'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  {isActive && <span className="w-1.5 h-1.5 rounded-full bg-[#111111]" />}
                  <span>{s.label}</span>
                </div>
                <span className="text-[11px] font-mono text-[#999999]">{s.n}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom: Active Datasets & AOI Callout */}
      <div className="p-4 border-t border-[#E8E8E5] space-y-3 bg-[#FAFAF8]">
        {/* Synchronized Header */}
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-mono font-bold tracking-wider text-[#737373] uppercase">
            ACTIVE DATASETS
          </span>
          <span className="text-[10px] font-mono text-emerald-600 font-semibold">
            {ws.datasets.length} Synchronized
          </span>
        </div>

        {/* Dataset Cards */}
        <div className="space-y-2">
          {ws.datasets.map((dataset, idx) => {
            const isSelected = activeDatasetIndex === idx;
            return (
              <div
                key={dataset.id}
                onClick={() => onSelectDataset(idx)}
                className={`p-3 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-white border-[#111111] shadow-sm ring-1 ring-black/5'
                    : 'bg-white/80 border-[#E8E8E5] hover:border-[#D0D0CB]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#111111]">{dataset.name}</span>
                  <span className="text-[11px] font-mono text-emerald-600 font-medium flex items-center gap-1">
                    <Check className="w-3 h-3 stroke-[2.5]" />{' '}
                    {dataset.status === 'valid' ? 'Valid' : 'Ready'}
                  </span>
                </div>
                <p className="text-[11px] text-[#737373] mt-1 font-mono">
                  {dataset.sensor} · {dataset.resolution} · {dataset.bands.split(' ')[0]} bands
                </p>
              </div>
            );
          })}

          {/* AOI Card */}
          <div className="p-3 rounded-xl border border-[#E8E8E5] bg-white flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono font-bold tracking-wider text-[#888888] uppercase block">
                AOI
              </span>
              <p className="text-xs font-semibold text-[#111111] mt-0.5">{scenarioName}</p>
              <p className="text-[11px] text-[#737373] font-mono">{scenarioAoiArea}</p>
            </div>
            <div className="w-7 h-7 rounded-lg bg-[#F3F3F0] flex items-center justify-center text-[#555555]">
              <MapPin className="w-3.5 h-3.5" />
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
