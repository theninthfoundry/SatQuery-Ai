'use client';

import React from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface MapMetadataProps {
  coordinates?: {
    lat: number;
    lon: number;
    utmE?: number;
    utmN?: number;
  } | null;
  crs?: string;
  gsdMeters?: number;
  scaleKm?: number;
}

export const MapMetadata: React.FC<MapMetadataProps> = ({
  coordinates,
  crs = 'EPSG:32643',
  gsdMeters = 10,
  scaleKm = 1.5,
}) => {
  const ws = useWorkspace();
  const activeLat = coordinates?.lat ?? ws.currentMission?.lat ?? 12.9716;
  const activeLon = coordinates?.lon ?? ws.currentMission?.lon ?? 77.5946;

  // Mathematically derive UTM zone and EPSG from the active geodetic position
  const zoneNumber = Math.floor((activeLon + 180) / 6) + 1;
  const isNorth = activeLat >= 0;
  const computedEpsg = isNorth ? 32600 + zoneNumber : 32700 + zoneNumber;
  const computedUtm = `UTM Zone ${zoneNumber}${isNorth ? 'N' : 'S'}`;
  const locationLabel = ws.currentMission?.name?.split('(')[0]?.trim() || 'TARGET AOI';

  const sensorStr =
    ws.activeLens === 'SAR'
      ? 'SENTINEL-1 C-SAR · 10m'
      : ws.activeLens === 'NIR'
      ? 'SENTINEL-2 MSI (CIR B08/B04/B03)'
      : ws.activeLens === 'SWIR'
      ? 'SENTINEL-2 MSI (SWIR B12/B8A/B04)'
      : 'SENTINEL-2 L2A · 10m';

  const latStr = `${Math.abs(activeLat).toFixed(4)}° ${activeLat >= 0 ? 'N' : 'S'}`;
  const lonStr = `${Math.abs(activeLon).toFixed(4)}° ${activeLon >= 0 ? 'E' : 'W'}`;

  return (
    <div className="absolute bottom-2 left-4 right-4 z-10 flex items-center justify-between pointer-events-none select-none text-[10px] font-mono text-neutral-400 tracking-wider">
      {/* Left: Minimal Scale Line */}
      <div className="flex items-center gap-1.5 pointer-events-auto bg-black/60 backdrop-blur-md px-2 py-1 rounded border border-white/10">
        <div className="flex flex-col">
          <div className="flex justify-between w-16 text-[8px] text-neutral-400 leading-none">
            <span>0</span>
            <span>{scaleKm} km</span>
          </div>
          <div className="w-16 h-0.5 border-b border-l border-r border-neutral-400 mt-0.5" />
        </div>
      </div>

      {/* Right: Geodetic Coordinates & Mission Parameters */}
      <div className="flex items-center gap-2 pointer-events-auto text-neutral-400 bg-black/75 backdrop-blur-md px-2.5 py-1 rounded border border-white/10 shadow-lg">
        <span className="text-white font-semibold tracking-normal truncate max-w-[180px] sm:max-w-none">
          {locationLabel}
        </span>
        <span className="text-neutral-600">·</span>
        <span className="text-neutral-200 font-mono">
          {latStr}  {lonStr}
        </span>
        <span className="text-neutral-600">·</span>
        <span className="text-satblue-400 font-mono font-medium">
          {computedUtm} (EPSG:{computedEpsg})
        </span>
        <span className="text-neutral-600">·</span>
        <span className="text-neutral-300">{sensorStr}</span>
      </div>
    </div>
  );
};

