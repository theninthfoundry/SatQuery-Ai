import React from 'react';
import { RasterMetadata } from '../types';
import { CRSBadge } from './CRSBadge';
import { BandStatsTable } from './BandStatsTable';
import { Maximize2, Sparkles, MapPin, HardDrive, FileText, Info } from 'lucide-react';

interface MetadataPanelProps {
  metadata: RasterMetadata;
}

export const MetadataPanel: React.FC<MetadataPanelProps> = ({ metadata }) => {
  return (
    <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 space-y-6">
      <div className="flex items-center justify-between pb-3 border-b border-space-800">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <span>{metadata.filename}</span>
          </h2>
          <div className="flex items-center space-x-2 mt-1">
            <CRSBadge crs={metadata.crs} />
            <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-space-800 text-slate-400 border border-space-700">
              {metadata.format} ({metadata.driver || 'Raster'})
            </span>
          </div>
        </div>

        {/* Modality Tag */}
        <div className="text-right">
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-mono bg-space-800 border border-space-700 text-satblue-400">
            <Sparkles className="w-3.5 h-3.5" />
            <span className="uppercase font-bold">{metadata.modality.detected}</span>
            {metadata.modality.confidence > 0 && (
              <span className="text-[10px] text-slate-400 font-normal">
                ({(metadata.modality.confidence * 100).toFixed(0)}%)
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Grid of raster specs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-space-950/60 p-3 rounded-lg border border-space-800">
          <span className="text-[11px] text-slate-400 font-mono block mb-1">Dimensions</span>
          <span className="text-sm font-bold font-mono text-slate-200">
            {metadata.width.toLocaleString()} × {metadata.height.toLocaleString()} px
          </span>
        </div>

        <div className="bg-space-950/60 p-3 rounded-lg border border-space-800">
          <span className="text-[11px] text-slate-400 font-mono block mb-1">Band Count</span>
          <span className="text-sm font-bold font-mono text-slate-200">
            {metadata.band_count} {metadata.band_count === 1 ? 'Band' : 'Bands'}
          </span>
        </div>

        <div className="bg-space-950/60 p-3 rounded-lg border border-space-800">
          <span className="text-[11px] text-slate-400 font-mono block mb-1">Data Type</span>
          <span className="text-sm font-bold font-mono text-satblue-400">{metadata.dtype}</span>
        </div>

        <div className="bg-space-950/60 p-3 rounded-lg border border-space-800">
          <span className="text-[11px] text-slate-400 font-mono block mb-1">Spatial Resolution</span>
          <span className="text-sm font-bold font-mono text-slate-200">
            {metadata.resolution.x_res} × {metadata.resolution.y_res} {metadata.resolution.units}
          </span>
        </div>
      </div>

      {/* Geospatial Bounding Box */}
      {metadata.bounds && (
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
            <MapPin className="w-3.5 h-3.5 text-satblue-400" />
            <span>Bounding Box & Spatial Extent</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
            {/* Native Bounds */}
            <div className="bg-space-950/60 p-3 rounded-lg border border-space-800 space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                Native Coordinates ({metadata.crs.epsg ? `EPSG:${metadata.crs.epsg}` : 'Local'})
              </span>
              <div className="text-slate-300">Min X: {metadata.bounds.min_x}</div>
              <div className="text-slate-300">Min Y: {metadata.bounds.min_y}</div>
              <div className="text-slate-300">Max X: {metadata.bounds.max_x}</div>
              <div className="text-slate-300">Max Y: {metadata.bounds.max_y}</div>
            </div>

            {/* WGS84 Extent */}
            {metadata.bounds.wgs84 && (
              <div className="bg-space-950/60 p-3 rounded-lg border border-space-800 space-y-1">
                <span className="text-[10px] uppercase font-bold text-emerald-400 block mb-1">
                  WGS84 Geographic Extent (Lat / Lon)
                </span>
                <div className="text-slate-300">Min Lat: {metadata.bounds.wgs84.min_lat}°</div>
                <div className="text-slate-300">Min Lon: {metadata.bounds.wgs84.min_lon}°</div>
                <div className="text-slate-300">Max Lat: {metadata.bounds.wgs84.max_lat}°</div>
                <div className="text-slate-300">Max Lon: {metadata.bounds.wgs84.max_lon}°</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Band Statistics */}
      <BandStatsTable bands={metadata.bands} />
    </div>
  );
};
