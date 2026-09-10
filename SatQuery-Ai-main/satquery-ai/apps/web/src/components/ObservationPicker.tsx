'use client';

import React, { useState, useMemo } from 'react';
import {
  Satellite,
  Calendar,
  Cloud,
  Check,
  CheckCircle2,
  X,
  Filter,
  Eye,
  Layers,
  ArrowRight,
  ShieldCheck,
  Sliders,
  Sparkles,
  Radio,
  Clock,
  Compass,
} from 'lucide-react';
import { useWorkspaceSafe } from '../context/WorkspaceContext';
import { SatelliteObservationItem, SearchEarthLocation } from '../types';

export interface ObservationPickerProps {
  observations?: SatelliteObservationItem[];
  location?: SearchEarthLocation | null;
  isOpen?: boolean;
  onClose?: () => void;
  onApplyMission?: (selectedObs: SatelliteObservationItem[]) => void;
  className?: string;
}

export const ObservationPicker: React.FC<ObservationPickerProps> = ({
  observations: propObservations,
  location: propLocation,
  isOpen: propIsOpen,
  onClose,
  onApplyMission,
  className = '',
}) => {
  const ws = useWorkspaceSafe();

  // Prefer props if provided, otherwise workspace state
  const isOpen = propIsOpen !== undefined ? propIsOpen : (ws?.isObservationPickerOpen ?? false);
  const observations = propObservations || ws?.stacObservations || [];
  const location = propLocation || ws?.searchLocationData || null;

  const [sensorFilter, setSensorFilter] = useState<'ALL' | 'SENTINEL-2' | 'SENTINEL-1'>('ALL');
  const [maxCloudTolerance, setMaxCloudTolerance] = useState<number>(35);
  const [previewObsId, setPreviewObsId] = useState<string | null>(null);

  // Close handler
  const handleClose = () => {
    if (onClose) {
      onClose();
    } else if (ws?.setIsObservationPickerOpen) {
      ws.setIsObservationPickerOpen(false);
    }
  };

  // Filter observations by sensor and cloud cover
  const filteredObservations = useMemo(() => {
    return observations.filter((obs) => {
      if (sensorFilter === 'SENTINEL-2' && !obs.sensor.includes('Sentinel-2')) return false;
      if (sensorFilter === 'SENTINEL-1' && !obs.sensor.includes('Sentinel-1')) return false;
      if (obs.modality === 'optical' && obs.cloudCoverPct > maxCloudTolerance) return false;
      return true;
    });
  }, [observations, sensorFilter, maxCloudTolerance]);

  if (!isOpen) return null;

  const selectedObservationIds = ws?.selectedObservationIds || [];
  const selectedCount = selectedObservationIds.length;

  const handleApplyMission = () => {
    const selectedObsList = observations.filter((obs) =>
      selectedObservationIds.includes(obs.id)
    );

    if (onApplyMission) {
      onApplyMission(selectedObsList);
    }

    handleClose();
  };

  return (
    <div
      id="observation-picker-modal"
      data-testid="observation-picker"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150 select-none"
    >
      <div
        id="observation-picker-container"
        className={`w-full max-w-4xl max-h-[92vh] flex flex-col bg-white rounded-3xl border border-[#E6E6E1] shadow-2xl overflow-hidden ${className}`}
      >
        {/* 1. Modal Header */}
        <div className="px-6 py-4 bg-[#FAF9F7] border-b border-[#E6E6E1] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#111111] text-white flex items-center justify-center shadow-sm">
              <Satellite className="w-5 h-5 text-satblue-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-[#111111]">
                  STAC Satellite Observation Picker
                </h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-satblue-50 text-satblue-700 border border-satblue-200">
                  COPERNICUS · AWS STAC v1.0.0
                </span>
              </div>
              <p className="text-xs text-[#6F6F6A] mt-0.5 font-mono">
                {location?.name || ws?.currentMission?.name || 'Active Mission'} · {location?.utmZone || ws?.currentMission?.utmZone || 'UTM Zone'} · {filteredObservations.length} Granules Retrieved
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              id="observation-picker-close-btn"
              onClick={handleClose}
              className="p-2 rounded-xl text-[#6F6F6A] hover:text-[#111111] hover:bg-[#EAEAE5] transition-colors"
              aria-label="Close Observation Picker"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 2. Filter Bar (Sensors & Cloud Cover) */}
        <div className="px-6 py-3 border-b border-[#F0EFEA] bg-white flex flex-wrap items-center justify-between gap-3">
          {/* Sensor Tabs */}
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-mono font-bold text-[#888888] uppercase mr-1">
              SENSOR MODALITY:
            </span>
            {(
              [
                { id: 'ALL', label: `ALL SENSORS (${observations.length})` },
                {
                  id: 'SENTINEL-2',
                  label: `SENTINEL-2 OPTICAL (${
                    observations.filter((o) => o.sensor.includes('Sentinel-2')).length
                  })`,
                },
                {
                  id: 'SENTINEL-1',
                  label: `SENTINEL-1 SAR (${
                    observations.filter((o) => o.sensor.includes('Sentinel-1')).length
                  })`,
                },
              ] as const
            ).map((tab) => (
              <button
                key={tab.id}
                id={`obs-filter-tab-${tab.id.toLowerCase()}`}
                onClick={() => setSensorFilter(tab.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all ${
                  sensorFilter === tab.id
                    ? 'bg-[#111111] text-white shadow-xs'
                    : 'bg-[#FAF9F7] text-[#6F6F6A] hover:text-[#111111] hover:bg-[#EBEBE6] border border-[#E6E6E1]'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Cloud Cover Slider Pill */}
          <div className="flex items-center gap-2.5 px-3 py-1 rounded-xl bg-[#FAF9F7] border border-[#E6E6E1] text-xs font-mono text-[#555555]">
            <Cloud className="w-3.5 h-3.5 text-[#888888]" />
            <span>Max Cloud Cover: <strong>{maxCloudTolerance}%</strong></span>
            <input
              id="obs-cloud-tolerance-slider"
              type="range"
              min="5"
              max="60"
              step="5"
              value={maxCloudTolerance}
              onChange={(e) => setMaxCloudTolerance(parseInt(e.target.value))}
              className="w-20 h-1.5 accent-[#111111] cursor-pointer"
            />
          </div>
        </div>

        {/* 3. Observations List Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3.5 bg-[#FAF9F7]/50">
          {filteredObservations.length === 0 ? (
            <div className="p-12 text-center space-y-2 bg-white rounded-2xl border border-[#E6E6E1]">
              <Cloud className="w-8 h-8 text-[#CCCCCC] mx-auto" />
              <h4 className="text-sm font-bold text-[#111111]">No Observations Match Filter</h4>
              <p className="text-xs text-[#6F6F6A] max-w-sm mx-auto">
                No scenes met the current cloud cover threshold ({maxCloudTolerance}%) or sensor filter. Increase the cloud slider to view more granules.
              </p>
            </div>
          ) : (
            filteredObservations.map((obs) => {
              const isIncludedInMission = selectedObservationIds.includes(obs.id);
              const dateT1 = ws?.dateT1 || 'Mar 14, 2024';
              const dateT2 = ws?.dateT2 || 'Mar 19, 2026';
              const isT1 = dateT1.includes(obs.dateFormatted) || obs.dateFormatted.includes(dateT1);
              const isT2 = dateT2.includes(obs.dateFormatted) || obs.dateFormatted.includes(dateT2);
              const isOptical = obs.modality === 'optical';
              const isSar = obs.modality === 'sar';

              return (
                <div
                  key={obs.id}
                  id={`observation-card-${obs.id}`}
                  className={`p-4 rounded-2xl border transition-all ${
                    isIncludedInMission
                      ? 'bg-white border-[#111111] shadow-md ring-1 ring-black/5'
                      : 'bg-white border-[#E6E6E1] hover:border-[#CCCCCC]'
                  }`}
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                    {/* Left Column: Metadata */}
                    <div className="space-y-1.5">
                      {/* Badges strip */}
                      <div className="flex items-center gap-2 flex-wrap">
                        {/* Sensor Tag */}
                        <span
                          className={`px-2.5 py-0.5 rounded-lg text-[10px] font-mono font-bold ${
                            isSar
                              ? 'bg-satblue-100 text-satblue-900 border border-satblue-200'
                              : isOptical
                              ? 'bg-emerald-100 text-emerald-900 border border-emerald-200'
                              : 'bg-amber-100 text-amber-900 border border-amber-200'
                          }`}
                        >
                          {obs.sensor}
                        </span>

                        {/* Modality Label */}
                        <span className="text-[10px] font-mono text-[#6F6F6A] uppercase">
                          {isSar ? 'Active C-Band SAR' : 'Multispectral Optical'}
                        </span>

                        {/* Role Flags */}
                        {isT1 && (
                          <span className="px-2 py-0.5 rounded-lg text-[9px] font-mono font-bold bg-satblue-600 text-white shadow-xs">
                            CURRENT T1 BASELINE
                          </span>
                        )}
                        {isT2 && (
                          <span className="px-2 py-0.5 rounded-lg text-[9px] font-mono font-bold bg-emerald-700 text-white shadow-xs">
                            CURRENT T2 TARGET
                          </span>
                        )}
                      </div>

                      {/* Title & Date */}
                      <div className="flex items-center gap-3">
                        <h4 className="text-sm font-bold text-[#111111]">{obs.title}</h4>
                      </div>

                      {/* Core Metadata Items */}
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs font-mono text-[#555555]">
                        {/* Acquisition Date */}
                        <div className="flex items-center gap-1 text-[#111111] font-semibold">
                          <Calendar className="w-3.5 h-3.5 text-satblue-600" />
                          <span>Acquisition: {obs.dateFormatted}</span>
                        </div>

                        {/* Cloud Cover Metadata */}
                        {isOptical ? (
                          <div className="flex items-center gap-1">
                            <Cloud className="w-3.5 h-3.5 text-[#888888]" />
                            <span
                              className={`font-semibold ${
                                obs.cloudCoverPct < 10
                                  ? 'text-emerald-700'
                                  : obs.cloudCoverPct < 25
                                  ? 'text-amber-700'
                                  : 'text-red-700'
                              }`}
                            >
                              Cloud Cover: {obs.cloudCoverPct}%
                            </span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1 text-satblue-700 font-semibold">
                            <Radio className="w-3.5 h-3.5 text-satblue-600" />
                            <span>0.0% Cloud (All-Weather SAR)</span>
                          </div>
                        )}

                        {/* Orbit & Track */}
                        <div className="flex items-center gap-1 text-[#6F6F6A]">
                          <Clock className="w-3.5 h-3.5 text-[#888888]" />
                          <span>{obs.orbit}</span>
                        </div>

                        {/* Resolution */}
                        <div className="text-[#6F6F6A]">
                          Resolution: <strong>{obs.resolution}</strong>
                        </div>
                      </div>

                      {/* Bands & Processing Level */}
                      <div className="flex items-center gap-1.5 flex-wrap pt-0.5">
                        <span className="text-[10px] font-mono text-[#888888]">Bands:</span>
                        {obs.bands.map((band) => (
                          <span
                            key={band}
                            className="px-2 py-0.5 rounded bg-[#F4F4F0] text-[10px] font-mono text-[#444444] border border-[#E6E6E1]"
                          >
                            {band}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Right Column: Toggle Controls to Build Mission */}
                    <div className="flex flex-row md:flex-col items-end justify-between gap-2 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-[#F0EFEA]">
                      {/* Quality Score */}
                      <span className="text-[10px] font-mono font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                        {obs.qualityScore}% Q-Score
                      </span>

                      {/* Action & Toggle Buttons */}
                      <div className="flex items-center gap-1.5 flex-wrap justify-end">
                        {/* Toggle as T1 Button */}
                        <button
                          id={`btn-set-t1-${obs.id}`}
                          type="button"
                          onClick={() => ws?.applyObservationAsT1?.(obs)}
                          className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all ${
                            isT1
                              ? 'bg-satblue-600 text-white shadow-xs'
                              : 'bg-[#F0EFEA] hover:bg-[#E2E1DC] text-[#333333]'
                          }`}
                          title="Set this observation as T1 baseline scene"
                        >
                          {isT1 ? '✓ T1 Baseline' : 'Set as T1'}
                        </button>

                        {/* Toggle as T2 Button */}
                        <button
                          id={`btn-set-t2-${obs.id}`}
                          type="button"
                          onClick={() => ws?.applyObservationAsT2?.(obs)}
                          className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all ${
                            isT2
                              ? 'bg-emerald-700 text-white shadow-xs'
                              : 'bg-[#F0EFEA] hover:bg-[#E2E1DC] text-[#333333]'
                          }`}
                          title="Set this observation as T2 target scene"
                        >
                          {isT2 ? '✓ T2 Target' : 'Set as T2'}
                        </button>

                        {/* Toggle Active Scene View in Canvas */}
                        <button
                          id={`btn-view-${obs.id}`}
                          type="button"
                          onClick={() => {
                            if (isSar) {
                              ws?.setActiveLens?.('SAR');
                            } else {
                              ws?.setActiveLens?.('True Color');
                            }
                          }}
                          className="p-1.5 rounded-lg bg-[#FAF9F7] hover:bg-[#EAEAE5] text-[#333333] border border-[#E6E6E1] transition-colors"
                          title="Preview scene in map canvas"
                        >
                          <Eye className="w-3.5 h-3.5 text-[#555555]" />
                        </button>

                        {/* Toggle In Mission Package */}
                        <button
                          id={`btn-toggle-mission-${obs.id}`}
                          type="button"
                          onClick={() => ws?.toggleObservationInMission?.(obs)}
                          className={`flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                            isIncludedInMission
                              ? 'bg-[#111111] text-white shadow-xs'
                              : 'bg-white border border-[#CCCCCC] text-[#444444] hover:border-[#111111]'
                          }`}
                          title="Toggle observation inclusion in mission dataset package"
                        >
                          {isIncludedInMission ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-400 stroke-[3]" />
                              <span>In Mission</span>
                            </>
                          ) : (
                            <span>+ Add to Mission</span>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* 4. Bottom Mission Builder Summary & Commit Bar */}
        <div className="px-6 py-4 bg-[#FAF9F7] border-t border-[#E6E6E1] flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#111111]">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>
                Configured Mission Package: <strong>{selectedCount} Scenes Included</strong>
              </span>
            </div>
            <p className="text-[11px] font-mono text-[#6F6F6A]">
              T1 Baseline: <strong>{ws?.dateT1 || 'Mar 14, 2024'}</strong> · T2 Target: <strong>{ws?.dateT2 || 'Mar 19, 2026'}</strong> · Active AOI: <strong>{location?.name || ws?.currentMission?.name || 'Active AOI'}</strong>
            </p>
          </div>

          <div className="flex items-center gap-2.5 w-full sm:w-auto justify-end">
            <button
              id="observation-picker-cancel-btn"
              type="button"
              onClick={handleClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-[#555555] hover:text-[#111111] hover:bg-[#EAEAE5] transition-colors"
            >
              Close
            </button>

            <button
              id="observation-picker-apply-btn"
              type="button"
              onClick={handleApplyMission}
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2 rounded-xl bg-[#111111] hover:bg-[#2A2A2A] text-white text-xs font-semibold shadow-md transition-all"
            >
              <span>Build & Commit Mission</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
