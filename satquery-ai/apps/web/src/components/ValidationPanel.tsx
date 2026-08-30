import React from 'react';
import { ValidationResult } from '../types';
import { CheckCircle2, AlertTriangle, XCircle, ShieldCheck } from 'lucide-react';

interface ValidationPanelProps {
  validation: ValidationResult;
}

export const ValidationPanel: React.FC<ValidationPanelProps> = ({ validation }) => {
  const hasWarnings = validation.warnings.length > 0;
  const hasErrors = validation.errors.length > 0;

  return (
    <div className="bg-space-900 border border-space-700/80 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-satblue-400" />
          <h3 className="text-sm font-semibold text-slate-200">Validation Status</h3>
        </div>
        <div>
          {validation.valid && !hasWarnings && (
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="w-3 h-3" />
              <span>Valid Geospatial Asset</span>
            </span>
          )}
          {validation.valid && hasWarnings && (
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-mono bg-amber-500/10 text-amber-300 border border-amber-500/20">
              <AlertTriangle className="w-3 h-3 text-amber-400" />
              <span>Valid with Warnings</span>
            </span>
          )}
          {!validation.valid && (
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-mono bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <XCircle className="w-3 h-3 text-rose-400" />
              <span>Validation Failed</span>
            </span>
          )}
        </div>
      </div>

      {hasErrors && (
        <div className="space-y-1.5 pt-1">
          {validation.errors.map((err, idx) => (
            <div
              key={idx}
              className="flex items-start space-x-2 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-md p-2"
            >
              <XCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-rose-400" />
              <span>{err}</span>
            </div>
          ))}
        </div>
      )}

      {hasWarnings && (
        <div className="space-y-1.5 pt-1">
          {validation.warnings.map((warn, idx) => (
            <div
              key={idx}
              className="flex items-start space-x-2 text-xs text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-md p-2"
            >
              <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-amber-400" />
              <span>{warn}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
