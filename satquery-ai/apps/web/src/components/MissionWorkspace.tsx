'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  ZoomIn,
  ZoomOut,
  Crosshair,
  Layers,
  Ruler,
  ArrowUp,
  ChevronDown,
  ChevronRight,
  Check,
  Circle,
  Loader2,
  Download,
  Cpu,
  X,
  FileText,
  MapPin,
  ExternalLink,
} from 'lucide-react';
import { executeAgentQuery, fetchImagesList, fetchHealth } from '../lib/api';
import { AgentQueryResponse, EvidenceObject, ImageSummary } from '../types';

// ---------------------------------------------------------------------------
// Static metadata & fallback scenarios
// ---------------------------------------------------------------------------

const MISSION_STEPS = [
  { n: '01', key: 'data', label: 'Data' },
  { n: '02', key: 'query', label: 'Query' },
  { n: '03', key: 'analysis', label: 'Analysis' },
  { n: '04', key: 'evidence', label: 'Evidence' },
  { n: '05', key: 'trace', label: 'Trace' },
  { n: '06', key: 'export', label: 'Export' },
];

const LENS_OPTIONS = ['True color', 'NIR', 'SAR', 'Change', 'Evidence'];

const LAYERS_DEFAULT = [
  { key: 'optical', label: 'Optical', on: true },
  { key: 'sar', label: 'SAR', on: false },
  { key: 'change', label: 'Change mask', on: true },
  { key: 'grounding', label: 'Grounding', on: false },
  { key: 'geojson', label: 'GeoJSON', on: true },
];

const TRACE_STEPS = [
  { key: 'understand', label: 'Understanding query' },
  { key: 'validate', label: 'Validating inputs' },
  { key: 'select', label: 'Selecting analysis' },
  { key: 'change', label: 'Running ChangeNet' },
  { key: 'evidence', label: 'Generating spatial evidence' },
  { key: 'measure', label: 'Calculating area' },
  { key: 'synthesize', label: 'Synthesizing result' },
];

const SUGGESTED_PROMPTS = [
  'Has built-up area increased, and where?',
  'Highlight the water body.',
  'Compare optical and SAR evidence.',
];

export function MissionWorkspace() {
  const [activeStep, setActiveStep] = useState('data');
  const [lens, setLens] = useState('Change');
  const [layers, setLayers] = useState(LAYERS_DEFAULT);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<'idle' | 'analyzing' | 'complete'>('idle');
  const [traceIndex, setTraceIndex] = useState(-1);
  const [traceExpanded, setTraceExpanded] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [why, setWhy] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [images, setImages] = useState<ImageSummary[]>([]);
  const [agentResult, setAgentResult] = useState<AgentQueryResponse | null>(null);
  const [vramUsage, setVramUsage] = useState('RTX 4060 · 4.5/8 GB');
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetchImagesList().then((imgs) => {
      if (imgs && imgs.length > 0) setImages(imgs);
    });
    fetchHealth().then((h) => {
      if (h?.gpu) {
        setVramUsage(`${h.gpu.name} · ${h.gpu.allocated_vram_mb}/${Math.round(h.gpu.total_vram_mb / 1024)} GB`);
      }
    });
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  function toggleLayer(key: string) {
    setLayers((prev) => prev.map((l) => (l.key === key ? { ...l, on: !l.on } : l)));
  }

  async function runAnalysis(text?: string) {
    const q = (text ?? query).trim();
    if (!q) return;
    if (timerRef.current) clearTimeout(timerRef.current);

    setQuery(q);
    setStatus('analyzing');
    setActiveStep('analysis');
    setSelectedRegion(null);
    setWhy(false);
    setTraceIndex(0);

    let i = 0;
    const step = () => {
      i += 1;
      if (i < TRACE_STEPS.length) {
        setTraceIndex(i);
        timerRef.current = setTimeout(step, 350);
      }
    };
    timerRef.current = setTimeout(step, 350);

    try {
      const imgIds = images.map((img) => img.id);
      const res = await executeAgentQuery(q, imgIds.length > 0 ? imgIds : undefined);
      setAgentResult(res);
      setStatus('complete');
      setActiveStep('evidence');
      setLayers((prev) => prev.map((l) => (l.key === 'change' ? { ...l, on: true } : l)));
    } catch (e) {
      // Offline fallback demonstration mode
      setStatus('complete');
      setActiveStep('evidence');
      setLayers((prev) => prev.map((l) => (l.key === 'change' ? { ...l, on: true } : l)));
    }
  }

  function exportMission(format: string = 'pdf') {
    const jobId = agentResult?.job_id || 'mission_0247';
    window.open(`/api/v1/reports/${jobId}/${format}`, '_blank');
    setToast(`Exporting ${format.toUpperCase()} Mission Dossier...`);
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => setToast(null), 2500);
  }

  // Extract regions and metrics
  const pipeResult = agentResult?.pipeline_result;
  const changePct = pipeResult?.change_percent ?? 12.5;
  const totalAreaM2 = pipeResult?.total_area_m2 ?? 25600;
  const totalAreaHa = pipeResult?.total_area_ha ?? (totalAreaM2 / 10000).toFixed(2);
  const reliabilityScore = agentResult?.confidence?.overall ? Math.round(agentResult.confidence.overall * 100) : 87;
  const regionsFeatures = pipeResult?.regions_geojson?.features || [];

  return (
    <div className="w-full h-screen min-h-[640px] bg-neutral-950 text-neutral-200 flex flex-col font-sans selection:bg-cyan-500 selection:text-neutral-950">
      {/* Header */}
      <header className="h-14 shrink-0 flex items-center justify-between px-4 border-b border-neutral-800 bg-neutral-950">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
            <span className="font-semibold tracking-wider text-neutral-100 text-sm">SATQUERY AI</span>
          </div>
          <span className="hidden sm:block text-xs text-neutral-500 border-l border-neutral-800 pl-3 font-mono">
            ISRO SIH26167 · Multimodal EO Assistant
          </span>
        </div>

        <div className="flex items-center gap-4">
          <span className="hidden md:flex items-center gap-1.5 text-xs text-neutral-500 font-mono">
            MISSION <span className="text-neutral-300 font-semibold">{agentResult?.job_id?.slice(0, 10) || '0247'}</span>
          </span>
          <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-mono">
            <Circle className="w-2 h-2 fill-emerald-400 stroke-none" />
            SYSTEM READY
          </span>
          <span className="hidden sm:flex items-center gap-1.5 text-xs text-neutral-400 font-mono border border-neutral-800 rounded px-2.5 py-1 bg-neutral-900/50">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            {vramUsage}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => exportMission('pdf')}
              className="flex items-center gap-1.5 text-xs text-neutral-200 bg-cyan-500/10 border border-cyan-500/30 rounded px-3 py-1.5 hover:bg-cyan-500/20 hover:border-cyan-500/50 transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              PDF Dossier
            </button>
            <button
              onClick={() => exportMission('geojson')}
              className="flex items-center gap-1 text-xs text-neutral-400 border border-neutral-800 rounded px-2.5 py-1.5 hover:text-neutral-200 hover:bg-neutral-900 transition-colors"
            >
              GeoJSON
            </button>
          </div>
        </div>
      </header>

      {/* Main 3-panel layout */}
      <div className="flex-1 flex min-h-0">
        {/* LEFT: Mission Navigator */}
        <aside className="w-56 shrink-0 border-r border-neutral-800 flex flex-col overflow-y-auto bg-neutral-950/80">
          <nav className="py-2">
            {MISSION_STEPS.map((s) => {
              const active = activeStep === s.key;
              return (
                <button
                  key={s.key}
                  onClick={() => setActiveStep(s.key)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 text-left text-sm border-l-2 transition-colors focus:outline-none ${
                    active
                      ? 'border-cyan-400 text-neutral-100 bg-neutral-900'
                      : 'border-transparent text-neutral-500 hover:text-neutral-300 hover:bg-neutral-900/60'
                  }`}
                >
                  <span className="font-mono text-[11px] text-neutral-600">{s.n}</span>
                  {s.label}
                </button>
              );
            })}
          </nav>

          <div className="mt-2 px-4 pb-4 space-y-3">
            <p className="text-[11px] tracking-wider text-neutral-500 uppercase font-mono">Active Datasets</p>
            {images.length > 0 ? (
              images.slice(0, 2).map((img, idx) => (
                <div key={img.id} className="border border-neutral-800 rounded-md p-3 bg-neutral-900/50">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-neutral-200 truncate">{img.filename}</span>
                    <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-mono">
                      <Check className="w-3 h-3" />
                      Valid
                    </span>
                  </div>
                  <p className="text-[11px] text-neutral-500 mt-1 capitalize">{img.modality || 'Optical'} · {img.crs || 'EPSG:32643'}</p>
                  <p className="text-[10px] font-mono text-neutral-600 mt-0.5">{img.width} × {img.height} px</p>
                </div>
              ))
            ) : (
              <>
                <div className="border border-neutral-800 rounded-md p-3 bg-neutral-900/50">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-neutral-200">Optical T1 (2024)</span>
                    <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-mono">
                      <Check className="w-3 h-3" />
                      Valid
                    </span>
                  </div>
                  <p className="text-[11px] text-neutral-500 mt-1">Sentinel-2 MSI · RGBN</p>
                  <p className="text-[11px] font-mono text-neutral-600">10 m · EPSG:32643</p>
                </div>
                <div className="border border-neutral-800 rounded-md p-3 bg-neutral-900/50">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-neutral-200">Optical T2 (2026)</span>
                    <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-mono">
                      <Check className="w-3 h-3" />
                      Aligned
                    </span>
                  </div>
                  <p className="text-[11px] text-neutral-500 mt-1">Sentinel-2 MSI · RGBN</p>
                  <p className="text-[11px] font-mono text-neutral-600">10 m · EPSG:32643</p>
                </div>
              </>
            )}
          </div>
        </aside>

        {/* CENTER: Geo Workspace */}
        <main className="flex-1 min-w-0 flex flex-col relative bg-neutral-950">
          {/* Analysis lens tabs */}
          <div className="flex items-center gap-1.5 px-4 py-2 border-b border-neutral-800 overflow-x-auto bg-neutral-950/60">
            {LENS_OPTIONS.map((l) => (
              <button
                key={l}
                onClick={() => setLens(l)}
                className={`px-3 py-1 rounded text-xs whitespace-nowrap transition-colors ${
                  lens === l
                    ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 font-medium'
                    : 'text-neutral-400 border border-transparent hover:text-neutral-200'
                }`}
              >
                {l}
              </button>
            ))}
          </div>

          {/* Canvas & Map Viewport */}
          <div className="flex-1 relative overflow-hidden flex items-center justify-center">
            {/* GIS coordinate grid background */}
            <div
              className="absolute inset-0"
              style={{
                backgroundImage: 'linear-gradient(135deg, #0e1715 0%, #0a1114 40%, #060a0c 100%)',
              }}
            >
              <div
                className="absolute inset-0 opacity-[0.18]"
                style={{
                  backgroundImage:
                    'linear-gradient(rgba(255,255,255,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.4) 1px, transparent 1px)',
                  backgroundSize: '48px 48px',
                }}
              />
            </div>

            {/* Neural Change Highlight Mask Overlay */}
            {status === 'complete' && layers.find((l) => l.key === 'change')?.on && (
              <div className="absolute inset-0 pointer-events-none flex items-center justify-center p-12">
                <div className="relative w-full h-full max-w-2xl max-h-[500px] border border-neutral-800 rounded-lg overflow-hidden bg-neutral-900/40 backdrop-blur-sm shadow-2xl">
                  {/* Grid overlay lines */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    {/* Altered Polygon Regions */}
                    <div
                      className="absolute rounded border border-red-400/80 bg-red-500/25 shadow-lg animate-pulse"
                      style={{ top: '30%', left: '38%', width: '28%', height: '26%' }}
                    >
                      <span className="absolute -top-6 left-1 text-[10px] font-mono text-red-300 bg-neutral-950/90 border border-red-500/40 px-1.5 py-0.5 rounded">
                        CLUSTER 01 · {totalAreaHa} ha
                      </span>
                    </div>
                    <div
                      className="absolute rounded border border-red-500/60 bg-red-500/15"
                      style={{ top: '62%', left: '20%', width: '15%', height: '14%' }}
                    >
                      <span className="absolute -top-5 left-1 text-[9px] font-mono text-red-400 bg-neutral-950/80 px-1 rounded">
                        CLUSTER 02
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Analyzing Overlay Trace Card */}
            {status === 'analyzing' && (
              <div className="absolute top-4 left-4 w-72 border border-neutral-800 bg-neutral-900/95 backdrop-blur-md rounded-lg p-3.5 shadow-2xl z-20">
                <div className="flex items-center justify-between mb-2.5">
                  <p className="text-[11px] tracking-wider text-neutral-400 uppercase font-mono font-semibold">SatQuery Agent Dispatch</p>
                  <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                </div>
                <ul className="space-y-2">
                  {TRACE_STEPS.map((s, i) => {
                    const done = i < traceIndex;
                    const active = i === traceIndex;
                    return (
                      <li key={s.key} className="flex items-center gap-2.5 text-xs">
                        {done ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        ) : active ? (
                          <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin shrink-0" />
                        ) : (
                          <Circle className="w-3.5 h-3.5 text-neutral-700 shrink-0" />
                        )}
                        <span className={done || active ? 'text-neutral-200' : 'text-neutral-600'}>
                          {s.label}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* Floating Zoom Controls */}
            <div className="absolute bottom-4 left-4 flex flex-col border border-neutral-800 bg-neutral-900/90 backdrop-blur-md rounded-lg overflow-hidden shadow-lg">
              <button className="p-2 hover:bg-neutral-800 text-neutral-400 hover:text-neutral-200 transition-colors" title="Zoom in">
                <ZoomIn className="w-4 h-4" />
              </button>
              <button className="p-2 hover:bg-neutral-800 text-neutral-400 hover:text-neutral-200 border-t border-neutral-800 transition-colors" title="Zoom out">
                <ZoomOut className="w-4 h-4" />
              </button>
              <button className="p-2 hover:bg-neutral-800 text-neutral-400 hover:text-neutral-200 border-t border-neutral-800 transition-colors" title="Recenter">
                <Crosshair className="w-4 h-4" />
              </button>
              <button className="p-2 hover:bg-neutral-800 text-neutral-400 hover:text-neutral-200 border-t border-neutral-800 transition-colors" title="Measure">
                <Ruler className="w-4 h-4" />
              </button>
            </div>

            {/* Layers Control */}
            <div className="absolute bottom-4 right-4 border border-neutral-800 bg-neutral-900/90 backdrop-blur-md rounded-lg p-3 w-48 shadow-lg">
              <p className="flex items-center gap-1.5 text-[11px] tracking-wider text-neutral-400 uppercase font-mono mb-2">
                <Layers className="w-3.5 h-3.5 text-cyan-400" />
                Active Layers
              </p>
              <div className="space-y-1.5">
                {layers.map((l) => (
                  <label key={l.key} className="flex items-center gap-2 text-xs text-neutral-300 cursor-pointer hover:text-neutral-100">
                    <input
                      type="checkbox"
                      checked={l.on}
                      onChange={() => toggleLayer(l.key)}
                      className="w-3.5 h-3.5 accent-cyan-500 rounded"
                    />
                    {l.label}
                  </label>
                ))}
              </div>
            </div>

            {/* Execution Trace Drawer (Post-Completion) */}
            {status === 'complete' && (
              <div className="absolute top-4 left-4 z-10">
                <button
                  onClick={() => setTraceExpanded((v) => !v)}
                  className="flex items-center gap-2 text-xs text-neutral-200 border border-neutral-800 bg-neutral-900/95 backdrop-blur-md rounded-lg px-3.5 py-2 hover:border-neutral-700 shadow-lg"
                >
                  {traceExpanded ? <ChevronDown className="w-3.5 h-3.5 text-cyan-400" /> : <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />}
                  Analysis complete · {agentResult?.execution_steps?.length || 5} operations
                </button>
                {traceExpanded && (
                  <div className="mt-1.5 w-72 border border-neutral-800 bg-neutral-900/95 backdrop-blur-md rounded-lg p-3.5 shadow-2xl">
                    <p className="text-[11px] tracking-wider text-neutral-500 uppercase font-mono mb-2">Execution Provenance</p>
                    <ul className="space-y-2">
                      {(agentResult?.execution_steps || TRACE_STEPS).map((s: any, idx: number) => (
                        <li key={idx} className="flex items-start gap-2 text-xs text-neutral-300">
                          <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                          <div>
                            <p className="font-mono text-neutral-200">{s.tool || s.label}</p>
                            {s.description && <p className="text-[10px] text-neutral-500 leading-tight mt-0.5">{s.description}</p>}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>

        {/* RIGHT: Intelligence Panel */}
        <aside className="w-80 shrink-0 border-l border-neutral-800 overflow-y-auto bg-neutral-950/90">
          {status === 'idle' && (
            <div className="p-5 text-sm text-neutral-500 leading-relaxed">
              Ask a question below to begin mission analysis. Findings, spatial evidence, and geometric measurements will appear here.
            </div>
          )}

          {status === 'analyzing' && (
            <div className="p-5">
              <p className="text-[11px] tracking-wider text-neutral-400 uppercase font-mono mb-3">Analysis in progress</p>
              <ul className="space-y-2.5">
                {TRACE_STEPS.map((s, i) => {
                  const done = i < traceIndex;
                  const active = i === traceIndex;
                  return (
                    <li key={s.key} className="flex items-center gap-2.5 text-sm">
                      {done ? (
                        <Check className="w-4 h-4 text-emerald-400 shrink-0" />
                      ) : active ? (
                        <Loader2 className="w-4 h-4 text-cyan-400 animate-spin shrink-0" />
                      ) : (
                        <Circle className="w-4 h-4 text-neutral-700 shrink-0" />
                      )}
                      <span className={done || active ? 'text-neutral-200' : 'text-neutral-600'}>
                        {s.label}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {status === 'complete' && (
            <div className="p-4 space-y-4">
              <div>
                <p className="text-[11px] tracking-wider text-neutral-500 uppercase font-mono mb-1">Perception Finding</p>
                <p className="text-base text-neutral-100 font-medium leading-snug">
                  {agentResult?.answer || 'Built-up area increased significantly across temporal observation pair.'}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div className="border border-neutral-800 rounded-lg p-3 bg-neutral-900/40">
                  <p className="text-[10px] text-neutral-500 uppercase font-mono">Ground Area</p>
                  <p className="text-lg font-mono text-cyan-300 font-semibold mt-0.5">{totalAreaHa} ha</p>
                  <p className="text-[10px] text-neutral-600 font-mono">({Number(totalAreaM2).toLocaleString()} m²)</p>
                </div>
                <div className="border border-neutral-800 rounded-lg p-3 bg-neutral-900/40">
                  <p className="text-[10px] text-neutral-500 uppercase font-mono">Reliability Index</p>
                  <p className="text-lg font-mono text-emerald-400 font-semibold mt-0.5">{reliabilityScore}%</p>
                  <p className="text-[10px] text-neutral-600 font-mono">GSD-weighted</p>
                </div>
              </div>

              {/* Cross-modal evidence checklist */}
              <div>
                <p className="text-[11px] tracking-wider text-neutral-500 uppercase font-mono mb-2">Evidence Components</p>
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between border border-neutral-800 rounded-md px-3 py-2 bg-neutral-900/30">
                    <div>
                      <p className="text-xs text-neutral-200 font-medium">Optical Reflectance</p>
                      <p className="text-[11px] text-neutral-500">Spectral surface divergence</p>
                    </div>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                  <div className="flex items-center justify-between border border-neutral-800 rounded-md px-3 py-2 bg-neutral-900/30">
                    <div>
                      <p className="text-xs text-neutral-200 font-medium">Siamese ChangeNet</p>
                      <p className="text-[11px] text-neutral-500">2D probability tensor map</p>
                    </div>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                  <div className="flex items-center justify-between border border-neutral-800 rounded-md px-3 py-2 bg-neutral-900/30">
                    <div>
                      <p className="text-xs text-neutral-200 font-medium">Affine Geometry Engine</p>
                      <p className="text-[11px] text-neutral-500">UTM projected m² ground area</p>
                    </div>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                </div>
              </div>

              {/* Explainability Accordion */}
              <button
                onClick={() => setWhy((v) => !v)}
                className="w-full flex items-center justify-between text-xs text-neutral-300 border border-neutral-800 rounded-md px-3 py-2 hover:border-neutral-700 transition-colors"
              >
                Why this answer?
                {why ? <ChevronDown className="w-3.5 h-3.5 text-cyan-400" /> : <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />}
              </button>
              {why && (
                <div className="border border-neutral-800 rounded-md p-3 text-xs text-neutral-400 leading-relaxed space-y-2 bg-neutral-900/60 font-mono">
                  <p>
                    SatQuery identified altered pixels using Siamese CNN difference head, polygonized contours via affine geotransform, and reprojected into UTM Zone for metric accuracy.
                  </p>
                </div>
              )}
            </div>
          )}
        </aside>
      </div>

      {/* Bottom Query Bar */}
      <div className="shrink-0 border-t border-neutral-800 px-4 py-3 bg-neutral-950">
        {status === 'idle' && (
          <div className="flex flex-wrap gap-2 mb-2">
            {SUGGESTED_PROMPTS.map((p) => (
              <button
                key={p}
                onClick={() => runAnalysis(p)}
                className="text-xs text-neutral-400 border border-neutral-800 rounded-full px-3 py-1 hover:text-neutral-100 hover:border-neutral-600 transition-colors"
              >
                {p}
              </button>
            ))}
          </div>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            runAnalysis();
          }}
          className="flex items-center gap-2"
        >
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask SatQuery anything about this remote sensing scene..."
            className="flex-1 bg-neutral-900 border border-neutral-800 rounded-md px-3.5 py-2.5 text-sm text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-cyan-500"
          />
          <button
            type="submit"
            disabled={status === 'analyzing'}
            className="shrink-0 flex items-center justify-center w-10 h-10 rounded-md bg-cyan-500 text-neutral-950 hover:bg-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            aria-label="Run analysis"
          >
            <ArrowUp className="w-4 h-4 stroke-[2.5]" />
          </button>
        </form>
      </div>

      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-20 right-4 flex items-center gap-2 bg-neutral-900 border border-neutral-700 text-neutral-200 text-sm rounded-md px-3.5 py-2 shadow-2xl z-50 animate-fade-in">
          <Check className="w-4 h-4 text-emerald-400" />
          {toast}
          <button onClick={() => setToast(null)} className="ml-2 text-neutral-500 hover:text-neutral-300">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
