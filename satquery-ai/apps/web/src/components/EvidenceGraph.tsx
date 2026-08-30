'use client';

import React from 'react';
import { Bot, Layers, MapPin, Ruler, CheckCircle2, ShieldCheck, ArrowRight } from 'lucide-react';
import { EvidenceObject } from '../types';

interface EvidenceGraphProps {
  evidence?: EvidenceObject | null;
  changePercent?: number;
  areaHa?: string | number;
  reliabilityScore?: number;
}

export function EvidenceGraph({
  evidence,
  changePercent = 12.5,
  areaHa = '2.56',
  reliabilityScore = 87,
}: EvidenceGraphProps) {
  return (
    <div className="border border-neutral-800 rounded-xl p-5 bg-neutral-900/60 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          <h3 className="font-semibold text-neutral-200 text-sm">Interactive Evidence Graph (DAG)</h3>
        </div>
        <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded">
          <ShieldCheck className="w-3.5 h-3.5" />
          Auditable Provenance
        </span>
      </div>

      <p className="text-xs text-neutral-400 leading-relaxed">
        SatQuery links every natural-language finding through an immutable Directed Acyclic Graph connecting raw sensor inputs to neural inference and deterministic geospatial calculations.
      </p>

      {/* DAG Visualization Nodes */}
      <div className="relative py-4 flex flex-col md:flex-row items-center justify-between gap-3 overflow-x-auto">
        {/* Node 1: Sensor Inputs */}
        <div className="flex-1 w-full border border-neutral-800 rounded-lg p-3 bg-neutral-950/80 shadow-md">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] uppercase font-mono text-neutral-500">Node 01 · Sensor Assets</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <p className="text-xs font-semibold text-neutral-200">Optical + SAR Pair</p>
          <p className="text-[10px] font-mono text-neutral-500 mt-1">Sentinel-2 (10m) · S1 C-band</p>
        </div>

        <ArrowRight className="hidden md:block w-4 h-4 text-neutral-600 shrink-0" />

        {/* Node 2: Neural Perception */}
        <div className="flex-1 w-full border border-neutral-800 rounded-lg p-3 bg-neutral-950/80 shadow-md">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] uppercase font-mono text-neutral-500">Node 02 · Perception</span>
            <Bot className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <p className="text-xs font-semibold text-neutral-200">Siamese ChangeNet</p>
          <p className="text-[10px] font-mono text-neutral-500 mt-1">2D Tensor: {changePercent}% Altered</p>
        </div>

        <ArrowRight className="hidden md:block w-4 h-4 text-neutral-600 shrink-0" />

        {/* Node 3: Deterministic Geometry */}
        <div className="flex-1 w-full border border-neutral-800 rounded-lg p-3 bg-neutral-950/80 shadow-md">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] uppercase font-mono text-neutral-500">Node 03 · Geometry</span>
            <Ruler className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <p className="text-xs font-semibold text-neutral-200">Affine Reprojection</p>
          <p className="text-[10px] font-mono text-neutral-500 mt-1">UTM Zone 43N · {areaHa} ha</p>
        </div>

        <ArrowRight className="hidden md:block w-4 h-4 text-neutral-600 shrink-0" />

        {/* Node 4: Verified Evidence */}
        <div className="flex-1 w-full border border-cyan-500/40 rounded-lg p-3 bg-cyan-500/5 shadow-md">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] uppercase font-mono text-cyan-400">Node 04 · Synthesis</span>
            <MapPin className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <p className="text-xs font-semibold text-cyan-200">Auditable Dossier</p>
          <p className="text-[10px] font-mono text-cyan-400/80 mt-1">Reliability Index: {reliabilityScore}%</p>
        </div>
      </div>
    </div>
  );
}
