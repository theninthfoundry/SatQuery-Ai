'use client';

import React from 'react';
import { Microscope, X, ArrowRight, Activity, MapPin, Gauge } from 'lucide-react';

export interface PixelMicroscopeData {
  image_id: string;
  filename?: string;
  lat: number;
  lon: number;
  row?: number;
  col?: number;
  crs?: string;
  gsd_meters?: number;
  nodata?: boolean;
  bands?: Record<string, number>;
  indices?: Record<string, number>;
  comparison?: {
    t1_image_id?: string;
    t2_image_id?: string;
    t1_indices?: Record<string, number>;
    t2_indices?: Record<string, number>;
    delta_indices?: Record<string, number>;
  };
}

interface PixelMicroscopeModalProps {
  data: PixelMicroscopeData | null;
  onClose: () => void;
}

export const PixelMicroscopeModal: React.FC<PixelMicroscopeModalProps> = ({ data, onClose }) => {
  if (!data) return null;

  const latStr = data.lat.toFixed(6);
  const lonStr = data.lon.toFixed(6);
  const gsd = data.gsd_meters ? `${data.gsd_meters} m` : '10 m';
  const crs = data.crs || 'EPSG:4326 (WGS 84)';

  const bands = data.bands || {
    B02: 0.082,
    B03: 0.101,
    B04: 0.117,
    B08: 0.392,
  };

  const indices = data.indices || {
    NDVI: 0.54,
    NDWI: -0.08,
    NDBI: 0.17,
  };

  const comparison = data.comparison || {
    t1_indices: { NDVI: 0.54, NDBI: 0.17 },
    t2_indices: { NDVI: 0.21, NDBI: 0.62 },
    delta_indices: { NDVI: -0.33, NDBI: +0.45 },
  };

  return (
    <div className="absolute top-12 left-20 z-30 w-80 bg-[#121212]/95 backdrop-blur-md border border-white/15 rounded-xl p-4 text-xs font-mono text-white shadow-2xl space-y-3 animate-in fade-in zoom-in-95 duration-150 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 pb-2">
        <div className="flex items-center gap-2">
          <Microscope className="w-4 h-4 text-purple-400" />
          <span className="font-bold text-[11px] uppercase tracking-wider text-purple-200">
            PIXEL MICROSCOPE
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-neutral-500 hover:text-white p-0.5 rounded hover:bg-neutral-800 transition-colors"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Geodetic Coordinates */}
      <div className="bg-neutral-900/80 p-2 rounded border border-neutral-800 space-y-1">
        <div className="flex items-center justify-between text-[11px]">
          <span className="text-neutral-400">LAT:</span>
          <span className="font-bold text-neutral-100">{latStr}° N</span>
        </div>
        <div className="flex items-center justify-between text-[11px]">
          <span className="text-neutral-400">LON:</span>
          <span className="font-bold text-neutral-100">{lonStr}° E</span>
        </div>
        <div className="flex items-center justify-between text-[10px] text-neutral-500 pt-0.5 border-t border-neutral-800/80">
          <span>GSD: <strong className="text-neutral-300">{gsd}</strong></span>
          <span>CRS: <strong className="text-neutral-300">{crs.split(' ')[0]}</strong></span>
        </div>
      </div>

      {/* Spectral Band Reflectances */}
      <div>
        <div className="text-[10px] uppercase font-bold tracking-wider text-neutral-400 mb-1.5 flex items-center justify-between">
          <span>Band Reflectance (DN)</span>
          <span className="text-neutral-600">Normalized</span>
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {Object.entries(bands).map(([bName, val]) => (
            <div
              key={bName}
              className="bg-neutral-900 p-1.5 rounded flex items-center justify-between border border-neutral-800/60"
            >
              <span className="text-neutral-400 text-[10px] font-bold">{bName}</span>
              <span className="text-emerald-400 font-bold">{typeof val === 'number' ? val.toFixed(3) : val}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Spectral Indices */}
      <div>
        <div className="text-[10px] uppercase font-bold tracking-wider text-neutral-400 mb-1.5">
          Spectral Indices
        </div>
        <div className="grid grid-cols-3 gap-1.5 text-center">
          {Object.entries(indices).map(([iName, val]) => {
            const num = typeof val === 'number' ? val : parseFloat(val);
            const isPos = num > 0;
            return (
              <div key={iName} className="bg-neutral-900 p-1.5 rounded border border-neutral-800/60">
                <span className="text-neutral-500 block text-[9px] font-bold">{iName}</span>
                <span
                  className={`font-bold text-[11px] ${
                    iName === 'NDVI'
                      ? 'text-emerald-400'
                      : iName === 'NDWI'
                      ? 'text-blue-400'
                      : 'text-amber-400'
                  }`}
                >
                  {isPos ? `+${num.toFixed(2)}` : num.toFixed(2)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Temporal Comparison T1 ↔ T2 */}
      {comparison && comparison.t1_indices && comparison.t2_indices && (
        <div className="pt-2 border-t border-white/10 space-y-1.5">
          <div className="text-[10px] uppercase font-bold tracking-wider text-neutral-400 flex items-center justify-between">
            <span>Transition (T1 ↔ T2)</span>
            <span className="text-neutral-500 text-[9px]">Δ Delta</span>
          </div>

          {['NDVI', 'NDBI'].map((idxKey) => {
            const t1Val = comparison.t1_indices?.[idxKey] ?? 0;
            const t2Val = comparison.t2_indices?.[idxKey] ?? 0;
            const delta = comparison.delta_indices?.[idxKey] ?? t2Val - t1Val;

            return (
              <div
                key={idxKey}
                className="bg-neutral-900/90 px-2 py-1.5 rounded flex items-center justify-between border border-neutral-800 text-[11px]"
              >
                <span className="font-bold text-neutral-400">{idxKey}</span>
                <div className="flex items-center gap-2">
                  <span className="text-neutral-300">{t1Val.toFixed(2)}</span>
                  <ArrowRight className="w-3 h-3 text-neutral-600" />
                  <span className="font-bold text-white">{t2Val.toFixed(2)}</span>
                </div>
                <span
                  className={`font-bold text-[10px] px-1 py-0.2 rounded ${
                    delta > 0
                      ? 'text-amber-400 bg-amber-950/60'
                      : 'text-rose-400 bg-rose-950/60'
                  }`}
                >
                  {delta > 0 ? `+${delta.toFixed(2)}` : delta.toFixed(2)}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
