'use client';

import React from 'react';
import { X, MapPin, Database, Check, Layers, ArrowUpRight } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface SceneDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SceneDrawer: React.FC<SceneDrawerProps> = ({ isOpen, onClose }) => {
  const ws = useWorkspace();
  if (!isOpen) return null;

  const currentMission = ws.currentMission;

  return (
    <div className="fixed inset-y-0 left-0 z-50 w-96 bg-white border-r border-[#E6E6E1] shadow-2xl flex flex-col transition-transform duration-300 animate-in slide-in-from-left select-none">
      {/* Header */}
      <div className="h-14 px-5 border-b border-[#E6E6E1] flex items-center justify-between bg-[#FAF9F7]">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-[#111111]" />
          <h2 className="text-xs font-bold tracking-tight text-[#111111] uppercase font-mono">
            Scene Assets & Ingestion
          </h2>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-[#6F6F6A] hover:text-[#111111] hover:bg-[#EAEAE5] transition-colors"
          aria-label="Close Scene Drawer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        {/* Scene Summary */}
        <div className="p-4 rounded-xl bg-[#FAF9F7] border border-[#E6E6E1] space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold tracking-wider text-[#6F6F6A] uppercase">
              ACTIVE SCENE
            </span>
            <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
              ● {ws.datasets.length} SYNCHRONIZED
            </span>
          </div>
          <h3 className="text-sm font-bold text-[#111111]">{currentMission.name}</h3>
          <div className="flex items-center gap-1.5 text-xs text-[#6F6F6A]">
            <MapPin className="w-3.5 h-3.5 text-[#111111]" />
            <span>{currentMission.location}</span>
          </div>
          <div className="pt-2 border-t border-[#E6E6E1] grid grid-cols-2 gap-2 text-[11px] font-mono text-[#555555]">
            <div>
              <span className="text-[#888888] block text-[9px]">PROJECTION</span>
              <span>{currentMission.utmZone}</span>
            </div>
            <div>
              <span className="text-[#888888] block text-[9px]">TOTAL AOI</span>
              <span>{currentMission.areaAoi}</span>
            </div>
          </div>
        </div>

        {/* Datasets List */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono font-bold tracking-wider text-[#6F6F6A] uppercase">
              CO-REGISTERED RASTERS
            </span>
            <span className="text-[10px] font-mono text-[#888888]">10m GSD Native</span>
          </div>

          <div className="space-y-2.5">
            {ws.datasets.map((dataset, idx) => {
              const isSelected = ws.activeDatasetIndex === idx;
              return (
                <div
                  key={dataset.id}
                  onClick={() => ws.setActiveDatasetIndex(idx)}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-white border-[#111111] shadow-sm ring-1 ring-black/5'
                      : 'bg-white border-[#E6E6E1] hover:border-[#CCCCCC]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#111111]">{dataset.name}</span>
                    <span className="text-[10px] font-mono text-emerald-700 font-semibold flex items-center gap-1">
                      <Check className="w-3 h-3 stroke-[2.5]" />
                      {dataset.status === 'valid' ? 'CRS VALID' : 'READY'}
                    </span>
                  </div>
                  <div className="mt-1.5 space-y-0.5 text-[11px] font-mono text-[#6F6F6A]">
                    <p>{dataset.sensor} · {dataset.resolution}</p>
                    <p>{dataset.bands}</p>
                    <p className="text-[10px] text-[#888888]">{dataset.dimensions} · {dataset.projection}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Action: Ingest New Dataset */}
        <div className="pt-2">
          <button
            onClick={() => {
              onClose();
              ws.setActiveTab('diagnostics');
            }}
            className="w-full flex items-center justify-between px-4 py-3 rounded-xl border border-[#E6E6E1] bg-white hover:bg-[#FAF9F7] text-xs font-semibold text-[#111111] transition-all group"
          >
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#111111]" />
              <span>Ingest New GeoTIFF Raster</span>
            </div>
            <ArrowUpRight className="w-4 h-4 text-[#6F6F6A] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
          </button>
        </div>
      </div>
    </div>
  );
};
