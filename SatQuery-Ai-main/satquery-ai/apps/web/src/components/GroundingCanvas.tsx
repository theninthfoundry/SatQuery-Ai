import React from 'react';
import { GroundingFeature } from '../types';

interface GroundingCanvasProps {
  features?: GroundingFeature[];
}

export const GroundingCanvas: React.FC<GroundingCanvasProps> = ({ features }) => {
  if (!features || features.length === 0) return null;

  return (
    <div className="absolute inset-0 pointer-events-none">
      <svg className="w-full h-full" viewBox="0 0 1000 1000" preserveAspectRatio="none">
        {features.map((feat, idx) => {
          const { bbox_normalized, label, area_m2, confidence } = feat.properties;
          const x = bbox_normalized.xmin * 1000;
          const y = bbox_normalized.ymin * 1000;
          const width = (bbox_normalized.xmax - bbox_normalized.xmin) * 1000;
          const height = (bbox_normalized.ymax - bbox_normalized.ymin) * 1000;

          return (
            <g key={idx} className="pointer-events-auto group">
              {/* Highlight bounding rectangle */}
              <rect
                x={x}
                y={y}
                width={width}
                height={height}
                fill="rgba(56, 189, 248, 0.25)"
                stroke="#38bdf8"
                strokeWidth="3"
                strokeDasharray="6 3"
                className="transition-all duration-200 group-hover:fill-opacity-40"
              />

              {/* Corner crosshairs */}
              <circle cx={x} cy={y} r="5" fill="#38bdf8" />
              <circle cx={x + width} cy={y} r="5" fill="#38bdf8" />
              <circle cx={x} cy={y + height} r="5" fill="#38bdf8" />
              <circle cx={x + width} cy={y + height} r="5" fill="#38bdf8" />
            </g>
          );
        })}
      </svg>

      {/* HTML Badges positioned over regions */}
      {features.map((feat, idx) => {
        const { bbox_normalized, label, area_m2, confidence } = feat.properties;
        const leftPercent = bbox_normalized.xmin * 100;
        const topPercent = Math.max(0, bbox_normalized.ymin * 100 - 4);

        return (
          <div
            key={`badge-${idx}`}
            style={{ left: `${leftPercent}%`, top: `${topPercent}%` }}
            className="absolute -translate-y-full flex items-center space-x-1.5 px-2 py-0.5 rounded font-mono text-[10px] bg-space-950/90 text-satblue-300 border border-satblue-400/50 shadow-lg pointer-events-auto"
          >
            <span className="font-bold">{label}</span>
            <span className="text-slate-400">|</span>
            <span className="text-emerald-400">{area_m2.toLocaleString()} m²</span>
            <span className="text-slate-400">|</span>
            <span className="text-slate-400">{Math.round(confidence * 100)}%</span>
          </div>
        );
      })}
    </div>
  );
};
