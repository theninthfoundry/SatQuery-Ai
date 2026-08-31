'use client';

import React from 'react';
import { LensMode, TemporalViewMode, ChangeCluster } from '../../context/WorkspaceContext';

interface SatelliteObservationCanvasProps {
  activeLens: LensMode;
  activeDatasetIndex: number;
  temporalMode: TemporalViewMode;
  sliderPos: number;
  onSliderChange?: (pos: number) => void;
  clusters: ChangeCluster[];
  selectedClusterId: string | null;
  onSelectCluster: (id: string | null) => void;
  previewUrl?: string | null;
  dateT1: string;
  dateT2: string;
}

export const SatelliteObservationCanvas: React.FC<SatelliteObservationCanvasProps> = ({
  activeLens,
  activeDatasetIndex,
  temporalMode,
  sliderPos,
  clusters,
  selectedClusterId,
  onSelectCluster,
  previewUrl,
  dateT1,
  dateT2,
}) => {
  const isT1 = activeDatasetIndex === 0;
  const isSAR = activeDatasetIndex === 2 || activeLens === 'SAR';

  // Authentic Remote Sensing Raster Layer Visuals
  // T1 (2024 Baseline): Rural-urban fringe with open vegetation, water bodies, and sparse settlement
  const renderOpticalT1 = () => (
    <svg className="w-full h-full" viewBox="0 0 1000 1000" preserveAspectRatio="none">
      <defs>
        {/* Terrain Gradients */}
        <linearGradient id="t1-ground" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4A5844" />
          <stop offset="40%" stopColor="#556B48" />
          <stop offset="75%" stopColor="#3E4C38" />
          <stop offset="100%" stopColor="#45543D" />
        </linearGradient>

        {/* Agricultural Pattern */}
        <pattern id="t1-agri-fields" width="80" height="80" patternUnits="userSpaceOnUse">
          <rect width="78" height="78" fill="#586E4B" opacity="0.8" />
          <rect x="80" width="78" height="78" fill="#4D6141" opacity="0.6" />
          <line x1="0" y1="0" x2="80" y2="0" stroke="#33402C" strokeWidth="2" />
          <line x1="0" y1="0" x2="0" y2="80" stroke="#33402C" strokeWidth="2" />
        </pattern>

        {/* Urban Settlement Texture */}
        <pattern id="t1-urban-grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <rect width="36" height="36" fill="#8C8880" opacity="0.6" />
          <rect x="4" y="4" width="12" height="12" fill="#A39E94" />
          <rect x="20" y="4" width="12" height="12" fill="#B5AEA3" />
          <rect x="4" y="20" width="12" height="12" fill="#999388" />
          <rect x="20" y="20" width="12" height="12" fill="#827D74" />
        </pattern>
      </defs>

      {/* Base Vegetation / Soil Layer */}
      <rect width="1000" height="1000" fill="url(#t1-ground)" />
      <rect x="50" y="50" width="900" height="900" fill="url(#t1-agri-fields)" opacity="0.7" />

      {/* Natural Water Reservoirs / Lakes */}
      <path
        d="M 680 180 Q 750 140 840 190 T 920 320 T 820 420 T 700 350 Z"
        fill="#1E3338"
        stroke="#142428"
        strokeWidth="3"
      />
      <path
        d="M 120 720 Q 180 680 240 740 T 280 840 T 190 900 T 110 820 Z"
        fill="#1E3338"
        stroke="#142428"
        strokeWidth="2"
      />

      {/* Primary Transportation Corridor (NH-44 Bypass) */}
      <path
        d="M 0 450 Q 300 480 600 420 T 1000 410"
        fill="none"
        stroke="#3A3835"
        strokeWidth="14"
      />
      <path
        d="M 0 450 Q 300 480 600 420 T 1000 410"
        fill="none"
        stroke="#6B665F"
        strokeWidth="10"
      />

      {/* Secondary Arterial Roads */}
      <path d="M 420 0 L 460 1000" stroke="#524E48" strokeWidth="6" />
      <path d="M 720 0 L 680 1000" stroke="#524E48" strokeWidth="5" />
      <path d="M 0 780 L 1000 720" stroke="#524E48" strokeWidth="5" />

      {/* Existing Built-up Settlements in 2024 */}
      <rect x="440" y="320" width="140" height="90" fill="url(#t1-urban-grid)" />
      <rect x="180" y="220" width="160" height="180" fill="url(#t1-urban-grid)" />
      <rect x="680" y="520" width="180" height="150" fill="url(#t1-urban-grid)" />

      {/* Undeveloped Land Parcels (Candidate Change Areas in 2024) */}
      <rect x="360" y="470" width="190" height="160" fill="#637854" opacity="0.9" stroke="#4F6143" strokeWidth="2" />
      <rect x="580" y="460" width="180" height="170" fill="#5F7351" opacity="0.9" stroke="#4F6143" strokeWidth="2" />
    </svg>
  );

  // T2 (2026 Post-Expansion): Urban expansion, new construction, cleared ground, industrial roofs
  const renderOpticalT2 = () => (
    <svg className="w-full h-full" viewBox="0 0 1000 1000" preserveAspectRatio="none">
      <defs>
        <linearGradient id="t2-ground" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4A5844" />
          <stop offset="40%" stopColor="#556B48" />
          <stop offset="75%" stopColor="#3E4C38" />
          <stop offset="100%" stopColor="#45543D" />
        </linearGradient>

        <pattern id="t2-agri-fields" width="80" height="80" patternUnits="userSpaceOnUse">
          <rect width="78" height="78" fill="#586E4B" opacity="0.8" />
          <rect x="80" width="78" height="78" fill="#4D6141" opacity="0.6" />
          <line x1="0" y1="0" x2="80" y2="0" stroke="#33402C" strokeWidth="2" />
          <line x1="0" y1="0" x2="0" y2="80" stroke="#33402C" strokeWidth="2" />
        </pattern>

        <pattern id="t2-urban-grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <rect width="36" height="36" fill="#8C8880" opacity="0.6" />
          <rect x="4" y="4" width="12" height="12" fill="#A39E94" />
          <rect x="20" y="4" width="12" height="12" fill="#B5AEA3" />
          <rect x="4" y="20" width="12" height="12" fill="#999388" />
          <rect x="20" y="20" width="12" height="12" fill="#827D74" />
        </pattern>

        {/* New Tech Park / Concrete Roofs Texture */}
        <pattern id="t2-tech-park" width="30" height="30" patternUnits="userSpaceOnUse">
          <rect width="28" height="28" fill="#C2BBB0" stroke="#8C857B" strokeWidth="1" />
          <rect x="3" y="3" width="10" height="10" fill="#D9D4CB" />
          <rect x="15" y="15" width="10" height="10" fill="#E8E4DC" />
        </pattern>
      </defs>

      {/* Base Layer */}
      <rect width="1000" height="1000" fill="url(#t2-ground)" />
      <rect x="50" y="50" width="900" height="900" fill="url(#t2-agri-fields)" opacity="0.6" />

      {/* Water Bodies (Slight seasonal boundary shift) */}
      <path
        d="M 680 180 Q 750 140 840 190 T 920 320 T 820 420 T 700 350 Z"
        fill="#1A2D32"
        stroke="#142428"
        strokeWidth="3"
      />
      <path
        d="M 120 720 Q 180 680 240 740 T 280 840 T 190 900 T 110 820 Z"
        fill="#1A2D32"
        stroke="#142428"
        strokeWidth="2"
      />

      {/* Highway Network */}
      <path d="M 0 450 Q 300 480 600 420 T 1000 410" fill="none" stroke="#2B2A28" strokeWidth="14" />
      <path d="M 0 450 Q 300 480 600 420 T 1000 410" fill="none" stroke="#5A5650" strokeWidth="10" />
      <path d="M 420 0 L 460 1000" stroke="#45423D" strokeWidth="6" />
      <path d="M 720 0 L 680 1000" stroke="#45423D" strokeWidth="5" />
      <path d="M 0 780 L 1000 720" stroke="#45423D" strokeWidth="5" />

      {/* Pre-existing Settlements */}
      <rect x="440" y="320" width="140" height="90" fill="url(#t2-urban-grid)" />
      <rect x="180" y="220" width="160" height="180" fill="url(#t2-urban-grid)" />
      <rect x="680" y="520" width="180" height="150" fill="url(#t2-urban-grid)" />

      {/* NEW 2026 BUILT-UP EXPANSION CLUSTER 01 (12,400 m²) */}
      <rect x="360" y="470" width="190" height="160" fill="url(#t2-tech-park)" stroke="#7A746B" strokeWidth="2" />
      <rect x="375" y="485" width="70" height="60" fill="#EAE5DC" stroke="#9E988E" strokeWidth="1.5" />
      <rect x="460" y="485" width="75" height="60" fill="#E0DBD2" stroke="#9E988E" strokeWidth="1.5" />
      <rect x="375" y="560" width="160" height="55" fill="#D4CEC5" stroke="#9E988E" strokeWidth="1.5" />

      {/* NEW 2026 BUILT-UP EXPANSION CLUSTER 02 (13,200 m²) */}
      <rect x="580" y="460" width="180" height="170" fill="url(#t2-tech-park)" stroke="#7A746B" strokeWidth="2" />
      <rect x="595" y="475" width="150" height="65" fill="#EAE5DC" stroke="#9E988E" strokeWidth="1.5" />
      <rect x="595" y="555" width="70" height="60" fill="#E0DBD2" stroke="#9E988E" strokeWidth="1.5" />
      <rect x="675" y="555" width="70" height="60" fill="#D4CEC5" stroke="#9E988E" strokeWidth="1.5" />
    </svg>
  );

  // False Color NIR (Near-Infrared Composite): Vegetation is bright red/magenta, built-up cyan, water black
  const renderNIR = () => (
    <svg className="w-full h-full" viewBox="0 0 1000 1000" preserveAspectRatio="none">
      <defs>
        <linearGradient id="nir-vegetation" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#A82038" />
          <stop offset="40%" stopColor="#C42845" />
          <stop offset="75%" stopColor="#8F1B30" />
          <stop offset="100%" stopColor="#A82038" />
        </linearGradient>

        <pattern id="nir-agri" width="80" height="80" patternUnits="userSpaceOnUse">
          <rect width="78" height="78" fill="#D63150" opacity="0.8" />
          <rect x="80" width="78" height="78" fill="#B5223E" opacity="0.6" />
        </pattern>
      </defs>

      {/* High Chlorophyll Vegetative Matrix */}
      <rect width="1000" height="1000" fill="url(#nir-vegetation)" />
      <rect x="50" y="50" width="900" height="900" fill="url(#nir-agri)" opacity="0.7" />

      {/* Deep Black Water Absorption */}
      <path
        d="M 680 180 Q 750 140 840 190 T 920 320 T 820 420 T 700 350 Z"
        fill="#080D10"
        stroke="#040608"
        strokeWidth="3"
      />
      <path
        d="M 120 720 Q 180 680 240 740 T 280 840 T 190 900 T 110 820 Z"
        fill="#080D10"
        stroke="#040608"
        strokeWidth="2"
      />

      {/* Cyan / Gray Built-up Reflectance */}
      <path d="M 0 450 Q 300 480 600 420 T 1000 410" fill="none" stroke="#2B4045" strokeWidth="12" />
      <rect x="440" y="320" width="140" height="90" fill="#587A82" opacity="0.9" />
      <rect x="180" y="220" width="160" height="180" fill="#587A82" opacity="0.9" />
      <rect x="680" y="520" width="180" height="150" fill="#587A82" opacity="0.9" />

      {/* Converted Alteration Zones in NIR */}
      <rect x="360" y="470" width="190" height="160" fill="#75A1AC" stroke="#4A6F78" strokeWidth="2" />
      <rect x="580" y="460" width="180" height="170" fill="#75A1AC" stroke="#4A6F78" strokeWidth="2" />
    </svg>
  );

  // Sentinel-1 C-band SAR (Synthetic Aperture Radar Backscatter σ⁰): Specular water is black, double-bounce urban structures are white
  const renderSAR = () => (
    <svg className="w-full h-full" viewBox="0 0 1000 1000" preserveAspectRatio="none">
      <defs>
        {/* Radar Speckle Noise Simulation */}
        <pattern id="sar-speckle" width="20" height="20" patternUnits="userSpaceOnUse">
          <rect width="20" height="20" fill="#3D3D3D" />
          <circle cx="3" cy="5" r="1.5" fill="#666666" />
          <circle cx="12" cy="14" r="1" fill="#222222" />
          <circle cx="17" cy="6" r="1.2" fill="#555555" />
          <circle cx="7" cy="18" r="1" fill="#777777" />
        </pattern>
      </defs>

      {/* Rough Soil / Canopy Matrix (-18 dB) */}
      <rect width="1000" height="1000" fill="url(#sar-speckle)" />

      {/* Specular Water Absorption (-26 dB) */}
      <path
        d="M 680 180 Q 750 140 840 190 T 920 320 T 820 420 T 700 350 Z"
        fill="#0A0A0A"
        stroke="#1A1A1A"
        strokeWidth="2"
      />
      <path
        d="M 120 720 Q 180 680 240 740 T 280 840 T 190 900 T 110 820 Z"
        fill="#0A0A0A"
        stroke="#1A1A1A"
        strokeWidth="2"
      />

      {/* Moderate Urban Backscatter (-15 dB) */}
      <rect x="440" y="320" width="140" height="90" fill="#999999" />
      <rect x="180" y="220" width="160" height="180" fill="#999999" />
      <rect x="680" y="520" width="180" height="150" fill="#999999" />

      {/* High Double-Bounce Radar Return on New Concrete Roofs (-14.5 dB) */}
      <rect x="360" y="470" width="190" height="160" fill="#E0E0E0" stroke="#FFFFFF" strokeWidth="2" />
      <rect x="375" y="485" width="70" height="60" fill="#FFFFFF" />
      <rect x="460" y="485" width="75" height="60" fill="#FFFFFF" />

      <rect x="580" y="460" width="180" height="170" fill="#E0E0E0" stroke="#FFFFFF" strokeWidth="2" />
      <rect x="595" y="475" width="150" height="65" fill="#FFFFFF" />
      <rect x="595" y="555" width="70" height="60" fill="#FFFFFF" />
    </svg>
  );

  // Direct ChangeNet 2D Probability Heatmap
  const renderChangeHeatmap = () => (
    <svg className="w-full h-full" viewBox="0 0 1000 1000" preserveAspectRatio="none">
      {/* Background T2 Observation */}
      {renderOpticalT2()}

      {/* Neural Probability Heatmap Layer */}
      <defs>
        <radialGradient id="heat-c1" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#EF4444" stopOpacity="0.85" />
          <stop offset="70%" stopColor="#F97316" stopOpacity="0.55" />
          <stop offset="100%" stopColor="#EF4444" stopOpacity="0.0" />
        </radialGradient>
        <radialGradient id="heat-c2" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#EF4444" stopOpacity="0.85" />
          <stop offset="70%" stopColor="#F97316" stopOpacity="0.55" />
          <stop offset="100%" stopColor="#EF4444" stopOpacity="0.0" />
        </radialGradient>
      </defs>

      {/* Heatmap Blobs on Altered Regions */}
      <ellipse cx="455" cy="550" rx="110" ry="90" fill="url(#heat-c1)" />
      <ellipse cx="670" cy="545" rx="105" ry="95" fill="url(#heat-c2)" />
    </svg>
  );

  return (
    <div className="relative w-full h-full select-none overflow-hidden flex items-center justify-center bg-[#0A0A0A]">
      {/* 1. Temporal Swipe Mode (T1 on Left, T2 on Right with divider) */}
      {temporalMode === 'Swipe' && (activeLens === 'CHANGE' || activeLens === 'True Color') ? (
        <div className="relative w-full h-full overflow-hidden">
          {/* Base Layer: T2 (2026) */}
          <div className="absolute inset-0 w-full h-full">
            {renderOpticalT2()}
          </div>

          {/* Clipped Top Layer: T1 (2024) */}
          <div
            className="absolute inset-y-0 left-0 overflow-hidden border-r-2 border-white shadow-[0_0_16px_rgba(255,255,255,0.8)] z-10"
            style={{ width: `${sliderPos}%` }}
          >
            <div
              className="absolute inset-y-0 left-0 h-full"
              style={{ width: `${100 / (sliderPos / 100)}%` }}
            >
              {renderOpticalT1()}
            </div>

            {/* T1 Label Badge */}
            <div className="absolute top-16 left-4 bg-black/80 backdrop-blur-md text-white px-2.5 py-1 rounded-md text-[10px] font-mono font-bold border border-white/20">
              T1 · {dateT1}
            </div>
          </div>

          {/* T2 Label Badge */}
          <div className="absolute top-16 right-4 bg-black/80 backdrop-blur-md text-white px-2.5 py-1 rounded-md text-[10px] font-mono font-bold border border-white/20 z-5">
            T2 · {dateT2}
          </div>
        </div>
      ) : temporalMode === 'SideBySide' ? (
        /* 2. Side-By-Side Mode (Dual Viewports) */
        <div className="grid grid-cols-2 w-full h-full divide-x divide-white/20">
          <div className="relative w-full h-full overflow-hidden">
            {renderOpticalT1()}
            <div className="absolute top-16 left-4 bg-black/80 backdrop-blur-md text-white px-2.5 py-1 rounded-md text-[10px] font-mono font-bold border border-white/20">
              T1 · {dateT1}
            </div>
          </div>
          <div className="relative w-full h-full overflow-hidden">
            {renderOpticalT2()}
            <div className="absolute top-16 left-4 bg-black/80 backdrop-blur-md text-white px-2.5 py-1 rounded-md text-[10px] font-mono font-bold border border-white/20">
              T2 · {dateT2}
            </div>
          </div>
        </div>
      ) : activeLens === 'NIR' ? (
        /* 3. NIR Multispectral View */
        renderNIR()
      ) : isSAR ? (
        /* 4. Sentinel-1 SAR Radar View */
        renderSAR()
      ) : activeLens === 'CHANGE' ? (
        /* 5. ChangeNet Probability Heatmap */
        renderChangeHeatmap()
      ) : isT1 ? (
        /* 6. Single Image T1 */
        renderOpticalT1()
      ) : (
        /* 7. Single Image T2 */
        renderOpticalT2()
      )}

      {/* Vector Polygons Over Change Regions */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none z-20"
        viewBox="0 0 1000 1000"
        preserveAspectRatio="none"
      >
        {clusters.map((cluster) => {
          const x = cluster.bbox.xmin * 1000;
          const y = cluster.bbox.ymin * 1000;
          const w = (cluster.bbox.xmax - cluster.bbox.xmin) * 1000;
          const h = (cluster.bbox.ymax - cluster.bbox.ymin) * 1000;
          const isSelected = selectedClusterId === cluster.id;

          return (
            <g
              key={cluster.id}
              onClick={(e) => {
                e.stopPropagation();
                onSelectCluster(isSelected ? null : cluster.id);
              }}
              className="pointer-events-auto cursor-pointer group"
            >
              {/* Alteration Region Bounding Polygon */}
              <rect
                x={x}
                y={y}
                width={w}
                height={h}
                fill={isSelected ? 'rgba(239, 68, 68, 0.40)' : 'rgba(239, 68, 68, 0.22)'}
                stroke="#EF4444"
                strokeWidth={isSelected ? '3.5' : '2'}
                strokeDasharray="6 4"
                className="transition-all duration-200"
              />

              {/* Tag Callout (01 / 02) */}
              <rect
                x={x - 12}
                y={y - 12}
                width="24"
                height="24"
                rx="4"
                fill="#EF4444"
                className="drop-shadow-md"
              />
              <text
                x={x}
                y={y + 4}
                textAnchor="middle"
                fill="#FFFFFF"
                fontSize="11"
                fontFamily="ui-monospace, monospace"
                fontWeight="bold"
              >
                {cluster.tag}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
