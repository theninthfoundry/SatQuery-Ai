import React, { useState, useRef } from 'react';
import { UploadCloud, FileType, Loader2, AlertCircle } from 'lucide-react';
import { inspectImageFile } from '../lib/api';
import { ImageInspectionResponse } from '../types';

interface UploadZoneProps {
  onInspectionComplete: (data: ImageInspectionResponse) => void;
  isLoading?: boolean;
  setIsLoading?: (loading: boolean) => void;
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  onInspectionComplete,
  isLoading: externalLoading,
  setIsLoading: externalSetIsLoading,
}) => {
  const [internalLoading, setInternalLoading] = useState(false);
  const loading = externalLoading ?? internalLoading;
  const setLoading = (val: boolean) => {
    setInternalLoading(val);
    if (externalSetIsLoading) externalSetIsLoading(val);
  };
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const processFile = async (file: File) => {
    setError(null);
    setLoading(true);
    try {
      const result = await inspectImageFile(file);
      onInspectionComplete(result);
    } catch (err: any) {
      setError(err.message || 'Failed to inspect image');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-3">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${
          dragActive
            ? 'border-satblue-400 bg-satblue-500/10'
            : 'border-space-700 hover:border-space-600 bg-space-900/60 hover:bg-space-900'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".tif,.tiff,.geotif,.geotiff,.png,.jpg,.jpeg"
          onChange={handleChange}
          className="hidden"
          disabled={loading}
        />

        {loading ? (
          <div className="flex flex-col items-center space-y-3 py-3">
            <Loader2 className="w-8 h-8 text-satblue-400 animate-spin" />
            <div className="text-center">
              <p className="text-sm font-medium text-slate-200">Inspecting Raster & Extracting Metadata...</p>
              <p className="text-xs text-slate-400 font-mono mt-0.5">Reading header, CRS, bands, and rendering preview</p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center text-center space-y-3">
            <div className="p-3 bg-satblue-500/10 border border-satblue-500/20 rounded-full text-satblue-400">
              <UploadCloud className="w-7 h-7" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-200">
                Click to upload or drag & drop satellite imagery
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Supports GeoTIFF (<span className="font-mono text-slate-300">.tif</span>, <span className="font-mono text-slate-300">.tiff</span>) optical/multispectral/SAR or standard imagery
              </p>
            </div>
            <div className="flex items-center space-x-2 pt-1">
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-space-800 text-slate-400 border border-space-700">
                Single/Multi-band
              </span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-space-800 text-slate-400 border border-space-700">
                Projected & Geographic CRS
              </span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-space-800 text-slate-400 border border-space-700">
                Max 512 MB
              </span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-start space-x-2 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-lg p-3">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block">Upload Failed</span>
            <span>{error}</span>
          </div>
        </div>
      )}
    </div>
  );
};
