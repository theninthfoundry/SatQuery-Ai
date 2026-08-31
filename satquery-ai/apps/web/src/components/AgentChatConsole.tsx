import React, { useState } from 'react';
import { Send, Bot, Sparkles, Loader2, AlertCircle, Download, CheckCircle2 } from 'lucide-react';
import { submitAgentQuery } from '../lib/api';
import { AgentQueryResponse } from '../types';
import { ReportExportModal } from './ReportExportModal';

interface AgentChatConsoleProps {
  currentImageId?: string | null;
  activeImageId?: string | null;
  allImageIds?: string[];
  onQueryResult: (res: AgentQueryResponse) => void;
}

export const AgentChatConsole: React.FC<AgentChatConsoleProps> = ({
  currentImageId,
  activeImageId,
  allImageIds = [],
  onQueryResult,
}) => {
  const effectiveImageId = currentImageId || activeImageId || null;
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<AgentQueryResponse | null>(null);
  const [showExportModal, setShowExportModal] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !effectiveImageId) return;

    setError(null);
    setIsLoading(true);

    try {
      // Pass current image plus any other registered images for multi-modal / multitemporal contexts
      const imageIds = [effectiveImageId, ...allImageIds.filter((id) => id !== effectiveImageId)];
      const response = await submitAgentQuery(query, imageIds);
      setLastResponse(response);
      onQueryResult(response);
    } catch (err: any) {
      setError(err.message || 'Agent orchestration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const sampleAgentQueries = [
    'What land cover classes dominate this scene?',
    'Highlight the water body and compute its area',
    'Detect surface changes between before and after images',
    'Corroborate optical findings with SAR radar backscatter',
  ];

  return (
    <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 space-y-4 shadow-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 bg-satblue-500/10 rounded-lg text-satblue-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100">SatQuery Agentic Assistant</h3>
            <p className="text-[11px] text-slate-400">Autonomous RS toolchain routing & evidence synthesis</p>
          </div>
        </div>

        {lastResponse && (
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold bg-satblue-500/10 text-satblue-400 border border-satblue-500/20">
              Intent: {lastResponse.intent}
            </span>
            <button
              onClick={() => setShowExportModal(true)}
              className="px-2.5 py-1 rounded text-[11px] font-mono bg-space-800 hover:bg-space-700 text-slate-300 hover:text-white border border-space-700 flex items-center space-x-1 transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-satblue-400" />
              <span>Export</span>
            </button>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={
            !effectiveImageId
              ? 'Upload an image first to query...'
              : 'Ask any natural-language question or give an instruction...'
          }
          disabled={!effectiveImageId || isLoading}
          className="flex-1 bg-space-950/80 border border-space-700 rounded-lg px-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-satblue-400 transition-colors disabled:opacity-50 font-mono"
        />
        <button
          type="submit"
          disabled={!effectiveImageId || !query.trim() || isLoading}
          className="px-4 py-2.5 bg-satblue-600 hover:bg-satblue-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-sm"
        >
          {isLoading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Sparkles className="w-3.5 h-3.5" />
          )}
          <span>{isLoading ? 'Orchestrating...' : 'Ask Agent'}</span>
        </button>
      </form>

      {/* Suggested prompts */}
      {effectiveImageId && (
        <div className="space-y-1 pt-1">
          <span className="text-[10px] font-mono text-slate-500 uppercase block">Sample Prompts:</span>
          <div className="flex flex-wrap gap-1.5">
            {sampleAgentQueries.map((sq, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setQuery(sq)}
                className="text-[11px] font-mono px-2.5 py-1 rounded bg-space-950/60 hover:bg-space-800 text-slate-400 hover:text-satblue-300 border border-space-800 hover:border-satblue-500/30 transition-colors text-left"
              >
                {sq}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="flex items-start space-x-2 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-lg p-2.5">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Report Export Modal */}
      {lastResponse && (
        <ReportExportModal
          isOpen={showExportModal}
          onClose={() => setShowExportModal(false)}
          jobId={lastResponse.job_id}
          reportUrls={lastResponse.report_urls}
        />
      )}
    </div>
  );
};
