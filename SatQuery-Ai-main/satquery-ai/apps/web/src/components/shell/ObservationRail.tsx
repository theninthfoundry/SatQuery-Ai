'use client';

import { Plus, Check } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface ObservationRailProps {
  onAddObservation?: () => void;
}

export const ObservationRail: React.FC<ObservationRailProps> = ({ onAddObservation }) => {
  const ws = useWorkspace();

  const handleAdd = () => {
    if (onAddObservation) {
      onAddObservation();
    } else {
      ws.setActiveTab('diagnostics');
    }
  };

  return (
    <aside className="w-64 shrink-0 bg-[#FAF9F7] border-r border-[#E6E6E1] flex flex-col justify-between p-4 select-none overflow-y-auto">
      {/* Top: Observation Cards List */}
      <div className="space-y-4">
        {/* Section Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono font-bold tracking-wider text-[#111111] uppercase">
              OBSERVATIONS
            </span>
          </div>
          <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
            {ws.datasets.length} Synchronized
          </span>
        </div>

        {/* Observation Cards */}
        <div className="space-y-2.5">
          {ws.datasets.map((dataset, idx) => {
            const isSelected = ws.activeDatasetIndex === idx;
            const isOptical = dataset.modality === 'optical' || dataset.modality === 'multispectral';

            return (
              <div
                key={dataset.id}
                onClick={() => {
                  ws.setActiveDatasetIndex(idx);
                  if (isOptical) {
                    if (ws.activeLens === 'SAR') ws.setActiveLens('True Color');
                  } else {
                    ws.setActiveLens('SAR');
                  }
                }}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-white border-[#111111] shadow-sm ring-1 ring-black/5'
                    : 'bg-white/80 border-[#E6E6E1] hover:border-[#CCCCCC]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[#111111]">
                      {dataset.name}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-emerald-700 font-semibold flex items-center gap-1">
                    <Check className="w-3 h-3 stroke-[2.5]" />
                    {idx === 1 ? 'Registered' : 'Compatible'}
                  </span>
                </div>

                <div className="mt-2 space-y-0.5 text-[11px] font-mono text-[#6F6F6A]">
                  <p>{dataset.sensor} · {dataset.date}</p>
                  <p>{dataset.resolution} · {dataset.bands.split(' ')[0]} bands</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Add Observation Button */}
        <button
          onClick={handleAdd}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl border border-dashed border-[#CCCCCC] hover:border-[#111111] bg-white hover:bg-[#FAF9F7] text-xs font-semibold text-[#111111] transition-all group"
        >
          <Plus className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
          <span>Add observation</span>
        </button>
      </div>

      {/* Bottom Scene AOI Pill */}
      <div className="pt-4 border-t border-[#E6E6E1] space-y-1 text-[11px] font-mono text-[#6F6F6A]">
        <div className="flex items-center justify-between text-[#888888] text-[10px] uppercase">
          <span>Target AOI</span>
          <span>{ws.currentMission.areaAoi}</span>
        </div>
        <p className="text-xs font-semibold text-[#111111] font-sans truncate">
          {ws.currentMission.name}
        </p>
        <p className="text-[10px] text-[#888888]">
          {ws.currentMission.utmZone}
        </p>
      </div>
    </aside>
  );
};
