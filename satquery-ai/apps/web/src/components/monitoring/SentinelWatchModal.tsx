'use client';

import React, { useState } from 'react';
import {
  X,
  Radio,
  Eye,
  BellRing,
  CheckCircle2,
  AlertTriangle,
  Plus,
  Trash2,
  Play,
  Pause,
  Sparkles,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import { SentinelWatch } from '../../types/aoi';
import { useWorkspace } from '../../context/WorkspaceContext';

interface SentinelWatchModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeAOIName?: string;
  activeAOIId?: string;
}

export const SAMPLE_WATCHES: SentinelWatch[] = [
  {
    id: 'watch_01_hyd',
    name: 'Hyderabad Urban Expansion',
    aoiId: 'aoi_hyd_industrial',
    aoiName: 'Hyderabad Industrial Corridor',
    aoiCenter: { lat: 17.385, lon: 78.4867 },
    sensors: ['Sentinel-2 MSI (10m)', 'Sentinel-1 C-SAR (10m)'],
    frequency: 'Every available acquisition (5 days)',
    conditions: {
      builtUpIncreaseHa: 1.0,
      ndviDecreasePct: 15.0,
      sarAnomalyDb: 3.5,
    },
    status: 'MONITORING',
    lastCheck: '08 Sep 2026',
    nextScene: 'Pending (in 2 days)',
    metrics: {
      builtUpDeltaHa: 1.42,
      vegetationDeltaPct: -8.3,
      sarAnomaly: 'None (+1.1 dB)',
    },
    createdAt: '2026-08-01T00:00:00Z',
  },
  {
    id: 'watch_02_blr',
    name: 'Bangalore Peri-Urban Tech Encroachment',
    aoiId: 'aoi_blr_periurban',
    aoiName: 'Bangalore Peri-Urban Tech Zone',
    aoiCenter: { lat: 12.9716, lon: 77.5946 },
    sensors: ['Sentinel-2 Optical (10m)', 'Sentinel-1 SAR C-band'],
    frequency: 'Every available acquisition',
    conditions: {
      builtUpIncreaseHa: 0.75,
      ndviDecreasePct: 10.0,
    },
    status: 'TRIGGERED',
    lastCheck: '07 Sep 2026',
    nextScene: 'Processing',
    metrics: {
      builtUpDeltaHa: 1.82,
      vegetationDeltaPct: -14.2,
      sarAnomaly: 'Confirmed (+4.2 dB corner reflection)',
    },
    createdAt: '2026-08-15T00:00:00Z',
  },
];

export const SentinelWatchModal: React.FC<SentinelWatchModalProps> = ({
  isOpen,
  onClose,
  activeAOIName,
  activeAOIId,
}) => {
  const ws = useWorkspace();
  const [watches, setWatches] = useState<SentinelWatch[]>(SAMPLE_WATCHES);
  const [isCreatingNew, setIsCreatingNew] = useState<boolean>(false);

  // Form State for new Watch
  const [newWatchName, setNewWatchName] = useState<string>(
    activeAOIName ? `${activeAOIName} Continuous Watch` : 'New Sentinel Monitoring Watch'
  );
  const [builtUpThreshold, setBuiltUpThreshold] = useState<number>(1.0);
  const [ndviThreshold, setNdviThreshold] = useState<number>(15.0);
  const [sarThreshold, setSarThreshold] = useState<number>(3.5);
  const [frequency, setFrequency] = useState<string>('Every available acquisition');

  if (!isOpen) return null;

  const handleCreateWatch = () => {
    const newWatch: SentinelWatch = {
      id: `watch_${Date.now()}`,
      name: newWatchName,
      aoiId: activeAOIId || 'current_mission_aoi',
      aoiName: activeAOIName || ws.currentMission.name,
      aoiCenter: { lat: ws.currentMission.lat, lon: ws.currentMission.lon },
      sensors: ['Sentinel-2 MSI (10m)', 'Sentinel-1 C-SAR (10m)'],
      frequency,
      conditions: {
        builtUpIncreaseHa: builtUpThreshold,
        ndviDecreasePct: ndviThreshold,
        sarAnomalyDb: sarThreshold,
      },
      status: 'MONITORING',
      lastCheck: 'Just now',
      nextScene: 'Pending next orbital pass',
      metrics: {
        builtUpDeltaHa: 0.0,
        vegetationDeltaPct: 0.0,
        sarAnomaly: 'Nominal',
      },
      createdAt: new Date().toISOString(),
    };

    setWatches((prev) => [newWatch, ...prev]);
    setIsCreatingNew(false);
  };

  const handleInvestigate = (watch: SentinelWatch) => {
    ws.updateMissionLocation({
      name: watch.aoiName,
      lat: watch.aoiCenter.lat,
      lon: watch.aoiCenter.lon,
      utmZone: `EPSG:${Math.floor((watch.aoiCenter.lon + 180) / 6) + 32601}`,
      areaAoi: '15.0 km²',
    });

    const query = `Investigate Sentinel Watch trigger for "${watch.name}". Built-up changed by +${watch.metrics.builtUpDeltaHa} ha, NDVI ${watch.metrics.vegetationDeltaPct}%, SAR: ${watch.metrics.sarAnomaly}.`;
    ws.setQueryText(query);
    ws.runQuery(query);

    onClose();
  };

  const handleDeleteWatch = (id: string) => {
    setWatches((prev) => prev.filter((w) => w.id !== id));
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 select-none">
      <div className="bg-[#121212] border border-neutral-800 rounded-lg w-full max-w-2xl shadow-2xl flex flex-col overflow-hidden max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-800 bg-[#161616]">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded bg-emerald-500/20 text-emerald-400">
              <BellRing className="w-4 h-4 animate-bounce" />
            </div>
            <div>
              <h2 className="text-sm font-mono font-bold text-white tracking-wide">
                SENTINEL WATCH · CONTINUOUS MONITORING
              </h2>
              <p className="text-[10px] font-mono text-neutral-400">
                Persistent Automated Earth Observation Triggers (S2 MSI + S1 SAR)
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

        {/* Content */}
        <div className="p-4 overflow-y-auto space-y-4 text-xs font-mono">
          {!isCreatingNew ? (
            <>
              {/* Top Action to Create New Watch */}
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-neutral-400 uppercase tracking-wider">
                  ACTIVE WATCH DIRECTIVE ({watches.length})
                </span>
                <button
                  onClick={() => setIsCreatingNew(true)}
                  className="px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center gap-1 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>NEW SENTINEL WATCH</span>
                </button>
              </div>

              {/* Active Watches List */}
              <div className="space-y-3">
                {watches.map((watch) => {
                  const isTriggered = watch.status === 'TRIGGERED';
                  return (
                    <div
                      key={watch.id}
                      className={`p-3.5 rounded-lg border transition-all ${
                        isTriggered
                          ? 'border-amber-500/80 bg-amber-950/20'
                          : 'border-neutral-800 bg-[#161616]'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-sm font-bold text-white">{watch.name}</h3>
                            <span
                              className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                                isTriggered
                                  ? 'bg-amber-500 text-black animate-pulse'
                                  : 'bg-emerald-500/20 text-emerald-300'
                              }`}
                            >
                              ● {watch.status}
                            </span>
                          </div>
                          <span className="text-[10px] text-neutral-400 block mt-0.5">
                            AOI: {watch.aoiName} · {watch.frequency}
                          </span>
                        </div>

                        <button
                          onClick={() => handleDeleteWatch(watch.id)}
                          className="text-neutral-500 hover:text-rose-400 p-1 rounded"
                          title="Delete Watch"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      {/* Watch Conditions & Metrics */}
                      <div className="grid grid-cols-3 gap-2 my-2 text-[10px]">
                        <div className="bg-black/40 p-2 rounded border border-white/5">
                          <span className="text-neutral-500 block text-[9px]">BUILT-UP CHANGE</span>
                          <strong
                            className={
                              watch.metrics.builtUpDeltaHa > 0 ? 'text-amber-400' : 'text-neutral-300'
                            }
                          >
                            +{watch.metrics.builtUpDeltaHa} ha
                          </strong>
                          <span className="text-neutral-600 block text-[8px]">
                            Trigger: &gt;{watch.conditions.builtUpIncreaseHa} ha
                          </span>
                        </div>

                        <div className="bg-black/40 p-2 rounded border border-white/5">
                          <span className="text-neutral-500 block text-[9px]">VEGETATION (NDVI)</span>
                          <strong
                            className={
                              watch.metrics.vegetationDeltaPct < 0 ? 'text-rose-400' : 'text-emerald-400'
                            }
                          >
                            {watch.metrics.vegetationDeltaPct}%
                          </strong>
                          <span className="text-neutral-600 block text-[8px]">
                            Trigger: &lt;-{watch.conditions.ndviDecreasePct}%
                          </span>
                        </div>

                        <div className="bg-black/40 p-2 rounded border border-white/5">
                          <span className="text-neutral-500 block text-[9px]">SAR RADAR ANOMALY</span>
                          <strong className="text-cyan-300 truncate block">
                            {watch.metrics.sarAnomaly}
                          </strong>
                          <span className="text-neutral-600 block text-[8px]">
                            Trigger: &gt;+{watch.conditions.sarAnomalyDb} dB
                          </span>
                        </div>
                      </div>

                      {/* Card Footer Actions */}
                      <div className="flex items-center justify-between pt-2 border-t border-white/5 text-[10px]">
                        <div className="text-neutral-400">
                          Last check: <span className="text-white">{watch.lastCheck}</span> · Next scene:{' '}
                          <span className="text-neutral-300">{watch.nextScene}</span>
                        </div>

                        <button
                          onClick={() => handleInvestigate(watch)}
                          className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded font-bold flex items-center gap-1 transition-colors"
                        >
                          <Sparkles className="w-3 h-3" />
                          <span>INVESTIGATE IN WORKSPACE</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          ) : (
            /* Create New Watch Form */
            <div className="space-y-3 bg-[#161616] p-4 rounded-lg border border-neutral-800">
              <div className="flex items-center justify-between border-b border-neutral-800 pb-2">
                <span className="font-bold text-white text-xs">DEFINE NEW SENTINEL WATCH</span>
                <button
                  onClick={() => setIsCreatingNew(false)}
                  className="text-neutral-400 hover:text-white text-xs"
                >
                  Cancel
                </button>
              </div>

              <div>
                <label className="text-[10px] text-neutral-400 uppercase tracking-wider block mb-1">
                  WATCH DIRECTIVE NAME:
                </label>
                <input
                  type="text"
                  value={newWatchName}
                  onChange={(e) => setNewWatchName(e.target.value)}
                  className="w-full bg-[#0E0E0E] border border-neutral-800 rounded px-2.5 py-1.5 text-xs text-white focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-neutral-400 uppercase tracking-wider block mb-1">
                    TARGET AOI:
                  </label>
                  <div className="p-2 rounded bg-black/40 border border-neutral-800 text-neutral-300 text-xs truncate">
                    {activeAOIName || ws.currentMission.name}
                  </div>
                </div>

                <div>
                  <label className="text-[10px] text-neutral-400 uppercase tracking-wider block mb-1">
                    FREQUENCY:
                  </label>
                  <select
                    value={frequency}
                    onChange={(e) => setFrequency(e.target.value)}
                    className="w-full bg-[#0E0E0E] border border-neutral-800 rounded px-2 py-1.5 text-xs text-white focus:outline-none"
                  >
                    <option>Every available acquisition (5 days)</option>
                    <option>Weekly audit pass</option>
                    <option>Bi-weekly synthesis</option>
                  </select>
                </div>
              </div>

              {/* Conditions */}
              <div className="space-y-2 pt-2 border-t border-neutral-800">
                <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider block">
                  AUTOMATED ALERT TRIGGER CONDITIONS:
                </span>

                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-[#0E0E0E] p-2 rounded border border-neutral-800">
                    <span className="text-[9px] text-neutral-500 block">BUILT-UP INCREASE</span>
                    <div className="flex items-center gap-1 mt-1">
                      <span className="text-neutral-400">&gt;</span>
                      <input
                        type="number"
                        step="0.1"
                        value={builtUpThreshold}
                        onChange={(e) => setBuiltUpThreshold(parseFloat(e.target.value) || 0)}
                        className="w-16 bg-neutral-900 border border-neutral-700 rounded px-1.5 py-0.5 text-white text-xs"
                      />
                      <span className="text-neutral-400 text-[10px]">ha</span>
                    </div>
                  </div>

                  <div className="bg-[#0E0E0E] p-2 rounded border border-neutral-800">
                    <span className="text-[9px] text-neutral-500 block">NDVI DECREASE</span>
                    <div className="flex items-center gap-1 mt-1">
                      <span className="text-neutral-400">&gt;</span>
                      <input
                        type="number"
                        step="1"
                        value={ndviThreshold}
                        onChange={(e) => setNdviThreshold(parseFloat(e.target.value) || 0)}
                        className="w-16 bg-neutral-900 border border-neutral-700 rounded px-1.5 py-0.5 text-white text-xs"
                      />
                      <span className="text-neutral-400 text-[10px]">%</span>
                    </div>
                  </div>

                  <div className="bg-[#0E0E0E] p-2 rounded border border-neutral-800">
                    <span className="text-[9px] text-neutral-500 block">SAR BACKSCATTER ANOMALY</span>
                    <div className="flex items-center gap-1 mt-1">
                      <span className="text-neutral-400">&gt;</span>
                      <input
                        type="number"
                        step="0.5"
                        value={sarThreshold}
                        onChange={(e) => setSarThreshold(parseFloat(e.target.value) || 0)}
                        className="w-16 bg-neutral-900 border border-neutral-700 rounded px-1.5 py-0.5 text-white text-xs"
                      />
                      <span className="text-neutral-400 text-[10px]">dB</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  onClick={() => setIsCreatingNew(false)}
                  className="px-3 py-1.5 rounded bg-neutral-800 text-neutral-300 text-xs hover:bg-neutral-700"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateWatch}
                  className="px-4 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>ACTIVATE SENTINEL WATCH</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t border-neutral-800 bg-[#161616] flex items-center justify-between text-[10px] font-mono text-neutral-500">
          <span>Continuous Sentinel-1 & Sentinel-2 ESA orbital telemetry monitoring</span>
          <button onClick={onClose} className="hover:text-white transition-colors">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
