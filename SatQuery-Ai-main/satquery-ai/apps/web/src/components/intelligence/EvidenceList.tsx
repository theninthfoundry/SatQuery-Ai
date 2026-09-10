'use client';

import React from 'react';
import { Check, Layers, ShieldCheck, Activity, Info } from 'lucide-react';
import { useWorkspace, EvidenceLayerItem } from '../../context/WorkspaceContext';

interface EvidenceListProps {
  activeLayerId?: string | null;
  onSelectLayer?: (layerId: string) => void;
  layers?: EvidenceLayerItem[];
}

export const EvidenceList: React.FC<EvidenceListProps> = ({
  activeLayerId: propActiveLayerId,
  onSelectLayer: propOnSelectLayer,
  layers: propLayers,
}) => {
  const ws = useWorkspace();

  const activeLayerId =
    propActiveLayerId !== undefined ? propActiveLayerId : ws.activeEvidenceLayerId;
  const layers = propLayers || ws.evidenceLayers;

  const handleSelect = (layer: EvidenceLayerItem) => {
    if (propOnSelectLayer) {
      propOnSelectLayer(layer.id);
    } else {
      ws.selectEvidenceLayer(layer.id);
    }
  };

  return (
    <div className="space-y-2 select-none">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono font-bold tracking-wider text-[#888888] uppercase block">
          SUPPORTING EVIDENCE BREAKDOWN
        </span>
        <button
          onClick={() => ws.setIsEvidenceModalOpen(true)}
          className="text-[10px] font-mono text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-1.5 py-0.5 rounded border border-emerald-200 flex items-center gap-1 transition-colors"
          title="Open Detailed Scientific Evidence Inspector"
        >
          <Info className="w-2.5 h-2.5" />
          <span>INSPECT</span>
        </button>
      </div>

      <div className="space-y-2">
        {layers.map((layer) => {
          const isActive = activeLayerId === layer.id;
          const pct = Math.round(layer.score * 100);

          return (
            <div
              key={layer.id}
              onClick={() => handleSelect(layer)}
              className={`p-3 rounded-xl border transition-all cursor-pointer space-y-2 group ${
                isActive
                  ? 'bg-white border-[#111111] shadow-sm ring-1 ring-black/5'
                  : 'bg-white/80 border-[#E8E8E5] hover:border-[#D0D0CB] hover:bg-white'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-mono font-bold uppercase tracking-wider text-[#888888]">
                      {layer.category}
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-[#111111] group-hover:text-black">
                    {layer.title}
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-xs font-mono font-bold text-emerald-700">
                    {pct}%
                  </span>
                </div>
              </div>

              {/* Visual Evidence Bar */}
              <div className="space-y-1">
                <div className="w-full h-1.5 rounded-full bg-[#EAEAEA] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-emerald-600 transition-all duration-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <p className="text-[10px] text-[#737373] font-mono leading-tight">
                  {layer.subtitle}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
export type { EvidenceLayerItem };
