import React from 'react';
import { OpticalSARAnalysisResult } from '../types';
import { ShieldCheck, Radio, Sun, CheckCircle2, Sparkles, AlertTriangle } from 'lucide-react';

interface CorroborationCardProps {
  result: OpticalSARAnalysisResult;
}

export const CorroborationCard: React.FC<CorroborationCardProps> = ({ result }) => {
  const agreementPercent = Math.round(result.corroboration_score * 100);

  return (
    <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 space-y-4 shadow-lg">
      <div className="flex items-center justify-between pb-3 border-b border-space-800">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-bold text-slate-100">Cross-Modal Corroboration</h3>
        </div>
        <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>{agreementPercent}% Mutual Agreement</span>
        </div>
      </div>

      {/* Joint Claim */}
      <div className="bg-space-950/70 p-3.5 rounded-lg border border-space-800">
        <span className="text-[10px] font-mono text-satblue-400 uppercase font-bold block mb-1">
          Joint Multimodal Finding (DOFA ViT-Base Fusion)
        </span>
        <p className="text-xs text-slate-200 font-medium leading-relaxed">{result.joint_claim}</p>
      </div>

      {/* Sensor Comparison Telemetry */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
        {/* Optical Sensor Box */}
        <div className="bg-space-950/60 p-3 rounded-lg border border-space-800 space-y-1.5">
          <div className="flex items-center space-x-1.5 text-amber-400 font-bold">
            <Sun className="w-3.5 h-3.5" />
            <span>Optical (Sentinel-2)</span>
          </div>
          <div className="text-slate-300 text-[11px]">Bands: {result.optical_features.band_count}</div>
          <div className="text-slate-300 text-[11px]">
            Mean RGB: [{result.optical_features.mean_spectral.join(', ')}]
          </div>
          <div className="text-slate-400 text-[10px]">
            Water Proxy: {Math.round(result.optical_features.water_fraction_proxy * 100)}%
          </div>
        </div>

        {/* SAR Sensor Box */}
        <div className="bg-space-950/60 p-3 rounded-lg border border-space-800 space-y-1.5">
          <div className="flex items-center space-x-1.5 text-satblue-400 font-bold">
            <Radio className="w-3.5 h-3.5" />
            <span>SAR (Sentinel-1 / RISAT)</span>
          </div>
          <div className="text-slate-300 text-[11px]">
            Polarization: {result.sar_features.polarization}
          </div>
          <div className="text-slate-300 text-[11px]">
            Mean Backscatter: {result.sar_features.mean_sigma0_db} dB
          </div>
          <div className="text-slate-400 text-[10px]">
            Range: [{result.sar_features.min_sigma0_db} dB, {result.sar_features.max_sigma0_db} dB]
          </div>
        </div>
      </div>
    </div>
  );
};
