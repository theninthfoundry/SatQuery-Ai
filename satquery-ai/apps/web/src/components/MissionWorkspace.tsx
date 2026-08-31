'use client';

import React from 'react';
import { TopHeader } from './shell/TopHeader';
import { GeoWorkspace } from './map/GeoWorkspace';
import { QueryBar } from './query/QueryBar';
import { AgentExecution } from './query/AgentExecution';
import { SceneDrawer } from './drawers/SceneDrawer';
import { EvidenceDrawer } from './drawers/EvidenceDrawer';
import { TraceDrawer } from './drawers/TraceDrawer';
import { LayersDrawer } from './drawers/LayersDrawer';
import { ReportExportModal } from './ReportExportModal';
import { SettingsModal } from './modals/SettingsModal';
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

  const handleDiagnostics = () => {
    if (onSwitchToDiagnostics) {
      onSwitchToDiagnostics();
    } else {
      ws.setActiveTab('diagnostics');
    }
  };

  const handleReports = () => {
    if (onSwitchToReports) {
      onSwitchToReports();
    } else {
      ws.openExport('pdf');
    }
  };

  return (
    <div className="w-full h-screen min-h-[700px] flex flex-col bg-[#0A0A0A] text-[#111111] font-sans antialiased overflow-hidden select-none">
      {/* 1. Minimal Top Header */}
      <TopHeader
        activeTab={ws.activeTab}
        onSelectTab={(tab) => {
          if (tab === 'diagnostics') handleDiagnostics();
          else if (tab === 'reports') handleReports();
          else ws.setActiveTab('workspace');
        }}
        onOpenSettings={() => ws.setIsSettingsOpen(true)}
      />

      {/* 2. Unified Hero Earth Observation Canvas (Dominates the Workspace) */}
      <div className="flex-1 flex min-h-0 overflow-hidden relative">
        <main className="flex-1 relative flex flex-col min-w-0 bg-[#0A0A0A] overflow-hidden">
          <GeoWorkspace />
        </main>

        {/* Progressive Disclosure Slide-Over Drawers (Rendered over the canvas without layout shift) */}
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
      </div>

      {/* 3. Bottom Persistent Command Surface & Execution Trace */}
      <div className="shrink-0 bg-[#F7F7F5] border-t border-[#E6E6E1] px-6 py-3 space-y-2 z-20">
        {/* Observable Agent Execution Progression */}
        {ws.isAnalyzing && (
          <AgentExecution currentStepIndex={ws.executionStepIndex} />
        )}

        {/* Natural Language Query Composer */}
        <QueryBar />
      </div>

      {/* 4. Production Modals */}
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
        }}
      />

      <SettingsModal />
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
