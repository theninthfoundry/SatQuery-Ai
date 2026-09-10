'use client';

import React, { useState, useRef } from 'react';
import {
  X,
  Upload,
  FileCode,
  ShieldCheck,
  AlertTriangle,
  Check,
  Layers,
  MapPin,
  Sparkles,
  Maximize2,
  Copy,
} from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { parseAndValidateAOI } from '../../lib/aoiParser';
import { CustomAOI } from '../../types/aoi';

interface CustomAOIImporterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAOILoaded?: (aoi: CustomAOI) => void;
}

const SAMPLE_PRESETS: { name: string; tag: string; description: string; geojson: string }[] = [
  {
    name: 'Hyderabad HITEC Industrial Corridor',
    tag: 'HYDERABAD 25 km²',
    description: 'Bespoke industrial expansion zone with rapid built-up growth (17.44°N, 78.38°E)',
    geojson: JSON.stringify(
      {
        type: 'Feature',
        properties: { name: 'Hyderabad HITEC Industrial Corridor' },
        geometry: {
          type: 'Polygon',
          coordinates: [
            [
              [78.365, 17.435],
              [78.405, 17.435],
              [78.415, 17.465],
              [78.375, 17.475],
              [78.355, 17.455],
              [78.365, 17.435],
            ],
          ],
        },
      },
      null,
      2
    ),
  },
  {
    name: 'Bangalore Peri-Urban Tech Hub',
    tag: 'BANGALORE 12.64 ha',
    description: 'Outer Ring Road commercial development polygon (12.97°N, 77.59°E)',
    geojson: JSON.stringify(
      {
        type: 'Feature',
        properties: { name: 'Bangalore Peri-Urban Tech Hub' },
        geometry: {
          type: 'Polygon',
          coordinates: [
            [
              [77.585, 12.965],
              [77.615, 12.965],
              [77.625, 12.985],
              [77.595, 12.995],
              [77.575, 12.980],
              [77.585, 12.965],
            ],
          ],
        },
      },
      null,
      2
    ),
  },
  {
    name: 'Assam Wetland & Brahmaputra Basin',
    tag: 'ASSAM 18.45 ha',
    description: 'High-NDWI seasonal flood drainage basin (26.20°N, 92.93°E)',
    geojson: JSON.stringify(
      {
        type: 'Feature',
        properties: { name: 'Assam Wetland & Brahmaputra Basin' },
        geometry: {
          type: 'Polygon',
          coordinates: [
            [
              [92.920, 26.190],
              [92.955, 26.195],
              [92.965, 26.220],
              [92.930, 26.225],
              [92.915, 26.205],
              [92.920, 26.190],
            ],
          ],
        },
      },
      null,
      2
    ),
  },
];

export const CustomAOIImporterModal: React.FC<CustomAOIImporterModalProps> = ({
  isOpen,
  onClose,
  onAOILoaded,
}) => {
  const ws = useWorkspace();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [activeTab, setActiveTab] = useState<'paste' | 'upload' | 'presets'>('presets');
  const [inputText, setInputText] = useState<string>(SAMPLE_PRESETS[0].geojson);
  const [aoiName, setAoiName] = useState<string>('Custom Survey Area');
  const [clipImagery, setClipImagery] = useState<boolean>(true);
  const [validationResult, setValidationResult] = useState<{
    success: boolean;
    aoi?: CustomAOI;
    error?: string;
    warnings?: string[];
  } | null>(() => parseAndValidateAOI(SAMPLE_PRESETS[0].geojson, SAMPLE_PRESETS[0].name));

  if (!isOpen) return null;

  const handleValidate = (text: string, name: string) => {
    const result = parseAndValidateAOI(text, name);
    setValidationResult(result);
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setInputText(val);
    handleValidate(val, aoiName);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setAoiName(file.name.replace(/\.[^/.]+$/, ''));
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setInputText(content);
      handleValidate(content, file.name.replace(/\.[^/.]+$/, ''));
      setActiveTab('paste');
    };
    reader.readAsText(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    setAoiName(file.name.replace(/\.[^/.]+$/, ''));
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setInputText(content);
      handleValidate(content, file.name.replace(/\.[^/.]+$/, ''));
      setActiveTab('paste');
    };
    reader.readAsText(file);
  };

  const handleSelectPreset = (preset: typeof SAMPLE_PRESETS[0]) => {
    setInputText(preset.geojson);
    setAoiName(preset.name);
    handleValidate(preset.geojson, preset.name);
  };

  const handleApplyAOI = () => {
    if (!validationResult || !validationResult.success || !validationResult.aoi) return;

    const aoi = {
      ...validationResult.aoi,
      isMaskingEnabled: clipImagery,
    };

    // Fly workspace to centroid & set mission coordinates
    ws.updateMissionLocation({
      name: aoi.name,
      lat: aoi.bounds.centerLat,
      lon: aoi.bounds.centerLon,
      utmZone: `EPSG:${Math.floor((aoi.bounds.centerLon + 180) / 6) + 32601}`,
      areaAoi: `${aoi.areaHa} ha`,
    });

    // Notify workspace
    if (onAOILoaded) {
      onAOILoaded(aoi);
    }

    // Auto-prompt query bar
    ws.setQueryText(
      `Analyze land cover and bi-temporal surface changes inside imported AOI "${aoi.name}" (${aoi.areaHa} ha)`
    );

    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#121212] border border-neutral-800 rounded-lg w-full max-w-2xl shadow-2xl flex flex-col overflow-hidden max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-800 bg-[#161616]">
          <div className="flex items-center gap-2">
            <div className="p-1 rounded bg-blue-500/20 text-blue-400">
              <Upload className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-mono font-bold text-white tracking-wide">
                CUSTOM AOI IMPORTER
              </h2>
              <p className="text-[10px] font-mono text-neutral-400">
                GeoJSON · KML · Shapefile · Geodesic Reprojection Engine
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-neutral-800 text-neutral-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-neutral-800 bg-[#141414] px-4 text-xs font-mono">
          <button
            onClick={() => setActiveTab('presets')}
            className={`py-2 px-3 border-b-2 font-medium transition-colors ${
              activeTab === 'presets'
                ? 'border-blue-500 text-white'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            CANONICAL PRESETS
          </button>
          <button
            onClick={() => setActiveTab('paste')}
            className={`py-2 px-3 border-b-2 font-medium transition-colors ${
              activeTab === 'paste'
                ? 'border-blue-500 text-white'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            PASTE GEOJSON / KML
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`py-2 px-3 border-b-2 font-medium transition-colors ${
              activeTab === 'upload'
                ? 'border-blue-500 text-white'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            DRAG & DROP FILE
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4 overflow-y-auto space-y-4 text-xs font-mono">
          {/* Presets Tab */}
          {activeTab === 'presets' && (
            <div className="space-y-2">
              <span className="text-[10px] text-neutral-500 uppercase tracking-widest block">
                SELECT CANONICAL TEST AOI REGION:
              </span>
              <div className="grid grid-cols-1 gap-2">
                {SAMPLE_PRESETS.map((preset) => (
                  <button
                    key={preset.name}
                    onClick={() => handleSelectPreset(preset)}
                    className={`text-left p-3 rounded-md border transition-all ${
                      aoiName === preset.name
                        ? 'border-blue-500/80 bg-blue-950/20'
                        : 'border-neutral-800 bg-[#181818] hover:border-neutral-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-white text-xs">{preset.name}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-300">
                        {preset.tag}
                      </span>
                    </div>
                    <p className="text-[11px] text-neutral-400">{preset.description}</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Paste Tab */}
          {activeTab === 'paste' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-[10px] text-neutral-400 uppercase tracking-wider">
                  PASTE RAW GEOJSON OR KML STRING:
                </label>
                <button
                  onClick={() => {
                    navigator.clipboard.readText().then((txt) => {
                      setInputText(txt);
                      handleValidate(txt, aoiName);
                    });
                  }}
                  className="text-[10px] text-blue-400 hover:text-blue-300 flex items-center gap-1"
                >
                  <Copy className="w-3 h-3" />
                  <span>Paste from clipboard</span>
                </button>
              </div>
              <textarea
                value={inputText}
                onChange={handleTextChange}
                rows={7}
                placeholder='{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [...]}}'
                className="w-full bg-[#0E0E0E] border border-neutral-800 rounded p-2 text-[11px] font-mono text-neutral-200 focus:border-blue-500 focus:outline-none"
              />
            </div>
          )}

          {/* Upload Tab */}
          {activeTab === 'upload' && (
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-neutral-800 hover:border-blue-500/80 rounded-lg p-8 text-center cursor-pointer bg-[#141414] transition-colors"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".geojson,.json,.kml,.zip"
                onChange={handleFileUpload}
                className="hidden"
              />
              <FileCode className="w-8 h-8 text-neutral-500 mx-auto mb-2" />
              <p className="text-sm font-medium text-white mb-1">
                Drop your GeoJSON, KML, or Shapefile here
              </p>
              <p className="text-[11px] text-neutral-500">
                Supports Polygon, MultiPolygon, EPSG:4326, EPSG:3857, and UTM Zone projections
              </p>
            </div>
          )}

          {/* AOI Details & Settings */}
          <div className="grid grid-cols-2 gap-3 pt-1">
            <div>
              <label className="text-[10px] text-neutral-400 uppercase tracking-wider block mb-1">
                AOI IDENTIFIER NAME:
              </label>
              <input
                type="text"
                value={aoiName}
                onChange={(e) => {
                  setAoiName(e.target.value);
                  handleValidate(inputText, e.target.value);
                }}
                className="w-full bg-[#0E0E0E] border border-neutral-800 rounded px-2.5 py-1.5 text-xs text-white focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div className="flex flex-col justify-end">
              <label className="flex items-center gap-2 cursor-pointer select-none text-xs text-neutral-300">
                <input
                  type="checkbox"
                  checked={clipImagery}
                  onChange={(e) => setClipImagery(e.target.checked)}
                  className="rounded border-neutral-700 text-blue-600 focus:ring-0 bg-[#161616]"
                />
                <span>Clip and mask satellite imagery to AOI bounds</span>
              </label>
            </div>
          </div>

          {/* Validation Status & Geodesic Calculation Output */}
          {validationResult && (
            <div
              className={`p-3 rounded-md border text-xs ${
                validationResult.success
                  ? 'border-emerald-500/40 bg-emerald-950/20 text-emerald-300'
                  : 'border-rose-500/40 bg-rose-950/20 text-rose-300'
              }`}
            >
              <div className="flex items-center gap-1.5 font-bold mb-1">
                {validationResult.success ? (
                  <>
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span>GEOMETRY & CRS VERIFIED (VALID WGS84)</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-4 h-4 text-rose-400" />
                    <span>VALIDATION ERROR</span>
                  </>
                )}
              </div>

              {validationResult.error && (
                <p className="text-[11px] text-rose-300 mt-1">{validationResult.error}</p>
              )}

              {validationResult.warnings && validationResult.warnings.length > 0 && (
                <div className="text-[11px] text-amber-300 mt-1 space-y-0.5">
                  {validationResult.warnings.map((w, idx) => (
                    <div key={idx} className="flex items-center gap-1">
                      <span>⚠</span>
                      <span>{w}</span>
                    </div>
                  ))}
                </div>
              )}

              {validationResult.success && validationResult.aoi && (
                <div className="grid grid-cols-4 gap-2 text-center mt-2 pt-2 border-t border-emerald-500/20 text-[11px]">
                  <div className="bg-black/40 p-1.5 rounded">
                    <span className="text-neutral-400 block text-[9px]">GEODESIC AREA</span>
                    <strong className="text-emerald-400">{validationResult.aoi.areaHa} ha</strong>
                  </div>
                  <div className="bg-black/40 p-1.5 rounded">
                    <span className="text-neutral-400 block text-[9px]">PERIMETER</span>
                    <strong className="text-white">
                      {(validationResult.aoi.perimeterM / 1000).toFixed(2)} km
                    </strong>
                  </div>
                  <div className="bg-black/40 p-1.5 rounded">
                    <span className="text-neutral-400 block text-[9px]">VERTICES</span>
                    <strong className="text-white">{validationResult.aoi.vertexCount} pts</strong>
                  </div>
                  <div className="bg-black/40 p-1.5 rounded">
                    <span className="text-neutral-400 block text-[9px]">CRS</span>
                    <strong className="text-white truncate block">
                      {validationResult.aoi.crs.split(' ')[0]}
                    </strong>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-neutral-800 bg-[#161616]">
          <div className="text-[10px] font-mono text-neutral-500">
            Pipeline: File → Security → Reprojection → Validation → Map Overlay
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded text-xs font-mono text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleApplyAOI}
              disabled={!validationResult || !validationResult.success}
              className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-mono text-xs font-bold rounded flex items-center gap-1.5 transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>LOAD & FIT AOI TO WORKSPACE</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
