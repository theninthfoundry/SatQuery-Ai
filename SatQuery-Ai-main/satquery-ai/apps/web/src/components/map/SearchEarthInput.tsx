'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Globe,
  Search,
  X,
  Satellite,
  Layers,
  MapPin,
  Calendar,
  Cloud,
  Check,
  ChevronDown,
  ChevronUp,
  Sparkles,
  ArrowRight,
  Filter,
  ExternalLink,
  Loader2,
  Sliders,
  Compass,
} from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface SatelliteObservationItem {
  id: string;
  title: string;
  sensor: 'Sentinel-2 L2A' | 'Sentinel-1 C-SAR' | 'Landsat-9 OLI';
  modality: 'optical' | 'sar' | 'multispectral';
  date: string;
  dateFormatted: string;
  cloudCoverPct: number;
  sunElevationDeg: number;
  orbit: string;
  polarization?: string;
  resolution: string;
  bands: string[];
  thumbnailUrl: string;
  previewUrl?: string;
  utmZone: string;
  epsg: number;
  bbox: [number, number, number, number];
  stacCollection: string;
  provider: string;
  qualityScore: number;
  processingLevel: string;
}

interface SearchLocation {
  name: string;
  displayName: string;
  lat: number;
  lon: number;
  utmZone: string;
  epsg: number;
  bbox: [number, number, number, number];
  country: string;
  areaEstimateKm2?: number;
}

const POPULAR_EO_PRESETS = [
  { name: 'Hyderabad Urban Corridor', query: 'Hyderabad, India', lat: 17.385, lon: 78.4867, desc: 'Urban Expansion & Lake Basin' },
  { name: 'ISRO SAC Ahmedabad', query: 'Ahmedabad, India', lat: 23.0225, lon: 72.5085, desc: 'EO Operations Headquarters' },
  { name: 'ISRO URSC Bangalore', query: 'Bangalore, India', lat: 12.9716, lon: 77.5946, desc: 'High-Density Tech Corridor' },
  { name: 'SDSC Sriharikota', query: 'Sriharikota, India', lat: 13.7199, lon: 80.2304, desc: 'Launch Complex & Coastal Lagoon' },
  { name: 'Sundarbans Biosphere', query: 'Sundarbans, India', lat: 21.9497, lon: 88.9004, desc: 'Mangrove Delta Ecosystem' },
  { name: 'Tokyo Bay Logistics', query: 'Tokyo Bay, Japan', lat: 35.6762, lon: 139.6503, desc: 'Port & Infrastructure Hub' },
  { name: 'Cairo Nile River Basin', query: 'Cairo, Egypt', lat: 30.0444, lon: 31.2357, desc: 'Desert-River Agrarian Edge' },
];

export const SearchEarthInput: React.FC = () => {
  const ws = useWorkspace();
  const [query, setQuery] = useState<string>('');
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [location, setLocation] = useState<SearchLocation | null>(null);
  const [observations, setObservations] = useState<SatelliteObservationItem[]>([]);
  const [sensorFilter, setSensorFilter] = useState<'all' | 'Sentinel-2 L2A' | 'Sentinel-1 C-SAR' | 'Landsat-9 OLI'>('all');
  const [maxCloud, setMaxCloud] = useState<number>(30);
  const [selectedObsId, setSelectedObsId] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Detect coordinates in input in real-time
  const detectedCoords = React.useMemo(() => {
    const trimmed = query.trim();
    // Standard lat, lon decimal
    const match = trimmed.match(/^(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)$/);
    if (match) {
      const lat = parseFloat(match[1]);
      const lon = parseFloat(match[2]);
      if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
        const zoneNumber = Math.floor((lon + 180) / 6) + 1;
        const isNorth = lat >= 0;
        return {
          lat,
          lon,
          utmZone: `UTM Zone ${zoneNumber}${isNorth ? 'N' : 'S'}`,
          epsg: isNorth ? 32600 + zoneNumber : 32700 + zoneNumber,
        };
      }
    }
    return null;
  }, [query]);

  // Keyboard shortcut listener (Cmd/Ctrl + K or '/')
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsOpen(true);
        setTimeout(() => inputRef.current?.focus(), 50);
      } else if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Click outside to collapse flyout
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const executeSearch = async (searchTarget?: string) => {
    const searchQuery = searchTarget !== undefined ? searchTarget : query;
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    setError(null);
    setIsOpen(true);

    try {
      const res = await fetch(
        `/api/v1/satellite/search?q=${encodeURIComponent(searchQuery.trim())}&sensor=${sensorFilter}&maxCloud=${maxCloud}`
      );
      const data = await res.json();

      if (data.status === 'success') {
        setLocation(data.location);
        setObservations(data.observations || []);
        if (data.observations && data.observations.length > 0) {
          setSelectedObsId(data.observations[0].id);
        }
      } else {
        setError(data.message || 'Failed to fetch satellite observations');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Network error querying satellite catalog';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyAoi = (targetLoc: SearchLocation, obs?: SatelliteObservationItem) => {
    ws.updateMissionLocation({
      name: targetLoc.name,
      lat: targetLoc.lat,
      lon: targetLoc.lon,
      utmZone: targetLoc.utmZone,
      areaAoi: `${targetLoc.areaEstimateKm2 || 25.0} km²`,
      dateT1: obs ? obs.dateFormatted : ws.dateT1,
      dateT2: ws.dateT2,
    });

    if (obs) {
      if (obs.modality === 'sar') {
        ws.setActiveLens('SAR');
      } else {
        ws.setActiveLens('True Color');
      }
    }

    setIsOpen(false);
  };

  const handleSetT1 = (obs: SatelliteObservationItem) => {
    if (location) {
      ws.updateMissionLocation({
        name: location.name,
        lat: location.lat,
        lon: location.lon,
        utmZone: location.utmZone,
        areaAoi: `${location.areaEstimateKm2 || 25.0} km²`,
        dateT1: obs.dateFormatted,
      });
    }
  };

  const handleSetT2 = (obs: SatelliteObservationItem) => {
    if (location) {
      ws.updateMissionLocation({
        name: location.name,
        lat: location.lat,
        lon: location.lon,
        utmZone: location.utmZone,
        areaAoi: `${location.areaEstimateKm2 || 25.0} km²`,
        dateT2: obs.dateFormatted,
      });
    }
  };

  const handleRunAiQuery = (obs: SatelliteObservationItem) => {
    if (!location) return;
    const promptText = `Analyze urban morphology, built-up changes, and land cover for ${location.name} using ${obs.sensor} imagery (${obs.dateFormatted}).`;
    ws.setQueryText(promptText);
    handleApplyAoi(location, obs);
  };

  const filteredObservations = observations.filter((obs) => {
    if (sensorFilter !== 'all' && !obs.sensor.includes(sensorFilter)) return false;
    if (obs.cloudCoverPct > maxCloud && obs.modality === 'optical') return false;
    return true;
  });

  return (
    <div ref={containerRef} className="relative z-30 select-none">
      {/* Compact / Docked Search Input Bar */}
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/95 backdrop-blur-md border border-[#E6E6E1] shadow-lg transition-all ${
          isOpen ? 'ring-2 ring-[#111111]/20 w-80 sm:w-96' : 'w-64 sm:w-76 hover:border-[#CCCCCC]'
        }`}
      >
        <Globe className="w-4 h-4 text-satblue-600 shrink-0" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onFocus={() => setIsOpen(true)}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              executeSearch();
            }
          }}
          placeholder="Search Earth (place or lat, lon)..."
          className="flex-1 bg-transparent text-xs text-[#111111] placeholder:text-[#888888] focus:outline-none font-medium truncate"
        />

        {/* Real-time Coordinate detected badge indicator */}
        {detectedCoords && (
          <span className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-satblue-50 text-satblue-700 border border-satblue-200">
            COORD
          </span>
        )}

        {/* Clear query button */}
        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery('');
              inputRef.current?.focus();
            }}
            className="p-0.5 text-[#888888] hover:text-[#111111] transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}

        {/* Search trigger button */}
        <button
          type="button"
          disabled={isLoading}
          onClick={() => executeSearch()}
          className="p-1 rounded-lg bg-[#111111] text-white hover:bg-[#2A2A2A] disabled:opacity-50 transition-colors shrink-0"
          title="Search Satellite Catalog"
        >
          {isLoading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Search className="w-3.5 h-3.5" />
          )}
        </button>
      </div>

      {/* Expanded Results & Imagery Observations Flyout */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-[440px] sm:w-[540px] max-w-[92vw] bg-white rounded-2xl border border-[#E6E6E1] shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 z-50">
          {/* Header Bar */}
          <div className="flex items-center justify-between px-4 py-3 bg-[#FAF9F7] border-b border-[#E6E6E1]">
            <div className="flex items-center gap-2">
              <Satellite className="w-4 h-4 text-[#111111]" />
              <span className="text-xs font-bold text-[#111111] tracking-tight">
                Earth Observation Provider Query
              </span>
            </div>
            <div className="flex items-center gap-2 text-[10px] font-mono text-[#888888]">
              <span>STAC v1.0.0</span>
              <span>·</span>
              <span className="text-emerald-700 font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                ESA / AWS LIVE
              </span>
            </div>
          </div>

          {/* Quick Presets Strip (shown when no results yet or as quick jumps) */}
          <div className="px-4 py-2 border-b border-[#F0EFEA] bg-white">
            <div className="text-[10px] font-mono font-bold text-[#888888] uppercase tracking-wider mb-1.5">
              Verified Satellite Targets
            </div>
            <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1">
              {POPULAR_EO_PRESETS.map((preset) => (
                <button
                  key={preset.name}
                  onClick={() => {
                    setQuery(preset.query);
                    executeSearch(preset.query);
                  }}
                  className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-[#F7F7F5] hover:bg-[#EBEBE6] text-[#333333] border border-[#E6E6E1] transition-colors whitespace-nowrap shrink-0 flex items-center gap-1"
                >
                  <MapPin className="w-3 h-3 text-[#6F6F6A]" />
                  <span>{preset.name.split(' ')[0]}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Real-time Coordinate Preview Banner if coordinates detected */}
          {detectedCoords && (
            <div className="px-4 py-2 bg-satblue-50/70 border-b border-satblue-100 flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2 text-satblue-900">
                <Compass className="w-4 h-4 text-satblue-600" />
                <span>
                  Lat: <strong>{detectedCoords.lat.toFixed(4)}°</strong> · Lon:{' '}
                  <strong>{detectedCoords.lon.toFixed(4)}°</strong>
                </span>
              </div>
              <span className="text-[10px] bg-white px-2 py-0.5 rounded text-satblue-700 font-bold border border-satblue-200">
                {detectedCoords.utmZone} · EPSG:{detectedCoords.epsg}
              </span>
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="p-8 flex flex-col items-center justify-center text-center space-y-3">
              <div className="relative">
                <div className="w-12 h-12 rounded-full border-2 border-satblue-200 border-t-satblue-600 animate-spin"></div>
                <Satellite className="w-5 h-5 text-satblue-600 absolute inset-0 m-auto" />
              </div>
              <div>
                <p className="text-xs font-bold text-[#111111]">
                  Querying Copernicus & Planetary STAC Provider...
                </p>
                <p className="text-[11px] text-[#6F6F6A] mt-0.5 font-mono">
                  Fetching Sentinel-2 L2A & Sentinel-1 C-SAR observation granules
                </p>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && !isLoading && (
            <div className="p-4 m-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800 flex items-start gap-2">
              <span className="font-bold">Notice:</span>
              <p>{error}</p>
            </div>
          )}

          {/* Results Area */}
          {!isLoading && location && (
            <div className="max-h-[380px] overflow-y-auto">
              {/* Target Location Metadata Banner */}
              <div className="px-4 py-3 bg-[#FAF9F7] border-b border-[#E6E6E1] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-bold text-[#111111]">{location.name}</h4>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-[#E6E6E1] text-[#444444]">
                      {location.country}
                    </span>
                  </div>
                  <p className="text-[11px] text-[#6F6F6A] font-mono mt-0.5">
                    {location.lat.toFixed(4)}°N, {location.lon.toFixed(4)}°E · {location.utmZone} (EPSG:{location.epsg})
                  </p>
                </div>
                <button
                  onClick={() => handleApplyAoi(location)}
                  className="px-3 py-1.5 rounded-lg bg-[#111111] text-white text-xs font-semibold hover:bg-[#2A2A2A] transition-colors shrink-0 flex items-center justify-center gap-1.5 shadow-sm"
                >
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Set as Active AOI</span>
                </button>
              </div>

              {/* Filtering Controls */}
              <div className="px-4 py-2 border-b border-[#F0EFEA] flex flex-wrap items-center justify-between gap-2 text-xs">
                {/* Modality Filter */}
                <div className="flex items-center gap-1">
                  <span className="text-[10px] font-mono font-bold text-[#888888] uppercase mr-1">
                    SENSOR:
                  </span>
                  {(['all', 'Sentinel-2 L2A', 'Sentinel-1 C-SAR', 'Landsat-9 OLI'] as const).map((s) => (
                    <button
                      key={s}
                      onClick={() => setSensorFilter(s)}
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold transition-colors ${
                        sensorFilter === s
                          ? 'bg-[#111111] text-white'
                          : 'bg-[#F0EFEA] text-[#6F6F6A] hover:text-[#111111]'
                      }`}
                    >
                      {s === 'all' ? 'ALL' : s.split(' ')[0]}
                    </button>
                  ))}
                </div>

                {/* Cloud Cover Slider Pill */}
                <div className="flex items-center gap-2 text-[10px] font-mono text-[#6F6F6A]">
                  <Cloud className="w-3 h-3 text-[#888888]" />
                  <span>Max Cloud: {maxCloud}%</span>
                  <input
                    type="range"
                    min="5"
                    max="60"
                    step="5"
                    value={maxCloud}
                    onChange={(e) => setMaxCloud(parseInt(e.target.value))}
                    className="w-16 h-1 accent-[#111111] cursor-pointer"
                  />
                </div>
              </div>

              {/* Observations Granules List */}
              <div className="p-3 space-y-2.5">
                <div className="text-[10px] font-mono font-bold text-[#888888] uppercase tracking-wider px-1">
                  Available Scenes & Granules ({filteredObservations.length})
                </div>

                {filteredObservations.length === 0 ? (
                  <div className="p-6 text-center text-xs text-[#888888]">
                    No satellite observations matched the cloud cover or sensor filter. Try adjusting the cloud threshold.
                  </div>
                ) : (
                  filteredObservations.map((obs) => {
                    const isSelected = selectedObsId === obs.id;
                    const isOptical = obs.modality === 'optical';
                    const isSar = obs.modality === 'sar';

                    return (
                      <div
                        key={obs.id}
                        className={`p-3 rounded-xl border transition-all ${
                          isSelected
                            ? 'border-[#111111] bg-[#FAF9F7] shadow-sm'
                            : 'border-[#E6E6E1] bg-white hover:border-[#CCCCCC]'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="space-y-1">
                            {/* Sensor and Modality Badges */}
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                                  isSar
                                    ? 'bg-satblue-100 text-satblue-800'
                                    : isOptical
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : 'bg-amber-100 text-amber-800'
                                }`}
                              >
                                {obs.sensor}
                              </span>

                              <span className="flex items-center gap-1 text-[11px] font-medium text-[#444444]">
                                <Calendar className="w-3 h-3 text-[#888888]" />
                                <strong>{obs.dateFormatted}</strong>
                              </span>

                              {isOptical ? (
                                <span className="flex items-center gap-1 text-[10px] font-mono text-[#6F6F6A]">
                                  <Cloud className="w-3 h-3 text-[#888888]" />
                                  {obs.cloudCoverPct}% Cloud
                                </span>
                              ) : (
                                <span className="text-[10px] font-mono text-satblue-700 bg-satblue-50 px-1.5 py-0.2 rounded">
                                  All-Weather SAR
                                </span>
                              )}

                              <span className="text-[10px] font-mono text-[#888888]">
                                {obs.resolution}
                              </span>
                            </div>

                            {/* Technical Granule Details */}
                            <p className="text-[10px] font-mono text-[#6F6F6A] truncate">
                              ID: {obs.id} · {obs.orbit}
                            </p>

                            {/* Bands Tags */}
                            <div className="flex items-center gap-1 flex-wrap pt-0.5">
                              {obs.bands.slice(0, 4).map((b) => (
                                <span
                                  key={b}
                                  className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-[#F0EFEA] text-[#555555]"
                                >
                                  {b.split(' ')[0]}
                                </span>
                              ))}
                              {obs.bands.length > 4 && (
                                <span className="text-[9px] font-mono text-[#888888]">
                                  +{obs.bands.length - 4} bands
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Quality Score Badge */}
                          <div className="text-right shrink-0">
                            <span className="text-[10px] font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                              {obs.qualityScore}% Q-Score
                            </span>
                          </div>
                        </div>

                        {/* Granule Action Buttons */}
                        <div className="mt-2.5 pt-2 border-t border-[#F0EFEA] flex items-center justify-between gap-1 flex-wrap">
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => handleSetT1(obs)}
                              className="px-2 py-1 rounded text-[10px] font-mono font-bold bg-[#F0EFEA] hover:bg-[#E2E1DC] text-[#333333] transition-colors"
                              title="Set observation as T1 baseline scene"
                            >
                              Set as T1 ({obs.dateFormatted.split(',')[0]})
                            </button>
                            <button
                              onClick={() => handleSetT2(obs)}
                              className="px-2 py-1 rounded text-[10px] font-mono font-bold bg-[#F0EFEA] hover:bg-[#E2E1DC] text-[#333333] transition-colors"
                              title="Set observation as T2 target scene"
                            >
                              Set as T2 ({obs.dateFormatted.split(',')[0]})
                            </button>
                          </div>

                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() => handleRunAiQuery(obs)}
                              className="px-2.5 py-1 rounded text-[10px] font-medium bg-satblue-50 text-satblue-700 hover:bg-satblue-100 transition-colors flex items-center gap-1"
                              title="Send this scene to AI Agent query bar"
                            >
                              <Sparkles className="w-3 h-3 text-satblue-600" />
                              <span>AI Query</span>
                            </button>

                            <button
                              onClick={() => handleApplyAoi(location, obs)}
                              className="px-2.5 py-1 rounded text-[10px] font-bold bg-[#111111] text-white hover:bg-[#2A2A2A] transition-colors flex items-center gap-1"
                              title="Load scene directly into workspace"
                            >
                              <span>Load Scene</span>
                              <ArrowRight className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}

          {/* Initial Search Prompt when flyout opens without a query */}
          {!isLoading && !location && !error && (
            <div className="p-6 text-center space-y-2">
              <Globe className="w-8 h-8 text-[#888888] mx-auto opacity-70" />
              <div className="text-xs font-bold text-[#111111]">
                Query Any Location or Global Coordinates
              </div>
              <p className="text-[11px] text-[#6F6F6A] max-w-xs mx-auto leading-relaxed">
                Type any city, province, or decimal coordinates (e.g.{' '}
                <span className="font-mono font-bold text-[#111111]">17.3850, 78.4867</span>) to query
                Copernicus Sentinel-2 & Sentinel-1 SAR observations.
              </p>
            </div>
          )}

          {/* Footer Bar */}
          <div className="px-4 py-2.5 bg-[#FAF9F7] border-t border-[#E6E6E1] flex items-center justify-between text-[10px] font-mono text-[#888888]">
            <span>Press Enter to Query · Esc to Close</span>
            <button
              onClick={() => {
                ws.setIsEarthExplorerOpen(true);
                setIsOpen(false);
              }}
              className="text-satblue-700 hover:text-satblue-900 font-semibold flex items-center gap-1"
            >
              <span>Open Full Earth Explorer</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
