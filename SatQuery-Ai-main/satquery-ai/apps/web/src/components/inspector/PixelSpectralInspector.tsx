'use client';

import React, { useState } from 'react';
import {
  Activity,
  Radio,
  Layers,
  ChevronDown,
  ChevronUp,
  X,
  Sparkles,
  BarChart2,
  Maximize2,
  HelpCircle,
} from 'lucide-react';
import { SpectralPointData, ZonalStatistics } from '../../types/aoi';
import { useWorkspace } from '../../context/WorkspaceContext';

interface PixelSpectralInspectorProps {
  pointData: SpectralPointData | null;
  zonalStats: ZonalStatistics | null;
  onClose?: () => void;
}

const WAVELENGTHS = [
  { band: 'B02', name: 'Blue', wl: 490, key: 'b02', color: '#3B82F6' },
  { band: 'B03', name: 'Green', wl: 560, key: 'b03', color: '#10B981' },
  { band: 'B04', name: 'Red', wl: 665, key: 'b04', color: '#EF4444' },
  { band: 'B05', name: 'RE1', wl: 705, key: 'b05', color: '#F59E0B' },
  { band: 'B06', name: 'RE2', wl: 740, key: 'b06', color: '#EAB308' },
  { band: 'B07', name: 'RE3', wl: 783, key: 'b07', color: '#84CC16' },
  { band: 'B08', name: 'NIR', wl: 842, key: 'b08', color: '#065F46' },
  { band: 'B8A', name: 'NNIR', wl: 865, key: 'b8a', color: '#047857' },
  { band: 'B11', name: 'SWIR1', wl: 1610, key: 'b11', color: '#D97706' },
  { band: 'B12', name: 'SWIR2', wl: 2190, key: 'b12', color: '#92400E' },
];

export const PixelSpectralInspector: React.FC<PixelSpectralInspectorProps> = ({
  pointData,
  zonalStats,
  onClose,
}) => {
  const ws = useWorkspace();
  const [activeTab, setActiveTab] = useState<'pixel' | 'zonal'>('pixel');
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [hoveredBand, setHoveredBand] = useState<string | null>(null);

  if (!pointData && !zonalStats) return null;

  // Fallback point data if inspecting without click yet
  const pt = pointData || {
    lat: ws.currentMission.lat,
    lon: ws.currentMission.lon,
    utmE: 485120,
    utmN: 1387400,
    gsd: '10 m',
    landCover: 'URBAN BUILT-UP / VEGETATION',
    bands: {
      b02: 0.081,
      b03: 0.104,
      b04: 0.097,
      b05: 0.183,
      b06: 0.241,
      b07: 0.298,
      b08: 0.512,
      b8a: 0.481,
      b11: 0.214,
      b12: 0.176,
    },
    indices: {
      ndvi: 0.68,
      ndwi: 0.12,
      ndbi: -0.31,
    },
    sar: {
      vvDb: -8.4,
      vhDb: -15.7,
      ratioDb: 7.3,
    },
  };

  // Generate SVG points for the Reflectance vs Wavelength Curve
  // X range: 400nm to 2300nm -> mapping to SVG width 340px (padding 30px to 330px)
  // Y range: 0.0 to 0.7 -> mapping to SVG height 110px (padding 90px to 15px)
  const svgWidth = 340;
  const svgHeight = 110;
  const minWl = 400;
  const maxWl = 2300;
  const maxY = 0.7;

  const points = WAVELENGTHS.map((item) => {
    const val = (pt.bands as any)[item.key] || 0;
    const x = 30 + ((item.wl - minWl) / (maxWl - minWl)) * (svgWidth - 45);
    const y = svgHeight - 20 - (val / maxY) * (svgHeight - 35);
    return { ...item, val, x, y };
  });

  const pathD = points.reduce((acc, p, idx) => {
    return idx === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
  }, '');

  return (
    <div className="bg-[#121212]/95 backdrop-blur-md border border-neutral-800 rounded-lg shadow-2xl text-xs font-mono w-88 max-w-[360px] overflow-hidden flex flex-col transition-all">
      {/* Inspector Title Bar */}
      <div className="flex items-center justify-between px-3 py-2 bg-[#181818] border-b border-neutral-800 select-none">
        <div className="flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          <span className="font-bold text-white text-[11px] tracking-wide uppercase">
            {activeTab === 'pixel' ? 'PIXEL INSPECTOR' : 'ZONAL STATISTICS'}
          </span>
          <span className="text-[9px] px-1 py-0.2 rounded bg-neutral-800 text-neutral-400">
            {pt.gsd}
          </span>
        </div>

        <div className="flex items-center gap-1">
          {zonalStats && (
            <div className="flex bg-neutral-900 rounded p-0.5 border border-neutral-800 text-[9px] mr-1">
              <button
                onClick={() => setActiveTab('pixel')}
                className={`px-1.5 py-0.5 rounded ${
                  activeTab === 'pixel' ? 'bg-neutral-800 text-white font-bold' : 'text-neutral-400'
                }`}
              >
                POINT
              </button>
              <button
                onClick={() => setActiveTab('zonal')}
                className={`px-1.5 py-0.5 rounded ${
                  activeTab === 'zonal' ? 'bg-neutral-800 text-white font-bold' : 'text-neutral-400'
                }`}
              >
                ZONAL
              </button>
            </div>
          )}

          <button
            onClick={() => setIsMinimized((v) => !v)}
            className="p-1 text-neutral-400 hover:text-white rounded hover:bg-neutral-800"
            title={isMinimized ? 'Expand' : 'Minimize'}
          >
            {isMinimized ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
          </button>

          {onClose && (
            <button
              onClick={onClose}
              className="p-1 text-neutral-400 hover:text-white rounded hover:bg-neutral-800"
              title="Close Inspector"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {!isMinimized && (
        <div className="p-3 space-y-3 max-h-[480px] overflow-y-auto">
          {activeTab === 'pixel' ? (
            <>
              {/* Geodetic & Coordinate Header */}
              <div className="bg-[#181818] p-2 rounded border border-neutral-800/80 flex items-center justify-between text-[10px]">
                <div>
                  <span className="text-neutral-500 block">GEODETIC (WGS84)</span>
                  <strong className="text-white">
                    {pt.lat.toFixed(4)}°N, {pt.lon.toFixed(4)}°E
                  </strong>
                </div>
                <div className="text-right">
                  <span className="text-neutral-500 block">UTM PROJECTED</span>
                  <span className="text-neutral-300">
                    E:{pt.utmE} N:{pt.utmN}
                  </span>
                </div>
              </div>

              {/* Spectral Reflectance Curve Graph */}
              <div className="bg-[#0A0A0A] p-2 rounded border border-neutral-800/80">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[9px] text-neutral-400 uppercase font-bold tracking-wider">
                    REFLECTANCE vs WAVELENGTH (nm)
                  </span>
                  {hoveredBand && (
                    <span className="text-[10px] text-emerald-400 font-bold">
                      {hoveredBand}
                    </span>
                  )}
                </div>

                <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-24 overflow-visible">
                  {/* Grid Lines */}
                  <line x1="30" y1="20" x2={svgWidth - 10} y2="20" stroke="#262626" strokeDasharray="2,2" />
                  <line x1="30" y1="50" x2={svgWidth - 10} y2="50" stroke="#262626" strokeDasharray="2,2" />
                  <line x1="30" y1="80" x2={svgWidth - 10} y2="80" stroke="#262626" strokeDasharray="2,2" />

                  {/* Y Axis Labels */}
                  <text x="5" y="24" fill="#737373" fontSize="8" fontFamily="monospace">
                    0.6
                  </text>
                  <text x="5" y="54" fill="#737373" fontSize="8" fontFamily="monospace">
                    0.3
                  </text>
                  <text x="5" y="84" fill="#737373" fontSize="8" fontFamily="monospace">
                    0.0
                  </text>

                  {/* Spectral Signature Curve */}
                  <path d={pathD} fill="none" stroke="#10B981" strokeWidth="1.8" />

                  {/* Band Points */}
                  {points.map((p) => (
                    <circle
                      key={p.band}
                      cx={p.x}
                      cy={p.y}
                      r={hoveredBand?.includes(p.band) ? '4.5' : '2.5'}
                      fill={p.color}
                      stroke="#FFFFFF"
                      strokeWidth="0.8"
                      className="cursor-pointer transition-all"
                      onMouseEnter={() =>
                        setHoveredBand(`${p.band} (${p.wl}nm): ${p.val}`)
                      }
                      onMouseLeave={() => setHoveredBand(null)}
                    />
                  ))}
                </svg>

                <div className="flex justify-between text-[8px] text-neutral-500 font-mono px-2 pt-0.5 border-t border-neutral-900">
                  <span>490nm (Blue)</span>
                  <span>842nm (NIR)</span>
                  <span>2190nm (SWIR)</span>
                </div>
              </div>

              {/* Sentinel-2 10-Band Multi-Spectral Matrix */}
              <div className="space-y-1">
                <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-widest block">
                  SENTINEL-2 MULTI-SPECTRAL BANDS
                </span>
                <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[10px] bg-[#161616] p-2 rounded border border-neutral-800/80">
                  <div className="flex justify-between">
                    <span className="text-neutral-400">B02 Blue</span>
                    <strong className="text-blue-400">{pt.bands.b02}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">B03 Green</span>
                    <strong className="text-emerald-400">{pt.bands.b03}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">B04 Red</span>
                    <strong className="text-rose-400">{pt.bands.b04}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">B05 Red Edge</span>
                    <strong className="text-amber-400">{pt.bands.b05}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">B06 Red Edge</span>
                    <strong className="text-amber-300">{pt.bands.b06}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">B07 Red Edge</span>
                    <strong className="text-lime-400">{pt.bands.b07}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">B08 NIR (10m)</span>
                    <strong className="text-emerald-300 font-bold">{pt.bands.b08}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">B8A Narrow NIR</span>
                    <strong className="text-emerald-400">{pt.bands.b8a}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">B11 SWIR-1</span>
                    <strong className="text-orange-400">{pt.bands.b11}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">B12 SWIR-2</span>
                    <strong className="text-orange-300">{pt.bands.b12}</strong>
                  </div>
                </div>
              </div>

              {/* Spectral Indices & Sentinel-1 SAR Radar */}
              <div className="grid grid-cols-2 gap-2">
                {/* Biophysical Indices */}
                <div className="bg-[#161616] p-2 rounded border border-neutral-800/80 space-y-1">
                  <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider block">
                    SPECTRAL INDICES
                  </span>
                  <div className="flex justify-between text-[10px]">
                    <span className="text-neutral-400">NDVI</span>
                    <strong className="text-emerald-400">{pt.indices.ndvi}</strong>
                  </div>
                  <div className="flex justify-between text-[10px]">
                    <span className="text-neutral-400">NDWI</span>
                    <strong className="text-blue-400">{pt.indices.ndwi}</strong>
                  </div>
                  <div className="flex justify-between text-[10px]">
                    <span className="text-neutral-400">NDBI</span>
                    <strong className="text-amber-400">{pt.indices.ndbi}</strong>
                  </div>
                </div>

                {/* Sentinel-1 SAR Backscatter */}
                <div className="bg-[#161616] p-2 rounded border border-neutral-800/80 space-y-1">
                  <div className="flex items-center gap-1">
                    <Radio className="w-2.5 h-2.5 text-cyan-400" />
                    <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider">
                      SENTINEL-1 SAR
                    </span>
                  </div>
                  <div className="flex justify-between text-[10px]">
                    <span className="text-neutral-400">VV (dB)</span>
                    <strong className="text-cyan-400">{pt.sar.vvDb} dB</strong>
                  </div>
                  <div className="flex justify-between text-[10px]">
                    <span className="text-neutral-400">VH (dB)</span>
                    <strong className="text-cyan-300">{pt.sar.vhDb} dB</strong>
                  </div>
                  <div className="flex justify-between text-[10px]">
                    <span className="text-neutral-400">VV/VH Ratio</span>
                    <strong className="text-white">{pt.sar.ratioDb} dB</strong>
                  </div>
                </div>
              </div>
            </>
          ) : (
            /* Zonal Statistics Mode */
            zonalStats && (
              <div className="space-y-3">
                <div className="bg-[#181818] p-2.5 rounded border border-neutral-800 space-y-2">
                  <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider block">
                    ZONAL VEGETATION DYNAMICS (NDVI)
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div className="bg-black/40 p-2 rounded">
                      <span className="text-neutral-500 block text-[9px]">MEAN NDVI</span>
                      <strong className="text-emerald-400 text-sm">{zonalStats.meanNDVI}</strong>
                    </div>
                    <div className="bg-black/40 p-2 rounded">
                      <span className="text-neutral-500 block text-[9px]">MEDIAN NDVI</span>
                      <strong className="text-emerald-300 text-sm">{zonalStats.medianNDVI}</strong>
                    </div>
                    <div className="bg-black/40 p-2 rounded">
                      <span className="text-neutral-500 block text-[9px]">STD DEV</span>
                      <strong className="text-white text-sm">±{zonalStats.stdDevNDVI}</strong>
                    </div>
                    <div className="bg-black/40 p-2 rounded">
                      <span className="text-neutral-500 block text-[9px]">RANGE (MIN-MAX)</span>
                      <strong className="text-neutral-300 text-xs">
                        {zonalStats.minNDVI} → {zonalStats.maxNDVI}
                      </strong>
                    </div>
                  </div>
                </div>

                <div className="bg-[#181818] p-2.5 rounded border border-neutral-800 grid grid-cols-2 gap-2 text-[10px]">
                  <div>
                    <span className="text-neutral-500 block">GEODESIC AREA</span>
                    <strong className="text-emerald-400 text-xs">{zonalStats.areaHa} ha</strong>
                  </div>
                  <div>
                    <span className="text-neutral-500 block">PIXELS SAMPLED (10m)</span>
                    <strong className="text-white text-xs">
                      {zonalStats.pixelCount.toLocaleString()} px
                    </strong>
                  </div>
                  <div>
                    <span className="text-neutral-500 block">MEAN NDWI</span>
                    <strong className="text-blue-400">{zonalStats.meanNDWI}</strong>
                  </div>
                  <div>
                    <span className="text-neutral-500 block">MEAN SAR σ⁰</span>
                    <strong className="text-cyan-400">{zonalStats.meanSARdB} dB</strong>
                  </div>
                </div>
              </div>
            )
          )}

          {/* AI Query Prompt on this Point / AOI */}
          <button
            onClick={() => {
              const query =
                activeTab === 'pixel'
                  ? `Explain the spectral signature at (${pt.lat}°N, ${pt.lon}°E): NDVI ${pt.indices.ndvi}, SAR ${pt.sar.vvDb} dB, SWIR ${pt.bands.b11}. What material or surface state is present?`
                  : `Analyze zonal statistics over ${zonalStats?.areaHa} ha: Mean NDVI ${zonalStats?.meanNDVI}, SAR ${zonalStats?.meanSARdB} dB across ${zonalStats?.pixelCount} pixels.`;
              ws.setQueryText(query);
              ws.runQuery(query);
            }}
            className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-[10px] font-bold flex items-center justify-center gap-1.5 transition-colors shadow"
          >
            <Sparkles className="w-3 h-3 text-amber-300" />
            <span>DISPATCH SPECTRAL INFERENCE TO SATQUERY</span>
          </button>
        </div>
      )}
    </div>
  );
};
