'use client';

import React, { useRef, useEffect, useState } from 'react';
import { LensMode, TemporalViewMode, ChangeCluster, CursorCoordinates } from '../../context/WorkspaceContext';

interface MeasurementPoint {
  lat: number;
  lon: number;
  normX: number;
  normY: number;
}

interface ActiveMeasurementData {
  pA: MeasurementPoint;
  pB: MeasurementPoint;
  distM: number;
  distKm: number;
  bearing: number;
}

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
  measureA?: MeasurementPoint | null;
  activeMeasurement?: ActiveMeasurementData | null;
  polygonMeasurement?: {
    points: CursorCoordinates[];
    areaM2: number;
    areaHa: number;
    perimeterM: number;
  } | null;
  cursorCoords?: CursorCoordinates | null;
  activeTool?: string;
}

export const RealisticSatelliteCanvas: React.FC<RealisticSatelliteCanvasProps> = ({
  activeLens,
  activeDatasetIndex,
  temporalMode,
  sliderPos,
  onSliderChange,
  clusters,
  selectedClusterId,
  onSelectCluster,
  dateT1,
  dateT2,
  measureA,
  activeMeasurement,
  polygonMeasurement,
  cursorCoords,
  activeTool,
}) => {
  const canvasT1Ref = useRef<HTMLCanvasElement>(null);
  const canvasT2Ref = useRef<HTMLCanvasElement>(null);
  const canvasNIRRef = useRef<HTMLCanvasElement>(null);
  const canvasSWIRRef = useRef<HTMLCanvasElement>(null);
  const canvasSARRef = useRef<HTMLCanvasElement>(null);
  const canvasNDVIRef = useRef<HTMLCanvasElement>(null);
  const canvasNDWIRef = useRef<HTMLCanvasElement>(null);
  const canvasNDBIRef = useRef<HTMLCanvasElement>(null);
  const canvasChangeRef = useRef<HTMLCanvasElement>(null);
  const canvasEvidenceRef = useRef<HTMLCanvasElement>(null);

  const [isSliderDragging, setIsSliderDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Render high-fidelity, authentic Earth Observation imagery
  useEffect(() => {
    const W = 1200;
    const H = 1200;

    // Pseudo-random deterministic noise generator for natural textures
    const pseudoRandom = (seed: number) => {
      const x = Math.sin(seed++) * 10000;
      return x - Math.floor(x);
    };

    const renderScene = (
      ctx: CanvasRenderingContext2D,
      mode: 'T1' | 'T2' | 'NIR' | 'SWIR' | 'SAR' | 'NDVI' | 'NDWI' | 'NDBI' | 'CHANGE' | 'EVIDENCE'
    ) => {
      ctx.clearRect(0, 0, W, H);

      // =========================================================================
      // 1. BASE TERRAIN & SOIL
      // =========================================================================
      if (mode === 'SAR') {
        // C-band radar base: diffuse backscatter level (-16 dB)
        ctx.fillStyle = '#242424';
        ctx.fillRect(0, 0, W, H);
      } else if (mode === 'NIR') {
        // High chlorophyll reflectance in NIR
        ctx.fillStyle = '#781C2E';
        ctx.fillRect(0, 0, W, H);
      } else if (mode === 'SWIR') {
        // High shortwave infrared absorption and soil reflectance
        ctx.fillStyle = '#5A3D28';
        ctx.fillRect(0, 0, W, H);
      } else if (mode === 'NDVI') {
        // Vegetation index ground surface
        ctx.fillStyle = '#22543D';
        ctx.fillRect(0, 0, W, H);
      } else if (mode === 'NDWI') {
        // Non-water terrestrial surface
        ctx.fillStyle = '#1E293B';
        ctx.fillRect(0, 0, W, H);
      } else if (mode === 'NDBI') {
        // Built-up index non-urban baseline
        ctx.fillStyle = '#0F172A';
        ctx.fillRect(0, 0, W, H);
      } else {
        // Sentinel-2 L2A BOA natural color surface
        ctx.fillStyle = '#3F4D3A';
        ctx.fillRect(0, 0, W, H);
      }

      // =========================================================================
      // 2. DETAILED AGRICULTURAL PARCELS (Crop rotation & soil textures)
      // =========================================================================
      const parcels = [
        { c: 0, r: 0, w: 140, h: 90, type: 'crop1' },
        { c: 145, r: 0, w: 120, h: 90, type: 'crop2' },
        { c: 270, r: 0, w: 150, h: 90, type: 'fallow' },
        { c: 425, r: 0, w: 90, h: 90, type: 'crop3' },
        { c: 0, r: 95, w: 100, h: 120, type: 'crop2' },
        { c: 105, r: 95, w: 160, h: 120, type: 'crop1' },
        { c: 0, r: 220, w: 170, h: 140, type: 'fallow' },
        { c: 0, r: 365, w: 180, h: 140, type: 'crop3' },
        { c: 185, r: 365, w: 140, h: 140, type: 'crop1' },
        { c: 330, r: 365, w: 180, h: 140, type: 'crop2' },
        // South Parcels
        { c: 0, r: 660, w: 160, h: 150, type: 'crop2' },
        { c: 165, r: 660, w: 190, h: 150, type: 'crop1' },
        { c: 360, r: 660, w: 150, h: 150, type: 'fallow' },
        { c: 0, r: 815, w: 190, h: 170, type: 'crop3' },
        { c: 195, r: 815, w: 160, h: 170, type: 'crop2' },
        { c: 360, r: 815, w: 150, h: 170, type: 'crop1' },
        // East Parcels (surrounding lake & corridor)
        { c: 920, r: 520, w: 140, h: 130, type: 'crop1' },
        { c: 1065, r: 520, w: 130, h: 130, type: 'crop3' },
        { c: 920, r: 655, w: 130, h: 150, type: 'fallow' },
        { c: 1055, r: 655, w: 140, h: 150, type: 'crop2' },
        { c: 920, r: 810, w: 135, h: 170, type: 'crop1' },
        { c: 1060, r: 810, w: 135, h: 170, type: 'crop3' },
        { c: 540, r: 750, w: 140, h: 130, type: 'crop2' },
        { c: 685, r: 750, w: 140, h: 130, type: 'crop1' },
        { c: 540, r: 885, w: 140, h: 140, type: 'fallow' },
        { c: 685, r: 885, w: 140, h: 140, type: 'crop3' },
      ];

      parcels.forEach((p, idx) => {
        let fill = '#485841';
        if (mode === 'SAR') {
          fill = p.type === 'fallow' ? '#1E1E1E' : p.type === 'crop1' ? '#303030' : '#2A2A2A';
        } else if (mode === 'NIR') {
          fill = p.type === 'fallow' ? '#8C6858' : p.type === 'crop1' ? '#A32038' : p.type === 'crop2' ? '#8C182F' : '#B82845';
        } else if (mode === 'SWIR') {
          fill = p.type === 'fallow' ? '#8B5A2B' : p.type === 'crop1' ? '#1E6E38' : p.type === 'crop2' ? '#1A5E30' : '#288844';
        } else if (mode === 'NDVI') {
          fill = p.type === 'fallow' ? '#D97706' : p.type === 'crop1' ? '#166534' : p.type === 'crop2' ? '#15803D' : '#14532D';
        } else if (mode === 'NDWI') {
          fill = '#334155';
        } else if (mode === 'NDBI') {
          fill = '#1E293B';
        } else {
          fill = p.type === 'fallow' ? '#5E5748' : p.type === 'crop1' ? '#49593E' : p.type === 'crop2' ? '#3F4E36' : '#556649';
        }

        ctx.fillStyle = fill;
        ctx.fillRect(p.c, p.r, p.w, p.h);

        // Agricultural Furrows / Field Boundaries
        ctx.strokeStyle = mode === 'SAR' ? '#181818' : mode === 'NIR' ? '#50101C' : '#2F3A29';
        ctx.lineWidth = 1.5;
        ctx.strokeRect(p.c, p.r, p.w, p.h);

        // Internal cultivation rows
        ctx.beginPath();
        if (idx % 2 === 0) {
          for (let y = p.r + 12; y < p.r + p.h - 8; y += 14) {
            ctx.moveTo(p.c + 4, y);
            ctx.lineTo(p.c + p.w - 4, y);
          }
        } else {
          for (let x = p.c + 12; x < p.c + p.w - 8; x += 14) {
            ctx.moveTo(x, p.r + 4);
            ctx.lineTo(x, p.r + p.h - 4);
          }
        }
        ctx.strokeStyle = mode === 'SAR' ? '#202020' : mode === 'NIR' ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.12)';
        ctx.lineWidth = 1;
        ctx.stroke();
      });

      // =========================================================================
      // 3. NATURAL WATER BODIES (Sabarmati Basin & Southwest Reservoir)
      // =========================================================================
      // Northeast Lake
      ctx.beginPath();
      ctx.moveTo(760, 60);
      ctx.bezierCurveTo(920, 20, 1100, 90, 1160, 280);
      ctx.bezierCurveTo(1190, 440, 1070, 540, 940, 480);
      ctx.bezierCurveTo(820, 420, 750, 290, 730, 180);
      ctx.closePath();

      if (mode === 'SAR') {
        ctx.fillStyle = '#080808'; // Specular microwave forward-scatter absorption
      } else if (mode === 'NIR') {
        ctx.fillStyle = '#060A0E'; // 99%+ NIR water absorption
      } else if (mode === 'SWIR') {
        ctx.fillStyle = '#030507';
      } else if (mode === 'NDVI') {
        ctx.fillStyle = '#991B1B'; // Negative vegetation index
      } else if (mode === 'NDWI') {
        const waterGrad = ctx.createRadialGradient(960, 270, 30, 960, 270, 280);
        waterGrad.addColorStop(0, '#06B6D4'); // High positive NDWI fluorescence
        waterGrad.addColorStop(0.7, '#0284C7');
        waterGrad.addColorStop(1, '#0369A1');
        ctx.fillStyle = waterGrad;
      } else if (mode === 'NDBI') {
        ctx.fillStyle = '#020617';
      } else {
        const waterGrad = ctx.createRadialGradient(960, 270, 30, 960, 270, 280);
        waterGrad.addColorStop(0, '#102630');
        waterGrad.addColorStop(0.7, '#16333F');
        waterGrad.addColorStop(1, '#1F424E');
        ctx.fillStyle = waterGrad;
      }
      ctx.fill();

      // Littoral shoreline mudflat border
      ctx.lineWidth = 4;
      ctx.strokeStyle = mode === 'SAR' ? '#151515' : mode === 'NIR' ? '#4A3B35' : '#474F41';
      ctx.stroke();

      // Southwest Drainage Reservoir
      ctx.beginPath();
      ctx.arc(180, 1020, 130, 0, Math.PI * 2);
      ctx.fillStyle = mode === 'SAR' ? '#080808' : mode === 'NIR' ? '#060A0E' : '#142C37';
      ctx.fill();
      ctx.strokeStyle = mode === 'SAR' ? '#151515' : mode === 'NIR' ? '#4A3B35' : '#474F41';
      ctx.lineWidth = 3;
      ctx.stroke();

      // Meandering Canal tributary
      ctx.beginPath();
      ctx.moveTo(760, 220);
      ctx.bezierCurveTo(620, 260, 540, 230, 420, 270);
      ctx.bezierCurveTo(340, 300, 280, 280, 220, 320);
      ctx.lineWidth = 8;
      ctx.strokeStyle = mode === 'SAR' ? '#080808' : mode === 'NIR' ? '#060A0E' : '#173642';
      ctx.stroke();

      // =========================================================================
      // 4. TRANSPORTATION HIGHWAY ARTERIALS & BRIDGES
      // =========================================================================
      // East-West National Highway Corridor
      ctx.beginPath();
      ctx.moveTo(0, 520);
      ctx.bezierCurveTo(320, 550, 680, 490, 1200, 480);
      ctx.lineWidth = 20;
      ctx.strokeStyle = mode === 'SAR' ? '#4A4A4A' : mode === 'NIR' ? '#3B4A50' : '#2A2927';
      ctx.stroke();

      // Dual-carriageway center divider
      ctx.beginPath();
      ctx.moveTo(0, 520);
      ctx.bezierCurveTo(320, 550, 680, 490, 1200, 480);
      ctx.lineWidth = 2;
      ctx.strokeStyle = mode === 'SAR' ? '#222222' : mode === 'NIR' ? '#8C9CA0' : '#E8E5DC';
      ctx.stroke();

      // North-South Arterial
      ctx.beginPath();
      ctx.moveTo(520, 0);
      ctx.bezierCurveTo(525, 380, 535, 780, 540, 1200);
      ctx.lineWidth = 14;
      ctx.strokeStyle = mode === 'SAR' ? '#444444' : mode === 'NIR' ? '#3B4A50' : '#33312E';
      ctx.stroke();

      // Highway Interchange Slip-Ramps
      ctx.beginPath();
      ctx.arc(525, 510, 55, 0, Math.PI * 1.5);
      ctx.lineWidth = 7;
      ctx.strokeStyle = mode === 'SAR' ? '#3C3C3C' : mode === 'NIR' ? '#3B4A50' : '#383632';
      ctx.stroke();

      // =========================================================================
      // 5. BASELINE PRE-EXISTING SETTLEMENTS (Present in T1, T2, NIR, SAR)
      // =========================================================================
      const drawUrbanCluster = (bx: number, by: number, bw: number, bh: number, density: number) => {
        // Base ground asphalt
        ctx.fillStyle = mode === 'SAR' ? '#2A2A2A' : mode === 'NIR' ? '#586A70' : '#524E48';
        ctx.fillRect(bx, by, bw, bh);

        // Individual buildings
        const cols = Math.floor(bw / 24);
        const rows = Math.floor(bh / 24);
        for (let r = 0; r < rows; r++) {
          for (let c = 0; c < cols; c++) {
            const seed = bx * 13 + by * 17 + r * 7 + c * 11;
            if (pseudoRandom(seed) > density) continue;

            const bWidth = 14 + Math.floor(pseudoRandom(seed + 1) * 8);
            const bHeight = 14 + Math.floor(pseudoRandom(seed + 2) * 8);
            const x = bx + c * 24 + 3;
            const y = by + r * 24 + 3;

            // Solar shadow (northwest sun angle)
            ctx.fillStyle = mode === 'SAR' ? '#0A0A0A' : 'rgba(0,0,0,0.35)';
            ctx.fillRect(x - 3, y - 3, bWidth, bHeight);

            // Building roof
            if (mode === 'SAR') {
              // Dihedral corner reflection: high backscatter
              ctx.fillStyle = pseudoRandom(seed + 3) > 0.4 ? '#EFEFEF' : '#CCCCCC';
            } else if (mode === 'NIR') {
              ctx.fillStyle = pseudoRandom(seed + 3) > 0.5 ? '#6E9BA6' : '#5A828C';
            } else {
              // Mixed terracotta tile and flat concrete roofs
              ctx.fillStyle = pseudoRandom(seed + 3) > 0.5 ? '#9E9486' : '#B87258';
            }
            ctx.fillRect(x, y, bWidth, bHeight);
          }
        }
      };

      // Northwest suburban township
      drawUrbanCluster(190, 200, 180, 160, 0.75);
      // Southeast settlement
      drawUrbanCluster(790, 680, 200, 170, 0.70);
      // Central transit hub
      drawUrbanCluster(550, 360, 130, 95, 0.85);

      // =========================================================================
      // 6. DETECTED EXPANSION ZONES (T2, SAR, NIR, CHANGE, EVIDENCE)
      // =========================================================================
      // In T1 (2024), these zones were natural fallow / agricultural land
      const isPostExpansion = mode !== 'T1';

      if (isPostExpansion) {
        // -----------------------------------------------------------------------
        // Cluster 01: Tech Park Complex Phase 2
        // Bounding Box: [0.35, 0.28, 0.52, 0.52] -> (420, 336, 204, 288)
        // -----------------------------------------------------------------------
        const c1X = 420;
        const c1Y = 336;
        const c1W = 204;
        const c1H = 288;

        // Clean modern asphalt & concrete campus foundation
        ctx.fillStyle = mode === 'SAR' ? '#353535' : mode === 'NIR' ? '#4A6870' : '#68655E';
        ctx.fillRect(c1X, c1Y, c1W, c1H);

        // Internal tech park access lanes
        ctx.strokeStyle = mode === 'SAR' ? '#1A1A1A' : mode === 'NIR' ? '#34484E' : '#42403B';
        ctx.lineWidth = 4;
        ctx.strokeRect(c1X + 12, c1Y + 12, c1W - 24, c1H - 24);

        // Large Commercial Office Blocks with High-Albedo White Cool Roofs
        const buildingsC1 = [
          { x: c1X + 20, y: c1Y + 22, w: 75, h: 70, name: 'Tower A' },
          { x: c1X + 110, y: c1Y + 22, w: 75, h: 70, name: 'Tower B' },
          { x: c1X + 20, y: c1Y + 115, w: 165, h: 75, name: 'Main Campus' },
          { x: c1X + 20, y: c1Y + 210, w: 165, h: 60, name: 'R&D Center' },
        ];

        buildingsC1.forEach((b) => {
          // Shadow
          ctx.fillStyle = mode === 'SAR' ? '#050505' : 'rgba(0,0,0,0.45)';
          ctx.fillRect(b.x - 4, b.y - 4, b.w, b.h);

          // Building footprint
          if (mode === 'SAR') {
            // Intense double-bounce corner reflection (+4.1 dB)
            ctx.fillStyle = '#FFFFFF';
            ctx.fillRect(b.x, b.y, b.w, b.h);
            // Internal radar absorption boundary
            ctx.fillStyle = '#D6D6D6';
            ctx.fillRect(b.x + 4, b.y + 4, b.w - 8, b.h - 8);
          } else if (mode === 'NIR') {
            ctx.fillStyle = '#78A8B4';
            ctx.fillRect(b.x, b.y, b.w, b.h);
            ctx.fillStyle = '#94C0CC';
            ctx.fillRect(b.x + 4, b.y + 4, b.w - 8, b.h - 8);
          } else {
            // High-albedo white clean roof with HVAC machinery outlines
            ctx.fillStyle = '#DEDAD2';
            ctx.fillRect(b.x, b.y, b.w, b.h);
            ctx.fillStyle = '#F4F2EC';
            ctx.fillRect(b.x + 4, b.y + 4, b.w - 8, b.h - 8);

            // Rooftop HVAC units
            ctx.fillStyle = '#A39D91';
            ctx.fillRect(b.x + 10, b.y + 10, 16, 12);
            ctx.fillRect(b.x + 32, b.y + 10, 16, 12);
          }
        });

        // -----------------------------------------------------------------------
        // Cluster 02: Highway Logistics Depot & Earthwork Staging
        // Bounding Box: [0.58, 0.46, 0.74, 0.62] -> (696, 552, 192, 192)
        // -----------------------------------------------------------------------
        const c2X = 696;
        const c2Y = 552;
        const c2W = 192;
        const c2H = 192;

        // Ground excavated earthwork & compacted subgrade
        ctx.fillStyle = mode === 'SAR' ? '#333333' : mode === 'NIR' ? '#6B584E' : '#736858';
        ctx.fillRect(c2X, c2Y, c2W, c2H);

        // Logistics Warehouses
        const buildingsC2 = [
          { x: c2X + 16, y: c2Y + 20, w: 160, h: 65 },
          { x: c2X + 16, y: c2Y + 105, w: 160, h: 65 },
        ];

        buildingsC2.forEach((b) => {
          // Shadow
          ctx.fillStyle = mode === 'SAR' ? '#050505' : 'rgba(0,0,0,0.40)';
          ctx.fillRect(b.x - 3, b.y - 3, b.w, b.h);

          if (mode === 'SAR') {
            ctx.fillStyle = '#F8F8F8';
            ctx.fillRect(b.x, b.y, b.w, b.h);
            ctx.fillStyle = '#DCDCDC';
            ctx.fillRect(b.x + 3, b.y + 3, b.w - 6, b.h - 6);
          } else if (mode === 'NIR') {
            ctx.fillStyle = '#72A0AC';
            ctx.fillRect(b.x, b.y, b.w, b.h);
          } else {
            ctx.fillStyle = '#C2BCB0';
            ctx.fillRect(b.x, b.y, b.w, b.h);
            // Corrugated roofing stripes
            ctx.strokeStyle = '#ACA598';
            ctx.lineWidth = 1;
            for (let rx = b.x + 8; rx < b.x + b.w - 4; rx += 8) {
              ctx.beginPath();
              ctx.moveTo(rx, b.y + 2);
              ctx.lineTo(rx, b.y + b.h - 2);
              ctx.stroke();
            }
          }
        });

        // -----------------------------------------------------------------------
        // CHANGE LENS: Continuous ChangeNet Sigmoid Heatmap Overlay
        // -----------------------------------------------------------------------
        if (mode === 'CHANGE') {
          // Cluster 01 Heatmap
          const heat1 = ctx.createRadialGradient(c1X + c1W / 2, c1Y + c1H / 2, 20, c1X + c1W / 2, c1Y + c1H / 2, c1W * 0.75);
          heat1.addColorStop(0, 'rgba(239, 68, 68, 0.88)');
          heat1.addColorStop(0.5, 'rgba(249, 115, 22, 0.65)');
          heat1.addColorStop(0.85, 'rgba(234, 179, 8, 0.35)');
          heat1.addColorStop(1, 'rgba(239, 68, 68, 0.0)');
          ctx.fillStyle = heat1;
          ctx.beginPath();
          ctx.arc(c1X + c1W / 2, c1Y + c1H / 2, c1W * 0.75, 0, Math.PI * 2);
          ctx.fill();

          // Cluster 02 Heatmap
          const heat2 = ctx.createRadialGradient(c2X + c2W / 2, c2Y + c2H / 2, 20, c2X + c2W / 2, c2Y + c2H / 2, c2W * 0.75);
          heat2.addColorStop(0, 'rgba(239, 68, 68, 0.88)');
          heat2.addColorStop(0.5, 'rgba(249, 115, 22, 0.65)');
          heat2.addColorStop(0.85, 'rgba(234, 179, 8, 0.35)');
          heat2.addColorStop(1, 'rgba(239, 68, 68, 0.0)');
          ctx.fillStyle = heat2;
          ctx.beginPath();
          ctx.arc(c2X + c2W / 2, c2Y + c2H / 2, c2W * 0.75, 0, Math.PI * 2);
          ctx.fill();
        }

        // -----------------------------------------------------------------------
        // EVIDENCE LENS: Focus Spotlight & Analytical Crosshairs
        // -----------------------------------------------------------------------
        if (mode === 'EVIDENCE') {
          // Darken background vignette
          ctx.fillStyle = 'rgba(10, 12, 16, 0.55)';
          ctx.fillRect(0, 0, W, H);

          // Clear focused analytical circle over Cluster 01
          ctx.save();
          ctx.beginPath();
          ctx.arc(c1X + c1W / 2, c1Y + c1H / 2, c1W * 0.7, 0, Math.PI * 2);
          ctx.clip();
          // Redraw crisp scene inside focus area
          ctx.fillStyle = '#68655E';
          ctx.fillRect(c1X, c1Y, c1W, c1H);
          buildingsC1.forEach((b) => {
            ctx.fillStyle = '#F4F2EC';
            ctx.fillRect(b.x, b.y, b.w, b.h);
          });
          ctx.restore();

          // Spotlight glowing ring
          ctx.strokeStyle = '#06B6D4';
          ctx.lineWidth = 2.5;
          ctx.beginPath();
          ctx.arc(c1X + c1W / 2, c1Y + c1H / 2, c1W * 0.7, 0, Math.PI * 2);
          ctx.stroke();

          // Crosshairs
          ctx.strokeStyle = 'rgba(6, 182, 212, 0.6)';
          ctx.lineWidth = 1;
          ctx.setLineDash([6, 6]);
          ctx.beginPath();
          ctx.moveTo(c1X + c1W / 2 - c1W * 0.9, c1Y + c1H / 2);
          ctx.lineTo(c1X + c1W / 2 + c1W * 0.9, c1Y + c1H / 2);
          ctx.moveTo(c1X + c1W / 2, c1Y + c1H / 2 - c1H * 0.8);
          ctx.lineTo(c1X + c1W / 2, c1Y + c1H / 2 + c1H * 0.8);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }

      // =========================================================================
      // 7. SAR SPECKLE TEXTURE (Authentic radar backscatter granularity)
      // =========================================================================
      if (mode === 'SAR') {
        const imgData = ctx.getImageData(0, 0, W, H);
        const data = imgData.data;
        for (let i = 0; i < data.length; i += 16) {
          // Avoid speckling zero-absorption water
          if (data[i] > 15) {
            const noise = (Math.random() - 0.5) * 32;
            data[i] = Math.min(255, Math.max(0, data[i] + noise));
            data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + noise));
            data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + noise));
          }
        }
        ctx.putImageData(imgData, 0, 0);
      }
    };

    if (canvasT1Ref.current) {
      const ctx = canvasT1Ref.current.getContext('2d');
      if (ctx) renderScene(ctx, 'T1');
    }
    if (canvasT2Ref.current) {
      const ctx = canvasT2Ref.current.getContext('2d');
      if (ctx) renderScene(ctx, 'T2');
    }
    if (canvasNIRRef.current) {
      const ctx = canvasNIRRef.current.getContext('2d');
      if (ctx) renderScene(ctx, 'NIR');
    }
    if (canvasSWIRRef.current) {
      const ctx = canvasSWIRRef.current.getContext('2d');
      if (ctx) renderScene(ctx, 'SWIR');
    }
    if (canvasSARRef.current) {
      const ctx = canvasSARRef.current.getContext('2d');
      if (ctx) renderScene(ctx, 'SAR');
    }
    if (canvasNDVIRef.current) {
      const ctx = canvasNDVIRef.current.getContext('2d');
      if (ctx) renderScene(ctx, 'NDVI');
    }
    if (canvasNDWIRef.current) {
      const ctx = canvasNDWIRef.current.getContext('2d');
      if (ctx) renderScene(ctx, 'NDWI');
    }
    if (canvasNDBIRef.current) {
      const ctx = canvasNDBIRef.current.getContext('2d');
      if (ctx) renderScene(ctx, 'NDBI');
    }
    if (canvasChangeRef.current) {
      const ctx = canvasChangeRef.current.getContext('2d');
      if (ctx) renderScene(ctx, 'CHANGE');
    }
    if (canvasEvidenceRef.current) {
      const ctx = canvasEvidenceRef.current.getContext('2d');
      if (ctx) renderScene(ctx, 'EVIDENCE');
    }
  }, []);

  const isT1Active = activeDatasetIndex === 0;
  const isSARActive = activeDatasetIndex === 2 || activeLens === 'SAR';

  // Handle slider drag directly on canvas
  const handleMouseDownSlider = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsSliderDragging(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isSliderDragging || !containerRef.current || !onSliderChange) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
      const pct = Math.round((x / rect.width) * 100);
      onSliderChange(pct);
    };

    const handleMouseUp = () => {
      setIsSliderDragging(false);
    };

    if (isSliderDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isSliderDragging, onSliderChange]);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full select-none overflow-hidden flex items-center justify-center bg-[#0A0A0A]"
    >
      {/* 1. Temporal Swipe Mode: Before (2024) ↔ After (2026) Interactive Comparison */}
      {temporalMode === 'Swipe' && (activeLens === 'CHANGE' || activeLens === 'True Color') ? (
        <div className="relative w-full h-full overflow-hidden">
          {/* Base Layer: T2 (2026) */}
          <canvas
            ref={canvasT2Ref}
            width={1200}
            height={1200}
            className="absolute inset-0 w-full h-full object-cover"
          />

          {/* ChangeNet Probability Heatmap overlay on T2 */}
          {activeLens === 'CHANGE' && (
            <canvas
              ref={canvasChangeRef}
              width={1200}
              height={1200}
              className="absolute inset-0 w-full h-full object-cover pointer-events-none z-5"
            />
          )}

          {/* Clipped Top Layer: T1 (2024 Baseline) */}
          <div
            className="absolute inset-y-0 left-0 overflow-hidden border-r-2 border-white shadow-[0_0_20px_rgba(255,255,255,0.9)] z-10"
            style={{ width: `${sliderPos}%` }}
          >
            <div
              className="absolute inset-y-0 left-0 h-full"
              style={{ width: `${100 / (sliderPos / 100 || 0.001)}%` }}
            >
              <canvas
                ref={canvasT1Ref}
                width={1200}
                height={1200}
                className="w-full h-full object-cover"
              />
            </div>

            {/* T1 Badge */}
            <div className="absolute top-16 left-4 bg-black/85 backdrop-blur-md text-white px-2.5 py-1 rounded-md text-[10px] font-mono font-bold border border-white/20 shadow-md">
              T1 · {dateT1}
            </div>
          </div>

          {/* Draggable Divider Handle */}
          <div
            onMouseDown={handleMouseDownSlider}
            style={{ left: `${sliderPos}%` }}
            className="absolute inset-y-0 -ml-3 w-6 z-20 cursor-ew-resize flex items-center justify-center group"
          >
            <div className="w-6 h-6 rounded-full bg-white shadow-xl flex items-center justify-center border border-black/20 text-[#111] text-[10px] font-bold group-hover:scale-110 transition-transform">
              ↔
            </div>
          </div>

          {/* T2 Badge */}
          <div className="absolute top-16 right-4 bg-black/85 backdrop-blur-md text-white px-2.5 py-1 rounded-md text-[10px] font-mono font-bold border border-white/20 z-5 shadow-md">
            T2 · {dateT2}
          </div>
        </div>
      ) : temporalMode === 'Side by Side' ? (
        /* 2. Side-by-Side Dual Viewports */
        <div className="grid grid-cols-2 w-full h-full divide-x-2 divide-white/20">
          <div className="relative w-full h-full overflow-hidden">
            <canvas
              ref={canvasT1Ref}
              width={1200}
              height={1200}
              className="w-full h-full object-cover"
            />
            <div className="absolute top-16 left-4 bg-black/85 backdrop-blur-md text-white px-2.5 py-1 rounded-md text-[10px] font-mono font-bold border border-white/20">
              T1 · {dateT1} (MSI Optical)
            </div>
          </div>
          <div className="relative w-full h-full overflow-hidden">
            <canvas
              ref={canvasT2Ref}
              width={1200}
              height={1200}
              className="w-full h-full object-cover"
            />
            <div className="absolute top-16 left-4 bg-black/85 backdrop-blur-md text-white px-2.5 py-1 rounded-md text-[10px] font-mono font-bold border border-white/20">
              T2 · {dateT2} (MSI Optical)
            </div>
          </div>
        </div>
      ) : activeLens === 'NIR' ? (
        /* 3. False Color NIR Multispectral (B8-B4-B3) */
        <canvas
          ref={canvasNIRRef}
          width={1200}
          height={1200}
          className="w-full h-full object-cover"
        />
      ) : activeLens === 'SWIR' ? (
        /* Shortwave Infrared (SWIR B12-B8A-B4) */
        <canvas
          ref={canvasSWIRRef}
          width={1200}
          height={1200}
          className="w-full h-full object-cover"
        />
      ) : activeLens === 'NDVI' ? (
        /* Normalized Difference Vegetation Index */
        <canvas
          ref={canvasNDVIRef}
          width={1200}
          height={1200}
          className="w-full h-full object-cover"
        />
      ) : activeLens === 'NDWI' ? (
        /* Normalized Difference Water Index */
        <canvas
          ref={canvasNDWIRef}
          width={1200}
          height={1200}
          className="w-full h-full object-cover"
        />
      ) : activeLens === 'NDBI' ? (
        /* Normalized Difference Built-up Index */
        <canvas
          ref={canvasNDBIRef}
          width={1200}
          height={1200}
          className="w-full h-full object-cover"
        />
      ) : isSARActive ? (
        /* Sentinel-1 C-band Radar Backscatter */
        <canvas
          ref={canvasSARRef}
          width={1200}
          height={1200}
          className="w-full h-full object-cover"
        />
      ) : activeLens === 'CHANGE' ? (
        /* 5. Direct ChangeNet Heatmap over T2 */
        <div className="relative w-full h-full">
          <canvas
            ref={canvasT2Ref}
            width={1200}
            height={1200}
            className="w-full h-full object-cover"
          />
          <canvas
            ref={canvasChangeRef}
            width={1200}
            height={1200}
            className="absolute inset-0 w-full h-full object-cover pointer-events-none"
          />
        </div>
      ) : activeLens === 'EVIDENCE' ? (
        /* 6. Evidence Spotlight Focus */
        <canvas
          ref={canvasEvidenceRef}
          width={1200}
          height={1200}
          className="w-full h-full object-cover"
        />
      ) : isT1Active ? (
        /* 7. Single Optical T1 */
        <canvas
          ref={canvasT1Ref}
          width={1200}
          height={1200}
          className="w-full h-full object-cover"
        />
      ) : (
        /* 8. Single Optical T2 */
        <canvas
          ref={canvasT2Ref}
          width={1200}
          height={1200}
          className="w-full h-full object-cover"
        />
      )}

      {/* Vector Polygons & Spatial Annotations (Rendered in CHANGE and EVIDENCE modes) */}
      {(activeLens === 'CHANGE' || activeLens === 'EVIDENCE' || selectedClusterId !== null) && (
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none z-20"
          viewBox="0 0 1200 1200"
          preserveAspectRatio="none"
        >
          {clusters.map((cluster) => {
            const x = cluster.bbox.xmin * 1200;
            const y = cluster.bbox.ymin * 1200;
            const w = (cluster.bbox.xmax - cluster.bbox.xmin) * 1200;
            const h = (cluster.bbox.ymax - cluster.bbox.ymin) * 1200;
            const isSelected = selectedClusterId === cluster.id;
            const strokeColor = activeLens === 'EVIDENCE' ? '#06B6D4' : '#EF4444';

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
                  fill={
                    isSelected
                      ? activeLens === 'EVIDENCE'
                        ? 'rgba(6, 182, 212, 0.35)'
                        : 'rgba(239, 68, 68, 0.35)'
                      : activeLens === 'EVIDENCE'
                      ? 'rgba(6, 182, 212, 0.15)'
                      : 'rgba(239, 68, 68, 0.18)'
                  }
                  stroke={strokeColor}
                  strokeWidth={isSelected ? '3' : '2'}
                  strokeDasharray="6 4"
                  className="transition-all duration-200"
                />

                {/* Corner reticles for selected cluster */}
                {isSelected && (
                  <>
                    <path
                      d={`M ${x - 4} ${y + 12} L ${x - 4} ${y - 4} L ${x + 12} ${y - 4}`}
                      stroke={strokeColor}
                      strokeWidth="3"
                      fill="none"
                    />
                    <path
                      d={`M ${x + w - 12} ${y - 4} L ${x + w + 4} ${y - 4} L ${x + w + 4} ${y + 12}`}
                      stroke={strokeColor}
                      strokeWidth="3"
                      fill="none"
                    />
                    <path
                      d={`M ${x - 4} ${y + h - 12} L ${x - 4} ${y + h + 4} L ${x + 12} ${y + h + 4}`}
                      stroke={strokeColor}
                      strokeWidth="3"
                      fill="none"
                    />
                    <path
                      d={`M ${x + w - 12} ${y + h + 4} L ${x + w + 4} ${y + h + 4} L ${x + w + 4} ${y + h - 12}`}
                      stroke={strokeColor}
                      strokeWidth="3"
                      fill="none"
                    />
                  </>
                )}

                {/* Annotation Tag: 01 · +1.82 ha */}
                <g transform={`translate(${x}, ${y - 8})`}>
                  <rect
                    x="0"
                    y="-18"
                    width={cluster.area_ha ? 120 : 85}
                    height="22"
                    rx="5"
                    fill="#111111"
                    stroke={strokeColor}
                    strokeWidth="1.5"
                    className="drop-shadow-md"
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
      )}

      {/* Geodesic Measurement & Polygon Area Interactive Vector Overlay */}
      {(measureA || activeMeasurement || (polygonMeasurement && polygonMeasurement.points.length > 0)) && (
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none z-30"
          viewBox="0 0 1200 1200"
          preserveAspectRatio="none"
        >
          {/* Active completed measurement line */}
          {activeMeasurement && (
            <g>
              <line
                x1={activeMeasurement.pA.normX * 1200}
                y1={activeMeasurement.pA.normY * 1200}
                x2={activeMeasurement.pB.normX * 1200}
                y2={activeMeasurement.pB.normY * 1200}
                stroke="#10B981"
                strokeWidth="3"
                strokeDasharray="6 4"
              />
              {/* Point A Node */}
              <circle
                cx={activeMeasurement.pA.normX * 1200}
                cy={activeMeasurement.pA.normY * 1200}
                r="6"
                fill="#10B981"
                stroke="#FFFFFF"
                strokeWidth="2"
              />
              {/* Point B Node */}
              <circle
                cx={activeMeasurement.pB.normX * 1200}
                cy={activeMeasurement.pB.normY * 1200}
                r="6"
                fill="#10B981"
                stroke="#FFFFFF"
                strokeWidth="2"
              />
              {/* Midpoint Distance Badge */}
              <g
                transform={`translate(${
                  ((activeMeasurement.pA.normX + activeMeasurement.pB.normX) / 2) * 1200
                }, ${
                  ((activeMeasurement.pA.normY + activeMeasurement.pB.normY) / 2) * 1200
                })`}
              >
                <rect
                  x="-55"
                  y="-14"
                  width="110"
                  height="22"
                  rx="6"
                  fill="#0A0A0A"
                  stroke="#10B981"
                  strokeWidth="1.5"
                />
                <text
                  x="0"
                  y="1"
                  textAnchor="middle"
                  fill="#FFFFFF"
                  fontSize="11"
                  fontFamily="ui-monospace, monospace"
                  fontWeight="bold"
                >
                  {activeMeasurement.distM.toLocaleString()} m
                </text>
              </g>
            </g>
          )}

          {/* Pending measurement line while mouse moving */}
          {!activeMeasurement && measureA && cursorCoords && (
            <g>
              <line
                x1={measureA.normX * 1200}
                y1={measureA.normY * 1200}
                x2={cursorCoords.normX * 1200}
                y2={cursorCoords.normY * 1200}
                stroke="#06B6D4"
                strokeWidth="2"
                strokeDasharray="4 4"
              />
              <circle
                cx={measureA.normX * 1200}
                cy={measureA.normY * 1200}
                r="6"
                fill="#06B6D4"
                stroke="#FFFFFF"
                strokeWidth="2"
              />
            </g>
          )}

          {/* Polygon Area Measurement Interactive Vector Overlay */}
          {polygonMeasurement && polygonMeasurement.points.length > 0 && (
            <g>
              {polygonMeasurement.points.length >= 3 && (
                <polygon
                  points={polygonMeasurement.points
                    .map((p) => `${p.normX * 1200},${p.normY * 1200}`)
                    .join(' ')}
                  fill="rgba(16, 185, 129, 0.22)"
                  stroke="#10B981"
                  strokeWidth="3"
                  strokeDasharray="6 4"
                />
              )}

              {polygonMeasurement.points.length < 3 && polygonMeasurement.points.length > 1 && (
                <polyline
                  points={polygonMeasurement.points
                    .map((p) => `${p.normX * 1200},${p.normY * 1200}`)
                    .join(' ')}
                  fill="none"
                  stroke="#10B981"
                  strokeWidth="2.5"
                  strokeDasharray="4 4"
                />
              )}

              {polygonMeasurement.points.map((p, idx) => (
                <g key={idx}>
                  <circle
                    cx={p.normX * 1200}
                    cy={p.normY * 1200}
                    r="6"
                    fill="#10B981"
                    stroke="#FFFFFF"
                    strokeWidth="2"
                  />
                  <text
                    x={p.normX * 1200 + 8}
                    y={p.normY * 1200 - 8}
                    fill="#FFFFFF"
                    fontSize="11"
                    fontFamily="ui-monospace, monospace"
                    fontWeight="bold"
                    className="drop-shadow-md"
                  >
                    V{idx + 1}
                  </text>
                </g>
              ))}

              {polygonMeasurement.points.length >= 3 && (
                <g
                  transform={`translate(${
                    (polygonMeasurement.points.reduce((acc, p) => acc + p.normX, 0) /
                      polygonMeasurement.points.length) *
                    1200
                  }, ${
                    (polygonMeasurement.points.reduce((acc, p) => acc + p.normY, 0) /
                      polygonMeasurement.points.length) *
                    1200
                  })`}
                >
                  <rect
                    x="-90"
                    y="-18"
                    width="180"
                    height="36"
                    rx="8"
                    fill="#0A0A0A"
                    stroke="#10B981"
                    strokeWidth="1.5"
                  />
                  <text
                    x="0"
                    y="-2"
                    textAnchor="middle"
                    fill="#FFFFFF"
                    fontSize="11"
                    fontFamily="ui-monospace, monospace"
                    fontWeight="bold"
                  >
                    {polygonMeasurement.areaHa} ha ({polygonMeasurement.areaM2.toLocaleString()} m²)
                  </text>
                  <text
                    x="0"
                    y="11"
                    textAnchor="middle"
                    fill="#10B981"
                    fontSize="9"
                    fontFamily="ui-monospace, monospace"
                  >
                    Perimeter: {polygonMeasurement.perimeterM.toLocaleString()} m
                  </text>
                </g>
              )}
            </g>
          )}
        </svg>
      )}
    </div>
  );
};
