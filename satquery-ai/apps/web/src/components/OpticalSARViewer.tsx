import React, { useState } from 'react';
import { OpticalSARAnalysisResult } from '../types';
import { getPreviewUrl } from '../lib/api';
import { Radio, Sun, SplitSquareVertical, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface OpticalSARViewerProps {
  opticalPreviewUrl?: string | null;
  sarPreviewUrl?: string | null;
  fusionResult: OpticalSARAnalysisResult;
}

export const OpticalSARViewer: React.FC<OpticalSARViewerProps> = ({
  opticalPreviewUrl,
  sarPreviewUrl,
  fusionResult,
}) => {
  const [sliderPos, setSliderPos] = useState(50);
  const [zoom, setZoom] = useState(1);

  const optUrl = getPreviewUrl(opticalPreviewUrl);
  const sarUrl = getPreviewUrl(sarPreviewUrl);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.5));
  const handleResetZoom = () => setZoom(1);

  return (
    <div className="bg-space-900 border border-space-700/80 rounded-xl overflow-hidden flex flex-col shadow-lg">
      {/* Toolbar */}
      <div className="px-4 py-2.5 bg-space-950/80 border-b border-space-800 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-300">
          <SplitSquareVertical className="w-3.5 h-3.5 text-emerald-400" />
          <span>Multimodal Viewer (Optical RGB vs SAR Backscatter)</span>
        </div>

        <div className="flex items-center space-x-1">
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

      {/* Slider Viewport */}
      <div className="relative overflow-hidden p-4 flex items-center justify-center min-h-[380px] max-h-[520px] bg-space-950/40 select-none">
        <div
          style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
          className="relative inline-block transition-transform duration-150 max-h-[440px] w-auto shadow-2xl rounded-md overflow-hidden"
        >
          {/* SAR Image (Base Layer) */}
          {sarUrl && (
            <img
              src={sarUrl}
              alt="SAR Backscatter"
              className="max-h-[440px] w-auto object-contain block"
            />
          )}

          {/* Optical Image (Clipped top layer controlled by slider) */}
          {optUrl && (
            <div
              className="absolute inset-0 overflow-hidden"
              style={{ width: `${sliderPos}%` }}
            >
              <img
                src={optUrl}
                alt="Optical RGB"
                className="max-h-[440px] w-auto max-w-none object-contain block"
              />
            </div>
          )}

          {/* Split line indicator */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-emerald-400 cursor-ew-resize z-20 shadow-[0_0_8px_rgba(52,211,153,0.8)]"
            style={{ left: `${sliderPos}%` }}
          >
            <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-space-900 border-2 border-emerald-400 flex items-center justify-center text-[10px] text-emerald-300 font-bold">
              ↔
            </div>
          </div>
        </div>
      </div>

      {/* Slider Control Bar */}
      <div className="px-4 py-2.5 bg-space-950/80 border-t border-space-800 flex items-center justify-between gap-4 text-xs font-mono text-slate-400">
        <span className="text-amber-400 font-semibold flex items-center space-x-1">
          <Sun className="w-3.5 h-3.5" />
          <span>Optical RGB</span>
        </span>
        <input
          type="range"
          min="0"
          max="100"
          value={sliderPos}
          onChange={(e) => setSliderPos(Number(e.target.value))}
          className="flex-1 accent-emerald-500 cursor-pointer h-1.5 bg-space-800 rounded-lg"
        />
        <span className="text-satblue-400 font-semibold flex items-center space-x-1">
          <Radio className="w-3.5 h-3.5" />
          <span>SAR Radar (σ⁰)</span>
        </span>
      </div>
    </div>
  );
};
