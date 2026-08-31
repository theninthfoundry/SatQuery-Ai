'use client';

import React from 'react';
import {
  Pointer,
  Triangle,
  Square,
  MapPin,
  Ruler,
  Plus,
  Minus,
  MoreHorizontal,
  RotateCcw,
} from 'lucide-react';

export type MapTool = 'select' | 'polygon' | 'box' | 'pin' | 'measure';

interface MapControlsProps {
  activeTool: MapTool;
  onSelectTool: (tool: MapTool) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetZoom: () => void;
  isMeasuring?: boolean;
}

export const MapControls: React.FC<MapControlsProps> = ({
  activeTool,
  onSelectTool,
  onZoomIn,
  onZoomOut,
  onResetZoom,
  isMeasuring = false,
}) => {
  return (
    <div className="absolute top-4 left-4 z-20 flex flex-col bg-white/95 backdrop-blur-md rounded-xl border border-[#E8E8E5] shadow-panel overflow-hidden select-none divide-y divide-[#E8E8E5]">
      {/* Primary Selection & Drawing Tools */}
      <div className="flex flex-col p-1 gap-0.5">
        <button
          onClick={() => onSelectTool('select')}
          className={`p-2 rounded-lg text-xs transition-colors ${
            activeTool === 'select'
              ? 'bg-[#0A0A0A] text-white shadow-xs'
              : 'text-[#555555] hover:text-[#111111] hover:bg-[#F3F3F0]'
          }`}
          title="Selection Pointer"
        >
          <Pointer className="w-4 h-4 stroke-[2]" />
        </button>

        <button
          onClick={() => onSelectTool('polygon')}
          className={`p-2 rounded-lg text-xs transition-colors ${
            activeTool === 'polygon'
              ? 'bg-[#0A0A0A] text-white shadow-xs'
              : 'text-[#555555] hover:text-[#111111] hover:bg-[#F3F3F0]'
          }`}
          title="Polygon Area Boundary"
        >
          <Triangle className="w-4 h-4 rotate-180 stroke-[2]" />
        </button>

        <button
          onClick={() => onSelectTool('box')}
          className={`p-2 rounded-lg text-xs transition-colors ${
            activeTool === 'box'
              ? 'bg-[#0A0A0A] text-white shadow-xs'
              : 'text-[#555555] hover:text-[#111111] hover:bg-[#F3F3F0]'
          }`}
          title="Bounding Box Crop / AOI"
        >
          <Square className="w-4 h-4 stroke-[2]" />
        </button>

        <button
          onClick={() => onSelectTool('pin')}
          className={`p-2 rounded-lg text-xs transition-colors ${
            activeTool === 'pin'
              ? 'bg-[#0A0A0A] text-white shadow-xs'
              : 'text-[#555555] hover:text-[#111111] hover:bg-[#F3F3F0]'
          }`}
          title="Geodetic Coordinate Pin"
        >
          <MapPin className="w-4 h-4 stroke-[2]" />
        </button>

        <button
          onClick={() => onSelectTool('measure')}
          className={`p-2 rounded-lg text-xs transition-colors ${
            activeTool === 'measure' || isMeasuring
              ? 'bg-[#0A0A0A] text-white shadow-xs'
              : 'text-[#555555] hover:text-[#111111] hover:bg-[#F3F3F0]'
          }`}
          title="Geodesic Ruler (Measure Ground Distance)"
        >
          <Ruler className="w-4 h-4 stroke-[2]" />
        </button>
      </div>

      {/* Navigation & Zoom Tools */}
      <div className="flex flex-col p-1 gap-0.5">
        <button
          onClick={onZoomIn}
          className="p-2 rounded-lg text-[#555555] hover:text-[#111111] hover:bg-[#F3F3F0] transition-colors"
          title="Zoom In (+)"
        >
          <Plus className="w-4 h-4 stroke-[2]" />
        </button>

        <button
          onClick={onZoomOut}
          className="p-2 rounded-lg text-[#555555] hover:text-[#111111] hover:bg-[#F3F3F0] transition-colors"
          title="Zoom Out (-)"
        >
          <Minus className="w-4 h-4 stroke-[2]" />
        </button>

        <button
          onClick={onResetZoom}
          className="p-2 rounded-lg text-[#555555] hover:text-[#111111] hover:bg-[#F3F3F0] transition-colors"
          title="Reset View / Fit to Region"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
