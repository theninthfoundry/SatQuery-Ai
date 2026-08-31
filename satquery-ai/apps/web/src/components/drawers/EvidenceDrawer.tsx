'use client';

import React, { useState } from 'react';
import {
  X,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  FileText,
  Map,
  Table,
  Sparkles,
  Download,
  CheckCircle2,
} from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface EvidenceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({ isOpen, onClose }) => {
  const ws = useWorkspace();
  const [expandedId, setExpandedId] = useState<string | null>('temporal');
  const [showWhyThisAnswer, setShowWhyThisAnswer] = useState<boolean>(true);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-[450px] bg-white border-l border-[#E6E6E1] shadow-2xl flex flex-col transition-transform duration-300 animate-in slide-in-from-right select-none">
      {/* Header */}
      <div className="h-14 px-6 border-b border-[#E6E6E1] flex items-center justify-between bg-[#FAF9F7]">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#111111]" />
            <h2 className="text-xs font-bold tracking-tight text-[#111111] uppercase font-mono">
              EVIDENCE
            </h2>
          </div>
          <p className="text-[10px] text-[#6F6F6A]">Why does SatQuery believe this?</p>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-[#6F6F6A] hover:text-[#111111] hover:bg-[#EAEAE5] transition-colors"
          aria-label="Close Evidence Drawer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Composite Concordance Score */}
        <div className="p-4 rounded-2xl bg-[#FAF9F7] border border-[#E6E6E1] space-y-2">
          <div className="flex items-center justify-between font-mono">
            <span className="text-[10px] font-bold tracking-wider text-[#6F6F6A] uppercase">
              EVIDENCE SCORE
            </span>
            <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-md border border-emerald-200">
              {ws.evidenceScore}% CONCORDANCE
            </span>
          </div>
          <div className="w-full bg-[#EAEAE5] h-2 rounded-full overflow-hidden">
            <div
              className="bg-emerald-600 h-full rounded-full transition-all duration-500"
              style={{ width: `${ws.evidenceScore}%` }}
            />
          </div>
          <p className="text-[11px] text-[#6F6F6A] font-mono leading-relaxed">
            Platt-calibrated multimodal corroboration across dual-optical spectral divergence and Sentinel-1 C-band backscatter.
          </p>
        </div>

        {/* Structured 4-Part Evidence Stack */}
        <div className="space-y-3">
          <span className="text-[10px] font-mono font-bold tracking-wider text-[#888888] uppercase block">
            CORROBORATION FACTORS
          </span>

          <div className="space-y-3">
            {/* 01 Temporal Change */}
            <div className="rounded-2xl border border-[#E6E6E1] bg-white overflow-hidden shadow-xs">
              <button
                onClick={() => {
                  setExpandedId(expandedId === 'temporal' ? null : 'temporal');
                  ws.setActiveLens('CHANGE');
                }}
                className="w-full p-4 flex items-center justify-between hover:bg-[#FAF9F7] transition-colors text-left"
              >
                <div className="space-y-0.5">
                  <div className="text-[10px] font-mono font-bold text-[#888888]">01 TEMPORAL CHANGE</div>
                  <h4 className="text-xs font-bold text-[#111111]">Siamese ChangeNet</h4>
                  <div className="w-48 bg-[#EAEAE5] h-1.5 rounded-full overflow-hidden mt-1.5">
                    <div className="bg-emerald-600 h-full rounded-full" style={{ width: '94%' }} />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-mono font-bold text-[#111111]">94%</span>
                  {expandedId === 'temporal' ? (
                    <ChevronUp className="w-4 h-4 text-[#888888]" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-[#888888]" />
                  )}
                </div>
              </button>
              {expandedId === 'temporal' && (
                <div className="px-4 pb-4 pt-1 border-t border-[#F0EFEA] bg-[#FAF9F7] space-y-1.5 text-[11px] font-mono text-[#555555]">
                  <p><strong>Model:</strong> 2D Sigmoid Siamese CNN (mIoU: 0.78)</p>
                  <p><strong>Detected Alteration:</strong> 25,600 m² (2 distinct clusters)</p>
                  <p><strong>Threshold:</strong> Sigmoid activation &gt; 0.50</p>
                </div>
              )}
            </div>

            {/* 02 Optical */}
            <div className="rounded-2xl border border-[#E6E6E1] bg-white overflow-hidden shadow-xs">
              <button
                onClick={() => {
                  setExpandedId(expandedId === 'optical' ? null : 'optical');
                  ws.setActiveLens('True Color');
                }}
                className="w-full p-4 flex items-center justify-between hover:bg-[#FAF9F7] transition-colors text-left"
              >
                <div className="space-y-0.5">
                  <div className="text-[10px] font-mono font-bold text-[#888888]">02 OPTICAL</div>
                  <h4 className="text-xs font-bold text-[#111111]">Sentinel-2 Spectral Analysis</h4>
                  <div className="w-48 bg-[#EAEAE5] h-1.5 rounded-full overflow-hidden mt-1.5">
                    <div className="bg-emerald-600 h-full rounded-full" style={{ width: '88%' }} />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-mono font-bold text-[#111111]">88%</span>
                  {expandedId === 'optical' ? (
                    <ChevronUp className="w-4 h-4 text-[#888888]" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-[#888888]" />
                  )}
                </div>
              </button>
              {expandedId === 'optical' && (
                <div className="px-4 pb-4 pt-1 border-t border-[#F0EFEA] bg-[#FAF9F7] space-y-1.5 text-[11px] font-mono text-[#555555]">
                  <p><strong>Source:</strong> Sentinel-2 MSI Surface Reflectance</p>
                  <p><strong>Divergence:</strong> |NDWI_T2 - NDWI_T1| &gt; 0.35 confirmed</p>
                  <p><strong>Bands:</strong> B04 (Red), B03 (Green), B08 (NIR)</p>
                </div>
              )}
            </div>

            {/* 03 SAR */}
            <div className="rounded-2xl border border-[#E6E6E1] bg-white overflow-hidden shadow-xs">
              <button
                onClick={() => {
                  setExpandedId(expandedId === 'sar' ? null : 'sar');
                  ws.setActiveLens('SAR');
                }}
                className="w-full p-4 flex items-center justify-between hover:bg-[#FAF9F7] transition-colors text-left"
              >
                <div className="space-y-0.5">
                  <div className="text-[10px] font-mono font-bold text-[#888888]">03 SAR RADAR</div>
                  <h4 className="text-xs font-bold text-[#111111]">Sentinel-1 C-band Backscatter</h4>
                  <div className="w-48 bg-[#EAEAE5] h-1.5 rounded-full overflow-hidden mt-1.5">
                    <div className="bg-emerald-600 h-full rounded-full" style={{ width: '91%' }} />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-mono font-bold text-[#111111]">91%</span>
                  {expandedId === 'sar' ? (
                    <ChevronUp className="w-4 h-4 text-[#888888]" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-[#888888]" />
                  )}
                </div>
              </button>
              {expandedId === 'sar' && (
                <div className="px-4 pb-4 pt-1 border-t border-[#F0EFEA] bg-[#FAF9F7] space-y-1.5 text-[11px] font-mono text-[#555555]">
                  <p><strong>Sensor:</strong> Sentinel-1 C-SAR IW GRD (Dual-Pol VV/VH)</p>
                  <p><strong>Backscatter Value:</strong> -14.5 dB σ⁰</p>
                  <p><strong>Concordance:</strong> Radar roughness corroborates built-up expansion</p>
                </div>
              )}
            </div>

            {/* 04 Registration */}
            <div className="rounded-2xl border border-[#E6E6E1] bg-white overflow-hidden shadow-xs">
              <button
                onClick={() => setExpandedId(expandedId === 'registration' ? null : 'registration')}
                className="w-full p-4 flex items-center justify-between hover:bg-[#FAF9F7] transition-colors text-left"
              >
                <div className="space-y-0.5">
                  <div className="text-[10px] font-mono font-bold text-[#888888]">04 REGISTRATION</div>
                  <h4 className="text-xs font-bold text-[#111111]">Spatial Compatibility & Alignment</h4>
                  <div className="w-48 bg-[#EAEAE5] h-1.5 rounded-full overflow-hidden mt-1.5">
                    <div className="bg-emerald-600 h-full rounded-full" style={{ width: '96%' }} />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-mono font-bold text-[#111111]">96%</span>
                  {expandedId === 'registration' ? (
                    <ChevronUp className="w-4 h-4 text-[#888888]" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-[#888888]" />
                  )}
                </div>
              </button>
              {expandedId === 'registration' && (
                <div className="px-4 pb-4 pt-1 border-t border-[#F0EFEA] bg-[#FAF9F7] space-y-1.5 text-[11px] font-mono text-[#555555]">
                  <p><strong>Native GSD:</strong> 10m Ground Sample Distance</p>
                  <p><strong>Projected CRS:</strong> EPSG:32643 (UTM Zone 43N)</p>
                  <p><strong>Keypoint Alignment:</strong> ORB / RANSAC inlier ratio &gt; 95%</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Why This Answer (Provenance Timeline) */}
        <div className="rounded-2xl border border-[#E6E6E1] bg-white overflow-hidden">
          <button
            onClick={() => setShowWhyThisAnswer((prev) => !prev)}
            className="w-full p-4 flex items-center justify-between hover:bg-[#FAF9F7] transition-colors"
          >
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#111111]" />
              <span className="text-xs font-bold text-[#111111]">Why This Answer? (Provenance Timeline)</span>
            </div>
            {showWhyThisAnswer ? (
              <ChevronUp className="w-4 h-4 text-[#6F6F6A]" />
            ) : (
              <ChevronDown className="w-4 h-4 text-[#6F6F6A]" />
            )}
          </button>

          {showWhyThisAnswer && (
            <div className="p-4 border-t border-[#F0EFEA] bg-[#FAF9F7] space-y-3.5 text-xs">
              <div className="space-y-3 font-mono text-[11px] text-[#555555]">
                <div className="flex items-start gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-[#111111] text-white flex items-center justify-center text-[10px] shrink-0 mt-0.5">
                    1
                  </span>
                  <div>
                    <strong className="text-[#111111]">Input Compatibility:</strong> Optical T1/T2 + SAR rasters verified on disk (10m GSD).
                  </div>
                </div>

                <div className="flex items-start gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-[#111111] text-white flex items-center justify-center text-[10px] shrink-0 mt-0.5">
                    2
                  </span>
                  <div>
                    <strong className="text-[#111111]">Spatial Registration:</strong> ORB / RANSAC confirms sub-pixel spatial alignment (IoU: 0.95).
                  </div>
                </div>

                <div className="flex items-start gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-[#111111] text-white flex items-center justify-center text-[10px] shrink-0 mt-0.5">
                    3
                  </span>
                  <div>
                    <strong className="text-[#111111]">Siamese ChangeNet:</strong> 2D Sigmoid CNN detects altered surface clusters above 0.50 threshold.
                  </div>
                </div>

                <div className="flex items-start gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-[#111111] text-white flex items-center justify-center text-[10px] shrink-0 mt-0.5">
                    4
                  </span>
                  <div>
                    <strong className="text-[#111111]">SAR Corroboration:</strong> Sentinel-1 -14.5 dB backscatter confirms built-up expansion.
                  </div>
                </div>

                <div className="flex items-start gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-[#111111] text-white flex items-center justify-center text-[10px] shrink-0 mt-0.5">
                    5
                  </span>
                  <div className="p-2.5 rounded-xl bg-white border border-[#E6E6E1] space-y-1 w-full mt-1">
                    <div className="text-[10px] text-[#888888] font-bold uppercase">GEOSPATIAL AREA ENGINE</div>
                    <p>Pixels detected: <strong>2,560</strong></p>
                    <p>Native GSD: <strong>10m</strong></p>
                    <p>Projected CRS: <strong>EPSG:32643 (UTM 43N)</strong></p>
                    <p>Calculated Area: <strong className="text-[#111111]">25,600 m² (2.56 ha)</strong></p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 1-Click Export Dossier Actions */}
        <div className="space-y-2.5 pt-2">
          <span className="text-[10px] font-mono font-bold tracking-wider text-[#6F6F6A] uppercase block">
            EXPORT MISSION DOSSIER
          </span>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => ws.openExport('pdf')}
              className="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl border border-[#E6E6E1] bg-white hover:bg-[#FAF9F7] text-xs font-semibold text-[#111111] transition-all"
            >
              <FileText className="w-3.5 h-3.5 text-rose-600" />
              <span>PDF</span>
            </button>
            <button
              onClick={() => ws.openExport('geojson')}
              className="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl border border-[#E6E6E1] bg-white hover:bg-[#FAF9F7] text-xs font-semibold text-[#111111] transition-all"
            >
              <Map className="w-3.5 h-3.5 text-emerald-600" />
              <span>GeoJSON</span>
            </button>
            <button
              onClick={() => ws.openExport('csv')}
              className="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl border border-[#E6E6E1] bg-white hover:bg-[#FAF9F7] text-xs font-semibold text-[#111111] transition-all"
            >
              <Table className="w-3.5 h-3.5 text-sky-600" />
              <span>CSV</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
