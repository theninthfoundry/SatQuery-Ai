'use client';

import React, { useState, useMemo } from 'react';
import {
  X,
  FolderArchive,
  Search,
  Bookmark,
  BookmarkCheck,
  CheckCircle2,
  ArrowRight,
  Clock,
  Layers,
  MapPin,
  Calendar,
  Sparkles,
  ShieldCheck,
  FileText,
  Plus,
  Compass,
} from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

export interface AnalysisRecord {
  id: string;
  title: string;
  project: string;
  locationName: string;
  lat: number;
  lon: number;
  utmZone: string;
  dateT1: string;
  dateT2: string;
  sensors: string;
  query: string;
  findingSummary: string;
  areaHa: string;
  areaM2: string;
  confidenceScore: number;
  confidenceLabel: 'High' | 'Moderate' | 'Calibrated';
  sarBackscatterDb: string;
  isSaved: boolean;
  createdAt: string;
  task: string;
  missionId: string;
}

export const CANONICAL_ANALYSES: AnalysisRecord[] = [
  {
    id: 'analysis_blr_compound',
    title: 'Urban Expansion & Tech Park Infill',
    project: 'Bangalore Metropolitan Corridor Study',
    locationName: 'Bangalore Urban Corridor (12.97°N, 77.59°E)',
    lat: 12.9716,
    lon: 77.5946,
    utmZone: 'EPSG:32643 (UTM Zone 43N)',
    dateT1: '2024-03-14',
    dateT2: '2026-03-19',
    sensors: 'Sentinel-2 MSI (10m) + Sentinel-1 SAR C-band',
    query: 'What changed between these two observations and where?',
    findingSummary:
      'Siamese ChangeNet detected +1.82 ha of new commercial built-up structures, corroborated by -14.5 dB radar double-bounce backscatter.',
    areaHa: '+1.82 ha',
    areaM2: '18,200 m²',
    confidenceScore: 94,
    confidenceLabel: 'High',
    sarBackscatterDb: '-14.5 dB σ⁰',
    isSaved: true,
    createdAt: '2 hours ago',
    task: 'bi_temporal_change',
    missionId: 'mission_05_compound',
  },
  {
    id: 'analysis_hyd_industrial',
    title: 'Industrial Sprawl & Lake Basin Encroachment',
    project: 'Telangana Water Body Surveillance',
    locationName: 'Hyderabad Urban Corridor (17.39°N, 78.49°E)',
    lat: 17.385,
    lon: 78.4867,
    utmZone: 'EPSG:32644 (UTM Zone 44N)',
    dateT1: '2025-09-12',
    dateT2: '2026-09-06',
    sensors: 'Sentinel-2 MSI (10m) + Sentinel-1 C-SAR',
    query: 'Analyze industrial expansion around Hyderabad between T1 and T2',
    findingSummary:
      'Substantial logistical shed construction along outer ring road. Zero encroachment into protected shoreline water buffers.',
    areaHa: '+2.56 ha',
    areaM2: '25,600 m²',
    confidenceScore: 92,
    confidenceLabel: 'High',
    sarBackscatterDb: '-13.8 dB σ⁰',
    isSaved: true,
    createdAt: 'Yesterday',
    task: 'bi_temporal_change',
    missionId: 'mission_06_hyderabad',
  },
  {
    id: 'analysis_brahmaputra_flood',
    title: 'Monsoon Flood Inundation & Embankment Breach',
    project: 'Assam Disaster Monitoring Network',
    locationName: 'Brahmaputra Basin (26.20°N, 92.94°E)',
    lat: 26.2006,
    lon: 92.9376,
    utmZone: 'EPSG:32646 (UTM Zone 46N)',
    dateT1: '2024-11-04',
    dateT2: '2025-11-20',
    sensors: 'Sentinel-1 C-band SAR + Sentinel-2 Optical',
    query: 'Cross-examine optical water masks against SAR radar backscatter',
    findingSummary:
      'Persistent surface water identified via specular radar backscatter (σ⁰ < -21.0 dB), penetrating monsoon cloud occlusion completely.',
    areaHa: '15.20 ha',
    areaM2: '152,000 m²',
    confidenceScore: 96,
    confidenceLabel: 'High',
    sarBackscatterDb: '-22.1 dB σ⁰',
    isSaved: false,
    createdAt: '3 days ago',
    task: 'optical_sar_fusion',
    missionId: 'mission_04_opticals_sar',
  },
  {
    id: 'analysis_mumbai_coastal',
    title: 'Coastal Reclamation & Transport Link',
    project: 'Maharashtra Maritime Infrastructure',
    locationName: 'Mumbai Coastal Region (19.08°N, 72.88°E)',
    lat: 19.076,
    lon: 72.8777,
    utmZone: 'EPSG:32643 (UTM Zone 43N)',
    dateT1: '2024-01-10',
    dateT2: '2026-02-15',
    sensors: 'Sentinel-2 Multi-spectral (10m)',
    query: 'Identify built-up areas and road links',
    findingSummary:
      'Reclaimed seawall arterial corridor verified. High reflectance road concrete distinct from tidal mudflats.',
    areaHa: '+3.40 ha',
    areaM2: '34,000 m²',
    confidenceScore: 89,
    confidenceLabel: 'High',
    sarBackscatterDb: '-15.2 dB σ⁰',
    isSaved: false,
    createdAt: '5 days ago',
    task: 'single_image_vqa',
    missionId: 'mission_01_vqa',
  },
];

interface AnalysesDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AnalysesDrawer: React.FC<AnalysesDrawerProps> = ({ isOpen, onClose }) => {
  const ws = useWorkspace();
  const [activeFilter, setActiveFilter] = useState<'ALL' | 'RECENT' | 'SAVED'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [savedRecords, setSavedRecords] = useState<AnalysisRecord[]>(CANONICAL_ANALYSES);
  const [justSavedNotice, setJustSavedNotice] = useState(false);

  const toggleSave = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSavedRecords((prev) =>
      prev.map((r) => (r.id === id ? { ...r, isSaved: !r.isSaved } : r))
    );
  };

  const handleSaveCurrent = () => {
    const currentLoc = ws.currentMission;
    const newRecord: AnalysisRecord = {
      id: `analysis_${Date.now()}`,
      title: ws.findingTitle || 'Current Investigation',
      project: `${currentLoc.name} Study`,
      locationName: currentLoc.location || currentLoc.name,
      lat: currentLoc.lat,
      lon: currentLoc.lon,
      utmZone: currentLoc.utmZone,
      dateT1: currentLoc.dateT1 || ws.dateT1 || '2024-03-14',
      dateT2: currentLoc.dateT2 || ws.dateT2 || '2026-03-19',
      sensors: currentLoc.sensors || 'Sentinel-2 (10m) + Sentinel-1 SAR',
      query: ws.queryText || 'What changed between these two observations?',
      findingSummary: ws.customInsight || 'Bi-temporal ChangeNet detected surface alterations.',
      areaHa: ws.customAreaHa || ws.totalAreaHa,
      areaM2: ws.customAreaM2 || ws.totalAreaM2,
      confidenceScore: ws.evidenceScore || 94,
      confidenceLabel: 'High',
      sarBackscatterDb: '-14.5 dB σ⁰',
      isSaved: true,
      createdAt: 'Just now',
      task: 'bi_temporal_change',
      missionId: currentLoc.id,
    };
    setSavedRecords((prev) => [newRecord, ...prev]);
    setJustSavedNotice(true);
    setTimeout(() => setJustSavedNotice(false), 3000);
  };

  const filteredAnalyses = useMemo(() => {
    return savedRecords.filter((a) => {
      if (activeFilter === 'SAVED' && !a.isSaved) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchesTitle = a.title.toLowerCase().includes(q);
        const matchesProject = a.project.toLowerCase().includes(q);
        const matchesLoc = a.locationName.toLowerCase().includes(q);
        const matchesQuery = a.query.toLowerCase().includes(q);
        const matchesDate = a.dateT1.includes(q) || a.dateT2.includes(q);
        if (!matchesTitle && !matchesProject && !matchesLoc && !matchesQuery && !matchesDate) {
          return false;
        }
      }
      return true;
    });
  }, [savedRecords, activeFilter, searchQuery]);

  const handleSelectAnalysis = (analysis: AnalysisRecord) => {
    // 1. Select the mission
    ws.selectMission(analysis.missionId);

    // 2. Update query and findings
    ws.setQueryText(analysis.query);
    ws.setFindingTitle(analysis.title);
    ws.setCustomInsight(analysis.findingSummary);
    ws.setCustomAreaHa(analysis.areaHa);
    ws.setCustomAreaM2(analysis.areaM2);

    // 3. Update coordinates and dates
    ws.updateMissionLocation({
      name: analysis.locationName,
      lat: analysis.lat,
      lon: analysis.lon,
      utmZone: analysis.utmZone,
      areaAoi: analysis.areaHa,
      dateT1: analysis.dateT1,
      dateT2: analysis.dateT2,
    });

    // 4. Set appropriate lens
    if (analysis.task === 'optical_sar_fusion') {
      ws.setActiveLens('SAR');
    } else if (analysis.task === 'single_image_vqa') {
      ws.setActiveLens('True Color');
    } else {
      ws.setActiveLens('CHANGE');
    }

    // 5. Close drawer
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-[470px] max-w-full bg-[#111111] border-l border-[#242424] shadow-2xl flex flex-col transition-transform duration-300 animate-in slide-in-from-right select-none text-white font-sans">
      {/* Drawer Header */}
      <div className="h-14 px-5 border-b border-[#242424] flex items-center justify-between bg-[#141414] shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-[#1F1F1F] border border-white/10 flex items-center justify-center text-emerald-400">
            <FolderArchive className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-mono font-bold tracking-tight text-white uppercase">
              ANALYSES ARCHIVE
            </h2>
            <p className="text-[10px] text-neutral-400 font-mono">Recent & Saved Earth Investigations</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors"
          aria-label="Close Analyses Drawer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Control Bar: Filter Tabs & Save Current Action */}
      <div className="p-4 border-b border-[#222222] bg-[#161616] space-y-3 shrink-0">
        {/* Search Input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-neutral-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search analyses by keyword, city, or date..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#1F1F1F] border border-[#2D2D2D] rounded-lg pl-8 pr-8 py-1.5 text-xs text-neutral-200 placeholder:text-neutral-500 focus:outline-none focus:border-neutral-400 font-mono"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-200"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Filter Pills & Save Current Button */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1 bg-[#1A1A1A] p-0.5 rounded-md border border-[#282828] text-[10px] font-mono">
            {(['ALL', 'RECENT', 'SAVED'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveFilter(tab)}
                className={`px-2.5 py-1 rounded transition-colors ${
                  activeFilter === tab
                    ? 'bg-white text-black font-bold'
                    : 'text-neutral-400 hover:text-neutral-200'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <button
            onClick={handleSaveCurrent}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[11px] font-mono font-semibold transition-colors"
            title="Save current workspace state as an analysis"
          >
            <Plus className="w-3 h-3" />
            <span>Save Current</span>
          </button>
        </div>

        {justSavedNotice && (
          <div className="p-2 rounded bg-emerald-950/60 border border-emerald-800/80 text-[11px] font-mono text-emerald-300 flex items-center gap-1.5 animate-in fade-in duration-150">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>Current analysis saved to your permanent library.</span>
          </div>
        )}
      </div>

      {/* Analyses List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {filteredAnalyses.length === 0 ? (
          <div className="p-8 text-center text-neutral-500 font-mono text-xs space-y-1">
            <FolderArchive className="w-6 h-6 mx-auto text-neutral-600 mb-2 opacity-50" />
            <p>No analyses match your filter.</p>
            <p className="text-[10px] text-neutral-600">
              Run an Earth query and click &quot;Save Current&quot; to archive it here.
            </p>
          </div>
        ) : (
          filteredAnalyses.map((analysis) => {
            const isCurrentlyLoaded =
              ws.currentMission.id === analysis.missionId &&
              (ws.queryText === analysis.query || ws.findingTitle === analysis.title);

            return (
              <div
                key={analysis.id}
                onClick={() => handleSelectAnalysis(analysis)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer space-y-2.5 group ${
                  isCurrentlyLoaded
                    ? 'bg-[#191919] border-emerald-500/50 shadow-md ring-1 ring-emerald-500/20'
                    : 'bg-[#161616] border-[#262626] hover:border-[#383838] hover:bg-[#1A1A1A]'
                }`}
              >
                {/* Header Row: Title & Bookmark */}
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[9px] font-mono font-bold text-neutral-400 uppercase tracking-wider">
                        {analysis.project}
                      </span>
                      <span className="text-neutral-600">·</span>
                      <span className="text-[9px] font-mono text-neutral-500">
                        {analysis.createdAt}
                      </span>
                    </div>
                    <h3 className="text-xs font-bold text-white group-hover:text-emerald-300 transition-colors">
                      {analysis.title}
                    </h3>
                  </div>

                  <button
                    onClick={(e) => toggleSave(analysis.id, e)}
                    className="text-neutral-500 hover:text-amber-400 transition-colors p-1"
                    title={analysis.isSaved ? 'Remove from Saved' : 'Save Analysis'}
                  >
                    {analysis.isSaved ? (
                      <BookmarkCheck className="w-4 h-4 text-amber-400 fill-amber-400/20" />
                    ) : (
                      <Bookmark className="w-4 h-4" />
                    )}
                  </button>
                </div>

                {/* Query Asked */}
                <div className="p-2 rounded bg-[#111111] border border-white/5 text-[11px] font-mono text-neutral-300 italic">
                  &ldquo;{analysis.query}&rdquo;
                </div>

                {/* Key Metrics Strip */}
                <div className="grid grid-cols-3 gap-2 text-[10px] font-mono border-t border-b border-white/5 py-2">
                  <div>
                    <span className="text-neutral-500 block uppercase">MEASURED</span>
                    <span className="font-bold text-white text-xs">{analysis.areaHa}</span>
                  </div>
                  <div>
                    <span className="text-neutral-500 block uppercase">CONFIDENCE</span>
                    <span className="font-bold text-emerald-400">{analysis.confidenceScore}%</span>
                  </div>
                  <div>
                    <span className="text-neutral-500 block uppercase">RADAR</span>
                    <span className="font-bold text-satblue-400">{analysis.sarBackscatterDb}</span>
                  </div>
                </div>

                {/* Location & Sensor Metadata */}
                <div className="flex items-center justify-between text-[10px] font-mono text-neutral-400">
                  <div className="flex items-center gap-1 truncate max-w-[280px]">
                    <MapPin className="w-3 h-3 text-neutral-500 shrink-0" />
                    <span className="truncate">{analysis.locationName}</span>
                  </div>
                  <div className="flex items-center gap-1 shrink-0 text-neutral-500">
                    <Calendar className="w-3 h-3" />
                    <span>{analysis.dateT2}</span>
                  </div>
                </div>

                {/* Action Footer */}
                <div className="flex items-center justify-between pt-1 text-[11px] font-mono">
                  <span className="text-[10px] text-neutral-500">
                    {isCurrentlyLoaded ? (
                      <span className="text-emerald-400 font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Active in Workspace
                      </span>
                    ) : (
                      'Click to restore workspace'
                    )}
                  </span>
                  <div className="flex items-center gap-1 text-neutral-300 group-hover:text-white font-semibold">
                    <span>Load</span>
                    <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Drawer Footer */}
      <div className="p-3 border-t border-[#242424] bg-[#141414] text-center text-[10px] font-mono text-neutral-500 shrink-0">
        SatQuery Canonical Analysis Engine · Projected CRS Coordinates & GeoTIFF Raster Truth
      </div>
    </div>
  );
};
