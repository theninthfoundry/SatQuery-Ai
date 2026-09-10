'use client';

import React from 'react';
import {
  Plus,
  Minus,
  Maximize2,
  Scan,
  Ruler,
  Microscope,
  SplitSquareVertical,
  Layers,
  Sparkles,
} from 'lucide-react';
import { useWorkspace, MapTool } from '../../context/WorkspaceContext';

interface FloatingMapControlsProps {
  onOpenAOIModal: () => void;
  onToggleViewSelector: () => void;
}

export const FloatingMapControls: React.FC<FloatingMapControlsProps> = ({
  onOpenAOIModal,
  onToggleViewSelector,
}) => {
  const ws = useWorkspace();

  const isInspectActive = ws.activeTool === 'inspect';
  const isMeasureActive = ws.activeTool === 'measure' || ws.activeTool === 'measure_area';
  const isCompareActive = ws.temporalMode === 'Swipe' || ws.temporalMode === 'Difference';

  return (
    <div className="flex flex-col gap-2 pointer-events-auto select-none">
      {/* Zoom Control Pill */}
      <div className="flex flex-col bg-[#121212]/95 backdrop-blur-md border border-white/15 rounded-lg p-0.5 shadow-xl text-neutral-300">
        <button
          onClick={() => ws.zoomIn()}
          className="p-2 hover:bg-neutral-800 hover:text-white rounded transition-colors text-xs flex items-center justify-center"
          title="Zoom In (+)"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
        <div className="h-px bg-white/10 w-full" />
        <button
          onClick={() => ws.zoomOut()}
          className="p-2 hover:bg-neutral-800 hover:text-white rounded transition-colors text-xs flex items-center justify-center"
          title="Zoom Out (-)"
        >
          <Minus className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Floating Instrument Tools Stack */}
      <div className="flex flex-col bg-[#121212]/95 backdrop-blur-md border border-white/15 rounded-lg p-0.5 shadow-xl text-neutral-300 gap-0.5">
        {/* AOI Selection / Upload */}
        <button
          id="btn-aoi-tool"
          onClick={onOpenAOIModal}
          className="flex items-center gap-1.5 px-2.5 py-1.5 hover:bg-neutral-800 hover:text-white rounded transition-colors text-[11px] font-mono"
          title="Area of Interest (AOI) Upload & Boundaries"
        >
          <Scan className="w-3.5 h-3.5 text-emerald-400" />
          <span className="hidden sm:inline">AOI</span>
        </button>

        {/* Measure Tool */}
        <button
          id="btn-measure-tool"
          onClick={() => {
            if (isMeasureActive) {
              ws.setActiveTool('select');
              ws.resetMeasurement();
            } else {
              ws.setActiveTool('measure');
            }
          }}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded transition-colors text-[11px] font-mono ${
            isMeasureActive
              ? 'bg-white text-black font-bold shadow-sm'
              : 'hover:bg-neutral-800 hover:text-white text-neutral-300'
          }`}
          title="Precision Geodesic Measurement (Shortcut: M)"
        >
          <Ruler className={`w-3.5 h-3.5 ${isMeasureActive ? 'text-black' : 'text-blue-400'}`} />
          <span className="hidden sm:inline">Measure</span>
        </button>

        {/* Pixel Microscope Inspector */}
        <button
          id="btn-inspect-tool"
          onClick={() => {
            if (isInspectActive) {
              ws.setActiveTool('select');
            } else {
              ws.setActiveTool('inspect');
            }
          }}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded transition-colors text-[11px] font-mono ${
            isInspectActive
              ? 'bg-emerald-400 text-black font-bold shadow-sm'
              : 'hover:bg-neutral-800 hover:text-white text-neutral-300'
          }`}
          title="Microscope Pixel Inspector (Shortcut: I) — Click any pixel to sample bands & indices"
        >
          <Microscope className={`w-3.5 h-3.5 ${isInspectActive ? 'text-black' : 'text-purple-400'}`} />
          <span className="hidden sm:inline">Inspect</span>
        </button>

        {/* Compare Mode Toggle */}
        <button
          id="btn-compare-tool"
          onClick={() => {
            if (ws.temporalMode === 'Swipe') ws.setTemporalMode('Difference');
            else if (ws.temporalMode === 'Difference') ws.setTemporalMode('Side by Side');
            else ws.setTemporalMode('Swipe');
          }}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded transition-colors text-[11px] font-mono ${
            isCompareActive
              ? 'bg-amber-400 text-black font-bold shadow-sm'
              : 'hover:bg-neutral-800 hover:text-white text-neutral-300'
          }`}
          title="Cycle Compare Mode: Swipe / Difference (Shortcut: C)"
        >
          <SplitSquareVertical className={`w-3.5 h-3.5 ${isCompareActive ? 'text-black' : 'text-amber-400'}`} />
          <span className="hidden sm:inline">{ws.temporalMode}</span>
        </button>

        {/* Layers / View Trigger */}
        <button
          onClick={onToggleViewSelector}
          className="flex items-center gap-1.5 px-2.5 py-1.5 hover:bg-neutral-800 hover:text-white rounded transition-colors text-[11px] font-mono text-neutral-300"
          title="Map Layers & Spectral Views (Shortcut: L)"
        >
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span className="hidden sm:inline">Layers</span>
        </button>
      </div>
    </div>
  );
};
