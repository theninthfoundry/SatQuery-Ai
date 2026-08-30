'use client';

import React, { useState } from 'react';
import { MissionWorkspace } from '../components/MissionWorkspace';
import { Header } from '../components/Header';
import { UploadZone } from '../components/UploadZone';
import { ImageViewer } from '../components/ImageViewer';
import { ChangeViewer } from '../components/ChangeViewer';
import { OpticalSARViewer } from '../components/OpticalSARViewer';
import { MetadataPanel } from '../components/MetadataPanel';
import { ValidationPanel } from '../components/ValidationPanel';
import { QueryConsole } from '../components/QueryConsole';
import { AgentChatConsole } from '../components/AgentChatConsole';
import { EvidenceCard } from '../components/EvidenceCard';
import { ChangeMetricsCard } from '../components/ChangeMetricsCard';
import { CorroborationCard } from '../components/CorroborationCard';
import {
  HealthResponse,
  ImageInspectionResponse,
  VQAAnalysisResult,
  GroundingAnalysisResult,
  ChangeAnalysisResult,
  OpticalSARAnalysisResult,
  AgentQueryResponse,
  EvidenceObject,
  GroundingFeature,
  ImageSummary,
} from '../types';
import { fetchHealth, fetchImagesList } from '../lib/api';
import { Satellite, Bot, Layers, Sparkles, LayoutDashboard, Terminal } from 'lucide-react';

export default function Home() {
  const [viewMode, setViewMode] = useState<'mission_workspace' | 'deep_diagnostics'>('mission_workspace');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [inspectionData, setInspectionData] = useState<ImageInspectionResponse | null>(null);
  const [imagesList, setImagesList] = useState<ImageSummary[]>([]);
  const [activeEvidence, setActiveEvidence] = useState<EvidenceObject | null>(null);
  const [groundingFeatures, setGroundingFeatures] = useState<GroundingFeature[]>([]);
  const [changeResult, setChangeResult] = useState<ChangeAnalysisResult | null>(null);
  const [opticalSARResult, setOpticalSARResult] = useState<OpticalSARAnalysisResult | null>(null);

  React.useEffect(() => {
    fetchHealth().then(setHealth);
    fetchImagesList().then(setImagesList);
  }, []);

  const handleInspectionComplete = (data: ImageInspectionResponse) => {
    setInspectionData(data);
    setActiveEvidence(null);
    setGroundingFeatures([]);
    setChangeResult(null);
    setOpticalSARResult(null);
    fetchImagesList().then(setImagesList);
  };

  const handleAgentQueryResult = (res: AgentQueryResponse) => {
    setActiveEvidence(res.evidence);
    const intent = res.intent;

    if (intent === 'grounding') {
      const feats = res.pipeline_result?.regions_geojson?.features || [];
      setGroundingFeatures(feats);
      setChangeResult(null);
      setOpticalSARResult(null);
    } else if (intent === 'change_detection') {
      setChangeResult(res.pipeline_result);
      setGroundingFeatures([]);
      setOpticalSARResult(null);
    } else if (intent === 'optical_sar_fusion') {
      setOpticalSARResult(res.pipeline_result);
      setGroundingFeatures([]);
      setChangeResult(null);
    } else {
      setGroundingFeatures([]);
      setChangeResult(null);
      setOpticalSARResult(null);
    }
  };

  return (
    <div className="relative">
      {/* View Switcher Bar */}
      <div className="absolute top-2.5 right-64 z-50 flex items-center bg-neutral-900 border border-neutral-800 rounded-lg p-0.5 shadow-xl">
        <button
          onClick={() => setViewMode('mission_workspace')}
          className={`flex items-center gap-1.5 px-3 py-1 text-xs rounded-md font-medium transition-colors ${
            viewMode === 'mission_workspace'
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
              : 'text-neutral-400 hover:text-neutral-200'
          }`}
        >
          <LayoutDashboard className="w-3.5 h-3.5" />
          Mission Workspace
        </button>
        <button
          onClick={() => setViewMode('deep_diagnostics')}
          className={`flex items-center gap-1.5 px-3 py-1 text-xs rounded-md font-medium transition-colors ${
            viewMode === 'deep_diagnostics'
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
              : 'text-neutral-400 hover:text-neutral-200'
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          Diagnostics & Ingestion
        </button>
      </div>

      {viewMode === 'mission_workspace' ? (
        <MissionWorkspace />
      ) : (
        <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col font-sans">
          <Header health={health} />

          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
            <div className="flex items-center justify-between border-b border-neutral-800 pb-4">
              <div>
                <h1 className="text-xl font-bold tracking-tight text-neutral-100">SatQuery AI — Perception & Ingestion Console</h1>
                <p className="text-sm text-neutral-400 mt-0.5">
                  Multimodal Remote Sensing Vision-Language Assistant (SIH26167 · ISRO)
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="space-y-6">
                <UploadZone onInspectionComplete={handleInspectionComplete} />
                {inspectionData && <MetadataPanel inspection={inspectionData} />}
                {inspectionData && <ValidationPanel inspection={inspectionData} />}
              </div>

              <div className="lg:col-span-2 space-y-6">
                {changeResult ? (
                  <ChangeViewer result={changeResult} />
                ) : opticalSARResult ? (
                  <OpticalSARViewer result={opticalSARResult} />
                ) : (
                  <ImageViewer inspection={inspectionData} groundingFeatures={groundingFeatures} />
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {changeResult && <ChangeMetricsCard result={changeResult} />}
                  {opticalSARResult && <CorroborationCard result={opticalSARResult} />}
                </div>

                <div className="border border-neutral-800 rounded-xl p-5 bg-neutral-900/60 shadow-xl space-y-4">
                  <div className="flex items-center gap-2 border-b border-neutral-800 pb-3">
                    <Bot className="w-5 h-5 text-cyan-400" />
                    <h3 className="font-semibold text-neutral-200">Autonomous Agent Orchestrator</h3>
                  </div>
                  <AgentChatConsole
                    activeImageId={inspectionData?.id}
                    onQueryResult={handleAgentQueryResult}
                  />
                </div>

                {activeEvidence && <EvidenceCard evidence={activeEvidence} />}
              </div>
            </div>
          </main>
        </div>
      )}
    </div>
  );
}
