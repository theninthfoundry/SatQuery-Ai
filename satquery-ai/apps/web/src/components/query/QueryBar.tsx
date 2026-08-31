'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Mic, Loader2, Lightbulb, X, Sparkles } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

export const QueryBar: React.FC = () => {
  const ws = useWorkspace();
  const [isListening, setIsListening] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleVoiceInput = () => {
    if (
      typeof window !== 'undefined' &&
      ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)
    ) {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = () => setIsListening(false);

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          ws.setQueryText(transcript);
          ws.runQuery(transcript);
        }
      };

      recognition.start();
    } else {
      ws.setQueryText('Describe the dominant land cover and detect change in this satellite scene.');
      ws.runQuery('Describe the dominant land cover and detect change in this satellite scene.');
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ws.queryText.trim() || ws.isAnalyzing) return;
    setShowSuggestions(false);
    ws.runQuery();
  };

  const prompts = ws.currentMission.prompts || [];

  return (
    <div className="relative w-full max-w-4xl mx-auto" ref={containerRef}>
      {/* Contextual Suggestions Popover */}
      {showSuggestions && prompts.length > 0 && (
        <div className="absolute bottom-full mb-2 inset-x-0 bg-white border border-[#E6E6E1] rounded-2xl shadow-xl p-3 z-30 animate-in fade-in slide-in-from-bottom-2 duration-150 space-y-2">
          <div className="flex items-center justify-between px-1 text-[10px] font-mono font-bold text-[#6F6F6A] uppercase">
            <span className="flex items-center gap-1.5">
              <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
              <span>Contextual Queries for {ws.currentMission.tag}</span>
            </span>
            <button
              onClick={() => setShowSuggestions(false)}
              className="text-[#888888] hover:text-[#111111]"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-1.5">
            {prompts.map((p, idx) => (
              <button
                key={idx}
                onClick={() => {
                  ws.setQueryText(p);
                  setShowSuggestions(false);
                  ws.runQuery(p);
                }}
                className="w-full text-left p-2.5 rounded-xl hover:bg-[#FAF9F7] text-xs font-sans text-[#222222] transition-colors border border-transparent hover:border-[#E6E6E1] flex items-center justify-between group"
              >
                <span>{p}</span>
                <Sparkles className="w-3.5 h-3.5 text-[#AAAAAA] group-hover:text-[#111111] shrink-0 ml-2 transition-colors" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Query Bar */}
      <form
        onSubmit={handleSubmit}
        className={`relative flex items-center bg-white border rounded-2xl px-2 py-1.5 shadow-md transition-all ${
          ws.isAnalyzing
            ? 'border-amber-400 ring-2 ring-amber-100'
            : 'border-[#E6E6E1] hover:border-[#CCCCCC] focus-within:border-[#111111] focus-within:ring-1 focus-within:ring-black/5'
        }`}
      >
        {/* Suggestions Helper Toggle */}
        <button
          type="button"
          onClick={() => setShowSuggestions((prev) => !prev)}
          className={`p-2 rounded-xl transition-colors ${
            showSuggestions
              ? 'bg-[#FAF9F7] text-amber-600'
              : 'text-[#888888] hover:text-[#111111] hover:bg-[#FAF9F7]'
          }`}
          title="Contextual query suggestions"
        >
          <Lightbulb className="w-4 h-4" />
        </button>

        {/* Query Input */}
        <input
          type="text"
          value={ws.queryText}
          onChange={(e) => ws.setQueryText(e.target.value)}
          onFocus={() => {
            if (!ws.queryText.trim()) setShowSuggestions(true);
          }}
          placeholder={
            ws.isAnalyzing
              ? 'Analyzing query across remote-sensing observations...'
              : 'Ask SatQuery about these observations (Press / to focus)...'
          }
          disabled={ws.isAnalyzing}
          className="flex-1 px-3 py-2 text-xs font-sans text-[#111111] placeholder-[#888888] bg-transparent focus:outline-none disabled:opacity-75"
        />

        {/* Action Buttons */}
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={handleVoiceInput}
            className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${
              isListening
                ? 'bg-rose-500 text-white animate-pulse shadow-md'
                : 'text-[#6F6F6A] hover:text-[#111111] hover:bg-[#FAF9F7]'
            }`}
            title={isListening ? 'Listening via Web Speech API...' : 'Voice Query'}
          >
            <Mic className="w-4 h-4" />
          </button>

          <button
            type="submit"
            disabled={!ws.queryText.trim() || ws.isAnalyzing}
            className="w-8 h-8 rounded-full bg-[#111111] text-white flex items-center justify-center hover:bg-black transition-transform active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed shadow-sm"
            title="Dispatch Query (Enter)"
          >
            {ws.isAnalyzing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
            ) : (
              <ArrowUp className="w-4 h-4 stroke-[2.5]" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
