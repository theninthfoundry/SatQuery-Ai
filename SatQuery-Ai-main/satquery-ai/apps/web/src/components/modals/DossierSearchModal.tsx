'use client';

import React, { useState, useMemo } from 'react';
import {
  Search,
  X,
  Calendar,
  Filter,
  Check,
  FolderArchive,
  ArrowRight,
  ShieldCheck,
  MapPin,
  Satellite,
  FileText,
  RotateCcw,
  SlidersHorizontal,
} from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { InspectionDossier, PREVIOUS_INSPECTION_DOSSIERS } from '../../types/dossier';

interface DossierSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectDossier?: (dossier: InspectionDossier) => void;
}

export const DossierSearchModal: React.FC<DossierSearchModalProps> = ({
  isOpen,
  onClose,
  onSelectDossier,
}) => {
  const ws = useWorkspace();

  // Search & Filter State
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedYear, setSelectedYear] = useState<string>('ALL');
  const [specificDate, setSpecificDate] = useState<string>('');
  const [sortBy, setSortBy] = useState<'date-desc' | 'date-asc' | 'name-asc' | 'name-desc' | 'confidence-desc'>('date-desc');
  const [selectedDossierId, setSelectedDossierId] = useState<string | null>(null);

  // Available inspection dossiers from context or canonical records
  const allDossiers: InspectionDossier[] = useMemo(() => {
    // If context has dynamic dossiers, merge them with PREVIOUS_INSPECTION_DOSSIERS
    return PREVIOUS_INSPECTION_DOSSIERS;
  }, []);

  // Filtered & Sorted Dossiers
  const filteredDossiers = useMemo(() => {
    return allDossiers
      .filter((dossier) => {
        // 1. Search term filter (matches name, location, sensors, id, findings, or date string)
        if (searchTerm.trim()) {
          const q = searchTerm.toLowerCase().trim();
          const matchesName = dossier.name.toLowerCase().includes(q);
          const matchesLocation = dossier.location.toLowerCase().includes(q);
          const matchesId = dossier.id.toLowerCase().includes(q);
          const matchesSensors = dossier.sensors.toLowerCase().includes(q);
          const matchesDate = dossier.date.toLowerCase().includes(q);
          const matchesFindings = dossier.findings.toLowerCase().includes(q);
          if (!matchesName && !matchesLocation && !matchesId && !matchesSensors && !matchesDate && !matchesFindings) {
            return false;
          }
        }

        // 2. Specific Date filter (e.g. YYYY-MM-DD from date input)
        if (specificDate) {
          if (dossier.date !== specificDate) return false;
        }

        // 3. Year quick filter
        if (selectedYear !== 'ALL') {
          if (!dossier.date.startsWith(selectedYear)) return false;
        }

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'date-desc') {
          return new Date(b.date).getTime() - new Date(a.date).getTime();
        }
        if (sortBy === 'date-asc') {
          return new Date(a.date).getTime() - new Date(b.date).getTime();
        }
        if (sortBy === 'name-asc') {
          return a.name.localeCompare(b.name);
        }
        if (sortBy === 'name-desc') {
          return b.name.localeCompare(a.name);
        }
        if (sortBy === 'confidence-desc') {
          return b.confidence - a.confidence;
        }
        return 0;
      });
  }, [allDossiers, searchTerm, specificDate, selectedYear, sortBy]);

  if (!isOpen) return null;

  const handleLoadDossier = (dossier: InspectionDossier) => {
    setSelectedDossierId(dossier.id);
    if (onSelectDossier) {
      onSelectDossier(dossier);
    } else if (ws.loadDossier) {
      ws.loadDossier(dossier);
    } else {
      ws.selectMission(dossier.missionId);
    }
    onClose();
  };

  const handleResetFilters = () => {
    setSearchTerm('');
    setSelectedYear('ALL');
    setSpecificDate('');
    setSortBy('date-desc');
  };

  const hasActiveFilters = Boolean(searchTerm || specificDate || selectedYear !== 'ALL');

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="bg-white border border-[#E8E8E5] rounded-2xl max-w-4xl w-full h-[88vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="h-16 px-6 border-b border-[#E8E8E5] flex items-center justify-between bg-[#FAF9F7] shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#0A0A0A] flex items-center justify-center text-white">
              <FolderArchive className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-[#111111] font-mono tracking-tight">
                  Mission Inspection Dossiers Archive
                </h3>
                <span className="text-[10px] font-mono font-bold bg-[#EAEAE5] text-[#555555] px-2 py-0.5 rounded">
                  {filteredDossiers.length} of {allDossiers.length} DOSSIERS
                </span>
              </div>
              <p className="text-[11px] text-[#6F6F6A]">
                Filter previous multi-modal inspection records and verification audits by date or name
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#6F6F6A] hover:text-[#111111] hover:bg-[#EAEAE5] transition-colors"
            aria-label="Close Dossier Archive"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="p-5 border-b border-[#E8E8E5] bg-white space-y-3.5 shrink-0">
          <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
            {/* Search Input: Name, location, or keyword */}
            <div className="sm:col-span-7 relative">
              <Search className="w-4 h-4 text-[#888888] absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                id="dossier-search-name-input"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search dossiers by name, location, sensor, or keyword..."
                className="w-full pl-9 pr-8 py-2 text-xs font-medium border border-[#D5D5D0] rounded-xl bg-[#FAF9F7] focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#111111] text-[#111111] placeholder:text-[#888888] transition-all"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-[#888888] hover:text-[#111111]"
                  aria-label="Clear search input"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Date Filter Input: Specific Date */}
            <div className="sm:col-span-3 relative">
              <Calendar className="w-3.5 h-3.5 text-[#888888] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="date"
                id="dossier-filter-date-input"
                value={specificDate}
                onChange={(e) => {
                  setSpecificDate(e.target.value);
                  if (e.target.value) setSelectedYear('ALL');
                }}
                className="w-full pl-8 pr-2 py-2 text-xs font-mono border border-[#D5D5D0] rounded-xl bg-[#FAF9F7] focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#111111] text-[#111111]"
                title="Filter by exact acquisition date"
              />
              {specificDate && (
                <button
                  onClick={() => setSpecificDate('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 text-[#888888] hover:text-[#111111]"
                  title="Clear date filter"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>

            {/* Sort Dropdown */}
            <div className="sm:col-span-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="w-full py-2 px-2.5 text-xs font-medium border border-[#D5D5D0] rounded-xl bg-[#FAF9F7] focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#111111] text-[#111111]"
              >
                <option value="date-desc">Newest Date</option>
                <option value="date-asc">Oldest Date</option>
                <option value="name-asc">Name (A-Z)</option>
                <option value="name-desc">Name (Z-A)</option>
                <option value="confidence-desc">Confidence</option>
              </select>
            </div>
          </div>

          {/* Quick Date Chips Bar */}
          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono text-[#666666] flex items-center gap-1 font-semibold uppercase">
                <Filter className="w-3 h-3 text-[#888888]" />
                Filter by Date:
              </span>
              {(['ALL', '2026', '2025', '2024'] as const).map((year) => (
                <button
                  key={year}
                  onClick={() => {
                    setSelectedYear(year);
                    setSpecificDate('');
                  }}
                  className={`px-2.5 py-1 text-xs font-mono rounded-lg transition-all ${
                    selectedYear === year && !specificDate
                      ? 'bg-[#111111] text-white font-bold shadow-xs'
                      : 'bg-[#F0F0EB] text-[#555555] hover:bg-[#E5E5E0] hover:text-[#111111]'
                  }`}
                >
                  {year === 'ALL' ? 'All Dates' : `${year} Missions`}
                </button>
              ))}
            </div>

            {hasActiveFilters && (
              <button
                onClick={handleResetFilters}
                className="flex items-center gap-1 text-[11px] font-mono text-[#888888] hover:text-[#111111] transition-colors"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset Filters</span>
              </button>
            )}
          </div>
        </div>

        {/* Dossiers List Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-[#F8F8F6]">
          {filteredDossiers.length === 0 ? (
            <div className="h-64 flex flex-col items-center justify-center text-center space-y-3 p-6 bg-white rounded-2xl border border-[#E8E8E5]">
              <FolderArchive className="w-10 h-10 text-[#CCCCCC]" />
              <div>
                <h4 className="text-sm font-bold text-[#111111]">No Inspection Dossiers Found</h4>
                <p className="text-xs text-[#777777] mt-1 max-w-sm">
                  No previous inspection records match your current date or name criteria.
                </p>
              </div>
              <button
                onClick={handleResetFilters}
                className="px-4 py-2 rounded-xl bg-[#111111] text-white text-xs font-semibold hover:bg-black transition-colors"
              >
                Clear Search & Date Filters
              </button>
            </div>
          ) : (
            filteredDossiers.map((dossier) => {
              const isCurrentMission = ws.selectedMissionId === dossier.missionId;

              return (
                <div
                  key={dossier.id}
                  className={`bg-white border rounded-2xl p-5 transition-all shadow-xs hover:shadow-sm space-y-4 ${
                    isCurrentMission
                      ? 'border-[#111111] ring-1 ring-black/10'
                      : 'border-[#E8E8E5] hover:border-[#CCCCCC]'
                  }`}
                >
                  {/* Card Header */}
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono font-bold bg-[#FAF9F7] border border-[#E8E8E5] text-[#111111] px-2 py-0.5 rounded">
                          {dossier.id}
                        </span>
                        <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
                          <Calendar className="w-3 h-3 text-emerald-700" />
                          <span>{dossier.date}</span>
                          {dossier.time && <span className="text-[#888888]">· {dossier.time}</span>}
                        </span>
                        <span className="text-[10px] font-mono font-bold text-satblue-700 bg-satblue-50 px-2 py-0.5 rounded border border-satblue-200">
                          {dossier.status}
                        </span>
                        {isCurrentMission && (
                          <span className="text-[10px] font-mono font-bold text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                            ★ ACTIVE IN WORKSPACE
                          </span>
                        )}
                      </div>
                      <h4 className="text-sm font-bold text-[#111111] font-sans">
                        {dossier.name}
                      </h4>
                      <div className="flex items-center gap-3 text-xs text-[#6F6F6A]">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-[#111111]" />
                          {dossier.location}
                        </span>
                        <span>·</span>
                        <span className="flex items-center gap-1">
                          <Satellite className="w-3 h-3 text-[#111111]" />
                          {dossier.sensors}
                        </span>
                      </div>
                    </div>

                    {/* Calibrated Confidence Badge */}
                    <div className="text-right">
                      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#FAF9F7] border border-[#E6E6E1] font-mono">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                        <span className="text-xs font-bold text-[#111111]">
                          {dossier.confidence}%
                        </span>
                        <span className="text-[10px] text-[#888888]">CONCORDANCE</span>
                      </div>
                      <div className="text-[10px] font-mono text-[#888888] mt-1">
                        {dossier.utmZone} · {dossier.areaAoi}
                      </div>
                    </div>
                  </div>

                  {/* Summary Findings */}
                  <p className="text-xs text-[#444444] font-mono leading-relaxed bg-[#FAF9F7] p-3 rounded-xl border border-[#EFEFEA]">
                    {dossier.findings}
                  </p>

                  {/* Key Metrics Strip */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {dossier.keyMetrics.map((km, idx) => (
                      <div
                        key={idx}
                        className="bg-[#FFFFFF] p-2 rounded-lg border border-[#E8E8E5] text-center"
                      >
                        <span className="text-[10px] font-mono text-[#888888] block">{km.label}</span>
                        <span className="text-xs font-mono font-bold text-[#111111]">{km.value}</span>
                      </div>
                    ))}
                  </div>

                  {/* Action Bar */}
                  <div className="pt-2 border-t border-[#F0F0EB] flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          ws.selectMission(dossier.missionId);
                          ws.toggleDrawer('evidence');
                          onClose();
                        }}
                        className="px-3 py-1.5 rounded-lg border border-[#E6E6E1] hover:bg-[#FAF9F7] text-xs font-medium text-[#111111] transition-colors flex items-center gap-1.5"
                      >
                        <ShieldCheck className="w-3.5 h-3.5 text-satblue-600" />
                        <span>Inspect Evidence</span>
                      </button>

                      <button
                        onClick={() => {
                          ws.selectMission(dossier.missionId);
                          ws.openExport('pdf');
                          onClose();
                        }}
                        className="px-3 py-1.5 rounded-lg border border-[#E6E6E1] hover:bg-[#FAF9F7] text-xs font-medium text-[#111111] transition-colors flex items-center gap-1.5"
                      >
                        <FileText className="w-3.5 h-3.5 text-[#666666]" />
                        <span>Export Dossier (PDF/GeoJSON)</span>
                      </button>
                    </div>

                    <button
                      onClick={() => handleLoadDossier(dossier)}
                      className="px-4 py-1.5 rounded-xl bg-[#0A0A0A] hover:bg-[#222222] text-white text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-all group"
                    >
                      <span>Load into Workspace</span>
                      <ArrowRight className="w-3.5 h-3.5 text-emerald-400 group-hover:translate-x-0.5 transition-transform" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="h-12 px-6 border-t border-[#E8E8E5] flex items-center justify-between bg-[#FAF9F7] text-xs text-[#6F6F6A] shrink-0 font-mono">
          <div>
            Tip: Filter by date like <code className="bg-[#EAEAE5] px-1 py-0.5 rounded text-[#111111]">2026</code> or name like <code className="bg-[#EAEAE5] px-1 py-0.5 rounded text-[#111111]">Bangalore</code>
          </div>
          <button
            onClick={onClose}
            className="px-3 py-1 rounded-lg border border-[#E6E6E1] bg-white hover:bg-[#F3F3F0] text-xs font-medium text-[#111111]"
          >
            Close Archive
          </button>
        </div>
      </div>
    </div>
  );
};
