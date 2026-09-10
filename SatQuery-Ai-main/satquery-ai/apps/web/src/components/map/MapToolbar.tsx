'use client';

import React, { useState } from 'react';
import { LensMode } from '../../context/WorkspaceContext';
import { ChevronDown, Sparkles, Radio, Activity } from 'lucide-react';

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

export const MapToolbar: React.FC<MapToolbarProps> = ({
  activeLens,
  onSelectLens,
}) => {
  const [showIndicesSubmenu, setShowIndicesSubmenu] = useState(false);
  const [showChangeSubmenu, setShowChangeSubmenu] = useState(false);

  const isIndexActive = activeLens === 'NDVI' || activeLens === 'NDWI' || activeLens === 'NDBI';
  const isChangeActive = activeLens === 'CHANGE' || activeLens === 'EVIDENCE';

  return (
    <div className="absolute top-3 left-1/2 -translate-x-1/2 z-20 select-none flex flex-col items-center gap-1.5">
      {/* Primary Spectral & Modality Tier */}
      <div className="flex items-center p-1 rounded-md bg-[#121212]/90 backdrop-blur-md border border-white/10 shadow-lg text-[11px] font-mono gap-0.5 text-neutral-400">
        {/* RGB */}
        <button
          onClick={() => {
            onSelectLens('True Color');
            setShowIndicesSubmenu(false);
            setShowChangeSubmenu(false);
          }}
          className={`px-2.5 py-1 rounded transition-colors ${
            activeLens === 'True Color'
              ? 'bg-white text-black font-bold'
              : 'hover:text-white hover:bg-neutral-800'
          }`}
        >
          RGB
        </button>

        {/* NIR */}
        <button
          onClick={() => {
            onSelectLens('NIR');
            setShowIndicesSubmenu(false);
            setShowChangeSubmenu(false);
          }}
          className={`px-2.5 py-1 rounded transition-colors ${
            activeLens === 'NIR'
              ? 'bg-white text-black font-bold'
              : 'hover:text-white hover:bg-neutral-800'
          }`}
        >
          NIR
        </button>

        {/* SWIR */}
        <button
          onClick={() => {
            onSelectLens('SWIR');
            setShowIndicesSubmenu(false);
            setShowChangeSubmenu(false);
          }}
          className={`px-2.5 py-1 rounded transition-colors ${
            activeLens === 'SWIR'
              ? 'bg-white text-black font-bold'
              : 'hover:text-white hover:bg-neutral-800'
          }`}
        >
          SWIR
        </button>

        {/* SAR */}
        <button
          onClick={() => {
            onSelectLens('SAR');
            setShowIndicesSubmenu(false);
            setShowChangeSubmenu(false);
          }}
          className={`px-2.5 py-1 rounded transition-colors flex items-center gap-1 ${
            activeLens === 'SAR'
              ? 'bg-white text-black font-bold'
              : 'hover:text-white hover:bg-neutral-800'
          }`}
        >
          <Radio className="w-3 h-3" />
          <span>SAR</span>
        </button>

        {/* INDICES with Progressive Disclosure */}
        <button
          onClick={() => {
            setShowIndicesSubmenu(!showIndicesSubmenu);
            setShowChangeSubmenu(false);
            if (!isIndexActive) onSelectLens('NDVI');
          }}
          className={`px-2.5 py-1 rounded transition-colors flex items-center gap-1 ${
            isIndexActive
              ? 'bg-emerald-500 text-black font-bold'
              : 'hover:text-white hover:bg-neutral-800'
          }`}
        >
          <Activity className="w-3 h-3" />
          <span>{isIndexActive ? activeLens : 'INDICES'}</span>
          <ChevronDown className={`w-2.5 h-2.5 transition-transform ${showIndicesSubmenu ? 'rotate-180' : ''}`} />
        </button>

        {/* CHANGE with Progressive Disclosure */}
        <button
          onClick={() => {
            setShowChangeSubmenu(!showChangeSubmenu);
            setShowIndicesSubmenu(false);
            if (!isChangeActive) onSelectLens('CHANGE');
          }}
          className={`px-2.5 py-1 rounded transition-colors flex items-center gap-1 ${
            isChangeActive
              ? 'bg-white text-black font-bold'
              : 'hover:text-white hover:bg-neutral-800'
          }`}
        >
          <Sparkles className="w-3 h-3 text-amber-400" />
          <span>{activeLens === 'EVIDENCE' ? 'EVIDENCE' : 'CHANGE'}</span>
          <ChevronDown className={`w-2.5 h-2.5 transition-transform ${showChangeSubmenu ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {/* Sub-tier for INDICES: NDVI, NDWI, NDBI */}
      {showIndicesSubmenu && (
        <div className="flex items-center p-0.5 rounded-md bg-[#181818]/95 backdrop-blur-md border border-white/10 shadow-xl text-[10px] font-mono gap-0.5 text-neutral-400 animate-in fade-in slide-in-from-top-1 duration-150">
          <button
            onClick={() => {
              onSelectLens('NDVI');
              setShowIndicesSubmenu(false);
            }}
            className={`px-2 py-0.5 rounded transition-colors ${
              activeLens === 'NDVI' ? 'bg-emerald-500 text-black font-bold' : 'hover:text-white hover:bg-neutral-800'
            }`}
          >
            NDVI (Vegetation)
          </button>
          <button
            onClick={() => {
              onSelectLens('NDWI');
              setShowIndicesSubmenu(false);
            }}
            className={`px-2 py-0.5 rounded transition-colors ${
              activeLens === 'NDWI' ? 'bg-cyan-500 text-black font-bold' : 'hover:text-white hover:bg-neutral-800'
            }`}
          >
            NDWI (Water)
          </button>
          <button
            onClick={() => {
              onSelectLens('NDBI');
              setShowIndicesSubmenu(false);
            }}
            className={`px-2 py-0.5 rounded transition-colors ${
              activeLens === 'NDBI' ? 'bg-orange-500 text-black font-bold' : 'hover:text-white hover:bg-neutral-800'
            }`}
          >
            NDBI (Built-Up)
          </button>
        </div>
      )}

      {/* Sub-tier for CHANGE: ChangeNet vs Multi-modal Evidence Spotlight */}
      {showChangeSubmenu && (
        <div className="flex items-center p-0.5 rounded-md bg-[#181818]/95 backdrop-blur-md border border-white/10 shadow-xl text-[10px] font-mono gap-0.5 text-neutral-400 animate-in fade-in slide-in-from-top-1 duration-150">
          <button
            onClick={() => {
              onSelectLens('CHANGE');
              setShowChangeSubmenu(false);
            }}
            className={`px-2 py-0.5 rounded transition-colors ${
              activeLens === 'CHANGE' ? 'bg-white text-black font-bold' : 'hover:text-white hover:bg-neutral-800'
            }`}
          >
            ChangeNet Mask
          </button>
          <button
            onClick={() => {
              onSelectLens('EVIDENCE');
              setShowChangeSubmenu(false);
            }}
            className={`px-2 py-0.5 rounded transition-colors ${
              activeLens === 'EVIDENCE' ? 'bg-white text-black font-bold' : 'hover:text-white hover:bg-neutral-800'
            }`}
          >
            Evidence Spotlight
          </button>
        </div>
      )}
    </div>
  );
};
export type { LensMode };
