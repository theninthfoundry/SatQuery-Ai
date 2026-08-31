'use client';

import React, { useRef } from 'react';
import { MapToolbar, LensMode } from './MapToolbar';
import { MapControls } from './MapControls';
import { TemporalController } from './TemporalController';
import { MapMetadata } from './MapMetadata';
import { RealisticSatelliteCanvas } from './RealisticSatelliteCanvas';
import { FloatingFindingSurface } from '../intelligence/FloatingFindingSurface';
import { Ruler, X, Satellite } from 'lucide-react';
import { useWorkspace, ChangeCluster, CursorCoordinates } from '../../context/WorkspaceContext';

interface GeoWorkspaceProps {
  previewUrl?: string | null;
  activeLens?: LensMode;
  onSelectLens?: (lens: LensMode) => void;
  selectedRegionId?: string | null;
  onSelectRegion?: (regionId: string | null) => void;
  clusters?: ChangeCluster[];
  dateT1?: string;
  dateT2?: string;
}

export const GeoWorkspace: React.FC<GeoWorkspaceProps> = ({
  activeLens: propActiveLens,
  onSelectLens: propOnSelectLens,
  selectedRegionId: propSelectedRegionId,
  onSelectRegion: propOnSelectRegion,
  clusters: propClusters,
  dateT1: propDateT1,
  dateT2: propDateT2,
}) => {
  const ws = useWorkspace();

  const activeLens = propActiveLens || ws.activeLens;
  const onSelectLens = propOnSelectLens || ws.setActiveLens;
  const selectedRegionId =
    propSelectedRegionId !== undefined ? propSelectedRegionId : ws.selectedClusterId;
  const onSelectRegion = propOnSelectRegion || ws.selectCluster;
  const clusters = propClusters || ws.clusters;
  const dateT1 = propDateT1 || ws.dateT1;
  const dateT2 = propDateT2 || ws.dateT2;

  const containerRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef(false);
  const dragStartRef = useRef({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
    const y = Math.max(0, Math.min(e.clientY - rect.top, rect.height));

    const normX = x / rect.width;
    const normY = y / rect.height;

    // Projected UTM Zone coordinates derived from current mission
    const utmE = Math.round(485000 + normX * 10980 * 10);
    const utmN = Math.round(1387000 - normY * 10980 * 10);
    const lat = +(ws.currentMission.lat + (0.5 - normY) * 0.08).toFixed(5);
    const lon = +(ws.currentMission.lon + (normX - 0.5) * 0.08).toFixed(5);

    const coords: CursorCoordinates = { lat, lon, utmE, utmN, normX, normY };
    ws.setCursorCoords(coords);

    // Pan handling if in pan tool or dragging
    if (isDraggingRef.current && (ws.activeTool === 'pan' || e.buttons === 1)) {
      const dx = e.clientX - dragStartRef.current.x;
      const dy = e.clientY - dragStartRef.current.y;
      ws.setPan((prev) => ({ x: prev.x + dx * 0.4, y: prev.y + dy * 0.4 }));
      dragStartRef.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (ws.activeTool === 'pan' || ws.activeTool === 'select') {
      isDraggingRef.current = true;
      dragStartRef.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleCanvasClick = () => {
    if (ws.activeTool === 'measure' && ws.cursorCoords) {
      ws.handleCanvasMeasurementClick(ws.cursorCoords);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-[#0A0A0A] select-none overflow-hidden relative">
      {/* Central Satellite Map Canvas Frame */}
      <div className="flex-1 relative flex items-center justify-center overflow-hidden">
        {/* Main Map Box */}
        <div
          ref={containerRef}
          onMouseMove={handleMouseMove}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onClick={handleCanvasClick}
          className={`relative w-full h-full bg-[#0A0A0A] overflow-hidden flex items-center justify-center ${
            ws.activeTool === 'measure'
              ? 'cursor-crosshair'
              : ws.activeTool === 'pan'
              ? 'cursor-grab active:cursor-grabbing'
              : 'cursor-default'
          }`}
        >
          {/* Floating Top-Left Observation Launcher Badge */}
          <div className="absolute top-4 left-6 z-20 flex items-center gap-1.5 p-1 rounded-xl bg-white/95 backdrop-blur-md border border-[#E6E6E1] shadow-lg">
            <button
              onClick={() => ws.toggleDrawer('scene')}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono font-bold text-[#111111] hover:bg-[#FAF9F7] transition-colors"
              title="Open Observations Drawer"
            >
              <Satellite className="w-3.5 h-3.5 text-[#6F6F6A]" />
              <span>OBSERVATIONS · {ws.datasets.length}</span>
            </button>
            <div className="flex items-center gap-1 pl-1 border-l border-[#E6E6E1]">
              {ws.datasets.map((d, idx) => {
                const isActive = ws.activeDatasetIndex === idx;
                return (
                  <button
                    key={d.id}
                    onClick={() => {
                      ws.setActiveDatasetIndex(idx);
                      if (d.modality === 'sar') ws.setActiveLens('SAR');
                      else ws.setActiveLens('True Color');
                    }}
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold transition-all ${
                      isActive
                        ? 'bg-[#111111] text-white shadow-xs'
                        : 'text-[#6F6F6A] hover:text-[#111111] hover:bg-[#FAF9F7]'
                    }`}
                  >
                    {idx === 0 ? 'T1' : idx === 1 ? 'T2' : 'SAR'}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Floating Minimal Segmented View Lens Switcher */}
          <MapToolbar
            activeLens={activeLens}
            onSelectLens={onSelectLens}
          />

          {/* Floating Map Tools Rail */}
          <MapControls
            activeTool={ws.activeTool}
            onSelectTool={ws.setActiveTool}
            onZoomIn={ws.zoomIn}
            onZoomOut={ws.zoomOut}
            onResetZoom={ws.resetZoom}
            isMeasuring={ws.activeTool === 'measure'}
          />

          {/* Floating Spatial Finding Surface (Emerges on lower-right) */}
          <FloatingFindingSurface onInspectEvidence={() => ws.toggleDrawer('evidence')} />

          {/* Geodetic Map Reference Grid */}
          {ws.overlays.grid && (
            <div className="absolute inset-0 map-cross-grid pointer-events-none opacity-20 z-10" />
          )}

          {/* Satellite Scaled Image Container */}
          <div
            style={{
              transform: `scale(${ws.zoom}) translate(${ws.pan.x}px, ${ws.pan.y}px)`,
              transformOrigin: 'center center',
              transition: isDraggingRef.current
                ? 'none'
                : 'transform 180ms cubic-bezier(0.16, 1, 0.3, 1)',
            }}
            className="relative w-full h-full flex items-center justify-center"
          >
            {/* Real Earth Observation Scene Canvas */}
            <RealisticSatelliteCanvas
              activeLens={activeLens}
              activeDatasetIndex={ws.activeDatasetIndex}
              temporalMode={ws.temporalMode}
              sliderPos={ws.sliderPos}
              onSliderChange={ws.setSliderPos}
              clusters={clusters}
              selectedClusterId={selectedRegionId}
              onSelectCluster={onSelectRegion}
              dateT1={dateT1}
              dateT2={dateT2}
            />
          </div>

          {/* Floating Distance Ruler Callout */}
          {ws.activeMeasurement && (
            <div className="absolute bottom-16 left-1/2 -translate-x-1/2 bg-[#0A0A0A]/90 backdrop-blur-md text-white px-4 py-2 rounded-full shadow-floating z-30 flex items-center gap-3 border border-white/20 text-xs font-mono">
              <Ruler className="w-4 h-4 text-emerald-400" />
              <span>
                Geodesic Distance:{' '}
                <strong className="text-white">
                  {ws.activeMeasurement.distM.toLocaleString()} m
                </strong>{' '}
                ({ws.activeMeasurement.distKm} km)
              </span>
              <span className="text-white/40">|</span>
              <span className="text-white/70">Bearing: {ws.activeMeasurement.bearing}°</span>
              <button
                onClick={() => ws.resetMeasurement()}
                className="text-white/60 hover:text-white ml-1"
                title="Clear Measurement (ESC)"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Map Metadata Scale & Coordinates Strip */}
          <MapMetadata coordinates={ws.cursorCoords} />
        </div>
      </div>

      {/* Temporal Comparison Controller Bar Directly Underneath Canvas */}
      <TemporalController
        sliderPos={ws.sliderPos}
        onSliderChange={ws.setSliderPos}
        temporalMode={ws.temporalMode}
        onSelectTemporalMode={ws.setTemporalMode}
        dateT1={dateT1}
        dateT2={dateT2}
      />
    </div>
  );
};
export type { ChangeCluster };
