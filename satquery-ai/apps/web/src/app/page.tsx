'use client';

import React, { useState, useEffect } from 'react';
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
import { Satellite, Bot, Layers, Sparkles } from 'lucide-react';

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [inspectionData, setInspectionData] = useState<ImageInspectionResponse | null>(null);
  const [imagesList, setImagesList] = useState<ImageSummary[]>([]);
  const [activeEvidence, setActiveEvidence] = useState<EvidenceObject | null>(null);
  const [groundingFeatures, setGroundingFeatures] = useState<GroundingFeature[]>([]);
  const [changeResult, setChangeResult] = useState<ChangeAnalysisResult | null>(null);
  const [opticalSARResult, setOpticalSARResult] = useState<OpticalSARAnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchHealth().then(setHealth);
    fetchImagesList().then(setImagesList);
    const interval = setInterval(() => {
      fetchHealth().then(setHealth);
      fetchImagesList().then(setImagesList);
    }, 15000);
    return () => clearInterval(interval);
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

  const handleVQASuccess = (res: VQAAnalysisResult) => {
    setActiveEvidence(res.evidence);
    setGroundingFeatures([]);
    setChangeResult(null);
    setOpticalSARResult(null);
  };

  const handleGroundingSuccess = (res: GroundingAnalysisResult) => {
    setActiveEvidence(res.evidence);
    setGroundingFeatures(res.regions_geojson.features || []);
    setChangeResult(null);
    setOpticalSARResult(null);
  };

  const handleChangeSuccess = (res: ChangeAnalysisResult) => {
    setActiveEvidence(res.evidence);
    setGroundingFeatures([]);
    setChangeResult(res);
    setOpticalSARResult(null);
  };

  const handleOpticalSARSuccess = (res: OpticalSARAnalysisResult) => {
    setActiveEvidence(res.evidence);
    setGroundingFeatures([]);
    setChangeResult(null);
    setOpticalSARResult(res);
  };

  const allImageIds = imagesList.map((img) => img.id);

  return (
    <div className="min-h-screen flex flex-col">
      <Header health={health} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Upload Area */}
        <UploadZone
          onInspectionComplete={handleInspectionComplete}
          isLoading={isLoading}
          setIsLoading={setIsLoading}
        />

        {/* Dynamic Display Grid */}
        {inspectionData && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Col: Dynamic Viewer (Single / Change / Optical-SAR) & Agent Chat */}
            <div className="lg:col-span-6 space-y-6">
              {opticalSARResult ? (
                <OpticalSARViewer
                  opticalPreviewUrl={`/api/v1/images/${opticalSARResult.optical_image_id}/preview`}
                  sarPreviewUrl={`/api/v1/images/${opticalSARResult.sar_image_id}/preview`}
                  fusionResult={opticalSARResult}
                />
              ) : changeResult ? (
                <ChangeViewer
                  beforePreviewUrl={`/api/v1/images/${changeResult.image_before_id}/preview`}
                  afterPreviewUrl={`/api/v1/images/${changeResult.image_after_id}/preview`}
                  changeResult={changeResult}
                />
              ) : (
                <ImageViewer
                  preview={inspectionData.preview}
                  metadata={inspectionData.metadata}
                  groundingFeatures={groundingFeatures}
                />
              )}

              {/* Unified Agent Chat Console */}
              <AgentChatConsole
                currentImageId={inspectionData.id}
                allImageIds={allImageIds}
                onQueryResult={handleAgentQueryResult}
              />

              {/* Manual Toolchain Fallback Console */}
              <QueryConsole
                currentImageId={inspectionData.id}
                onVQASuccess={handleVQASuccess}
                onGroundingSuccess={handleGroundingSuccess}
                onChangeSuccess={handleChangeSuccess}
                onOpticalSARSuccess={handleOpticalSARSuccess}
              />

              <ValidationPanel validation={inspectionData.validation} />
            </div>

            {/* Right Col: Corroboration / Change Metrics / Evidence Card / Metadata */}
            <div className="lg:col-span-6 space-y-6">
              {/* Corroboration Card (Optical + SAR) */}
              {opticalSARResult && <CorroborationCard result={opticalSARResult} />}

              {/* Change Metrics Card (Bi-temporal) */}
              {changeResult && <ChangeMetricsCard result={changeResult} />}

              {/* Verifiable Evidence Card */}
              {activeEvidence && <EvidenceCard evidence={activeEvidence} />}

              {/* Metadata Panel */}
              {inspectionData.metadata ? (
                <MetadataPanel metadata={inspectionData.metadata} />
              ) : (
                <div className="bg-space-900 border border-space-700/80 rounded-xl p-8 text-center text-slate-400">
                  <p className="text-sm">Metadata unavailable for invalid raster.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Empty State Banner */}
        {!inspectionData && !isLoading && (
          <div className="border border-space-800 bg-space-900/40 rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-4 text-slate-400 text-xs shadow-md">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-space-800 rounded-lg text-satblue-400">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <p className="font-semibold text-slate-300">Phase 4 Agentic Orchestrator & Dossier Exporter Ready</p>
                <p className="text-slate-400">
                  Natural language intent routing, deterministic toolchain dispatch, and downloadable PDF / GeoJSON / CSV audit dossiers.
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 font-mono">
              <span className="px-2.5 py-1 rounded bg-space-800 border border-space-700 text-slate-300">
                Agent Orchestrator
              </span>
              <span className="px-2.5 py-1 rounded bg-space-800 border border-space-700 text-slate-300">
                PDF / GeoJSON / CSV
              </span>
              <span className="px-2.5 py-1 rounded bg-space-800 border border-space-700 text-slate-300">
                Observable Trace
              </span>
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-space-800 bg-space-950/80 py-4 text-center text-xs text-slate-500 font-mono">
        <span>SatQuery AI — ISRO Remote Sensing Vision-Language Assistant &bull; Phase 4 Complete</span>
      </footer>
    </div>
  );
}
