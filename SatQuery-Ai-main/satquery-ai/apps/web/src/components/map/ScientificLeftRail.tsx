'use client';

import React from 'react';
import {
  MousePointer,
  Move,
  Ruler,
  Hexagon,
  Plus,
  Minus,
  RotateCcw,
  Grid,
} from 'lucide-react';
import { useWorkspace, MapTool } from '../../context/WorkspaceContext';

export const ScientificLeftRail: React.FC = () => {
  const ws = useWorkspace();

  return (
    <aside className="select-none pointer-events-auto">
      {/* Precision Single-Column Instrument Rail */}
      <div className="w-10 bg-[#121212]/90 backdrop-blur-md border border-white/10 rounded-md p-1 flex flex-col items-center gap-1 shadow-lg text-neutral-400">
        {/* Pointer / Inspect */}
        <button
          onClick={() => ws.setActiveTool('select')}
          title="Pointer / Inspect Feature"
          className={`w-8 h-8 rounded flex items-center justify-center transition-colors ${
            ws.activeTool === 'select'
              ? 'bg-white text-black font-bold'
              : 'hover:text-white hover:bg-neutral-800'
          }`}
        >
          <MousePointer className="w-3.5 h-3.5 stroke-[2]" />
        </button>

        {/* Pan Viewport */}
        <button
          onClick={() => ws.setActiveTool('pan')}
          title="Pan Viewport"
          className={`w-8 h-8 rounded flex items-center justify-center transition-colors ${
            ws.activeTool === 'pan'
              ? 'bg-white text-black font-bold'
              : 'hover:text-white hover:bg-neutral-800'
          }`}
        >
          <Move className="w-3.5 h-3.5 stroke-[2]" />
        </button>

        {/* Geodesic Distance Tool */}
        <button
          onClick={() => ws.setActiveTool('measure')}
          title="Geodesic Distance Ruler (Point A → Point B with Bearing)"
          className={`w-8 h-8 rounded flex items-center justify-center transition-colors ${
            ws.activeTool === 'measure'
              ? 'bg-emerald-500 text-black font-bold'
              : 'hover:text-white hover:bg-neutral-800'
          }`}
        >
          <Ruler className="w-3.5 h-3.5 stroke-[2]" />
        </button>

        {/* Polygon Area Tool */}
        <button
          onClick={() => ws.setActiveTool('measure_area')}
          title="Polygon Area Calculator (Hectares & Square Meters)"
          className={`w-8 h-8 rounded flex items-center justify-center transition-colors ${
            ws.activeTool === 'measure_area'
              ? 'bg-emerald-500 text-black font-bold'
              : 'hover:text-white hover:bg-neutral-800'
          }`}
        >
          <Hexagon className="w-3.5 h-3.5 stroke-[2]" />
        </button>

        <div className="w-5 h-px bg-neutral-800 my-0.5" />

        {/* Zoom In */}
        <button
          onClick={() => ws.zoomIn()}
          title="Zoom In (+)"
          className="w-8 h-8 rounded flex items-center justify-center hover:text-white hover:bg-neutral-800 transition-colors"
        >
          <Plus className="w-3.5 h-3.5 stroke-[2]" />
        </button>

        {/* Zoom Out */}
        <button
          onClick={() => ws.zoomOut()}
          title="Zoom Out (-)"
          className="w-8 h-8 rounded flex items-center justify-center hover:text-white hover:bg-neutral-800 transition-colors"
        >
          <Minus className="w-3.5 h-3.5 stroke-[2]" />
        </button>

        {/* Reset View */}
        <button
          onClick={() => ws.resetZoom()}
          title="Reset Scale & Viewport"
          className="w-8 h-8 rounded flex items-center justify-center hover:text-white hover:bg-neutral-800 transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5 stroke-[2]" />
        </button>

        <div className="w-5 h-px bg-neutral-800 my-0.5" />

        {/* Grid Overlay Toggle */}
        <button
          onClick={() => ws.toggleOverlay('grid')}
          title={ws.overlays.grid ? 'Hide Coordinate Grid' : 'Show Coordinate Grid'}
          className={`w-8 h-8 rounded flex items-center justify-center transition-colors ${
            ws.overlays.grid
              ? 'text-emerald-400 bg-neutral-800'
              : 'hover:text-white hover:bg-neutral-800'
          }`}
        >
          <Grid className="w-3.5 h-3.5 stroke-[2]" />
        </button>
      </div>
    </aside>
  );
};
