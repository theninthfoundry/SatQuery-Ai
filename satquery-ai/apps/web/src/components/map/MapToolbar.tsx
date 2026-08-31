'use client';

import React from 'react';
import { LensMode } from '../../context/WorkspaceContext';

interface MapToolbarProps {
  activeLens: LensMode;
  onSelectLens: (lens: LensMode) => void;
  activeOverlays?: {
    regions: boolean;
    vectors: boolean;
    evidence: boolean;
    grid: boolean;
    geometry: boolean;
    minimap: boolean;
  };
  onToggleOverlay?: (key: 'regions' | 'vectors' | 'evidence' | 'grid' | 'geometry' | 'minimap') => void;
  is3DMode?: boolean;
  onToggle3D?: () => void;
}

const LENS_MODES: { id: LensMode; label: string }[] = [
  { id: 'True Color', label: 'TRUE COLOR' },
  { id: 'NIR', label: 'NIR' },
  { id: 'SAR', label: 'SAR' },
  { id: 'CHANGE', label: 'CHANGE' },
  { id: 'EVIDENCE', label: 'EVIDENCE' },
];

export const MapToolbar: React.FC<MapToolbarProps> = ({
  activeLens,
  onSelectLens,
}) => {
  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 select-none">
      {/* Precision Segmented Spectral Lens Controller */}
      <div className="flex items-center p-1 rounded-xl bg-white/90 backdrop-blur-md border border-[#E6E6E1] shadow-md gap-0.5">
        {LENS_MODES.map((mode) => {
          const isActive = activeLens === mode.id;
          return (
            <button
              key={mode.id}
              onClick={() => onSelectLens(mode.id)}
              className={`px-3 py-1 rounded-lg text-[11px] font-mono font-bold tracking-wider transition-all ${
                isActive
                  ? 'bg-[#111111] text-white shadow-sm'
                  : 'text-[#6F6F6A] hover:text-[#111111] hover:bg-[#F0EFEA]'
              }`}
            >
              {mode.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};
export type { LensMode };
