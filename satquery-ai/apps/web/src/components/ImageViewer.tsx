import React, { useState } from 'react';
import { PreviewInfo, RasterMetadata, GroundingFeature } from '../types';
import { getPreviewUrl } from '../lib/api';
import { GroundingCanvas } from './GroundingCanvas';
import { ZoomIn, ZoomOut, RotateCcw, Image as ImageIcon, Eye, Layers } from 'lucide-react';

interface ImageViewerProps {
  preview: PreviewInfo;
  metadata?: RasterMetadata | null;
  groundingFeatures?: GroundingFeature[];
}

export const ImageViewer: React.FC<ImageViewerProps> = ({
  preview,
  metadata,
  groundingFeatures,
}) => {
  const [zoom, setZoom] = useState(1);
  const [showOverlay, setShowOverlay] = useState(true);
  const previewUrl = getPreviewUrl(preview.preview_url);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.5));
  const handleResetZoom = () => setZoom(1);

  if (!preview.available || !previewUrl) {
    return (
      <div className="bg-space-900 border border-space-700/80 rounded-xl p-8 flex flex-col items-center justify-center min-h-[360px] text-center">
        <div className="p-4 bg-space-800 rounded-full text-slate-500 mb-3">
          <ImageIcon className="w-8 h-8" />
        </div>
        <p className="text-sm font-medium text-slate-300">No Image Selected</p>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          Upload a GeoTIFF or satellite image above to inspect raster metadata and render preview.
        </p>
      </div>
    );
  }

  const hasGrounding = groundingFeatures && groundingFeatures.length > 0;

  return (
    <div className="bg-space-900 border border-space-700/80 rounded-xl overflow-hidden flex flex-col shadow-lg">
      {/* Viewer toolbar */}
      <div className="px-4 py-2.5 bg-space-950/80 border-b border-space-800 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
          <Eye className="w-3.5 h-3.5 text-satblue-400" />
          <span>Web Preview (2%-98% Percentile Dynamic Stretch)</span>
        </div>

        <div className="flex items-center space-x-2">
          {hasGrounding && (
            <button
              onClick={() => setShowOverlay(!showOverlay)}
              className={`px-2 py-1 rounded text-[11px] font-mono flex items-center space-x-1 border transition-colors ${
                showOverlay
                  ? 'bg-satblue-500/20 text-satblue-300 border-satblue-400/40'
                  : 'bg-space-800 text-slate-400 border-space-700'
              }`}
            >
              <Layers className="w-3 h-3" />
              <span>Grounding Overlay</span>
            </button>
          )}

          <div className="flex items-center space-x-1 border-l border-space-800 pl-2">
            <button
              onClick={handleZoomOut}
              className="p-1 rounded hover:bg-space-800 text-slate-400 hover:text-slate-200 transition-colors"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-[11px] font-mono text-slate-400 px-1.5">{Math.round(zoom * 100)}%</span>
            <button
              onClick={handleZoomIn}
              className="p-1 rounded hover:bg-space-800 text-slate-400 hover:text-slate-200 transition-colors"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={handleResetZoom}
              className="p-1 rounded hover:bg-space-800 text-slate-400 hover:text-slate-200 transition-colors ml-1"
              title="Reset Zoom"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Image viewport with Grounding Overlay */}
      <div className="relative overflow-auto p-4 flex items-center justify-center min-h-[380px] max-h-[520px] bg-space-950/40">
        <div
          style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
          className="relative inline-block transition-transform duration-150"
        >
          <img
            src={previewUrl}
            alt={metadata?.filename || 'Satellite Image Preview'}
            className="max-h-[440px] w-auto object-contain rounded-md shadow-2xl block"
          />
          {hasGrounding && showOverlay && <GroundingCanvas features={groundingFeatures} />}
        </div>
      </div>

      {metadata && (
        <div className="px-4 py-2 bg-space-950/80 border-t border-space-800 text-[11px] font-mono text-slate-400 flex justify-between">
          <span>Raster: {metadata.width} × {metadata.height} px</span>
          <span>Bands: {metadata.band_count} ({metadata.dtype})</span>
        </div>
      )}
    </div>
  );
};
