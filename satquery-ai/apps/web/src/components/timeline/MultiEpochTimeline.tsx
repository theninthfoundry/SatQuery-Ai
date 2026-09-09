'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  Pause,
  SkipForward,
  FastForward,
  Calendar,
  Cloud,
  Radio,
  Sliders,
  ChevronRight,
  Sparkles,
  ArrowRight,
  Eye,
} from 'lucide-react';
import { EpochObservation } from '../../types/aoi';
import { useWorkspace } from '../../context/WorkspaceContext';

export const CANONICAL_EPOCHS: EpochObservation[] = [
  {
    id: 'epoch_2024_03',
    epochNumber: 1,
    date: '2024-03-14',
    sensor: 'Sentinel-2 MSI',
    cloudCoverPct: 1.8,
    resolution: '10m GSD',
    orbitMetadata: 'Relative Orbit 112 · Descending',
    sunElevationDeg: 62.4,
    isCloudFree: true,
    builtUpHa: 42.1,
    meanNdvi: 0.68,
    sarMeanDb: -14.2,
  },
  {
    id: 'epoch_2024_07',
    epochNumber: 2,
    date: '2024-07-22',
    sensor: 'Sentinel-1 C-SAR',
    cloudCoverPct: 24.5,
    resolution: '10m GSD',
    orbitMetadata: 'Pass 045 · Ascending C-band',
    sunElevationDeg: 58.1,
    isCloudFree: false,
    builtUpHa: 42.4,
    meanNdvi: 0.72,
    sarMeanDb: -13.9,
  },
  {
    id: 'epoch_2024_11',
    epochNumber: 3,
    date: '2024-11-08',
    sensor: 'Sentinel-2 MSI',
    cloudCoverPct: 3.2,
    resolution: '10m GSD',
    orbitMetadata: 'Relative Orbit 112 · Descending',
    sunElevationDeg: 48.6,
    isCloudFree: true,
    builtUpHa: 42.9,
    meanNdvi: 0.65,
    sarMeanDb: -14.0,
  },
  {
    id: 'epoch_2025_02',
    epochNumber: 4,
    date: '2025-02-17',
    sensor: 'Sentinel-2 MSI',
    cloudCoverPct: 0.8,
    resolution: '10m GSD',
    orbitMetadata: 'Relative Orbit 112 · Descending',
    sunElevationDeg: 54.2,
    isCloudFree: true,
    builtUpHa: 43.4,
    meanNdvi: 0.62,
    sarMeanDb: -13.5,
  },
  {
    id: 'epoch_2025_06',
    epochNumber: 5,
    date: '2025-06-25',
    sensor: 'Sentinel-2 + Sentinel-1',
    cloudCoverPct: 18.4,
    resolution: '10m GSD',
    orbitMetadata: 'Joint S2/S1 Coregistered Pair',
    sunElevationDeg: 64.1,
    isCloudFree: false,
    builtUpHa: 43.8,
    meanNdvi: 0.67,
    sarMeanDb: -13.1,
  },
  {
    id: 'epoch_2025_10',
    epochNumber: 6,
    date: '2025-10-14',
    sensor: 'Sentinel-2 MSI',
    cloudCoverPct: 4.1,
    resolution: '10m GSD',
    orbitMetadata: 'Relative Orbit 112 · Descending',
    sunElevationDeg: 52.0,
    isCloudFree: true,
    builtUpHa: 44.2,
    meanNdvi: 0.63,
    sarMeanDb: -12.8,
  },
  {
    id: 'epoch_2026_01',
    epochNumber: 7,
    date: '2026-01-20',
    sensor: 'Sentinel-2 MSI',
    cloudCoverPct: 2.1,
    resolution: '10m GSD',
    orbitMetadata: 'Relative Orbit 112 · Descending',
    sunElevationDeg: 51.4,
    isCloudFree: true,
    builtUpHa: 44.8,
    meanNdvi: 0.59,
    sarMeanDb: -12.4,
  },
  {
    id: 'epoch_2026_03',
    epochNumber: 8,
    date: '2026-03-19',
    sensor: 'Sentinel-2 + Sentinel-1',
    cloudCoverPct: 1.2,
    resolution: '10m GSD',
    orbitMetadata: 'Grand Showcase Coregistered Pair',
    sunElevationDeg: 62.8,
    isCloudFree: true,
    builtUpHa: 45.6,
    meanNdvi: 0.56,
    sarMeanDb: -11.9,
  },
];

interface MultiEpochTimelineProps {
  onSelectEpoch?: (epoch: EpochObservation) => void;
  activeT1EpochId?: string;
  activeT2EpochId?: string;
  onSetAsT1?: (epoch: EpochObservation) => void;
  onSetAsT2?: (epoch: EpochObservation) => void;
}

export const MultiEpochTimeline: React.FC<MultiEpochTimelineProps> = ({
  onSelectEpoch,
  activeT1EpochId = 'epoch_2024_03',
  activeT2EpochId = 'epoch_2026_03',
  onSetAsT1,
  onSetAsT2,
}) => {
  const ws = useWorkspace();
  const [selectedEpochIndex, setSelectedEpochIndex] = useState<number>(7); // Default to latest (2026)
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<1 | 2 | 5>(1);
  const playTimerRef = useRef<any>(null);

  const currentEpoch = CANONICAL_EPOCHS[selectedEpochIndex];
  const t1Epoch = CANONICAL_EPOCHS.find((e) => e.id === activeT1EpochId) || CANONICAL_EPOCHS[0];
  const t2Epoch = CANONICAL_EPOCHS.find((e) => e.id === activeT2EpochId) || CANONICAL_EPOCHS[7];

  // Cumulative change from baseline (T1)
  const builtUpDelta = +(currentEpoch.builtUpHa - t1Epoch.builtUpHa).toFixed(2);
  const ndviDeltaPct = +(((currentEpoch.meanNdvi - t1Epoch.meanNdvi) / t1Epoch.meanNdvi) * 100).toFixed(1);

  // Playback Loop
  useEffect(() => {
    if (!isPlaying) {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
      return;
    }

    const intervalMs = 2000 / playbackSpeed;
    playTimerRef.current = setInterval(() => {
      setSelectedEpochIndex((prev) => {
        const next = (prev + 1) % CANONICAL_EPOCHS.length;
        if (onSelectEpoch) onSelectEpoch(CANONICAL_EPOCHS[next]);
        return next;
      });
    }, intervalMs);

    return () => {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
    };
  }, [isPlaying, playbackSpeed, onSelectEpoch]);

  const handleSelect = (idx: number) => {
    setSelectedEpochIndex(idx);
    if (onSelectEpoch) onSelectEpoch(CANONICAL_EPOCHS[idx]);
  };

  const handleNextClear = () => {
    let nextIdx = (selectedEpochIndex + 1) % CANONICAL_EPOCHS.length;
    while (!CANONICAL_EPOCHS[nextIdx].isCloudFree && nextIdx !== selectedEpochIndex) {
      nextIdx = (nextIdx + 1) % CANONICAL_EPOCHS.length;
    }
    handleSelect(nextIdx);
  };

  return (
    <div className="bg-[#101010]/95 backdrop-blur-md border-t border-neutral-800 px-4 py-2.5 text-xs font-mono text-neutral-300 select-none">
      {/* Top Bar: Observation Metadata & Playback Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
        {/* Left: Active Scene Detailed Metadata */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-bold text-white">
            <Calendar className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-sm tracking-tight">{currentEpoch.date}</span>
          </div>

          <span className="text-neutral-600">·</span>

          <span className="text-neutral-300 font-medium">{currentEpoch.sensor}</span>

          <span className="text-neutral-600">·</span>

          {/* Cloud Cover */}
          <div className="flex items-center gap-1">
            <Cloud className="w-3 h-3 text-neutral-400" />
            <span
              className={`font-bold ${
                currentEpoch.cloudCoverPct <= 5
                  ? 'text-emerald-400'
                  : currentEpoch.cloudCoverPct <= 15
                  ? 'text-amber-400'
                  : 'text-rose-400'
              }`}
            >
              {currentEpoch.cloudCoverPct}% cloud
            </span>
          </div>

          <span className="text-neutral-600">·</span>

          <span className="text-neutral-400">{currentEpoch.resolution}</span>

          <span className="text-neutral-600 hidden md:inline">·</span>

          <span className="text-neutral-500 text-[11px] hidden md:inline">
            {currentEpoch.orbitMetadata}
          </span>
        </div>

        {/* Right: Playback & T1/T2 Comparison Indicators */}
        <div className="flex items-center gap-2">
          {/* Change From Baseline Readout */}
          <div className="flex items-center gap-2 bg-[#181818] px-2.5 py-1 rounded border border-neutral-800 text-[11px]">
            <span className="text-neutral-500 text-[9px] uppercase font-bold tracking-wider">
              VS BASELINE ({t1Epoch.date.slice(0, 7)}):
            </span>
            <span className={builtUpDelta >= 0 ? 'text-amber-400 font-bold' : 'text-emerald-400'}>
              Built-up: {builtUpDelta > 0 ? `+${builtUpDelta}` : builtUpDelta} ha
            </span>
            <span className="text-neutral-600">|</span>
            <span className={ndviDeltaPct <= 0 ? 'text-rose-400' : 'text-emerald-400'}>
              NDVI: {ndviDeltaPct > 0 ? `+${ndviDeltaPct}` : ndviDeltaPct}%
            </span>
          </div>

          {/* Playback Button */}
          <button
            onClick={() => setIsPlaying((v) => !v)}
            className="p-1.5 rounded bg-neutral-800 hover:bg-neutral-700 text-white transition-colors"
            title={isPlaying ? 'Pause Playback' : 'Play Observation Sequence'}
          >
            {isPlaying ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3 fill-white" />}
          </button>

          {/* Speed Toggle */}
          <button
            onClick={() => setPlaybackSpeed((s) => (s === 1 ? 2 : s === 2 ? 5 : 1))}
            className="px-2 py-1 rounded bg-neutral-800 hover:bg-neutral-700 text-neutral-300 font-bold text-[10px]"
            title="Toggle Playback Speed"
          >
            {playbackSpeed}x
          </button>

          {/* Jump to Next Cloud-Free Scene */}
          <button
            onClick={handleNextClear}
            className="px-2 py-1 rounded bg-neutral-800 hover:bg-neutral-700 text-emerald-400 font-bold text-[10px] flex items-center gap-1"
            title="Jump to Next Cloud-Free Acquisition"
          >
            <SkipForward className="w-2.5 h-2.5" />
            <span>CLEAR SCENE</span>
          </button>
        </div>
      </div>

      {/* Main Epoch Nodes Track */}
      <div className="relative pt-3 pb-1">
        {/* Horizontal Connecting Line */}
        <div className="absolute top-6 left-4 right-4 h-0.5 bg-neutral-800" />

        {/* Epoch Markers */}
        <div className="grid grid-cols-8 gap-1 relative z-10">
          {CANONICAL_EPOCHS.map((epoch, idx) => {
            const isSelected = selectedEpochIndex === idx;
            const isT1 = epoch.id === activeT1EpochId;
            const isT2 = epoch.id === activeT2EpochId;

            return (
              <div key={epoch.id} className="flex flex-col items-center group">
                {/* Epoch Node Button */}
                <button
                  onClick={() => handleSelect(idx)}
                  className={`w-5 h-5 rounded-full flex items-center justify-center transition-all ${
                    isSelected
                      ? 'bg-blue-500 ring-4 ring-blue-500/20 text-white scale-110'
                      : isT1
                      ? 'bg-amber-500 ring-2 ring-amber-500/30 text-black'
                      : isT2
                      ? 'bg-emerald-500 ring-2 ring-emerald-500/30 text-black'
                      : epoch.isCloudFree
                      ? 'bg-neutral-700 hover:bg-neutral-500'
                      : 'bg-neutral-800 opacity-60 hover:opacity-100'
                  }`}
                  title={`${epoch.sensor} · ${epoch.date} (${epoch.cloudCoverPct}% cloud)`}
                >
                  <div className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-white' : 'bg-transparent'}`} />
                </button>

                {/* Date Label */}
                <span
                  className={`mt-1.5 text-[10px] font-mono tracking-tight transition-colors ${
                    isSelected ? 'text-white font-bold' : 'text-neutral-500 group-hover:text-neutral-300'
                  }`}
                >
                  {epoch.date.slice(5)}
                </span>

                {/* Sub-label Badges (T1, T2, Sensor) */}
                <div className="flex items-center gap-0.5 mt-0.5">
                  {isT1 && (
                    <span className="text-[8px] bg-amber-500/20 text-amber-300 px-1 rounded font-bold">
                      T1
                    </span>
                  )}
                  {isT2 && (
                    <span className="text-[8px] bg-emerald-500/20 text-emerald-300 px-1 rounded font-bold">
                      T2
                    </span>
                  )}
                  <span className="text-[8px] text-neutral-600">
                    {epoch.sensor.includes('SAR') ? 'SAR' : 'MSI'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Epoch Comparison Quick Actions */}
      <div className="flex items-center justify-between pt-1 border-t border-neutral-900 mt-1 text-[10px]">
        <div className="flex items-center gap-2">
          <span className="text-neutral-500">SET ACTIVE ({currentEpoch.date}):</span>
          <button
            onClick={() => {
              if (onSetAsT1) onSetAsT1(currentEpoch);
              ws.dateT1 = currentEpoch.date;
            }}
            className="px-2 py-0.5 rounded bg-neutral-800 hover:bg-amber-900/40 hover:text-amber-300 text-neutral-300 transition-colors"
          >
            SET AS T1 (BASELINE)
          </button>
          <button
            onClick={() => {
              if (onSetAsT2) onSetAsT2(currentEpoch);
              ws.dateT2 = currentEpoch.date;
            }}
            className="px-2 py-0.5 rounded bg-neutral-800 hover:bg-emerald-900/40 hover:text-emerald-300 text-neutral-300 transition-colors"
          >
            SET AS T2 (COMPARISON)
          </button>
        </div>

        <button
          onClick={() => {
            ws.setQueryText(
              `Analyze multi-epoch change from ${t1Epoch.date} to ${t2Epoch.date}. Built-up expanded by ${builtUpDelta} ha.`
            );
            ws.runQuery(
              `Analyze multi-epoch change from ${t1Epoch.date} to ${t2Epoch.date}. Built-up expanded by ${builtUpDelta} ha.`
            );
          }}
          className="text-blue-400 hover:text-blue-300 flex items-center gap-1"
        >
          <Sparkles className="w-2.5 h-2.5" />
          <span>Query AI for this T1/T2 Interval</span>
        </button>
      </div>
    </div>
  );
};
