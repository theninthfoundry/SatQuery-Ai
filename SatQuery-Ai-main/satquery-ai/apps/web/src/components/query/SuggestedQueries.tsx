'use client';

import React from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';

interface SuggestedQueriesProps {
  prompts?: string[];
  onSelectPrompt?: (prompt: string) => void;
  disabled?: boolean;
}

export const SuggestedQueries: React.FC<SuggestedQueriesProps> = ({
  prompts: propPrompts,
  onSelectPrompt: propOnSelectPrompt,
  disabled: propDisabled,
}) => {
  const ws = useWorkspace();

  const prompts = propPrompts || ws.currentMission.prompts;
  const onSelectPrompt = propOnSelectPrompt || ws.runQuery;
  const disabled = propDisabled !== undefined ? propDisabled : ws.isAnalyzing;

  return (
    <div className="flex flex-wrap items-center gap-2 select-none">
      <span className="text-[10px] font-mono font-bold tracking-wider text-[#888888] uppercase mr-1">
        SUGGESTED QUERIES
      </span>

      {prompts.map((prompt) => (
        <button
          key={prompt}
          onClick={() => onSelectPrompt(prompt)}
          disabled={disabled}
          className="px-3 py-1 rounded-full text-xs font-sans text-[#555555] bg-white border border-[#E8E8E5] hover:border-[#CCCCCC] hover:text-[#111111] hover:shadow-subtle transition-all active:scale-98 disabled:opacity-40"
        >
          {prompt}
        </button>
      ))}
    </div>
  );
};
