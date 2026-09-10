import React, { useState, useEffect } from 'react';
import {
  Send,
  Bot,
  Sparkles,
  MapPin,
  MessageSquare,
  TrendingUp,
  Radio,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import {
  submitVQA,
  submitGrounding,
  submitChangeAnalysis,
  submitOpticalSARAnalysis,
  fetchImagesList,
} from '../lib/api';
import {
  VQAAnalysisResult,
  GroundingAnalysisResult,
  ChangeAnalysisResult,
  OpticalSARAnalysisResult,
  ImageSummary,
} from '../types';

interface QueryConsoleProps {
  currentImageId: string | null;
  onVQASuccess: (res: VQAAnalysisResult) => void;
  onGroundingSuccess: (res: GroundingAnalysisResult) => void;
  onChangeSuccess: (res: ChangeAnalysisResult) => void;
  onOpticalSARSuccess: (res: OpticalSARAnalysisResult) => void;
}

export const QueryConsole: React.FC<QueryConsoleProps> = ({
  currentImageId,
  onVQASuccess,
  onGroundingSuccess,
  onChangeSuccess,
  onOpticalSARSuccess,
}) => {
  const [activeTab, setActiveTab] = useState<'vqa' | 'grounding' | 'change' | 'optical_sar'>('vqa');
  const [query, setQuery] = useState('');
  const [imagesList, setImagesList] = useState<ImageSummary[]>([]);
  const [beforeId, setBeforeId] = useState<string>('');
  const [afterId, setAfterId] = useState<string>('');
  const [opticalId, setOpticalId] = useState<string>('');
  const [sarId, setSarId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchImagesList().then((imgs) => {
      setImagesList(imgs);
      if (imgs.length >= 2) {
        setBeforeId(imgs[imgs.length - 1].id);
        setAfterId(imgs[0].id);
        setOpticalId(imgs[0].id);
        setSarId(imgs[1].id);
      } else if (imgs.length === 1) {
        setBeforeId(imgs[0].id);
        setAfterId(imgs[0].id);
        setOpticalId(imgs[0].id);
        setSarId(imgs[0].id);
      }
    });
  }, [currentImageId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (activeTab === 'vqa') {
        if (!currentImageId || !query.trim()) return;
        const result = await submitVQA(currentImageId, query);
        onVQASuccess(result);
      } else if (activeTab === 'grounding') {
        if (!currentImageId || !query.trim()) return;
        const result = await submitGrounding(currentImageId, query);
        onGroundingSuccess(result);
      } else if (activeTab === 'change') {
        if (!beforeId || !afterId) {
          throw new Error('Please select both a Before image and an After image.');
        }
        const result = await submitChangeAnalysis(beforeId, afterId, 0.5);
        onChangeSuccess(result);
      } else if (activeTab === 'optical_sar') {
        if (!opticalId || !sarId) {
          throw new Error('Please select both an Optical image and a SAR image.');
        }
        const result = await submitOpticalSARAnalysis(opticalId, sarId);
        onOpticalSARSuccess(result);
      }
    } catch (err: any) {
      setError(err.message || 'Analysis request failed');
    } finally {
      setIsLoading(false);
    }
  };

  const sampleVQAQueries = [
    'What land cover types are visible in this scene?',
    'Identify dominant infrastructure and buildings.',
  ];

  const sampleGroundingQueries = [
    'Highlight the water body',
    'Locate industrial structures',
  ];

  return (
    <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 space-y-4 shadow-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Bot className="w-4 h-4 text-satblue-400" />
          <h3 className="text-sm font-bold text-slate-100">SatQuery Perception Console</h3>
        </div>

        {/* Tab switchers */}
        <div className="flex bg-space-950/80 p-0.5 rounded-lg border border-space-800 text-xs font-mono">
          <button
            onClick={() => {
              setActiveTab('vqa');
              setError(null);
            }}
            className={`px-2.5 py-1 rounded-md flex items-center space-x-1.5 transition-colors ${
              activeTab === 'vqa'
                ? 'bg-satblue-600 text-white font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>VQA</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('grounding');
              setError(null);
            }}
            className={`px-2.5 py-1 rounded-md flex items-center space-x-1.5 transition-colors ${
              activeTab === 'grounding'
                ? 'bg-satblue-600 text-white font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <MapPin className="w-3.5 h-3.5" />
            <span>Grounding</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('change');
              setError(null);
            }}
            className={`px-2.5 py-1 rounded-md flex items-center space-x-1.5 transition-colors ${
              activeTab === 'change'
                ? 'bg-rose-600 text-white font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Change</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('optical_sar');
              setError(null);
            }}
            className={`px-2.5 py-1 rounded-md flex items-center space-x-1.5 transition-colors ${
              activeTab === 'optical_sar'
                ? 'bg-emerald-600 text-white font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            <span>Optical+SAR</span>
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        {activeTab === 'vqa' || activeTab === 'grounding' ? (
          <div className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                !currentImageId
                  ? 'Upload an image first to query...'
                  : activeTab === 'vqa'
                  ? 'Ask a question about the image...'
                  : 'Enter referring expression (e.g. "Highlight the water body")...'
              }
              disabled={!currentImageId || isLoading}
              className="flex-1 bg-space-950/80 border border-space-700 rounded-lg px-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-satblue-400 transition-colors disabled:opacity-50 font-mono"
            />
            <button
              type="submit"
              disabled={!currentImageId || !query.trim() || isLoading}
              className="px-4 py-2.5 bg-satblue-600 hover:bg-satblue-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-sm"
            >
              {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
              <span>{isLoading ? 'Analyzing...' : 'Execute'}</span>
            </button>
          </div>
        ) : activeTab === 'change' ? (
          <div className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div>
                <label className="text-slate-400 block mb-1 text-[11px]">Before Image (T1):</label>
                <select
                  value={beforeId}
                  onChange={(e) => setBeforeId(e.target.value)}
                  className="w-full bg-space-950/80 border border-space-700 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-satblue-400"
                >
                  {imagesList.map((img) => (
                    <option key={`before-${img.id}`} value={img.id}>
                      {img.filename} ({img.id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1 text-[11px]">After Image (T2):</label>
                <select
                  value={afterId}
                  onChange={(e) => setAfterId(e.target.value)}
                  className="w-full bg-space-950/80 border border-space-700 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-satblue-400"
                >
                  {imagesList.map((img) => (
                    <option key={`after-${img.id}`} value={img.id}>
                      {img.filename} ({img.id})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={!beforeId || !afterId || isLoading}
              className="w-full py-2.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors shadow-sm"
            >
              {isLoading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <TrendingUp className="w-3.5 h-3.5" />
              )}
              <span>{isLoading ? 'Quantifying Change...' : 'Run Bi-Temporal Change Detection'}</span>
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div>
                <label className="text-slate-400 block mb-1 text-[11px]">Optical Asset (Sentinel-2):</label>
                <select
                  value={opticalId}
                  onChange={(e) => setOpticalId(e.target.value)}
                  className="w-full bg-space-950/80 border border-space-700 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-satblue-400"
                >
                  {imagesList.map((img) => (
                    <option key={`opt-${img.id}`} value={img.id}>
                      {img.filename} ({img.id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1 text-[11px]">SAR Asset (Sentinel-1 / RISAT):</label>
                <select
                  value={sarId}
                  onChange={(e) => setSarId(e.target.value)}
                  className="w-full bg-space-950/80 border border-space-700 rounded-lg px-3 py-2 text-slate-200 text-xs focus:outline-none focus:border-satblue-400"
                >
                  {imagesList.map((img) => (
                    <option key={`sar-${img.id}`} value={img.id}>
                      {img.filename} ({img.id})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={!opticalId || !sarId || isLoading}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors shadow-sm"
            >
              {isLoading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Radio className="w-3.5 h-3.5" />
              )}
              <span>{isLoading ? 'Corroborating Multimodal Data...' : 'Run DOFA Optical + SAR Corroboration'}</span>
            </button>
          </div>
        )}
      </form>

      {/* Suggested prompts for VQA/Grounding */}
      {currentImageId && (activeTab === 'vqa' || activeTab === 'grounding') && (
        <div className="space-y-1 pt-1">
          <span className="text-[10px] font-mono text-slate-500 uppercase block">Suggested:</span>
          <div className="flex flex-wrap gap-1.5">
            {(activeTab === 'vqa' ? sampleVQAQueries : sampleGroundingQueries).map((sq, idx) => (
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
    </div>
  );
};
