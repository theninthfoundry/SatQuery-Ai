'use client';

import React from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface MetricBlockProps {
  areaHa?: string | number;
  areaM2?: string | number;
  calibratedEce?: string | number;
  calibrationMethod?: string;
}

export const MetricBlock: React.FC<MetricBlockProps> = ({
  areaHa: propAreaHa,
  areaM2: propAreaM2,
  calibratedEce: propCalibratedEce,
  calibrationMethod: propCalibrationMethod,
}) => {
  const ws = useWorkspace();

  const areaHa = propAreaHa !== undefined ? propAreaHa : ws.totalAreaHa;
  const areaM2 = propAreaM2 !== undefined ? propAreaM2 : ws.totalAreaM2;
  const calibratedEce =
    propCalibratedEce !== undefined ? propCalibratedEce : ws.evidenceScore;
  const calibrationMethod =
    propCalibrationMethod || 'Platt Scaled Concordance';

  return (
    <div className="grid grid-cols-2 gap-3 select-none">
      {/* Altered Area Metric */}
      <div
        onClick={() => {
          if (ws.clusters.length > 0) {
            ws.selectCluster(ws.clusters[0].id);
          }
        }}
        className="p-3.5 rounded-xl bg-white border border-[#E8E8E5] hover:border-[#111111] hover:shadow-subtle transition-all cursor-pointer space-y-1 group"
        title="Click to center map on detected change clusters"
      >
        <span className="text-[10px] font-mono font-bold tracking-wider text-[#888888] uppercase block group-hover:text-black">
          ALTERED AREA
        </span>
        <p className="text-xl font-mono font-bold tracking-tight text-[#111111] leading-none">
          {typeof areaHa === 'number' ? `${areaHa} ha` : areaHa}
        </p>
        <p className="text-[11px] font-mono text-[#737373]">
          {typeof areaM2 === 'number' ? `${areaM2.toLocaleString()} m²` : areaM2}
        </p>
      </div>

      {/* Evidence Score / Calibrated Metric */}
      <div
        onClick={() => ws.setIsEvidenceModalOpen(true)}
        className="p-3.5 rounded-xl bg-white border border-[#E8E8E5] hover:border-emerald-600 hover:shadow-subtle transition-all cursor-pointer space-y-1 group"
        title="Click to open Evidence Calibration Inspector"
      >
        <span className="text-[10px] font-mono font-bold tracking-wider text-[#888888] uppercase block group-hover:text-emerald-700">
          EVIDENCE SCORE
        </span>
        <p className="text-xl font-mono font-bold tracking-tight text-emerald-600 leading-none">
          {typeof calibratedEce === 'number' ? `${calibratedEce}%` : calibratedEce}
        </p>
        <p className="text-[11px] font-mono text-[#737373]">
          {calibrationMethod}
        </p>
      </div>
    </div>
  );
};
