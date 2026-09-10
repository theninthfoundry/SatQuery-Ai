'use client';

import React, { useState, useRef, useEffect } from 'react';
import { LensMode } from '../../context/WorkspaceContext';
import { ChevronDown, Eye, Radio, Sparkles, Layers, Activity } from 'lucide-react';

interface CompactViewSelectorProps {
  activeLens: LensMode;
  onSelectLens: (lens: LensMode) => void;
}

const VIEW_MODES: { id: LensMode; label: string; desc: string; category: string }[] = [
  { id: 'True Color', label: 'True Color (RGB)', desc: 'Natural color Sentinel-2 composite', category: 'Optical' },
  { id: 'NIR', label: 'Color Infrared (NIR)', desc: 'B08 vegetation & canopy reflection', category: 'Optical' },
  { id: 'SWIR', label: 'Shortwave Infrared (SWIR)', desc: 'B11/B12 moisture & soil mineralogy', category: 'Optical' },
  { id: 'NDVI', label: 'NDVI (Vegetation Index)', desc: 'Normalized Difference Vegetation Index', category: 'Index' },
  { id: 'NDWI', label: 'NDWI (Water Index)', desc: 'McFeeters water inundation & moisture', category: 'Index' },
  { id: 'NDBI', label: 'NDBI (Built-up Index)', desc: 'Normalized Difference Built-up Index', category: 'Index' },
  { id: 'SAR', label: 'SAR Backscatter (σ⁰ dB)', desc: 'Calibrated Sentinel-1 microwave radar', category: 'Radar' },
  { id: 'CHANGE', label: 'Change Probability Mask', desc: 'Siamese ChangeNet neural alteration', category: 'Analytics' },
  { id: 'EVIDENCE', label: 'Optical + SAR Consensus', desc: 'Deterministic multi-sensor corroboration', category: 'Analytics' },
  { id: 'MNDWI_DEBUG', label: 'MNDWI (Green - SWIR)', desc: 'Modified Normalized Difference Water Index', category: 'Debug Pipeline' },
  { id: 'CLOUD_MASK', label: 'Cloud Quality Mask', desc: 'QA60 & SCL cloud contamination filter', category: 'Debug Pipeline' },
  { id: 'WATER_BINARY_MASK', label: 'Water Binary Mask', desc: 'Thresholded surface water classification', category: 'Debug Pipeline' },
  { id: 'CONNECTED_COMPONENTS', label: 'Connected Components', desc: 'Morphological contiguous region labeling', category: 'Debug Pipeline' },
];

export const CompactViewSelector: React.FC<CompactViewSelectorProps> = ({
  activeLens,
  onSelectLens,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const activeMode = VIEW_MODES.find((m) => m.id === activeLens) || VIEW_MODES[0];

  return (
    <div className="relative pointer-events-auto" ref={dropdownRef}>
      <button
        id="compact-view-selector-btn"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#121212]/95 hover:bg-[#1C1C1C] border border-white/15 backdrop-blur-md shadow-lg text-xs font-mono text-neutral-200 transition-all hover:border-white/30"
        title="Switch Map Spectral View Mode (Shortcut: L)"
      >
        <span className="text-[10px] uppercase font-bold tracking-widest text-neutral-400">VIEW</span>
        <span className="font-semibold text-white">{activeMode.label.split(' (')[0]}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-neutral-400 transition-transform duration-150 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full mt-1.5 left-1/2 -translate-x-1/2 w-64 bg-[#141414] border border-white/15 rounded-xl shadow-2xl p-1.5 z-50 text-xs font-mono backdrop-blur-xl animate-in fade-in zoom-in-95 duration-100">
          <div className="px-2 py-1 text-[10px] uppercase font-bold tracking-wider text-neutral-500 border-b border-white/10 mb-1">
            Spectral Lens & Analysis Modes
          </div>
          <div className="space-y-0.5">
            {VIEW_MODES.map((mode) => {
              const isSelected = mode.id === activeLens;
              return (
                <button
                  key={mode.id}
                  onClick={() => {
                    onSelectLens(mode.id);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg transition-colors flex items-center justify-between ${
                    isSelected
                      ? 'bg-white text-black font-bold'
                      : 'text-neutral-300 hover:bg-neutral-800/80 hover:text-white'
                  }`}
                >
                  <div>
                    <div className="font-medium text-[11px]">{mode.label}</div>
                    <div className={`text-[9px] ${isSelected ? 'text-neutral-700' : 'text-neutral-500'}`}>
                      {mode.desc}
                    </div>
                  </div>
                  {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
