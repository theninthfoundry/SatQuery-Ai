'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Globe,
  Search,
  X,
  Satellite,
  Compass,
  MapPin,
  Loader2,
  Database,
  SlidersHorizontal,
  CheckCircle2,
  Layers,
  Sparkles,
} from 'lucide-react';
import { useWorkspaceSafe } from '../context/WorkspaceContext';
import { SearchEarthLocation, SatelliteObservationItem } from '../types';

export interface SearchEarthProps {
  onSearchComplete?: (data: {
    location: SearchEarthLocation;
    observations: SatelliteObservationItem[];
  }) => void;
  onOpenPicker?: () => void;
  className?: string;
  compact?: boolean;
}

const POPULAR_EO_TARGETS = [
  { name: 'Hyderabad Urban Basin', query: 'Hyderabad, India', lat: 17.385, lon: 78.4867, desc: 'Urban Expansion & Lake Basin' },
  { name: 'ISRO SAC Ahmedabad', query: 'Ahmedabad, India', lat: 23.0225, lon: 72.5085, desc: 'Space Applications Centre' },
  { name: 'SDSC Sriharikota', query: 'Sriharikota, India', lat: 13.7199, lon: 80.2304, desc: 'Satish Dhawan Space Centre' },
  { name: 'Sundarbans Delta', query: 'Sundarbans, India', lat: 21.9497, lon: 88.9004, desc: 'Mangrove Biosphere Reserve' },
  { name: 'Tokyo Bay Logistics', query: 'Tokyo Bay, Japan', lat: 35.6762, lon: 139.6503, desc: 'Infrastructure Maritime Hub' },
  { name: 'Cairo Nile River Basin', query: 'Cairo, Egypt', lat: 30.0444, lon: 31.2357, desc: 'Agrarian Edge & Desert Corridor' },
];

export const SearchEarth: React.FC<SearchEarthProps> = ({
  onSearchComplete,
  onOpenPicker,
  className = '',
  compact = false,
}) => {
  const ws = useWorkspaceSafe();
  const [location, setLocation] = useState<string>('Hyderabad, India');
  const [results, setResults] = useState<SatelliteObservationItem[]>(ws?.stacObservations || []);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showPresets, setShowPresets] = useState<boolean>(false);
  const [showResultsList, setShowResultsList] = useState<boolean>(false);
  const [lastQueriedLocation, setLastQueriedLocation] = useState<SearchEarthLocation | null>(
    ws?.searchLocationData || {
      name: 'Hyderabad Urban Corridor',
      displayName: 'Hyderabad Urban Corridor, Telangana, India',
      lat: ws?.currentMission?.lat || 17.385,
      lon: ws?.currentMission?.lon || 78.4867,
      utmZone: ws?.currentMission?.utmZone || 'UTM Zone 44N',
      epsg: 32644,
      bbox: [78.2, 17.2, 78.7, 17.6],
      country: 'India',
      areaEstimateKm2: 25.0,
    }
  );

  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Sync with workspace stac observations if available and local results are empty
  useEffect(() => {
    if (ws?.stacObservations && ws.stacObservations.length > 0 && results.length === 0) {
      setResults(ws.stacObservations);
    }
  }, [ws?.stacObservations, results.length]);

  // Real-time Coordinate Detection Parser
  const parsedCoords = React.useMemo(() => {
    const trimmed = location.trim();
    // Match decimal formats: "17.385, 78.4867" or "17.385 -78.4867" or "17.3850 N, 78.4867 E"
    const match = trimmed.match(
      /^(-?\d+(?:\.\d+)?)\s*([NSns])?[,\s]+(-?\d+(?:\.\d+)?)\s*([EWew])?$/
    );

    if (match) {
      let lat = parseFloat(match[1]);
      const latHem = (match[2] || '').toUpperCase();
      if (latHem === 'S') lat = -Math.abs(lat);

      let lon = parseFloat(match[3]);
      const lonHem = (match[4] || '').toUpperCase();
      if (lonHem === 'W') lon = -Math.abs(lon);

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
  }, [location]);

  // Click outside to dismiss presets dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowPresets(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleQueryStac = async (targetLocation?: string) => {
    const locQuery = (targetLocation !== undefined ? targetLocation : location).trim();
    if (!locQuery) return;

    setIsLoading(true);
    setError(null);
    setShowPresets(false);

    try {
      const res = await fetch(`/api/v1/satellite/search?q=${encodeURIComponent(locQuery)}&maxCloud=35`);
      const data = await res.json();

      if (data.status === 'success') {
        const loc: SearchEarthLocation = data.location;
        const observations: SatelliteObservationItem[] = data.observations || [];

        // 1. Update local state with search results
        setResults(observations);
        setLastQueriedLocation(loc);
        setShowResultsList(true);

        // 2. Synchronize workspace context if available
        ws?.setSearchLocationData?.(loc);
        ws?.setStacObservations?.(observations);

        // Update active mission location in workspace
        ws?.updateMissionLocation?.({
          name: loc.name,
          lat: loc.lat,
          lon: loc.lon,
          utmZone: loc.utmZone,
          areaAoi: `${loc.areaEstimateKm2 || 25.0} km²`,
        });

        // Open the observation picker so the user can immediately toggle observations
        ws?.setIsObservationPickerOpen?.(true);

        if (onSearchComplete) {
          onSearchComplete({ location: loc, observations });
        }
        if (onOpenPicker) {
          onOpenPicker();
        }
      } else {
        setError(data.message || 'STAC catalog query did not return observations');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Network error querying STAC catalogue';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  // Active coordinates to display: parsed if available, otherwise last queried or current mission
  const activeLat = parsedCoords
    ? parsedCoords.lat
    : lastQueriedLocation?.lat ?? ws?.currentMission?.lat ?? 17.385;
  const activeLon = parsedCoords
    ? parsedCoords.lon
    : lastQueriedLocation?.lon ?? ws?.currentMission?.lon ?? 78.4867;
  const activeUtm = parsedCoords
    ? parsedCoords.utmZone
    : lastQueriedLocation?.utmZone ?? ws?.currentMission?.utmZone ?? 'UTM Zone 44N';
  const activeEpsg = parsedCoords
    ? parsedCoords.epsg
    : lastQueriedLocation?.epsg ?? 32644;

  const latFormatted = `${Math.abs(activeLat).toFixed(4)}° ${activeLat >= 0 ? 'N' : 'S'}`;
  const lonFormatted = `${Math.abs(activeLon).toFixed(4)}° ${activeLon >= 0 ? 'E' : 'W'}`;

  return (
    <div
      ref={containerRef}
      id="search-earth-container"
      data-testid="search-earth"
      className={`relative flex flex-col gap-2 ${className}`}
    >
      {/* Search Input Bar + Action Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 p-1.5 rounded-2xl bg-white/95 backdrop-blur-md border border-[#E6E6E1] shadow-lg">
        {/* 1. Location Input Field */}
        <div className="relative flex-1 flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#FAF9F7] border border-[#E6E6E1] focus-within:border-[#111111] focus-within:bg-white focus-within:ring-2 focus-within:ring-[#111111]/10 transition-all">
          <Globe className="w-4 h-4 text-satblue-600 shrink-0" />
          <input
            ref={inputRef}
            id="search-earth-location-input"
            data-testid="search-earth-location-input"
            data-test="search-earth-input"
            name="location"
            type="text"
            value={location}
            onFocus={() => setShowPresets(true)}
            onChange={(e) => setLocation(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleQueryStac();
              }
            }}
            placeholder="Enter location name or coordinates (e.g., 17.3850, 78.4867 or Hyderabad)..."
            aria-label="Location or coordinates"
            className="flex-1 bg-transparent text-xs text-[#111111] placeholder:text-[#888888] focus:outline-none font-medium truncate"
          />

          {/* Real-time Coordinate detected indicator */}
          {parsedCoords && (
            <span
              id="search-earth-coord-pill"
              className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-satblue-50 text-satblue-700 border border-satblue-200 shrink-0"
              title="Detected Valid Global Coordinates"
            >
              COORDINATES DETECTED
            </span>
          )}

          {/* Clear query button */}
          {location && (
            <button
              id="search-earth-clear-btn"
              data-testid="search-earth-clear-btn"
              type="button"
              onClick={() => {
                setLocation('');
                inputRef.current?.focus();
              }}
              className="p-1 rounded-md text-[#888888] hover:text-[#111111] hover:bg-[#EAEAE5] transition-colors"
              title="Clear input"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* 2. STAC Catalogue Query Button */}
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            id="search-earth-query-stac-btn"
            data-testid="search-earth-query-stac-btn"
            data-test="search-earth-button"
            type="button"
            disabled={isLoading || !location.trim()}
            onClick={() => handleQueryStac()}
            className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-3.5 py-2 rounded-xl bg-[#111111] text-white hover:bg-[#2A2A2A] disabled:opacity-50 disabled:pointer-events-none text-xs font-semibold shadow-sm transition-all"
            title="Query STAC-compliant Earth Observation catalogue"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-satblue-300" />
                <span>Searching EO Catalogue...</span>
              </>
            ) : (
              <>
                <Satellite className="w-3.5 h-3.5 text-satblue-300" />
                <span>Search EO Catalogue</span>
              </>
            )}
          </button>

          {/* Toggle Observation Picker Shortcut Button */}
          <button
            id="search-earth-open-picker-btn"
            data-testid="search-earth-open-picker-btn"
            type="button"
            onClick={() => {
              if (ws?.setIsObservationPickerOpen) {
                ws.setIsObservationPickerOpen(!ws.isObservationPickerOpen);
              }
              if (onOpenPicker) onOpenPicker();
            }}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-mono font-bold transition-all ${
              ws?.isObservationPickerOpen
                ? 'bg-satblue-50 border-satblue-300 text-satblue-800'
                : 'bg-[#FAF9F7] border-[#E6E6E1] text-[#333333] hover:bg-[#F0EFEA]'
            }`}
            title="Toggle STAC Observation Picker drawer/modal"
          >
            <Layers className="w-3.5 h-3.5 text-[#6F6F6A]" />
            <span className="hidden sm:inline">OBSERVATIONS</span>
            <span className="px-1.5 py-0.2 rounded text-[10px] bg-white border border-[#D5D5D0] text-[#111111]">
              {results.length}
            </span>
          </button>
        </div>
      </div>

      {/* 3. High-Precision Coordinate Display Panel */}
      <div
        id="search-earth-coordinate-display"
        data-testid="search-earth-coordinate-display"
        className="flex flex-wrap items-center justify-between gap-2 px-3 py-1.5 rounded-xl bg-white/90 backdrop-blur-md border border-[#E6E6E1] text-[11px] font-mono shadow-sm"
      >
        <div className="flex items-center gap-2 text-[#333333]">
          <Compass className="w-3.5 h-3.5 text-satblue-600 shrink-0" />
          <span className="font-bold text-[#111111]">COORDINATES:</span>
          <span>
            Lat: <strong className="text-[#111111]">{latFormatted}</strong> ({activeLat.toFixed(4)}°)
          </span>
          <span className="text-[#CCCCCC]">|</span>
          <span>
            Lon: <strong className="text-[#111111]">{lonFormatted}</strong> ({activeLon.toFixed(4)}°)
          </span>
        </div>

        <div className="flex items-center gap-2 text-[10px]">
          <span className="px-2 py-0.5 rounded bg-[#F4F4F0] border border-[#E6E6E1] text-[#444444] font-bold">
            {activeUtm}
          </span>
          <span className="px-2 py-0.5 rounded bg-[#F4F4F0] border border-[#E6E6E1] text-[#666666]">
            EPSG:{activeEpsg}
          </span>
          <span className="hidden md:inline-flex items-center gap-1 text-emerald-700 font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            STAC v1.0.0 COMPLIANT
          </span>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div
          id="search-earth-error"
          className="p-2.5 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800 flex items-center justify-between"
        >
          <div className="flex items-center gap-2">
            <span className="font-bold">Catalog Notice:</span>
            <span>{error}</span>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-xs text-red-600 hover:text-red-900 font-bold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* 4. Search Results Summary & Granules List (Local State) */}
      {results.length > 0 && (
        <div
          id="search-earth-results"
          data-testid="search-earth-results"
          className="p-2.5 rounded-xl bg-white/95 backdrop-blur-md border border-[#E6E6E1] shadow-sm text-xs font-mono"
        >
          <div className="flex items-center justify-between gap-2 pb-1.5 border-b border-[#F0EFEA]">
            <div className="flex items-center gap-2">
              <Database className="w-3.5 h-3.5 text-satblue-600" />
              <span className="font-bold text-[#111111]">
                EO CATALOGUE RESULTS:
              </span>
              <span
                id="search-earth-results-count"
                data-testid="search-earth-results-count"
                className="px-1.5 py-0.5 rounded bg-satblue-50 text-satblue-700 font-bold border border-satblue-200"
              >
                {results.length} Granules Available
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setShowResultsList(!showResultsList)}
                className="px-2 py-0.5 rounded bg-[#FAF9F7] hover:bg-[#F0EFEA] border border-[#E6E6E1] text-[#444444] text-[10px] font-semibold transition-colors"
              >
                {showResultsList ? 'Hide List' : 'Preview List'}
              </button>
              <button
                type="button"
                onClick={() => {
                  if (ws?.setIsObservationPickerOpen) {
                    ws.setIsObservationPickerOpen(true);
                  }
                  if (onOpenPicker) onOpenPicker();
                }}
                className="px-2.5 py-0.5 rounded bg-[#111111] text-white hover:bg-[#2A2A2A] text-[10px] font-semibold transition-colors"
              >
                Open Picker
              </button>
            </div>
          </div>

          {/* Granule Results List */}
          {showResultsList && (
            <div className="mt-2 space-y-1 max-h-48 overflow-y-auto pr-1">
              {results.slice(0, 5).map((obs) => (
                <div
                  key={obs.id}
                  className="flex items-center justify-between gap-2 p-1.5 rounded-lg bg-[#FAF9F7] hover:bg-[#F4F4F0] border border-[#ECECE8] text-[11px] transition-colors"
                >
                  <div className="flex items-center gap-1.5 min-w-0">
                    <Satellite className="w-3 h-3 text-[#6F6F6A] shrink-0" />
                    <span className="font-bold text-[#111111] truncate">{obs.title}</span>
                    <span className="text-[10px] text-[#6F6F6A] shrink-0">({obs.sensor})</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 text-[10px] text-[#555555]">
                    <span>{obs.dateFormatted}</span>
                    {obs.modality === 'optical' ? (
                      <span className="text-emerald-700 font-semibold">{obs.cloudCoverPct}% cloud</span>
                    ) : (
                      <span className="text-satblue-700 font-semibold">SAR (All-weather)</span>
                    )}
                  </div>
                </div>
              ))}
              {results.length > 5 && (
                <p className="text-[10px] text-[#888888] text-center pt-1">
                  +{results.length - 5} more observations in Observation Picker
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Presets Dropdown Panel (when input focused) */}
      {showPresets && (
        <div
          id="search-earth-presets-menu"
          className="absolute top-full left-0 right-0 mt-1 p-3 bg-white rounded-2xl border border-[#E6E6E1] shadow-2xl z-50 animate-in fade-in zoom-in-95 duration-150"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono font-bold text-[#888888] uppercase tracking-wider">
              Verified Earth Observation Targets
            </span>
            <span className="text-[10px] font-mono text-[#888888]">
              Copernicus Sentinel-2 & Sentinel-1 Co-registered
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
            {POPULAR_EO_TARGETS.map((target) => (
              <button
                key={target.name}
                type="button"
                onClick={() => {
                  setLocation(target.query);
                  handleQueryStac(target.query);
                }}
                className="flex flex-col text-left p-2 rounded-xl bg-[#FAF9F7] hover:bg-[#F0EFEA] border border-[#E6E6E1] hover:border-[#CCCCCC] transition-all group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#111111] group-hover:text-satblue-700">
                    {target.name}
                  </span>
                  <MapPin className="w-3 h-3 text-[#888888] group-hover:text-satblue-600" />
                </div>
                <span className="text-[10px] text-[#6F6F6A] mt-0.5 line-clamp-1">{target.desc}</span>
                <span className="text-[9px] font-mono text-[#888888] mt-1">
                  {target.lat.toFixed(4)}°N, {target.lon.toFixed(4)}°E
                </span>
              </button>
            ))}
          </div>

          <div className="mt-2.5 pt-2 border-t border-[#F0EFEA] flex items-center justify-between text-[10px] font-mono text-[#888888]">
            <span>Tip: Enter decimal coordinates like 17.3850, 78.4867 for custom AOI</span>
            <button
              onClick={() => setShowPresets(false)}
              className="text-[#555555] hover:text-[#111111] font-semibold"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
