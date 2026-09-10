'use client';

import React from 'react';
import {
  Database,
  Layers,
  Sparkles,
  ShieldCheck,
  GitCommit,
  Settings,
} from 'lucide-react';
import { useWorkspace, ActiveDrawer } from '../../context/WorkspaceContext';

interface InstrumentRailProps {
  onOpenSettings?: () => void;
}

const RAIL_ITEMS: {
  id: ActiveDrawer;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  { id: 'scene', label: 'Scene Assets', icon: Database },
  { id: 'layers', label: 'Spectral Layers', icon: Layers },
  { id: 'evidence', label: 'Evidence Stack', icon: ShieldCheck },
  { id: 'trace', label: 'Observable Trace', icon: GitCommit },
];

export const InstrumentRail: React.FC<InstrumentRailProps> = ({ onOpenSettings }) => {
  const ws = useWorkspace();

  const handleToggle = (id: ActiveDrawer) => {
    ws.toggleDrawer(id);
  };

  const handleSettings = () => {
    if (onOpenSettings) {
      onOpenSettings();
    } else {
      ws.setIsSettingsOpen(true);
    }
  };

  return (
    <aside className="w-12 shrink-0 bg-[#111111] flex flex-col items-center justify-between py-3 border-r border-[#222222] z-30 select-none">
      {/* Top Nav Action Group */}
      <div className="flex flex-col items-center gap-2.5 w-full px-1.5">
        {RAIL_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = ws.activeDrawer === item.id;

          return (
            <button
              key={item.id}
              onClick={() => handleToggle(item.id)}
              className={`w-9 h-9 flex items-center justify-center rounded-xl transition-all group relative ${
                isActive
                  ? 'bg-white text-[#111111] shadow-md font-semibold'
                  : 'text-[#888888] hover:text-white hover:bg-[#222222]'
              }`}
              title={item.label}
              aria-label={item.label}
            >
              <Icon
                className={`w-4 h-4 transition-transform group-hover:scale-110 ${
                  isActive ? 'text-[#111111]' : 'text-current'
                }`}
              />
            </button>
          );
        })}
      </div>

      {/* Bottom Settings Trigger */}
      <div className="w-full px-1.5">
        <button
          onClick={handleSettings}
          className="w-9 h-9 flex items-center justify-center rounded-xl text-[#777777] hover:text-white hover:bg-[#222222] transition-all group"
          title="System Settings"
          aria-label="System Settings"
        >
          <Settings className="w-4 h-4 transition-transform group-hover:rotate-45" />
        </button>
      </div>
    </aside>
  );
};
