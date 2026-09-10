'use client';

import React, { useState, useRef } from 'react';
import { Scan, X, Upload, CheckCircle2, AlertTriangle, FileCode, Clock, ArrowRight } from 'lucide-react';
import { uploadAOIFile } from '../../lib/api';
import { useWorkspace } from '../../context/WorkspaceContext';

interface AOIImportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AOIImportModal: React.FC<AOIImportModalProps> = ({ isOpen, onClose }) => {
  const ws = useWorkspace();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [importedAOI, setImportedAOI] = useState<any | null>(null);

  if (!isOpen) return null;

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setErrorMsg(null);

    try {
      const res = await uploadAOIFile(file);
      setImportedAOI(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to parse AOI boundary file.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleApplyAOI = () => {
    if (importedAOI) {
      ws.setQueryText(
        `Between 2024 and 2026, identify newly developed built-up areas within ${importedAOI.name} (${importedAOI.area_ha} ha) and corroborate with SAR.`
      );
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 font-mono select-none">
      <div className="w-full max-w-lg bg-[#141414] border border-white/15 rounded-2xl shadow-2xl p-6 space-y-4 text-xs text-neutral-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <Scan className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              AREA OF INTEREST (AOI) BOUNDARIES
            </h2>
          </div>
          <button onClick={onClose} className="text-neutral-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Upload Zone */}
        {!importedAOI ? (
          <div className="space-y-3">
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-white/20 hover:border-emerald-500/50 rounded-xl p-6 text-center cursor-pointer transition-colors bg-[#181818]/60 hover:bg-[#1C1C1C]"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".geojson,.json,.kml,.kmz,.zip"
                onChange={handleFileChange}
                className="hidden"
              />
              <Upload className="w-6 h-6 text-emerald-400 mx-auto mb-2" />
              <div className="font-bold text-neutral-100 text-[11px]">
                {isUploading ? 'Validating geometry...' : 'Upload AOI Boundary File'}
              </div>
              <div className="text-[10px] text-neutral-500 mt-1">
                Supports GeoJSON, KML, KMZ, or Shapefile (.zip)
              </div>
            </div>

            {errorMsg && (
              <div className="p-2.5 rounded-lg bg-rose-950/50 border border-rose-800 text-rose-300 text-[11px] flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
                <span>{errorMsg}</span>
              </div>
            )}
          </div>
        ) : (
          /* Validated AOI Geometry Details */
          <div className="space-y-3">
            <div className="p-3 rounded-xl bg-neutral-900 border border-emerald-500/30 space-y-2">
              <div className="flex items-center justify-between">
                <div className="font-bold text-sm text-white">{importedAOI.name}</div>
                <span className="text-[9px] font-bold text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800/80">
                  VALIDATED GEOMETRY
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-1 text-[11px]">
                <div className="bg-neutral-800/60 p-2 rounded">
                  <span className="text-neutral-500 text-[10px] block">GEODESIC AREA</span>
                  <strong className="text-emerald-400 text-sm">{importedAOI.area_ha} ha</strong>
                  <span className="text-neutral-400 text-[10px] block">
                    ({importedAOI.area_m2?.toLocaleString()} m²)
                  </span>
                </div>
                <div className="bg-neutral-800/60 p-2 rounded">
                  <span className="text-neutral-500 text-[10px] block">PERIMETER</span>
                  <strong className="text-white text-sm">{importedAOI.perimeter_m?.toLocaleString()} m</strong>
                  <span className="text-neutral-400 text-[10px] block">
                    CRS: {importedAOI.crs || 'EPSG:4326'}
                  </span>
                </div>
              </div>

              {importedAOI.bbox && (
                <div className="text-[10px] text-neutral-400 pt-1">
                  BBOX: [{importedAOI.bbox.join(', ')}]
                </div>
              )}
            </div>

            {/* Observation History Timeline */}
            <div className="space-y-1">
              <div className="text-[10px] uppercase font-bold tracking-wider text-neutral-400 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-neutral-400" />
                <span>Multi-Temporal Observation Epochs</span>
              </div>
              <div className="bg-neutral-900/80 rounded-lg p-2 divide-y divide-neutral-800 text-[11px]">
                <div className="py-1 flex items-center justify-between">
                  <span className="text-neutral-300">2024-01-18 · Sentinel-2A</span>
                  <span className="text-emerald-400 text-[10px]">Cloud: 1.2%</span>
                </div>
                <div className="py-1 flex items-center justify-between">
                  <span className="text-neutral-300">2024-08-02 · Sentinel-2B</span>
                  <span className="text-emerald-400 text-[10px]">Cloud: 4.8%</span>
                </div>
                <div className="py-1 flex items-center justify-between">
                  <span className="text-neutral-300">2025-02-14 · Sentinel-1A (SAR)</span>
                  <span className="text-cyan-400 text-[10px]">VV + VH</span>
                </div>
                <div className="py-1 flex items-center justify-between">
                  <span className="text-neutral-300">2026-03-21 · Sentinel-2A</span>
                  <span className="text-emerald-400 text-[10px]">Cloud: 0.4%</span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/10">
              <button
                onClick={() => setImportedAOI(null)}
                className="px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-xs font-bold transition-colors"
              >
                Upload Different File
              </button>
              <button
                onClick={handleApplyAOI}
                className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-1.5 transition-colors shadow-sm"
              >
                <span>Focus & Analyze AOI</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
