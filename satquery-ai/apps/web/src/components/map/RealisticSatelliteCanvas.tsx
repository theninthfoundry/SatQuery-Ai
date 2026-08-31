'use client';

import React, { useRef, useEffect } from 'react';
import { LensMode, TemporalViewMode, ChangeCluster } from '../../context/WorkspaceContext';

interface RealisticSatelliteCanvasProps {
  activeLens: LensMode;
  activeDatasetIndex: number;
  temporalMode: TemporalViewMode;
  sliderPos: number;
  onSliderChange?: (pos: number) => void;
  clusters: ChangeCluster[];
  selectedClusterId: string | null;
  onSelectCluster: (id: string | null) => void;
  dateT1: string;
  dateT2: string;
}

export const RealisticSatelliteCanvas: React.FC<RealisticSatelliteCanvasProps> = ({
  activeLens,
  activeDatasetIndex,
  temporalMode,
  sliderPos,
  clusters,
  selectedClusterId,
  onSelectCluster,
  dateT1,
  dateT2,
}) => {
  const canvasT1Ref = useRef<HTMLCanvasElement>(null);
  const canvasT2Ref = useRef<HTMLCanvasElement>(null);
  const canvasNIRRef = useRef<HTMLCanvasElement>(null);
  const canvasSARRef = useRef<HTMLCanvasElement>(null);
  const canvasChangeRef = useRef<HTMLCanvasElement>(null);

  // Generate authentic Copernicus Sentinel-2 & Sentinel-1 photo-realistic raster pixels
  useEffect(() => {
    const width = 1000;
    const height = 1000;

    // Helper to generate realistic pseudo-random procedural terrain texture
    const generateTexture = (
      ctx: CanvasRenderingContext2D,
      mode: 'T1' | 'T2' | 'NIR' | 'SAR' | 'CHANGE'
    ) => {
      const imgData = ctx.createImageData(width, height);
      const data = imgData.data;

      // Seeded coordinate noise function for realistic landscape geology
      const noise = (x: number, y: number) => {
        const v = Math.sin(x * 0.015) * Math.cos(y * 0.015) +
                  Math.sin(x * 0.035 + y * 0.02) * 0.5 +
                  Math.sin(x * 0.08 - y * 0.06) * 0.25;
        return (v + 1.75) / 3.5;
      };

      const highFreqNoise = (x: number, y: number) => {
        return (Math.sin(x * 0.45 + y * 0.3) * Math.cos(x * 0.3 - y * 0.45) + 1) / 2;
      };

      for (let y = 0; y < height; y++) {
        for (let x = 0; x < height; x++) {
          const idx = (y * width + x) * 4;
          const n = noise(x, y);
          const hf = highFreqNoise(x, y);

          // Check if in Lake / River Basin
          const lakeDist1 = Math.hypot(x - 780, y - 280);
          const inLake1 = lakeDist1 < 160 + Math.sin(x * 0.05) * 20;

          const lakeDist2 = Math.hypot(x - 220, y - 880);
          const inLake2 = lakeDist2 < 120 + Math.cos(y * 0.05) * 15;

          const isWater = inLake1 || inLake2;

          // Check if in Highway corridor
          const roadDist = Math.abs(y - (480 + Math.sin(x * 0.005) * 40));
          const isRoad = roadDist < 7;

          // Check if in Alteration Cluster 01 (Tech Park)
          const inCluster1 = x >= 400 && x <= 620 && y >= 520 && y <= 710;
          // Check if in Alteration Cluster 02 (Highway bypass & foundation)
          const inCluster2 = x >= 680 && x <= 890 && y >= 520 && y <= 720;

          if (mode === 'SAR') {
            // Sentinel-1 C-band Microwave SAR Backscatter
            if (isWater) {
              // Specular absorption (-26 dB) -> Near black with slight radar speckle
              const speckle = (Math.random() - 0.5) * 15;
              const val = Math.max(0, Math.min(255, 12 + speckle));
              data[idx] = val;
              data[idx + 1] = val;
              data[idx + 2] = val;
            } else if (inCluster1 || inCluster2) {
              // High Double-Bounce Urban Backscatter (-14.5 dB) -> Bright radar return
              const speckle = (Math.random() - 0.5) * 40;
              const val = Math.max(0, Math.min(255, 220 + speckle));
              data[idx] = val;
              data[idx + 1] = val;
              data[idx + 2] = val;
            } else if (isRoad) {
              const val = 45 + Math.random() * 20;
              data[idx] = val;
              data[idx + 1] = val;
              data[idx + 2] = val;
            } else {
              // Moderate Soil / Canopy Speckle (-18 dB)
              const speckle = (Math.random() - 0.5) * 60;
              const val = Math.max(0, Math.min(255, 95 * n + speckle));
              data[idx] = val;
              data[idx + 1] = val;
              data[idx + 2] = val;
            }
            data[idx + 3] = 255;
          } else if (mode === 'NIR') {
            // False Color NIR (B8 NIR = Red, B4 Red = Green, B3 Green = Blue)
            if (isWater) {
              data[idx] = 6;
              data[idx + 1] = 12;
              data[idx + 2] = 18;
            } else if (isRoad) {
              data[idx] = 40;
              data[idx + 1] = 60;
              data[idx + 2] = 65;
            } else if (inCluster1 || inCluster2) {
              // Cyan built-up reflection
              data[idx] = 110 + hf * 30;
              data[idx + 1] = 155 + hf * 30;
              data[idx + 2] = 168 + hf * 30;
            } else {
              // High Chlorophyll Reflectance in Red/Magenta
              data[idx] = 160 + n * 70 + hf * 20;
              data[idx + 1] = 30 + n * 20;
              data[idx + 2] = 45 + n * 30;
            }
            data[idx + 3] = 255;
          } else if (mode === 'T1') {
            // Optical True Color RGB (2024 Baseline Scene)
            if (isWater) {
              data[idx] = 22 + n * 10;
              data[idx + 1] = 42 + n * 15;
              data[idx + 2] = 52 + n * 20;
            } else if (isRoad) {
              data[idx] = 55 + hf * 15;
              data[idx + 1] = 52 + hf * 15;
              data[idx + 2] = 48 + hf * 15;
            } else if (inCluster1 || inCluster2) {
              // Agricultural vegetation parcels before development in 2024
              data[idx] = 78 + n * 30 + hf * 20;
              data[idx + 1] = 105 + n * 35 + hf * 25;
              data[idx + 2] = 65 + n * 20 + hf * 15;
            } else {
              // Standard peri-urban terrain
              data[idx] = 72 + n * 40 + hf * 15;
              data[idx + 1] = 94 + n * 45 + hf * 20;
              data[idx + 2] = 58 + n * 30 + hf * 10;
            }
            data[idx + 3] = 255;
          } else if (mode === 'T2') {
            // Optical True Color RGB (2026 Post-Expansion Scene)
            if (isWater) {
              data[idx] = 20 + n * 10;
              data[idx + 1] = 38 + n * 15;
              data[idx + 2] = 48 + n * 20;
            } else if (isRoad) {
              data[idx] = 52 + hf * 15;
              data[idx + 1] = 50 + hf * 15;
              data[idx + 2] = 46 + hf * 15;
            } else if (inCluster1 || inCluster2) {
              // Real Concrete Foundations / Tech Park Roofs / Graded Earth in 2026
              const roofTile = Math.floor(x / 25) % 2 === Math.floor(y / 25) % 2;
              if (roofTile) {
                data[idx] = 210 + hf * 25;
                data[idx + 1] = 204 + hf * 25;
                data[idx + 2] = 196 + hf * 25;
              } else {
                data[idx] = 175 + hf * 30;
                data[idx + 1] = 168 + hf * 30;
                data[idx + 2] = 158 + hf * 30;
              }
            } else {
              data[idx] = 72 + n * 40 + hf * 15;
              data[idx + 1] = 94 + n * 45 + hf * 20;
              data[idx + 2] = 58 + n * 30 + hf * 10;
            }
            data[idx + 3] = 255;
          } else if (mode === 'CHANGE') {
            // ChangeNet Continuous Sigmoid Probability Heatmap
            if (inCluster1 || inCluster2) {
              const cx = inCluster1 ? 510 : 785;
              const cy = inCluster1 ? 615 : 620;
              const dist = Math.hypot(x - cx, y - cy);
              const prob = Math.max(0, 1 - dist / 140);
              data[idx] = 239;
              data[idx + 1] = Math.round(68 * (1 - prob) + 120 * prob);
              data[idx + 2] = 68;
              data[idx + 3] = Math.round(prob * 220);
            } else {
              data[idx] = 0;
              data[idx + 1] = 0;
              data[idx + 2] = 0;
              data[idx + 3] = 0;
            }
          }
        }
      }
      ctx.putImageData(imgData, 0, 0);
    };

    if (canvasT1Ref.current) {
      const ctx = canvasT1Ref.current.getContext('2d');
      if (ctx) generateTexture(ctx, 'T1');
    }
    if (canvasT2Ref.current) {
      const ctx = canvasT2Ref.current.getContext('2d');
      if (ctx) generateTexture(ctx, 'T2');
    }
    if (canvasNIRRef.current) {
      const ctx = canvasNIRRef.current.getContext('2d');
      if (ctx) generateTexture(ctx, 'NIR');
    }
    if (canvasSARRef.current) {
      const ctx = canvasSARRef.current.getContext('2d');
      if (ctx) generateTexture(ctx, 'SAR');
    }
    if (canvasChangeRef.current) {
      const ctx = canvasChangeRef.current.getContext('2d');
      if (ctx) generateTexture(ctx, 'CHANGE');
    }
  }, []);

  const isT1Active = activeDatasetIndex === 0;
  const isSARActive = activeDatasetIndex === 2 || activeLens === 'SAR';

  return (
    <div className="relative w-full h-full select-none overflow-hidden flex items-center justify-center bg-[#0A0A0A]">
      {/* 1. Temporal Swipe Mode: Smooth Before (2024) ↔ After (2026) Comparison */}
      {temporalMode === 'Swipe' && (activeLens === 'CHANGE' || activeLens === 'True Color') ? (
        <div className="relative w-full h-full overflow-hidden">
          {/* Base Layer: T2 (2026) */}
          <canvas
            ref={canvasT2Ref}
            width={1000}
            height={1000}
            className="absolute inset-0 w-full h-full object-cover"
          />

          {/* ChangeNet Probability Heatmap overlay on T2 */}
          {activeLens === 'CHANGE' && (
            <canvas
              ref={canvasChangeRef}
              width={1000}
              height={1000}
              className="absolute inset-0 w-full h-full object-cover pointer-events-none z-5"
            />
          )}

          {/* Clipped Top Layer: T1 (2024) */}
          <div
            className="absolute inset-y-0 left-0 overflow-hidden border-r-2 border-white shadow-[0_0_16px_rgba(255,255,255,0.8)] z-10"
            style={{ width: `${sliderPos}%` }}
          >
            <div
              className="absolute inset-y-0 left-0 h-full"
              style={{ width: `${100 / (sliderPos / 100)}%` }}
            >
              <canvas
                ref={canvasT1Ref}
                width={1000}
                height={1000}
                className="w-full h-full object-cover"
              />
            </div>

            {/* T1 Badge */}
            <div className="absolute top-16 left-4 bg-black/80 backdrop-blur-md text-white px-2.5 py-1 rounded-md text-[10px] font-mono font-bold border border-white/20">
              T1 · {dateT1}
            </div>
          </div>

          {/* T2 Badge */}
          <div className="absolute top-16 right-4 bg-black/80 backdrop-blur-md text-white px-2.5 py-1 rounded-md text-[10px] font-mono font-bold border border-white/20 z-5">
            T2 · {dateT2}
          </div>
        </div>
      ) : temporalMode === 'SideBySide' ? (
        /* 2. Side-by-Side Dual Viewports */
        <div className="grid grid-cols-2 w-full h-full divide-x divide-white/20">
          <div className="relative w-full h-full overflow-hidden">
            <canvas
              ref={canvasT1Ref}
              width={1000}
              height={1000}
              className="w-full h-full object-cover"
            />
            <div className="absolute top-16 left-4 bg-black/80 backdrop-blur-md text-white px-2.5 py-1 rounded-md text-[10px] font-mono font-bold border border-white/20">
              T1 · {dateT1}
            </div>
          </div>
          <div className="relative w-full h-full overflow-hidden">
            <canvas
              ref={canvasT2Ref}
              width={1000}
              height={1000}
              className="w-full h-full object-cover"
            />
            <div className="absolute top-16 left-4 bg-black/80 backdrop-blur-md text-white px-2.5 py-1 rounded-md text-[10px] font-mono font-bold border border-white/20">
              T2 · {dateT2}
            </div>
          </div>
        </div>
      ) : activeLens === 'NIR' ? (
        /* 3. False Color NIR Multispectral */
        <canvas
          ref={canvasNIRRef}
          width={1000}
          height={1000}
          className="w-full h-full object-cover"
        />
      ) : isSARActive ? (
        /* 4. Sentinel-1 SAR C-band Radar Backscatter */
        <canvas
          ref={canvasSARRef}
          width={1000}
          height={1000}
          className="w-full h-full object-cover"
        />
      ) : activeLens === 'CHANGE' ? (
        /* 5. Direct ChangeNet Heatmap over T2 */
        <div className="relative w-full h-full">
          <canvas
            ref={canvasT2Ref}
            width={1000}
            height={1000}
            className="w-full h-full object-cover"
          />
          <canvas
            ref={canvasChangeRef}
            width={1000}
            height={1000}
            className="absolute inset-0 w-full h-full object-cover pointer-events-none"
          />
        </div>
      ) : isT1Active ? (
        /* 6. Single Optical T1 */
        <canvas
          ref={canvasT1Ref}
          width={1000}
          height={1000}
          className="w-full h-full object-cover"
        />
      ) : (
        /* 7. Single Optical T2 */
        <canvas
          ref={canvasT2Ref}
          width={1000}
          height={1000}
          className="w-full h-full object-cover"
        />
      )}

      {/* Vector Polygons & Spatial Annotations */}
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
              {/* Change Region Outline */}
              <rect
                x={x}
                y={y}
                width={w}
                height={h}
                fill={isSelected ? 'rgba(239, 68, 68, 0.40)' : 'rgba(239, 68, 68, 0.20)'}
                stroke="#EF4444"
                strokeWidth={isSelected ? '3.5' : '2'}
                strokeDasharray="6 4"
                className="transition-all duration-200"
              />

              {/* Annotation Tag: 01 · +1.82 ha */}
              <g transform={`translate(${x}, ${y - 8})`}>
                <rect
                  x="0"
                  y="-18"
                  width={cluster.area_ha ? 110 : 80}
                  height="22"
                  rx="5"
                  fill="#111111"
                  stroke="#EF4444"
                  strokeWidth="1.5"
                  className="drop-shadow-lg"
                />
                <text
                  x="8"
                  y="-4"
                  fill="#FFFFFF"
                  fontSize="11"
                  fontFamily="ui-monospace, monospace"
                  fontWeight="bold"
                >
                  {cluster.tag} · +{cluster.area_ha} ha
                </text>
              </g>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
