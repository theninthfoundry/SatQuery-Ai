'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Target,
  ChevronDown,
  Check,
} from 'lucide-react';
import { useWorkspace, Scenario, CANONICAL_MISSIONS } from '../../context/WorkspaceContext';

interface TopHeaderProps {
  scenarios?: Scenario[];
  selectedScenarioId?: string;
  onSelectScenario?: (id: string) => void;
  activeTab?: 'workspace' | 'diagnostics' | 'reports';
  onSelectTab?: (tab: 'workspace' | 'diagnostics' | 'reports') => void;
  onOpenSettings?: () => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  onSelectTab: propOnSelectTab,
  onOpenSettings: propOnOpenSettings,
}) => {
  const ws = useWorkspace();
  const [isMissionDropdownOpen, setIsMissionDropdownOpen] = useState<boolean>(false);
  const missionRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (missionRef.current && !missionRef.current.contains(event.target as Node)) {
        setIsMissionDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const currentMission = ws.currentMission;

  return (
    <header className="h-14 shrink-0 bg-white border-b border-[#E6E6E1] px-6 flex items-center justify-between z-30 select-none">
      {/* Left: Brand & Subtitle */}
      <div className="flex items-center gap-3">
        <div className="w-7 h-7 rounded-full bg-[#111111] flex items-center justify-center text-white shadow-sm">
          <Target className="w-3.5 h-3.5 text-white stroke-[2.4]" />
        </div>
        <div>
          <div className="font-sans font-bold text-xs tracking-tight text-[#111111] leading-none">
            SATQUERY AI
          </div>
          <div className="text-[9px] font-mono font-semibold tracking-wider text-[#888888] uppercase mt-0.5">
            Earth Observation Intelligence
          </div>
        </div>
      </div>

      {/* Center: Mission Selector */}
      <div className="relative" ref={missionRef}>
        <button
          onClick={() => setIsMissionDropdownOpen((prev) => !prev)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-[#E6E6E1] bg-[#FAF9F7] hover:bg-[#F3F3F0] text-xs font-semibold text-[#111111] transition-colors"
        >
          <span className="font-mono text-[10px] text-[#6F6F6A] font-bold">
            {currentMission.tag}
          </span>
          <span>{currentMission.name}</span>
          <ChevronDown className="w-3.5 h-3.5 text-[#6F6F6A]" />
        </button>

        {isMissionDropdownOpen && (
          <div className="absolute left-1/2 -translate-x-1/2 top-full mt-1.5 w-84 bg-white border border-[#E6E6E1] rounded-2xl shadow-2xl py-2 z-50 animate-in fade-in zoom-in-95 duration-150">
            <div className="px-3.5 py-1.5 text-[9px] font-mono font-bold tracking-wider text-[#888888] uppercase border-b border-[#F0EFEA]">
              CANONICAL MISSIONS SUITE
            </div>
            <div className="p-1.5 space-y-1">
              {CANONICAL_MISSIONS.map((m) => {
                const isSelected = ws.selectedMissionId === m.id;
                return (
                  <button
                    key={m.id}
                    onClick={() => {
                      ws.selectMission(m.id);
                      setIsMissionDropdownOpen(false);
                    }}
                    className={`w-full text-left p-2.5 rounded-xl text-xs transition-all flex items-start justify-between ${
                      isSelected
                        ? 'bg-[#FAF9F7] text-[#111111] font-bold ring-1 ring-[#E6E6E1]'
                        : 'text-[#444444] hover:bg-[#F7F7F5]'
                    }`}
                  >
                    <div>
                      <div className="font-mono text-[10px] text-[#6F6F6A] font-bold">{m.tag}</div>
                      <div className="mt-0.5">{m.name}</div>
                      <div className="text-[10px] text-[#888888] font-mono mt-0.5">{m.location}</div>
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-1" />}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Right: Quick Tabs (Workspace, Evidence, Reports) & Status Pill */}
      <div className="flex items-center gap-4">
        {/* Navigation Links */}
        <div className="flex items-center gap-1 text-xs font-semibold text-[#6F6F6A]">
          <button
            onClick={() => ws.closeDrawer()}
            className="px-3 py-1.5 rounded-lg hover:text-[#111111] hover:bg-[#FAF9F7] transition-colors"
          >
            Workspace
          </button>
          <button
            onClick={() => ws.toggleDrawer('evidence')}
            className="px-3 py-1.5 rounded-lg hover:text-[#111111] hover:bg-[#FAF9F7] transition-colors"
          >
            Evidence
          </button>
          <button
            onClick={() => ws.openExport('pdf')}
            className="px-3 py-1.5 rounded-lg hover:text-[#111111] hover:bg-[#FAF9F7] transition-colors"
          >
            Reports
          </button>
        </div>

        <span className="w-px h-4 bg-[#E6E6E1]" />

        {/* Unified System State Indicator */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[#FAF9F7] border border-[#E6E6E1] text-[11px] font-mono font-medium">
          {ws.systemState === 'ANALYZING' ? (
            <>
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              <span className="text-amber-800 font-bold">ANALYZING</span>
            </>
          ) : ws.systemState === 'VERIFIED' ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.6)]" />
              <span className="text-emerald-800 font-bold">VERIFIED</span>
            </>
          ) : ws.systemState === 'OFFLINE' ? (
            <>
              <span className="w-2 h-2 rounded-full bg-zinc-400" />
              <span className="text-zinc-600">OFFLINE</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.5)]" />
              <span className="text-[#111111] font-semibold">READY</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
export type { Scenario };
