import React, { useState } from 'react';
import { ChangeAnalysisResult } from '../types';
import { getPreviewUrl } from '../lib/api';
import { Eye, Layers, SplitSquareVertical, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface ChangeViewerProps {
  beforePreviewUrl?: string | null;
  afterPreviewUrl?: string | null;
  changeResult: ChangeAnalysisResult;
}

export const ChangeViewer: React.FC<ChangeViewerProps> = ({
  beforePreviewUrl,
  afterPreviewUrl,
  changeResult,
}) => {
  const [sliderPos, setSliderPos] = useState(50);
  const [showMask, setShowMask] = useState(true);
  const [zoom, setZoom] = useState(1);

  const beforeUrl = getPreviewUrl(beforePreviewUrl);
  const afterUrl = getPreviewUrl(afterPreviewUrl);
  const maskUrl = getPreviewUrl(changeResult.mask_preview_url);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.5));
  const handleResetZoom = () => setZoom(1);

  return (
    <div className="bg-space-900 border border-space-700/80 rounded-xl overflow-hidden flex flex-col shadow-lg">
      {/* Toolbar */}
      <div className="px-4 py-2.5 bg-space-950/80 border-b border-space-800 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-300">
          <SplitSquareVertical className="w-3.5 h-3.5 text-rose-400" />
          <span>Bi-Temporal Change Viewer (Before vs After)</span>
        </div>

        <div className="flex items-center space-x-2">
          {maskUrl && (
            <button
              onClick={() => setShowMask(!showMask)}
              className={`px-2 py-1 rounded text-[11px] font-mono flex items-center space-x-1 border transition-colors ${
                showMask
                  ? 'bg-rose-500/20 text-rose-300 border-rose-400/40'
                  : 'bg-space-800 text-slate-400 border-space-700'
              }`}
            >
              <Layers className="w-3 h-3" />
              <span>Change Mask</span>
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

      {/* Slider Comparison Viewport */}
      <div className="relative overflow-hidden p-4 flex items-center justify-center min-h-[380px] max-h-[520px] bg-space-950/40 select-none">
        <div
          style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
          className="relative inline-block transition-transform duration-150 max-h-[440px] w-auto shadow-2xl rounded-md overflow-hidden"
        >
          {/* After image (Base layer) */}
          {afterUrl && (
            <img
              src={afterUrl}
              alt="After Image"
              className="max-h-[440px] w-auto object-contain block"
            />
          )}

          {/* Before image (Clipped top layer controlled by slider) */}
          {beforeUrl && (
            <div
              className="absolute inset-0 overflow-hidden"
              style={{ width: `${sliderPos}%` }}
            >
              <img
                src={beforeUrl}
                alt="Before Image"
                className="max-h-[440px] w-auto max-w-none object-contain block"
              />
            </div>
          )}

          {/* Change Mask Highlight Overlay */}
          {maskUrl && showMask && (
            <img
              src={maskUrl}
              alt="Change Mask Overlay"
              className="absolute inset-0 w-full h-full object-contain pointer-events-none"
            />
          )}

          {/* Split line indicator */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-satblue-400 cursor-ew-resize z-20 shadow-[0_0_8px_rgba(56,189,248,0.8)]"
            style={{ left: `${sliderPos}%` }}
          >
            <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-space-900 border-2 border-satblue-400 flex items-center justify-center text-[10px] text-satblue-300 font-bold">
              ↔
            </div>
          </div>
        </div>
      </div>

      {/* Slider Control Bar */}
      <div className="px-4 py-2.5 bg-space-950/80 border-t border-space-800 flex items-center justify-between gap-4 text-xs font-mono text-slate-400">
        <span className="text-slate-300 font-semibold">T1 (Before)</span>
        <input
          type="range"
          min="0"
          max="100"
          value={sliderPos}
          onChange={(e) => setSliderPos(Number(e.target.value))}
          className="flex-1 accent-satblue-500 cursor-pointer h-1.5 bg-space-800 rounded-lg"
        />
        <span className="text-slate-300 font-semibold">T2 (After)</span>
      </div>
    </div>
  );
};
