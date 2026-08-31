'use client';

import React, { useState, useRef, useEffect } from 'react';
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
  Check,
  Eye,
  Camera,
  X,
} from 'lucide-react';
import { getPreviewUrl } from '../lib/api';

interface Point {
  x: number; // canvas pixel
  y: number;
  normX: number; // [0, 1]
  normY: number;
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
  geojsonFeatures?: any[];
  changePolygons?: any[];
  activeLens?: string;
  selectedRegionId?: string | null;
  onSelectRegion?: (id: string) => void;
}

export const InteractiveGeoMap: React.FC<InteractiveGeoMapProps> = ({
  previewUrl,
  imageWidth = 10980,
  imageHeight = 10980,
  gsdMeters = 10.0,
  crsCode = 'EPSG:32643',
  geojsonFeatures = [],
  changePolygons = [],
  activeLens = 'True color',
  selectedRegionId,
  onSelectRegion,
}) => {
  const [zoom, setZoom] = useState(1);
  const [isMeasuring, setIsMeasuring] = useState(false);
  const [measureStart, setMeasureStart] = useState<Point | null>(null);
  const [activeMeasurement, setActiveMeasurement] = useState<Measurement | null>(null);
  const [cursorPos, setCursorPos] = useState<Point | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Layer opacities
  const [changeOpacity, setChangeOpacity] = useState(0.8);
  const [vectorOpacity, setVectorOpacity] = useState(1.0);

  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.25, 3.5));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.25, 0.5));
  const handleResetZoom = () => {
    setZoom(1);
    setMeasureStart(null);
    setActiveMeasurement(null);
  };

  const computePoint = (clientX: number, clientY: number): Point | null => {
    if (!imgRef.current) return null;
    const rect = imgRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
    const y = Math.max(0, Math.min(clientY - rect.top, rect.height));

    const normX = x / rect.width;
    const normY = y / rect.height;

    // Simulated UTM Zone 43N base coordinates
    const utmE = Math.round(432000 + normX * (imageWidth * gsdMeters));
    const utmN = Math.round(1438000 - normY * (imageHeight * gsdMeters));

    return { x, y, normX, normY, utmE, utmN };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const pt = computePoint(e.clientX, e.clientY);
    if (!pt) return;
    setCursorPos(pt);

    if (isMeasuring && measureStart) {
      // Calculate live Euclidean distance
      const dxMeters = (pt.normX - measureStart.normX) * imageWidth * gsdMeters;
      const dyMeters = (pt.normY - measureStart.normY) * imageHeight * gsdMeters;
      const distM = Math.sqrt(dxMeters * dxMeters + dyMeters * dyMeters);
      const bearing = (Math.atan2(dxMeters, -dyMeters) * 180) / Math.PI;
      const normalizedBearing = (bearing + 360) % 360;

      setActiveMeasurement({
        pointA: measureStart,
        pointB: pt,
        distanceM: Math.round(distM),
        distanceKm: +(distM / 1000).toFixed(2),
        bearingDeg: Math.round(normalizedBearing),
      });
    }
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isMeasuring) return;
    const pt = computePoint(e.clientX, e.clientY);
    if (!pt) return;

    if (!measureStart) {
      setMeasureStart(pt);
      setActiveMeasurement(null);
    } else {
      // Complete measurement
      const dxMeters = (pt.normX - measureStart.normX) * imageWidth * gsdMeters;
      const dyMeters = (pt.normY - measureStart.normY) * imageHeight * gsdMeters;
      const distM = Math.sqrt(dxMeters * dxMeters + dyMeters * dyMeters);
      const bearing = (Math.atan2(dxMeters, -dyMeters) * 180) / Math.PI;
      const normalizedBearing = (bearing + 360) % 360;

      setActiveMeasurement({
        pointA: measureStart,
        pointB: pt,
        distanceM: Math.round(distM),
        distanceKm: +(distM / 1000).toFixed(2),
        bearingDeg: Math.round(normalizedBearing),
      });
      setMeasureStart(null); // finish segment
    }
  };

  const toggleMeasuringTool = () => {
    setIsMeasuring((v) => !v);
    setMeasureStart(null);
    setActiveMeasurement(null);
  };

  return (
    <div
      ref={containerRef}
      className={`relative w-full h-full flex flex-col bg-neutral-950 overflow-hidden select-none ${
        isFullscreen ? 'fixed inset-0 z-50' : ''
      }`}
    >
      {/* Top Map Action Toolbar */}
      <div className="h-10 shrink-0 bg-neutral-900/90 border-b border-neutral-800 px-3 flex items-center justify-between z-20 backdrop-blur-md">
        <div className="flex items-center space-x-2 text-xs font-mono text-neutral-300">
          <MapPin className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-semibold text-neutral-200">GIS Viewport</span>
          <span className="text-neutral-600">|</span>
          <span className="text-neutral-400">{crsCode}</span>
          <span className="text-neutral-600">|</span>
          <span className="text-emerald-400">{gsdMeters}m GSD</span>
        </div>

        <div className="flex items-center space-x-1.5">
          {/* Measurement Tool Button */}
          <button
            onClick={toggleMeasuringTool}
            className={`flex items-center space-x-1 px-2 py-1 rounded text-xs font-mono transition-colors ${
              isMeasuring
                ? 'bg-cyan-500 text-neutral-950 font-semibold shadow-md'
                : 'bg-neutral-800 text-neutral-300 hover:bg-neutral-700'
            }`}
          >
            <Ruler className="w-3.5 h-3.5" />
            <span>{isMeasuring ? 'Ruler Active (Click 2 Points)' : 'Measure Distance'}</span>
          </button>

          {/* Zoom controls */}
          <div className="flex items-center space-x-0.5 border-l border-neutral-800 pl-2">
            <button
              onClick={handleZoomOut}
              className="p-1 rounded hover:bg-neutral-800 text-neutral-400 hover:text-neutral-200"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="text-[11px] font-mono text-neutral-400 px-1">{Math.round(zoom * 100)}%</span>
            <button
              onClick={handleZoomIn}
              className="p-1 rounded hover:bg-neutral-800 text-neutral-400 hover:text-neutral-200"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleResetZoom}
              className="p-1 rounded hover:bg-neutral-800 text-neutral-400 hover:text-neutral-200"
              title="Reset View"
            >
              <RotateCcw className="w-3 h-3" />
            </button>
          </div>

          {/* Fullscreen toggle */}
          <button
            onClick={() => setIsFullscreen((v) => !v)}
            className="p-1 rounded hover:bg-neutral-800 text-neutral-400 hover:text-neutral-200 border-l border-neutral-800 pl-2"
            title="Toggle Fullscreen"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Main Map Canvas Area */}
      <div
        onMouseMove={handleMouseMove}
        onClick={handleCanvasClick}
        className={`flex-1 relative flex items-center justify-center overflow-hidden p-6 ${
          isMeasuring ? 'cursor-crosshair' : 'cursor-default'
        }`}
      >
        {/* Background Geodetic Grid Lines */}
        <div
          className="absolute inset-0 opacity-[0.20]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(56,189,248,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(56,189,248,0.3) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />

        {/* Scaled Image & Vector Container */}
        <div
          style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
          className="relative inline-block transition-transform duration-150 shadow-2xl"
        >
          {previewUrl ? (
            <img
              ref={imgRef}
              src={getPreviewUrl(previewUrl)}
              alt="Satellite Raster"
              className={`max-h-[500px] w-auto object-contain rounded-md border border-neutral-800 ${
                activeLens === 'NIR'
                  ? 'hue-rotate-90 saturate-150'
                  : activeLens === 'SAR'
                  ? 'grayscale contrast-150'
                  : ''
              }`}
            />
          ) : (
            <div
              ref={imgRef as any}
              className="w-[580px] h-[400px] bg-gradient-to-tr from-emerald-950/80 via-cyan-950/50 to-neutral-950 rounded-md border border-neutral-800 flex items-center justify-center"
            >
              <div className="text-center p-4 font-mono text-xs text-neutral-400">
                <Compass className="w-6 h-6 text-cyan-400 mx-auto mb-1 opacity-70" />
                <p>10m GSD · {crsCode} · Bangalore AOI</p>
              </div>
            </div>
          )}

          {/* SVG Vector Overlays */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 1000 1000" preserveAspectRatio="none">
            {/* Change Polygons */}
            {changePolygons.map((feat: any, idx: number) => {
              const bbox = feat.properties?.bbox_normalized || { xmin: 0.35, ymin: 0.28, xmax: 0.65, ymax: 0.58 };
              const x = bbox.xmin * 1000;
              const y = bbox.ymin * 1000;
              const w = (bbox.xmax - bbox.xmin) * 1000;
              const h = (bbox.ymax - bbox.ymin) * 1000;
              const id = feat.properties?.id || `REGION_${idx + 1}`;
              const isSelected = selectedRegionId === id;

              return (
                <g key={`change-poly-${idx}`} className="pointer-events-auto cursor-pointer">
                  <rect
                    x={x}
                    y={y}
                    width={w}
                    height={h}
                    fill={`rgba(239, 68, 68, ${isSelected ? 0.45 : changeOpacity * 0.25})`}
                    stroke={isSelected ? '#f87171' : '#ef4444'}
                    strokeWidth={isSelected ? '3' : '2'}
                    strokeDasharray="5 3"
                    onClick={() => onSelectRegion && onSelectRegion(id)}
                  />
                  <circle cx={x} cy={y} r="3.5" fill="#ef4444" />
                  <circle cx={x + w} cy={y + h} r="3.5" fill="#ef4444" />
                </g>
              );
            })}

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

        {/* Floating Live Measurement Callout */}
        {activeMeasurement && (
          <div className="absolute bottom-16 left-1/2 -translate-x-1/2 bg-neutral-900/95 border border-cyan-500/50 rounded-lg px-4 py-2 text-xs font-mono text-neutral-200 shadow-2xl z-30 flex items-center space-x-3">
            <Ruler className="w-4 h-4 text-cyan-400" />
            <div>
              <span className="text-neutral-400">Ground Distance: </span>
              <span className="text-cyan-300 font-bold text-sm">
                {activeMeasurement.distanceM.toLocaleString()} m ({activeMeasurement.distanceKm} km)
              </span>
              <span className="text-neutral-500 ml-2">| Bearing: {activeMeasurement.bearingDeg}°</span>
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
      </div>

      {/* Bottom Coordinates & Telemetry Status Bar */}
      <div className="h-8 shrink-0 bg-neutral-950/95 border-t border-neutral-800 px-4 flex items-center justify-between text-[11px] font-mono text-neutral-400 z-20">
        <div className="flex items-center space-x-3">
          <span>Raster: {imageWidth} × {imageHeight} px</span>
          <span className="text-neutral-700">|</span>
          <span>Target AOI: Bangalore Urban (12.97°N, 77.59°E)</span>
        </div>

        {cursorPos ? (
          <div className="flex items-center space-x-2 text-cyan-300 bg-neutral-900/80 px-2 py-0.5 rounded border border-neutral-800">
            <MapPin className="w-3 h-3 text-cyan-400" />
            <span>UTM 43N: {cursorPos.utmE.toLocaleString()}m E, {cursorPos.utmN.toLocaleString()}m N</span>
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
