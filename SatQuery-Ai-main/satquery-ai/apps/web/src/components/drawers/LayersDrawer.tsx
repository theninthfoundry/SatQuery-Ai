'use client';

import { X, Layers } from 'lucide-react';
import { useWorkspace, LensMode, TemporalViewMode } from '../../context/WorkspaceContext';

interface LayersDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

const LENSES: { id: LensMode; label: string; desc: string }[] = [
  { id: 'True Color', label: 'True Color RGB', desc: 'Sentinel-2 B04, B03, B02 visual natural color' },
  { id: 'NIR', label: 'False Color NIR', desc: 'Near-Infrared B08 vegetation & canopy reflection' },
  { id: 'SAR', label: 'SAR Radar C-band', desc: 'Sentinel-1 Dual-Pol VV/VH surface texture & backscatter' },
  { id: 'CHANGE', label: 'Temporal Change', desc: 'Siamese ChangeNet 2D probability alteration heatmap' },
  { id: 'EVIDENCE', label: 'Evidence Multi-Modal', desc: 'Platt-calibrated decision corroboration overlay' },
];

export const LayersDrawer: React.FC<LayersDrawerProps> = ({ isOpen, onClose }) => {
  const ws = useWorkspace();
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 left-0 z-50 w-96 bg-white border-r border-[#E6E6E1] shadow-2xl flex flex-col transition-transform duration-300 animate-in slide-in-from-left select-none">
      {/* Header */}
      <div className="h-14 px-5 border-b border-[#E6E6E1] flex items-center justify-between bg-[#FAF9F7]">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-[#111111]" />
          <h2 className="text-xs font-bold tracking-tight text-[#111111] uppercase font-mono">
            Spectral Lenses & Overlays
          </h2>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-[#6F6F6A] hover:text-[#111111] hover:bg-[#EAEAE5] transition-colors"
          aria-label="Close Layers Drawer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        {/* Spectral Lens Switcher */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono font-bold tracking-wider text-[#6F6F6A] uppercase">
              ACTIVE SPECTRAL LENS
            </span>
            <span className="text-[10px] font-mono text-emerald-700 font-semibold">
              ● {ws.activeLens}
            </span>
          </div>

          <div className="space-y-2">
            {LENSES.map((lens) => {
              const isSelected = ws.activeLens === lens.id;
              return (
                <div
                  key={lens.id}
                  onClick={() => ws.setActiveLens(lens.id)}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-white border-[#111111] shadow-sm ring-1 ring-black/5'
                      : 'bg-white border-[#E6E6E1] hover:border-[#CCCCCC]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#111111]">{lens.label}</span>
                    {isSelected && (
                      <span className="text-[10px] font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        ACTIVE
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] font-mono text-[#6F6F6A] mt-1">{lens.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Vector Overlays */}
        <div className="space-y-3">
          <span className="text-[11px] font-mono font-bold tracking-wider text-[#6F6F6A] uppercase block">
            MAP OVERLAYS & VECTORS
          </span>

          <div className="p-3.5 rounded-xl border border-[#E6E6E1] bg-[#FAF9F7] space-y-3">
            <label className="flex items-center justify-between cursor-pointer text-xs font-semibold text-[#111111]">
              <span>Change Polygons (Altered Clusters)</span>
              <input
                type="checkbox"
                checked={ws.overlays.regions}
                onChange={() => ws.toggleOverlay('regions')}
                className="rounded text-black focus:ring-0 w-4 h-4 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer text-xs font-semibold text-[#111111]">
              <span>Vector Bounding Boxes</span>
              <input
                type="checkbox"
                checked={ws.overlays.vectors}
                onChange={() => ws.toggleOverlay('vectors')}
                className="rounded text-black focus:ring-0 w-4 h-4 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer text-xs font-semibold text-[#111111]">
              <span>Coordinate UTM Grid (EPSG:32643)</span>
              <input
                type="checkbox"
                checked={ws.overlays.grid}
                onChange={() => ws.toggleOverlay('grid')}
                className="rounded text-black focus:ring-0 w-4 h-4 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer text-xs font-semibold text-[#111111]">
              <span>Overview Mini-Map</span>
              <input
                type="checkbox"
                checked={ws.overlays.minimap}
                onChange={() => ws.toggleOverlay('minimap')}
                className="rounded text-black focus:ring-0 w-4 h-4 cursor-pointer"
              />
            </label>
          </div>
        </div>

        {/* Temporal View Mode */}
        <div className="space-y-3">
          <span className="text-[11px] font-mono font-bold tracking-wider text-[#6F6F6A] uppercase block">
            TEMPORAL COMPARISON MODE
          </span>
          <div className="grid grid-cols-3 gap-2">
            {(['Swipe', 'Side by Side', 'Difference'] as TemporalViewMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => ws.setTemporalMode(mode)}
                className={`py-2 px-2.5 rounded-xl border text-xs font-semibold transition-all ${
                  ws.temporalMode === mode
                    ? 'bg-[#111111] text-white border-[#111111] shadow-sm'
                    : 'bg-white text-[#555555] border-[#E6E6E1] hover:bg-[#FAF9F7]'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
