import React from 'react';
import { FileText, Map, Table, Download, X } from 'lucide-react';
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
    <div className="fixed inset-0 z-50 bg-space-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-space-900 border border-space-700 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in duration-150">
        <div className="flex items-center justify-between pb-3 border-b border-space-800">
          <div className="flex items-center space-x-2">
            <Download className="w-5 h-5 text-satblue-400" />
            <h3 className="text-base font-bold text-slate-100">Export Mission Dossier</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-space-800 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="text-xs text-slate-400">
          Download complete auditable evidence, metrics, and spatial vectors for analysis job{' '}
          <span className="font-mono text-satblue-400 font-semibold">{jobId}</span>.
        </p>

        <div className="space-y-3">
          {/* PDF Download */}
          <a
            href={getReportDownloadUrl(reportUrls.pdf)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between p-3 rounded-xl bg-space-950/70 border border-space-800 hover:border-satblue-500/40 transition-colors group"
          >
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-200 group-hover:text-satblue-300">
                  PDF Mission Audit Report
                </p>
                <p className="text-[11px] text-slate-500">Executive summary, preview, confidence & trace</p>
              </div>
            </div>
            <Download className="w-4 h-4 text-slate-500 group-hover:text-satblue-400 transition-colors" />
          </a>

          {/* GeoJSON Download */}
          <a
            href={getReportDownloadUrl(reportUrls.geojson)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between p-3 rounded-xl bg-space-950/70 border border-space-800 hover:border-satblue-500/40 transition-colors group"
          >
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                <Map className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-200 group-hover:text-emerald-300">
                  GeoJSON Spatial Polygons
                </p>
                <p className="text-[11px] text-slate-500">GIS vectors, bounding boxes & m² properties</p>
              </div>
            </div>
            <Download className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 transition-colors" />
          </a>

          {/* CSV Download */}
          <a
            href={getReportDownloadUrl(reportUrls.csv)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between p-3 rounded-xl bg-space-950/70 border border-space-800 hover:border-satblue-500/40 transition-colors group"
          >
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                <Table className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-200 group-hover:text-amber-300">
                  CSV Metrics Spreadsheet
                </p>
                <p className="text-[11px] text-slate-500">Tabular execution log & cluster areas</p>
              </div>
            </div>
            <Download className="w-4 h-4 text-slate-500 group-hover:text-amber-400 transition-colors" />
          </a>
        </div>
      </div>
    </div>
  );
};
