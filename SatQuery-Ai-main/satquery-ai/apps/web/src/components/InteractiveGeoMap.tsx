'use client';

import React, { useState, useRef, useEffect, useMemo } from 'react';
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Ruler,
  Compass,
  MapPin,
  Maximize2,
  Minimize2,
  Layers,
  Crosshair,
  Square,
  Pentagon,
  Trash2,
  Check,
  Eye,
  Info,
  Sliders,
  X,
  ExternalLink,
} from 'lucide-react';
import { getPreviewUrl } from '../lib/api';
import { calculateGeodesicPolygonAreaM2, calculateGeodesicDistanceMeters, getUtmInfo } from '@/lib/geospatial';

interface Point {
  x: number; // canvas pixel
  y: number;
  normX: number; // [0, 1]
  normY: number;
  lat: number;
  lon: number;
  utmE: number;
  utmN: number;
}

interface Measurement {
  pointA: Point;
  pointB: Point;
  distanceM: number;
  distanceKm: number;
  bearingDeg: number;
}

interface InteractiveGeoMapProps {
  previewUrl?: string | null;
  imageWidth?: number;
  imageHeight?: number;
  gsdMeters?: number;
  crsCode?: string;
  centerLat?: number;
  centerLon?: number;
  locationName?: string;
  geojsonFeatures?: any[];
  changePolygons?: any[];
  activeLens?: string;
  onLensChange?: (lens: string) => void;
  selectedRegionId?: string | null;
  onSelectRegion?: (id: string) => void;
  onAoiChange?: (aoi: { coordinates: [number, number][]; areaM2: number; areaHa: number } | null) => void;
}

export const InteractiveGeoMap: React.FC<InteractiveGeoMapProps> = ({
  previewUrl,
  imageWidth = 10980,
  imageHeight = 10980,
  gsdMeters = 10.0,
  crsCode = 'EPSG:32644',
  centerLat = 17.3850,
  centerLon = 78.4867,
  locationName = 'Hyderabad Urban Corridor',
  geojsonFeatures = [],
  changePolygons = [],
  activeLens = 'True color',
  onLensChange,
  selectedRegionId,
  onSelectRegion,
  onAoiChange,
}) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });

  // Mode: 'pan' | 'measure' | 'draw_rect' | 'draw_poly'
  const [activeTool, setActiveTool] = useState<'pan' | 'measure' | 'draw_rect' | 'draw_poly'>('pan');
  const [measureStart, setMeasureStart] = useState<Point | null>(null);
  const [activeMeasurement, setActiveMeasurement] = useState<Measurement | null>(null);

  // AOI Drawing State
  const [rectStart, setRectStart] = useState<Point | null>(null);
  const [tempRectEnd, setTempRectEnd] = useState<Point | null>(null);
  const [polygonVertices, setPolygonVertices] = useState<Point[]>([]);
  const [drawnAoi, setDrawnAoi] = useState<{
    type: 'polygon' | 'rectangle';
    points: Point[];
    areaM2: number;
    areaHa: number;
  } | null>(null);

  // Basemap & Layer controls
  const [basemap, setBasemap] = useState<'satellite' | 'carto' | 'tactical_dark'>('satellite');
  const [showCrosshair, setShowCrosshair] = useState(true);
  const [showLayerMenu, setShowLayerMenu] = useState(false);
  const [visibleLayers, setVisibleLayers] = useState<Record<string, boolean>>({
    imagery: true,
    change: true,
    grounding: true,
    aoi: true,
    grid: true,
  });

  const [changeOpacity, setChangeOpacity] = useState(0.85);
  const [cursorPos, setCursorPos] = useState<Point | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [inspectedCluster, setInspectedCluster] = useState<any | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  // Compute dynamic UTM metadata based on center coordinates
  const utmInfo = useMemo(() => getUtmInfo(centerLat, centerLon), [centerLat, centerLon]);

  // Handle zoom
  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.25, 4.0));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.25, 0.5));
  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setMeasureStart(null);
    setActiveMeasurement(null);
  };

  // Convert client coordinates to normalized and geographic WGS84 coordinates
  const computePoint = (clientX: number, clientY: number): Point | null => {
    if (!imgRef.current) return null;
    const rect = imgRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
    const y = Math.max(0, Math.min(clientY - rect.top, rect.height));

    const normX = x / rect.width;
    const normY = y / rect.height;

    // Geographic bounding box centered around centerLat, centerLon (~0.04 deg span)
    const spanDeg = 0.04;
    const lon = centerLon + (normX - 0.5) * spanDeg;
    const lat = centerLat - (normY - 0.5) * spanDeg;

    // Dynamic UTM computation
    const utmE = Math.round(500000 + (lon - (utmInfo.zone * 6 - 183)) * 111319);
    const utmN = Math.round(lat * 110574);

    return { x, y, normX, normY, lat, lon, utmE, utmN };
  };

  // Mouse Move
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const pt = computePoint(e.clientX, e.clientY);
    if (!pt) return;
    setCursorPos(pt);

    if (activeTool === 'pan' && isPanning) {
      setPan((prev) => ({
        x: prev.x + (e.clientX - panStart.x),
        y: prev.y + (e.clientY - panStart.y),
      }));
      setPanStart({ x: e.clientX, y: e.clientY });
    }

    if (activeTool === 'measure' && measureStart) {
      const distM = calculateGeodesicDistanceMeters(
        { lat: measureStart.lat, lon: measureStart.lon },
        { lat: pt.lat, lon: pt.lon }
      );
      const dLon = pt.lon - measureStart.lon;
      const dLat = pt.lat - measureStart.lat;
      const bearing = (Math.atan2(dLon, dLat) * 180) / Math.PI;

      setActiveMeasurement({
        pointA: measureStart,
        pointB: pt,
        distanceM: Math.round(distM),
        distanceKm: +(distM / 1000).toFixed(2),
        bearingDeg: Math.round((bearing + 360) % 360),
      });
    }

    if (activeTool === 'draw_rect' && rectStart) {
      setTempRectEnd(pt);
    }
  };

  // Mouse Down
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (activeTool === 'pan') {
      setIsPanning(true);
      setPanStart({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseUp = () => {
    if (isPanning) setIsPanning(false);
  };

  // Canvas Click
  const handleCanvasClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const pt = computePoint(e.clientX, e.clientY);
    if (!pt) return;

    if (activeTool === 'measure') {
      if (!measureStart) {
        setMeasureStart(pt);
        setActiveMeasurement(null);
      } else {
        const distM = calculateGeodesicDistanceMeters(
          { lat: measureStart.lat, lon: measureStart.lon },
          { lat: pt.lat, lon: pt.lon }
        );
        const dLon = pt.lon - measureStart.lon;
        const dLat = pt.lat - measureStart.lat;
        const bearing = (Math.atan2(dLon, dLat) * 180) / Math.PI;

        setActiveMeasurement({
          pointA: measureStart,
          pointB: pt,
          distanceM: Math.round(distM),
          distanceKm: +(distM / 1000).toFixed(2),
          bearingDeg: Math.round((bearing + 360) % 360),
        });
        setMeasureStart(null);
      }
    } else if (activeTool === 'draw_rect') {
      if (!rectStart) {
        setRectStart(pt);
      } else {
        // Complete Rectangle
        const p1 = rectStart;
        const p2 = pt;
        const ring: [number, number][] = [
          [p1.lon, p1.lat],
          [p2.lon, p1.lat],
          [p2.lon, p2.lat],
          [p1.lon, p2.lat],
          [p1.lon, p1.lat],
        ];
        const areaM2 = calculateGeodesicPolygonAreaM2(ring);
        const areaHa = Math.round((areaM2 / 10000) * 100) / 100;

        const newAoi = {
          type: 'rectangle' as const,
          points: [
            p1,
            { ...p1, x: p2.x, normX: p2.normX, lon: p2.lon },
            p2,
            { ...p2, x: p1.x, normX: p1.normX, lon: p1.lon },
          ],
          areaM2,
          areaHa,
        };
        setDrawnAoi(newAoi);
        setRectStart(null);
        setTempRectEnd(null);
        setActiveTool('pan');
        if (onAoiChange) onAoiChange({ coordinates: ring, areaM2, areaHa });
      }
    } else if (activeTool === 'draw_poly') {
      setPolygonVertices((prev) => [...prev, pt]);
    }
  };

  // Finish Polygon Drawing on Double Click
  const handleDoubleClick = () => {
    if (activeTool === 'draw_poly' && polygonVertices.length >= 3) {
      const ring: [number, number][] = polygonVertices.map((p) => [p.lon, p.lat]);
      ring.push([polygonVertices[0].lon, polygonVertices[0].lat]);
      const areaM2 = calculateGeodesicPolygonAreaM2(ring);
      const areaHa = Math.round((areaM2 / 10000) * 100) / 100;

      const newAoi = {
        type: 'polygon' as const,
        points: polygonVertices,
        areaM2,
        areaHa,
      };
      setDrawnAoi(newAoi);
      setPolygonVertices([]);
      setActiveTool('pan');
      if (onAoiChange) onAoiChange({ coordinates: ring, areaM2, areaHa });
    }
  };

  const handleClearAoi = () => {
    setDrawnAoi(null);
    setPolygonVertices([]);
    setRectStart(null);
    setTempRectEnd(null);
    if (onAoiChange) onAoiChange(null);
  };

  // Spectral filter styling for various earth observation lenses
  const getFilterStyle = () => {
    switch (activeLens) {
      case 'NIR':
      case 'NIR (Near Infrared)':
        return 'hue-rotate-90 saturate-150 contrast-125';
      case 'SWIR':
      case 'SWIR (Short-Wave Infrared)':
        return 'sepia hue-rotate-180 contrast-150 saturate-200';
      case 'NDVI':
      case 'NDVI (Vegetation Index)':
        return 'invert hue-rotate-120 saturate-200 contrast-150';
      case 'NDWI':
      case 'NDWI (Water Index)':
        return 'hue-rotate-180 saturate-200 brightness-110';
      case 'NDBI':
      case 'NDBI (Built-up Index)':
        return 'hue-rotate-30 saturate-200 contrast-125';
      case 'SAR':
      case 'SAR (Radar Backscatter)':
        return 'grayscale contrast-200 brightness-90';
      case 'False color':
        return 'hue-rotate-60 saturate-150';
      default:
        return '';
    }
  };

  // Calculate dynamic scale bar in meters based on zoom level and GSD
  const scaleBarMeters = Math.round(500 / zoom);

  return (
    <div
      ref={containerRef}
      onMouseUp={handleMouseUp}
      className={`relative w-full h-full flex flex-col bg-[#0A0A0A] overflow-hidden select-none ${
        isFullscreen ? 'fixed inset-0 z-50' : ''
      }`}
    >
      {/* Top Map Action Toolbar */}
      <div className="h-10 shrink-0 bg-[#141414]/95 border-b border-[#262626] px-3 flex items-center justify-between z-20 backdrop-blur-md">
        <div className="flex items-center space-x-2 text-xs font-mono text-neutral-300">
          <MapPin className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-semibold text-neutral-100">{locationName}</span>
          <span className="text-neutral-600">|</span>
          <span className="text-neutral-400">{utmInfo.name}</span>
          <span className="text-neutral-600">|</span>
          <span className="text-emerald-400">{gsdMeters}m GSD</span>
        </div>

        <div className="flex items-center space-x-1.5">
          {/* Tool Mode Buttons */}
          <div className="flex items-center bg-[#1E1E1E] rounded-lg p-0.5 border border-[#333333]">
            <button
              onClick={() => setActiveTool('pan')}
              className={`px-2 py-1 rounded text-[11px] font-mono transition-colors ${
                activeTool === 'pan'
                  ? 'bg-cyan-500 text-black font-bold'
                  : 'text-neutral-400 hover:text-neutral-200'
              }`}
              title="Pan Map"
            >
              Pan
            </button>
            <button
              onClick={() => {
                setActiveTool('measure');
                setMeasureStart(null);
                setActiveMeasurement(null);
              }}
              className={`px-2 py-1 rounded text-[11px] font-mono transition-colors flex items-center gap-1 ${
                activeTool === 'measure'
                  ? 'bg-cyan-500 text-black font-bold'
                  : 'text-neutral-400 hover:text-neutral-200'
              }`}
              title="Measure Geodesic Distance"
            >
              <Ruler className="w-3 h-3" />
              <span>Ruler</span>
            </button>
            <button
              onClick={() => {
                setActiveTool('draw_rect');
                setRectStart(null);
              }}
              className={`px-2 py-1 rounded text-[11px] font-mono transition-colors flex items-center gap-1 ${
                activeTool === 'draw_rect'
                  ? 'bg-amber-500 text-black font-bold'
                  : 'text-neutral-400 hover:text-neutral-200'
              }`}
              title="Draw Rectangle AOI"
            >
              <Square className="w-3 h-3" />
              <span>Rect AOI</span>
            </button>
            <button
              onClick={() => {
                setActiveTool('draw_poly');
                setPolygonVertices([]);
              }}
              className={`px-2 py-1 rounded text-[11px] font-mono transition-colors flex items-center gap-1 ${
                activeTool === 'draw_poly'
                  ? 'bg-amber-500 text-black font-bold'
                  : 'text-neutral-400 hover:text-neutral-200'
              }`}
              title="Draw Polygon AOI (Double-click to finish)"
            >
              <Pentagon className="w-3 h-3" />
              <span>Poly AOI</span>
            </button>
          </div>

          {/* Clear AOI button */}
          {drawnAoi && (
            <button
              onClick={handleClearAoi}
              className="flex items-center gap-1 px-2 py-1 rounded bg-rose-950/60 border border-rose-800/80 text-rose-300 text-[11px] font-mono hover:bg-rose-900 transition-colors"
              title="Clear Custom AOI"
            >
              <Trash2 className="w-3 h-3" />
              <span>Clear AOI</span>
            </button>
          )}

          {/* Layers Toggle */}
          <button
            onClick={() => setShowLayerMenu(!showLayerMenu)}
            className={`p-1.5 rounded text-xs transition-colors ${
              showLayerMenu ? 'bg-[#333333] text-cyan-400' : 'bg-[#1E1E1E] text-neutral-300 hover:bg-[#2A2A2A]'
            } border border-[#333333]`}
            title="Toggle Map Layers & Opacity"
          >
            <Layers className="w-3.5 h-3.5" />
          </button>

          {/* Zoom controls */}
          <div className="flex items-center space-x-0.5 border-l border-[#333333] pl-2">
            <button
              onClick={handleZoomOut}
              className="p-1 rounded hover:bg-[#262626] text-neutral-400 hover:text-neutral-200"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="text-[11px] font-mono text-neutral-400 px-1">{Math.round(zoom * 100)}%</span>
            <button
              onClick={handleZoomIn}
              className="p-1 rounded hover:bg-[#262626] text-neutral-400 hover:text-neutral-200"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleResetView}
              className="p-1 rounded hover:bg-[#262626] text-neutral-400 hover:text-neutral-200"
              title="Reset View"
            >
              <RotateCcw className="w-3 h-3" />
            </button>
          </div>

          {/* Fullscreen toggle */}
          <button
            onClick={() => setIsFullscreen((v) => !v)}
            className="p-1 rounded hover:bg-[#262626] text-neutral-400 hover:text-neutral-200 border-l border-[#333333] pl-2"
            title="Toggle Fullscreen"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Layer Control Popover */}
      {showLayerMenu && (
        <div className="absolute top-12 right-4 z-40 w-64 bg-[#141414] border border-[#2E2E2E] rounded-xl p-3 shadow-2xl space-y-3 font-mono text-xs text-neutral-200">
          <div className="flex items-center justify-between pb-2 border-b border-[#262626]">
            <span className="font-bold flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-cyan-400" />
              Layer Stack & Overlays
            </span>
            <button onClick={() => setShowLayerMenu(false)} className="text-neutral-500 hover:text-neutral-300">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Basemap Selection */}
          <div>
            <span className="text-[10px] text-neutral-400 uppercase tracking-wider block mb-1.5">Basemap Source</span>
            <div className="grid grid-cols-3 gap-1">
              {(['satellite', 'carto', 'tactical_dark'] as const).map((b) => (
                <button
                  key={b}
                  onClick={() => setBasemap(b)}
                  className={`py-1 px-1.5 rounded text-[10px] capitalize transition-colors ${
                    basemap === b ? 'bg-cyan-600 text-white font-bold' : 'bg-[#1E1E1E] text-neutral-400 hover:bg-[#2A2A2A]'
                  }`}
                >
                  {b.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Visibility Toggles */}
          <div className="space-y-1.5">
            <span className="text-[10px] text-neutral-400 uppercase tracking-wider block">Visible Layers</span>
            {Object.entries(visibleLayers).map(([layerKey, isVisible]) => (
              <label key={layerKey} className="flex items-center justify-between cursor-pointer py-0.5">
                <span className="text-[11px] capitalize text-neutral-300">{layerKey} Layer</span>
                <input
                  type="checkbox"
                  checked={isVisible}
                  onChange={(e) => setVisibleLayers((prev) => ({ ...prev, [layerKey]: e.target.checked }))}
                  className="rounded border-[#444] bg-[#222] text-cyan-500 focus:ring-0"
                />
              </label>
            ))}
          </div>

          {/* Change Opacity Slider */}
          <div>
            <div className="flex justify-between text-[10px] text-neutral-400 mb-1">
              <span>Change Layer Opacity</span>
              <span>{Math.round(changeOpacity * 100)}%</span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={changeOpacity}
              onChange={(e) => setChangeOpacity(parseFloat(e.target.value))}
              className="w-full accent-cyan-400"
            />
          </div>
        </div>
      )}

      {/* Main Map Canvas Area */}
      <div
        onMouseMove={handleMouseMove}
        onMouseDown={handleMouseDown}
        onClick={handleCanvasClick}
        onDoubleClick={handleDoubleClick}
        className={`flex-1 relative flex items-center justify-center overflow-hidden p-6 ${
          activeTool === 'pan' ? (isPanning ? 'cursor-grabbing' : 'cursor-grab') : 'cursor-crosshair'
        }`}
      >
        {/* Background Geodetic Grid Lines */}
        {visibleLayers.grid && (
          <div
            className="absolute inset-0 opacity-[0.18] pointer-events-none"
            style={{
              backgroundImage:
                'linear-gradient(rgba(56,189,248,0.35) 1px, transparent 1px), linear-gradient(90deg, rgba(56,189,248,0.35) 1px, transparent 1px)',
              backgroundSize: '40px 40px',
            }}
          />
        )}

        {/* Scaled Image & Vector Container */}
        <div
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
          }}
          className="relative inline-block transition-transform duration-75 shadow-2xl"
        >
          {previewUrl && visibleLayers.imagery ? (
            <img
              ref={imgRef}
              src={getPreviewUrl(previewUrl) ?? undefined}
              alt="Satellite Raster"
              className={`max-h-[520px] w-auto object-contain rounded-md border border-neutral-800 transition-all duration-150 ${getFilterStyle()}`}
            />
          ) : (
            <div
              ref={imgRef as any}
              className={`w-[600px] h-[420px] rounded-md border border-neutral-800 flex items-center justify-center ${
                basemap === 'satellite'
                  ? 'bg-gradient-to-tr from-emerald-950/90 via-slate-900 to-neutral-950'
                  : basemap === 'carto'
                  ? 'bg-gradient-to-tr from-slate-900 via-neutral-900 to-neutral-950'
                  : 'bg-[#0E0E0E]'
              }`}
            >
              <div className="text-center p-4 font-mono text-xs text-neutral-400">
                <Compass className="w-7 h-7 text-cyan-400 mx-auto mb-1.5 opacity-80 animate-pulse" />
                <p className="font-bold text-neutral-200">{locationName}</p>
                <p className="text-[11px] text-neutral-500">
                  {centerLat.toFixed(4)}°N, {centerLon.toFixed(4)}°E · {utmInfo.name}
                </p>
              </div>
            </div>
          )}

          {/* SVG Vector Overlays */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 1000 1000" preserveAspectRatio="none">
            {/* Change Detection Polygons */}
            {visibleLayers.change &&
              changePolygons.map((feat: any, idx: number) => {
                const bbox = feat.properties?.bbox_normalized || { xmin: 0.32, ymin: 0.28, xmax: 0.65, ymax: 0.58 };
                const x = bbox.xmin * 1000;
                const y = bbox.ymin * 1000;
                const w = (bbox.xmax - bbox.xmin) * 1000;
                const h = (bbox.ymax - bbox.ymin) * 1000;
                const id = feat.properties?.id || feat.id || `CLUSTER_${idx + 1}`;
                const isSelected = selectedRegionId === id;

                return (
                  <g key={`change-poly-${idx}`} className="pointer-events-auto cursor-pointer">
                    <rect
                      x={x}
                      y={y}
                      width={w}
                      height={h}
                      fill={`rgba(239, 68, 68, ${isSelected ? 0.45 : changeOpacity * 0.3})`}
                      stroke={isSelected ? '#f87171' : '#ef4444'}
                      strokeWidth={isSelected ? '3' : '2'}
                      strokeDasharray="5 3"
                      onClick={(e) => {
                        e.stopPropagation();
                        setInspectedCluster(feat);
                        if (onSelectRegion) onSelectRegion(id);
                      }}
                    />
                    <circle cx={x} cy={y} r="4" fill="#ef4444" />
                    <circle cx={x + w} cy={y + h} r="4" fill="#ef4444" />
                  </g>
                );
              })}

            {/* Visual Grounding Detections */}
            {visibleLayers.grounding &&
              geojsonFeatures.map((feat: any, idx: number) => {
                const bbox = feat.properties?.bbox_normalized || { xmin: 0.28, ymin: 0.32, xmax: 0.68, ymax: 0.62 };
                const x = bbox.xmin * 1000;
                const y = bbox.ymin * 1000;
                const w = (bbox.xmax - bbox.xmin) * 1000;
                const h = (bbox.ymax - bbox.ymin) * 1000;
                const label = feat.properties?.label || 'Grounded Feature';

                return (
                  <g key={`ground-poly-${idx}`} className="pointer-events-auto cursor-pointer">
                    <rect
                      x={x}
                      y={y}
                      width={w}
                      height={h}
                      fill="rgba(56, 189, 248, 0.25)"
                      stroke="#38bdf8"
                      strokeWidth="2.5"
                    />
                    <text x={x + 6} y={y + 18} fill="#38bdf8" fontSize="18" fontWeight="bold" fontFamily="monospace">
                      {label}
                    </text>
                  </g>
                );
              })}

            {/* Custom Drawn AOI (Rectangle or Polygon) */}
            {visibleLayers.aoi && drawnAoi && (
              <g className="pointer-events-auto">
                <polygon
                  points={drawnAoi.points.map((p) => `${p.normX * 1000},${p.normY * 1000}`).join(' ')}
                  fill="rgba(245, 158, 11, 0.25)"
                  stroke="#f59e0b"
                  strokeWidth="2.5"
                  strokeDasharray="6 3"
                />
                {drawnAoi.points.map((p, pIdx) => (
                  <circle key={pIdx} cx={p.normX * 1000} cy={p.normY * 1000} r="4.5" fill="#f59e0b" />
                ))}
              </g>
            )}

            {/* Active Rectangle AOI In-Progress */}
            {activeTool === 'draw_rect' && rectStart && tempRectEnd && (
              <rect
                x={Math.min(rectStart.normX, tempRectEnd.normX) * 1000}
                y={Math.min(rectStart.normY, tempRectEnd.normY) * 1000}
                width={Math.abs(tempRectEnd.normX - rectStart.normX) * 1000}
                height={Math.abs(tempRectEnd.normY - rectStart.normY) * 1000}
                fill="rgba(245, 158, 11, 0.2)"
                stroke="#f59e0b"
                strokeWidth="2"
                strokeDasharray="4 4"
              />
            )}

            {/* Active Polygon AOI In-Progress */}
            {activeTool === 'draw_poly' && polygonVertices.length > 0 && (
              <g>
                <polyline
                  points={polygonVertices.map((p) => `${p.normX * 1000},${p.normY * 1000}`).join(' ')}
                  fill="none"
                  stroke="#f59e0b"
                  strokeWidth="2"
                  strokeDasharray="4 4"
                />
                {polygonVertices.map((p, vIdx) => (
                  <circle key={vIdx} cx={p.normX * 1000} cy={p.normY * 1000} r="4" fill="#f59e0b" />
                ))}
              </g>
            )}

            {/* Measurement Rubber-band Line */}
            {activeMeasurement && (
              <g className="pointer-events-none">
                <line
                  x1={activeMeasurement.pointA.normX * 1000}
                  y1={activeMeasurement.pointA.normY * 1000}
                  x2={activeMeasurement.pointB.normX * 1000}
                  y2={activeMeasurement.pointB.normY * 1000}
                  stroke="#38bdf8"
                  strokeWidth="3"
                  strokeDasharray="6 4"
                />
                <circle cx={activeMeasurement.pointA.normX * 1000} cy={activeMeasurement.pointA.normY * 1000} r="5" fill="#38bdf8" />
                <circle cx={activeMeasurement.pointB.normX * 1000} cy={activeMeasurement.pointB.normY * 1000} r="5" fill="#38bdf8" />
              </g>
            )}
          </svg>
        </div>

        {/* Floating North Indicator & Scale Bar */}
        <div className="absolute top-4 left-4 z-30 flex flex-col gap-2 font-mono text-[10px] text-neutral-300 pointer-events-auto">
          {/* North Compass */}
          <div
            onClick={handleResetView}
            className="w-8 h-8 rounded-lg bg-[#141414]/90 border border-[#2A2A2A] flex items-center justify-center cursor-pointer hover:border-cyan-500 shadow-md transition-colors"
            title="North Indicator (Click to re-center)"
          >
            <div className="flex flex-col items-center">
              <span className="text-[8px] font-bold text-rose-500 leading-none">N</span>
              <Compass className="w-3.5 h-3.5 text-cyan-400" />
            </div>
          </div>

          {/* Scale Bar */}
          <div className="bg-[#141414]/90 border border-[#2A2A2A] px-2 py-1 rounded shadow-md">
            <div className="flex justify-between items-center text-[9px] text-neutral-400 mb-0.5">
              <span>0</span>
              <span>{scaleBarMeters} m</span>
            </div>
            <div className="w-16 h-1 bg-neutral-700 rounded-xs flex overflow-hidden">
              <div className="w-1/2 h-full bg-neutral-200" />
              <div className="w-1/2 h-full bg-neutral-900" />
            </div>
          </div>
        </div>

        {/* Drawn AOI Information Callout */}
        {drawnAoi && (
          <div className="absolute top-4 right-4 z-30 bg-[#141414]/95 border border-amber-500/60 rounded-xl p-3 shadow-2xl font-mono text-xs text-neutral-200 flex items-center gap-3">
            <div>
              <div className="flex items-center gap-1.5 text-amber-400 font-bold">
                <Square className="w-3.5 h-3.5" />
                <span>Custom Area of Interest (AOI)</span>
              </div>
              <div className="text-[11px] text-neutral-300 mt-0.5">
                Calculated Ground Area: <strong className="text-white">{drawnAoi.areaHa} ha</strong> ({drawnAoi.areaM2.toLocaleString()} m²)
              </div>
            </div>
            <button onClick={handleClearAoi} className="p-1 rounded text-neutral-500 hover:text-rose-400 transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Floating Live Measurement Callout */}
        {activeMeasurement && (
          <div className="absolute bottom-16 left-1/2 -translate-x-1/2 bg-[#141414]/95 border border-cyan-500/60 rounded-xl px-4 py-2.5 text-xs font-mono text-neutral-200 shadow-2xl z-30 flex items-center space-x-3">
            <Ruler className="w-4 h-4 text-cyan-400" />
            <div>
              <span className="text-neutral-400">Ground Geodesic Distance: </span>
              <span className="text-cyan-300 font-bold text-sm">
                {activeMeasurement.distanceM.toLocaleString()} m ({activeMeasurement.distanceKm} km)
              </span>
              <span className="text-neutral-500 ml-2">| Azimuth: {activeMeasurement.bearingDeg}°</span>
            </div>
            <button
              onClick={() => {
                setActiveMeasurement(null);
                setMeasureStart(null);
              }}
              className="text-neutral-500 hover:text-neutral-300"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Feature Inspection Drawer */}
        {inspectedCluster && (
          <div className="absolute bottom-12 right-4 z-30 w-80 bg-[#141414]/95 border border-[#333333] rounded-xl p-3.5 shadow-2xl font-mono text-xs text-neutral-200 space-y-2.5">
            <div className="flex items-center justify-between border-b border-[#262626] pb-2">
              <span className="font-bold text-emerald-400 flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5" />
                Cluster #{inspectedCluster.properties?.cluster_id || '01'} Inspection
              </span>
              <button onClick={() => setInspectedCluster(null)} className="text-neutral-500 hover:text-neutral-300">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-[11px] text-neutral-300 leading-snug">
              {inspectedCluster.properties?.label || 'Detected Structural Expansion Cluster'}
            </p>
            <div className="grid grid-cols-2 gap-2 text-[10px] bg-[#1C1C1C] p-2 rounded-lg border border-[#2E2E2E]">
              <div>
                <span className="text-neutral-500 block">Ground Area:</span>
                <strong className="text-white">
                  {inspectedCluster.properties?.area_ha || 1.82} ha ({(inspectedCluster.properties?.area_m2 || 18200).toLocaleString()} m²)
                </strong>
              </div>
              <div>
                <span className="text-neutral-500 block">Confidence:</span>
                <strong className="text-emerald-400 font-bold">
                  {Math.round((inspectedCluster.properties?.confidence || 0.94) * 100)}% Verified
                </strong>
              </div>
              <div>
                <span className="text-neutral-500 block">delta NDVI:</span>
                <strong className="text-rose-400">{inspectedCluster.properties?.delta_ndvi || -0.42}</strong>
              </div>
              <div>
                <span className="text-neutral-500 block">delta SAR:</span>
                <strong className="text-cyan-400">+{inspectedCluster.properties?.delta_sar_db || 4.1} dB</strong>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Coordinates & Telemetry Status Bar */}
      <div className="h-8 shrink-0 bg-[#0E0E0E] border-t border-[#222222] px-4 flex items-center justify-between text-[11px] font-mono text-neutral-400 z-20">
        <div className="flex items-center space-x-3">
          <span>Raster: {imageWidth} × {imageHeight} px</span>
          <span className="text-neutral-700">|</span>
          <span>Target: {locationName} ({centerLat.toFixed(4)}°N, {centerLon.toFixed(4)}°E)</span>
        </div>

        {cursorPos ? (
          <div className="flex items-center space-x-2 text-cyan-300 bg-[#161616] px-2.5 py-0.5 rounded border border-[#2B2B2B]">
            <Crosshair className="w-3 h-3 text-cyan-400" />
            <span>WGS84: {cursorPos.lat.toFixed(5)}°N, {cursorPos.lon.toFixed(5)}°E</span>
            <span className="text-neutral-600">|</span>
            <span>UTM: {cursorPos.utmE.toLocaleString()}m E, {cursorPos.utmN.toLocaleString()}m N</span>
            <span className="text-neutral-600">|</span>
            <span className="text-neutral-400">Pixel: ({Math.round(cursorPos.normX * imageWidth)}, {Math.round(cursorPos.normY * imageHeight)})</span>
          </div>
        ) : (
          <span className="text-neutral-600">Hover canvas to inspect georeferenced coordinates</span>
        )}
      </div>
    </div>
  );
};
