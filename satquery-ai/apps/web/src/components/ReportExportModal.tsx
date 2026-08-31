'use client';

import React from 'react';
import { FileText, Map, Table, Download, X, Globe } from 'lucide-react';
import { getReportDownloadUrl } from '../lib/api';

interface ReportExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  jobId: string;
  reportUrls: {
    pdf: string;
    geojson: string;
    csv: string;
  };
}

export const ReportExportModal: React.FC<ReportExportModalProps> = ({
  isOpen,
  onClose,
  jobId,
  reportUrls,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 select-none">
      <div className="bg-white border border-[#E8E8E5] rounded-2xl max-w-md w-full p-6 space-y-5 shadow-panel animate-in fade-in zoom-in duration-150">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#E8E8E5]">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#0A0A0A] flex items-center justify-center text-white">
              <Download className="w-3.5 h-3.5" />
            </div>
            <h3 className="text-sm font-bold text-[#111111]">Export Mission Dossier</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-[#F3F3F0] text-[#777777] hover:text-[#111111] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="text-xs text-[#666666] leading-relaxed">
          Download complete verified evidence, geometric area metrics, and spatial vectors for mission job{' '}
          <span className="font-mono text-[#111111] font-semibold">{jobId}</span>.
        </p>

        <div className="space-y-2.5">
          {/* PDF Download */}
          <a
            href={getReportDownloadUrl(reportUrls.pdf)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between p-3 rounded-xl bg-[#F8F8F6] border border-[#E8E8E5] hover:border-[#111111] hover:bg-white transition-all group"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-600">
                <FileText className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-semibold text-[#111111] group-hover:text-black">
                  PDF Mission Audit Report
                </p>
                <p className="text-[11px] text-[#737373]">Executive summary, preview, confidence & trace</p>
              </div>
            </div>
            <Download className="w-4 h-4 text-[#888888] group-hover:text-[#111111] transition-colors" />
          </a>

          {/* GeoJSON Download */}
          <a
            href={getReportDownloadUrl(reportUrls.geojson)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between p-3 rounded-xl bg-[#F8F8F6] border border-[#E8E8E5] hover:border-[#111111] hover:bg-white transition-all group"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
                <Map className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-semibold text-[#111111] group-hover:text-black">
                  GeoJSON Spatial Polygons
                </p>
                <p className="text-[11px] text-[#737373]">GIS vectors, bounding boxes & m² properties</p>
              </div>
            </div>
            <Download className="w-4 h-4 text-[#888888] group-hover:text-[#111111] transition-colors" />
          </a>

          {/* CSV Download */}
          <a
            href={getReportDownloadUrl(reportUrls.csv)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between p-3 rounded-xl bg-[#F8F8F6] border border-[#E8E8E5] hover:border-[#111111] hover:bg-white transition-all group"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600">
                <Table className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-semibold text-[#111111] group-hover:text-black">
                  CSV Metrics Spreadsheet
                </p>
                <p className="text-[11px] text-[#737373]">Tabular execution log & cluster areas</p>
              </div>
            </div>
            <Download className="w-4 h-4 text-[#888888] group-hover:text-[#111111] transition-colors" />
          </a>
        </div>
      </div>
    </div>
  );
};
