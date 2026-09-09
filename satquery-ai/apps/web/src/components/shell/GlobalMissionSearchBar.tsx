'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  Target,
  FileText,
  MapPin,
  Globe,
  Loader2,
  X,
  Sparkles,
  Command,
} from 'lucide-react';
import { useWorkspace, CANONICAL_MISSIONS } from '../../context/WorkspaceContext';

interface Suggestion {
  id: string;
  type: 'mission' | 'report' | 'coordinate' | 'stac' | 'finding';
  title: string;
  subtitle: string;
  badge: string;
  data: any;
}

export const GlobalMissionSearchBar: React.FC = () => {
  const ws = useWorkspace();
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceTimerRef = useRef<any>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard shortcut (⌘K or Ctrl+K) to focus search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
        setIsOpen(true);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Debounced API fetch
  useEffect(() => {
    if (!query.trim()) {
      setSuggestions([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);

    debounceTimerRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`/api/v1/search?q=${encodeURIComponent(query.trim())}`);
        if (res.ok) {
          const data = await res.json();
          setSuggestions(data.suggestions || []);
          setSelectedIndex(0);
          setIsOpen(true);
        }
      } catch (err) {
        console.error('Search query error:', err);
      } finally {
        setIsLoading(false);
      }
    }, 220);

    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, [query]);

  const handleSelect = (item: Suggestion) => {
    setIsOpen(false);
    setQuery('');

    if (item.type === 'mission') {
      ws.selectMission(item.data.id);
    } else if (item.type === 'coordinate') {
      const { lat, lon } = item.data;
      ws.updateMissionLocation({
        name: `Coordinates (${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E)`,
        lat,
        lon,
        utmZone: `EPSG:${Math.floor((lon + 180) / 6) + 32601}`,
        areaAoi: '15.0 km²',
      });
      ws.setQueryText(`Analyze land cover at coordinates ${lat}°N, ${lon}°E`);
    } else if (item.type === 'report') {
      ws.openExport('pdf');
    } else if (item.type === 'stac') {
      ws.setIsEarthExplorerOpen(true);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || suggestions.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % suggestions.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + suggestions.length) % suggestions.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      handleSelect(suggestions[selectedIndex]);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const getItemIcon = (type: string) => {
    switch (type) {
      case 'mission':
        return <Target className="w-3.5 h-3.5 text-blue-400" />;
      case 'report':
        return <FileText className="w-3.5 h-3.5 text-amber-400" />;
      case 'coordinate':
        return <MapPin className="w-3.5 h-3.5 text-emerald-400" />;
      case 'stac':
        return <Globe className="w-3.5 h-3.5 text-cyan-400" />;
      default:
        return <Sparkles className="w-3.5 h-3.5 text-neutral-400" />;
    }
  };

  return (
    <div className="relative w-72 md:w-88" ref={containerRef}>
      {/* Search Input Field */}
      <div className="relative flex items-center">
        <Search className="w-3.5 h-3.5 text-neutral-500 absolute left-2.5 pointer-events-none" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (suggestions.length > 0) setIsOpen(true);
          }}
          onKeyDown={handleKeyDown}
          placeholder="Search missions, reports, coords... (⌘K)"
          className="w-full bg-[#141414] border border-neutral-800 focus:border-neutral-600 rounded-md pl-8 pr-7 py-1 text-xs font-mono text-white placeholder-neutral-500 focus:outline-none transition-colors"
        />

        <div className="absolute right-2 flex items-center gap-1">
          {isLoading ? (
            <Loader2 className="w-3 h-3 text-neutral-400 animate-spin" />
          ) : query ? (
            <button
              onClick={() => {
                setQuery('');
                setSuggestions([]);
                setIsOpen(false);
              }}
              className="text-neutral-500 hover:text-white"
            >
              <X className="w-3 h-3" />
            </button>
          ) : (
            <kbd className="hidden sm:inline-block px-1 py-0.2 text-[9px] font-mono text-neutral-500 bg-neutral-900 border border-neutral-800 rounded">
              ⌘K
            </kbd>
          )}
        </div>
      </div>

      {/* Debounced Suggestion Dropdown */}
      {isOpen && suggestions.length > 0 && (
        <div className="absolute left-0 right-0 top-full mt-1 bg-[#141414] border border-neutral-800 rounded-md shadow-2xl z-50 overflow-hidden text-xs font-mono max-h-80 overflow-y-auto">
          <div className="px-3 py-1.5 text-[9px] font-bold text-neutral-500 uppercase tracking-widest border-b border-neutral-800 bg-[#161616] flex justify-between">
            <span>SUGGESTED RESULTS</span>
            <span>{suggestions.length} MATCHES</span>
          </div>

          <div className="py-1">
            {suggestions.map((item, idx) => {
              const isSelected = selectedIndex === idx;
              return (
                <button
                  key={item.id}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`w-full text-left px-3 py-2 flex items-start gap-2.5 transition-colors ${
                    isSelected ? 'bg-neutral-800 text-white' : 'text-neutral-300 hover:bg-neutral-800/60'
                  }`}
                >
                  <div className="mt-0.5 shrink-0">{getItemIcon(item.type)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1 mb-0.5">
                      <span className="font-medium text-white truncate text-[11px]">
                        {item.title}
                      </span>
                      <span className="text-[8px] px-1.5 py-0.2 rounded bg-neutral-900 border border-neutral-700/60 text-neutral-400 font-bold shrink-0">
                        {item.badge}
                      </span>
                    </div>
                    <p className="text-[10px] text-neutral-400 truncate">{item.subtitle}</p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
