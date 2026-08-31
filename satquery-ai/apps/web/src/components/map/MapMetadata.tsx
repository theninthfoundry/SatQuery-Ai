'use client';

import React from 'react';

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
  crs = 'EPSG:4326',
  gsdMeters = 10,
  scaleKm = 1.5,
}) => {
  const latStr = coordinates ? `${coordinates.lat.toFixed(4)}° N` : '12.9716° N';
  const lonStr = coordinates ? `${coordinates.lon.toFixed(4)}° E` : '77.5946° E';

  return (
    <div className="absolute bottom-4 left-6 right-6 z-10 flex items-center justify-between pointer-events-none select-none">
      {/* Left: Minimal Scale Bar */}
      <div className="flex items-center gap-2 bg-white/90 backdrop-blur-md px-2.5 py-1 rounded-md border border-[#E8E8E5] shadow-subtle pointer-events-auto">
        <div className="flex flex-col items-center">
          <div className="flex justify-between w-20 text-[9px] font-mono text-[#555555] px-0.5 leading-none">
            <span>0</span>
            <span>0.5</span>
            <span>1</span>
            <span>{scaleKm} km</span>
          </div>
          <div className="w-20 h-1 border-b-2 border-l-2 border-r-2 border-[#111111] mt-0.5" />
        </div>
      </div>

      {/* Right: Geodetic Coordinates & Projection Badge */}
      <div className="flex items-center gap-3 bg-white/90 backdrop-blur-md px-3 py-1 rounded-md border border-[#E8E8E5] shadow-subtle text-[11px] font-mono text-[#555555] pointer-events-auto">
        <span className="text-[#111111] font-medium">
          {latStr}, {lonStr}
        </span>
        <span className="text-[#CCCCCC]">|</span>
        <span>{crs}</span>
        <span className="text-[#CCCCCC]">|</span>
        <span className="text-emerald-700 font-semibold">{gsdMeters}m GSD</span>
      </div>
    </div>
  );
};
