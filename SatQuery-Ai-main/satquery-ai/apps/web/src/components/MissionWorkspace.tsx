'use client';

import React, { useState, useEffect } from 'react';
import { TopHeader } from './shell/TopHeader';
import { GeoWorkspace } from './map/GeoWorkspace';
import { QueryBar } from './query/QueryBar';
import { AgentExecution } from './query/AgentExecution';
import { SceneDrawer } from './drawers/SceneDrawer';
import { EvidenceDrawer } from './drawers/EvidenceDrawer';
import { TraceDrawer } from './drawers/TraceDrawer';
import { LayersDrawer } from './drawers/LayersDrawer';
import { ChatAssistantDrawer } from './drawers/ChatAssistantDrawer';
import { AnalysesDrawer } from './drawers/AnalysesDrawer';
import { ReportExportModal } from './ReportExportModal';
import { AOIImportModal } from './modals/AOIImportModal';
import { SystemHubModal } from './modals/SystemHubModal';
import { ObservationPicker } from './ObservationPicker';
import { WorkspaceProvider, useWorkspace } from '../context/WorkspaceContext';

interface MissionWorkspaceProps {
  onSwitchToDiagnostics?: () => void;
  onSwitchToReports?: () => void;
}

function MissionWorkspaceInner({
  onSwitchToDiagnostics,
  onSwitchToReports,
}: MissionWorkspaceProps) {
  const ws = useWorkspace();
  const [isSystemHubOpen, setIsSystemHubOpen] = useState(false);
  const [isAOIModalOpen, setIsAOIModalOpen] = useState(false);

  // Global Keyboard Navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore when focused in text input
      const target = document.activeElement as HTMLElement | null;
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) {
        if (e.key === 'Escape') {
          target.blur();
        }
        return;
      }

      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        const input = document.querySelector('input[type="text"]') as HTMLInputElement;
        if (input) input.focus();
      } else if (e.key.toLowerCase() === 'm') {
        ws.setActiveTool(ws.activeTool === 'measure' ? 'select' : 'measure');
      } else if (e.key.toLowerCase() === 'i') {
        ws.setActiveTool(ws.activeTool === 'inspect' ? 'select' : 'inspect');
      } else if (e.key.toLowerCase() === 'l') {
        const btn = document.getElementById('compact-view-selector-btn');
        if (btn) btn.click();
      } else if (e.key.toLowerCase() === 'c') {
        ws.setTemporalMode(ws.temporalMode === 'Swipe' ? 'Difference' : 'Swipe');
      } else if (e.key.toLowerCase() === 'e') {
        ws.toggleDrawer('evidence');
      } else if (e.key === 'Escape') {
        ws.closeDrawer();
        setIsSystemHubOpen(false);
        setIsAOIModalOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [ws]);

  return (
    <div className="w-full h-screen min-h-[700px] flex flex-col bg-[#0A0A0A] text-[#111111] font-sans antialiased overflow-hidden select-none">
      {/* 1. Ultra-Minimal Top Header (SATQUERY AI · Study · ● Ready · System) */}
      <TopHeader
        onOpenSystemHub={() => setIsSystemHubOpen(true)}
        onOpenAOIModal={() => setIsAOIModalOpen(true)}
      />

      {/* 2. Hero Earth Observation Map (Dominant Surface) */}
      <div className="flex-1 flex min-h-0 overflow-hidden relative">
        <main className="flex-1 relative flex flex-col min-w-0 bg-[#0A0A0A] overflow-hidden">
          <GeoWorkspace onOpenSystemHub={() => setIsSystemHubOpen(true)} />
        </main>

        {/* Contextual Slide-Over Drawers (Only displayed when invoked) */}
        <SceneDrawer
          isOpen={ws.activeDrawer === 'scene'}
          onClose={() => ws.closeDrawer()}
        />

        <LayersDrawer
          isOpen={ws.activeDrawer === 'layers'}
          onClose={() => ws.closeDrawer()}
        />

        <EvidenceDrawer
          isOpen={ws.activeDrawer === 'evidence'}
          onClose={() => ws.closeDrawer()}
        />

        <TraceDrawer
          isOpen={ws.activeDrawer === 'trace'}
          onClose={() => ws.closeDrawer()}
        />

        <ChatAssistantDrawer
          isOpen={ws.activeDrawer === 'chat'}
          onClose={() => ws.closeDrawer()}
        />

        <AnalysesDrawer
          isOpen={ws.activeDrawer === 'analysis'}
          onClose={() => ws.closeDrawer()}
        />
      </div>

      {/* 3. Bottom Centered Natural Language Query Bar */}
      <div className="shrink-0 bg-[#0C0C0C] border-t border-white/10 px-6 py-2.5 space-y-2 z-20">
        {ws.isAnalyzing && (
          <AgentExecution currentStepIndex={ws.executionStepIndex} />
        )}
        <QueryBar />
      </div>

      {/* 4. Essential Production Modals */}
      <AOIImportModal
        isOpen={isAOIModalOpen}
        onClose={() => setIsAOIModalOpen(false)}
      />

      <SystemHubModal
        isOpen={isSystemHubOpen}
        onClose={() => setIsSystemHubOpen(false)}
      />

      <ReportExportModal
        isOpen={ws.isExportOpen}
        onClose={ws.closeExport}
        jobId={ws.agentResult?.job_id || `mission_${ws.selectedMissionId}`}
        reportUrls={{
          pdf:
            ws.agentResult?.report_urls?.pdf ||
            `/api/v1/reports/mission_${ws.selectedMissionId}/pdf`,
          geojson:
            ws.agentResult?.report_urls?.geojson ||
            `/api/v1/reports/mission_${ws.selectedMissionId}/geojson`,
          csv:
            ws.agentResult?.report_urls?.csv ||
            `/api/v1/reports/mission_${ws.selectedMissionId}/csv`,
          json:
            ws.agentResult?.report_urls?.json ||
            `/api/v1/reports/mission_${ws.selectedMissionId}/json`,
        }}
      />

      <ObservationPicker />
    </div>
  );
}

export function MissionWorkspace(props: MissionWorkspaceProps) {
  return (
    <WorkspaceProvider>
      <MissionWorkspaceInner {...props} />
    </WorkspaceProvider>
  );
}

export { SearchEarth } from './SearchEarth';
export { ObservationPicker } from './ObservationPicker';
