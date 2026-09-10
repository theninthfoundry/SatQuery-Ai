'use client';

import React from 'react';
import { FileText, Map, Table, Globe } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface ExportPanelProps {
  onExport?: (format: 'pdf' | 'geojson' | 'csv' | 'kml') => void;
}

export const ExportPanel: React.FC<ExportPanelProps> = ({ onExport }) => {
  const ws = useWorkspace();

  const handleExportClick = (format: 'pdf' | 'geojson' | 'csv' | 'kml') => {
    if (onExport) {
      onExport(format);
    } else {
      ws.openExport(format);
    }
  };

  return (
    <div className="space-y-2 select-none">
      <span className="text-[10px] font-mono font-bold tracking-wider text-[#888888] uppercase block">
        EXPORT THIS ANALYSIS
      </span>

      <div className="grid grid-cols-4 gap-2">
        {/* PDF Report */}
        <button
          onClick={() => handleExportClick('pdf')}
          className="p-2.5 rounded-xl border border-[#E8E8E5] bg-white hover:border-[#D0D0CB] hover:shadow-subtle transition-all flex flex-col items-center justify-center text-center group"
          title="Download PDF Mission Audit Dossier"
        >
          <div className="w-7 h-7 rounded-lg bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-600 mb-1.5 group-hover:scale-105 transition-transform">
            <FileText className="w-3.5 h-3.5" />
          </div>
          <span className="text-[10px] font-mono font-medium text-[#444444] group-hover:text-black">
            PDF Report
          </span>
        </button>

        {/* GeoJSON */}
        <button
          onClick={() => handleExportClick('geojson')}
          className="p-2.5 rounded-xl border border-[#E8E8E5] bg-white hover:border-[#D0D0CB] hover:shadow-subtle transition-all flex flex-col items-center justify-center text-center group"
          title="Download GeoJSON Polygons & Bounding Boxes"
        >
          <div className="w-7 h-7 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 mb-1.5 group-hover:scale-105 transition-transform">
            <Map className="w-3.5 h-3.5" />
          </div>
          <span className="text-[10px] font-mono font-medium text-[#444444] group-hover:text-black">
            GeoJSON
          </span>
        </button>

        {/* CSV Metrics */}
        <button
          onClick={() => handleExportClick('csv')}
          className="p-2.5 rounded-xl border border-[#E8E8E5] bg-white hover:border-[#D0D0CB] hover:shadow-subtle transition-all flex flex-col items-center justify-center text-center group"
          title="Download Tabular CSV Area Metrics"
        >
          <div className="w-7 h-7 rounded-lg bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600 mb-1.5 group-hover:scale-105 transition-transform">
            <Table className="w-3.5 h-3.5" />
          </div>
          <span className="text-[10px] font-mono font-medium text-[#444444] group-hover:text-black">
            CSV Metrics
          </span>
        </button>

        {/* KML */}
        <button
          onClick={() => handleExportClick('kml')}
          className="p-2.5 rounded-xl border border-[#E8E8E5] bg-white hover:border-[#D0D0CB] hover:shadow-subtle transition-all flex flex-col items-center justify-center text-center group"
          title="Download KML Geographic Coordinates Layer"
        >
          <div className="w-7 h-7 rounded-lg bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600 mb-1.5 group-hover:scale-105 transition-transform">
            <Globe className="w-3.5 h-3.5" />
          </div>
          <span className="text-[10px] font-mono font-medium text-[#444444] group-hover:text-black">
            KML
          </span>
        </button>
      </div>
    </div>
  );
};
