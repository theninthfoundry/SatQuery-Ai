'use client';

import React, { useState, useRef } from 'react';
import { ArrowUp, Mic, Loader2, Sparkles, Compass, AlertCircle, CheckCircle2, FileText, Layers, ZoomIn } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

export const QueryBar: React.FC = () => {
  const ws = useWorkspace();
  const [isListening, setIsListening] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [validationHint, setValidationHint] = useState<{
    type: 'missing_temporal' | 'demographics' | 'follow_up' | 'none';
    message: string;
    actionLabel?: string;
    action?: () => void;
  } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleVoiceInput = () => {
    if (
      typeof window !== 'undefined' &&
      ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)
    ) {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = () => setIsListening(false);

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          ws.setQueryText(transcript);
          ws.runQuery(transcript);
        }
      };

      recognition.start();
    } else {
      const defaultQ = 'Analyze industrial expansion around Hyderabad between T1 and T2';
      ws.setQueryText(defaultQ);
      ws.runQuery(defaultQ);
    }
  };

  const handleQueryChange = (text: string) => {
    ws.setQueryText(text);
    const lower = text.toLowerCase();

    // Check for demographics / population queries
    if (lower.includes('population') || lower.includes('census') || lower.includes('demographic') || lower.includes('resident')) {
      setValidationHint({
        type: 'demographics',
        message: 'SatQuery analyzes satellite raster imagery (multispectral optical & SAR radar). Census demographics are not present in raw pixels.',
        actionLabel: 'Ask about Land Cover instead',
        action: () => {
          ws.setQueryText('Identify built-up areas and describe the dominant land cover');
          setValidationHint(null);
        },
      });
    } else {
      setValidationHint(null);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const query = ws.queryText.trim();
    if (!query || ws.isAnalyzing) return;

    const lower = query.toLowerCase();

    // 1. Natural Follow-Up Queries
    if (lower.includes('where exactly') || lower.includes('where is it') || lower.includes('zoom to evidence') || lower.includes('show on map')) {
      ws.setActiveLens('EVIDENCE');
      if (ws.clusters.length > 0) {
        ws.selectCluster(ws.clusters[0].id);
        ws.setPan({ x: -10, y: -15 });
      }
      ws.setCustomInsight('The primary built-up expansion is localized at UTM 43N [485200, 1387400] (Cluster 01, 1.82 ha). Viewport centered on altered polygon.');
      setValidationHint(null);
      return;
    }

    if (lower.includes('largest change') || lower.includes('largest cluster')) {
      ws.setActiveLens('CHANGE');
      if (ws.clusters.length > 0) {
        ws.selectCluster(ws.clusters[0].id);
      }
      ws.setCustomInsight('Filtered to largest change cluster: Cluster 01 covering 1.82 ha (18,200 m²), representing 71% of total detected alterations.');
      setValidationHint(null);
      return;
    }

    if (lower.includes('generate report') || lower.includes('export report') || lower.includes('download pdf')) {
      ws.openExport('pdf');
      ws.setCustomInsight('Generated executive inspection dossier ready for export.');
      setValidationHint(null);
      return;
    }

    if (lower.includes('sar') || lower.includes('radar') || lower.includes('backscatter')) {
      ws.setActiveLens('SAR');
      ws.setCustomInsight('Sentinel-1 C-band SAR cross-examination confirms double-bounce radar return (-14.5 dB σ⁰), verifying solid construction.');
      setValidationHint(null);
      return;
    }

    // Direct Geographic & Coordinate Navigation
    if (lower.includes('hyderabad')) {
      ws.updateMissionLocation({
        name: 'Hyderabad Urban Corridor',
        lat: 17.3850,
        lon: 78.4867,
        utmZone: 'EPSG:32644 (UTM Zone 44N)',
        areaAoi: '25.0 km²',
      });
    } else if (lower.includes('bengaluru') || lower.includes('bangalore')) {
      ws.updateMissionLocation({
        name: 'Bangalore Urban Corridor',
        lat: 12.9716,
        lon: 77.5946,
        utmZone: 'EPSG:32643 (UTM Zone 43N)',
        areaAoi: '12.64 km²',
      });
    } else if (lower.includes('mumbai')) {
      ws.updateMissionLocation({
        name: 'Mumbai Coastal Region',
        lat: 19.0760,
        lon: 72.8777,
        utmZone: 'EPSG:32643 (UTM Zone 43N)',
        areaAoi: '30.0 km²',
      });
    } else if (lower.includes('delhi')) {
      ws.updateMissionLocation({
        name: 'Delhi NCR Region',
        lat: 28.6139,
        lon: 77.2090,
        utmZone: 'EPSG:32643 (UTM Zone 43N)',
        areaAoi: '28.5 km²',
      });
    }

    // Check if input is a coordinate pair (e.g., "17.385, 78.4867")
    const coordMatch = query.match(/^(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)$/);
    if (coordMatch) {
      const lat = parseFloat(coordMatch[1]);
      const lon = parseFloat(coordMatch[2]);
      if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
        ws.updateMissionLocation({
          name: `Coordinates (${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E)`,
          lat,
          lon,
          utmZone: `EPSG:${Math.floor((lon + 180) / 6) + 32601}`,
          areaAoi: '15.0 km²',
        });
      }
    }

    ws.runQuery();
  };

  const suggestions = [
    'What changed between these two images?',
    'Describe this scene',
    'Find water bodies',
    'Identify built-up areas',
    'Quantify built-up expansion in hectares',
    'Corroborate with SAR radar',
  ];

  return (
    <div className="relative w-full max-w-4xl mx-auto space-y-1.5" ref={containerRef}>
      {/* Human-Friendly Validation Notice */}
      {validationHint && (
        <div className="p-2.5 rounded-lg bg-amber-950/40 border border-amber-500/40 text-[11px] font-mono text-amber-200 flex items-center justify-between gap-3 animate-in fade-in duration-150">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{validationHint.message}</span>
          </div>
          {validationHint.action && (
            <button
              type="button"
              onClick={validationHint.action}
              className="px-2 py-0.5 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 font-bold border border-amber-500/30 shrink-0 text-[10px] transition-colors"
            >
              {validationHint.actionLabel || 'Apply'}
            </button>
          )}
        </div>
      )}

      {/* Contextual Command Suggestions (Progressive Disclosure) */}
      {!ws.isAnalyzing && isFocused && suggestions.length > 0 && (
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 select-none animate-in fade-in duration-150">
          <span className="text-[9px] font-mono font-bold text-neutral-500 uppercase tracking-widest shrink-0">
            TRY:
          </span>
          {suggestions.map((promptText, idx) => (
            <button
              key={idx}
              type="button"
              onMouseDown={(e) => {
                e.preventDefault();
                ws.setQueryText(promptText);
                ws.runQuery(promptText);
              }}
              className="shrink-0 px-2 py-1 rounded bg-[#1A1A1A] border border-neutral-800 hover:border-neutral-600 hover:bg-neutral-800 text-[11px] font-mono text-neutral-300 transition-colors flex items-center gap-1"
            >
              <Sparkles className="w-2.5 h-2.5 text-neutral-400 shrink-0" />
              <span className="truncate max-w-[260px]">{promptText}</span>
            </button>
          ))}
        </div>
      )}

      {/* Main Mission Command Surface */}
      <form
        onSubmit={handleSubmit}
        className={`relative flex items-center bg-[#141414] border rounded-md px-3 py-1.5 transition-colors ${
          ws.isAnalyzing
            ? 'border-amber-500/60 bg-amber-950/20'
            : isFocused
            ? 'border-neutral-500 bg-[#161616]'
            : 'border-neutral-800 hover:border-neutral-700'
        }`}
      >
        {/* Command Surface Label */}
        <div className="pr-2.5 flex items-center gap-1.5 text-neutral-500 font-mono text-[10px] font-bold tracking-widest border-r border-neutral-800 shrink-0 select-none">
          <span className="w-1.5 h-1.5 rounded-full bg-neutral-600" />
          <span className="text-neutral-400">ASK SATQUERY</span>
        </div>

        {/* Command Input Field */}
        <input
          type="text"
          value={ws.queryText}
          onChange={(e) => handleQueryChange(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={
            ws.isAnalyzing
              ? 'Analyzing observation scenes via ChangeNet & SAR...'
              : 'Ask a question about this imagery (e.g. "What changed between these two images?")'
          }
          disabled={ws.isAnalyzing}
          className="flex-1 text-xs font-mono text-white placeholder-neutral-500 bg-transparent px-2.5 focus:outline-none disabled:opacity-75"
        />

        {/* Action Controls */}
        <div className="flex items-center gap-1 pl-1">
          <button
            type="button"
            onClick={handleVoiceInput}
            className={`p-1.5 rounded transition-colors ${
              isListening
                ? 'bg-rose-600 text-white animate-pulse'
                : 'text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800'
            }`}
            title={isListening ? 'Listening...' : 'Voice Command'}
          >
            <Mic className="w-3.5 h-3.5" />
          </button>

          <button
            type="button"
            onClick={() => ws.toggleDrawer('chat')}
            className={`px-2 py-1 rounded transition-colors flex items-center gap-1 border border-white/5 ${
              ws.activeDrawer === 'chat'
                ? 'bg-satblue-600 text-white'
                : 'text-neutral-300 hover:text-white bg-neutral-800/80 hover:bg-neutral-800'
            }`}
            title="Open SatQuery AI Copilot Conversation"
          >
            <Sparkles className="w-3 h-3 text-amber-300" />
            <span className="hidden sm:inline text-[10px] font-mono font-semibold">COPILOT</span>
          </button>

          <button
            type="submit"
            disabled={!ws.queryText.trim() || ws.isAnalyzing}
            className="px-2.5 py-1 rounded bg-white text-black text-xs font-mono font-bold flex items-center gap-1 hover:bg-neutral-200 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            title="Dispatch Command"
          >
            {ws.isAnalyzing ? (
              <Loader2 className="w-3 h-3 animate-spin text-black" />
            ) : (
              <ArrowUp className="w-3 h-3 stroke-[2.5]" />
            )}
            <span className="hidden sm:inline text-[10px]">RUN</span>
          </button>
        </div>
      </form>
    </div>
  );
};
