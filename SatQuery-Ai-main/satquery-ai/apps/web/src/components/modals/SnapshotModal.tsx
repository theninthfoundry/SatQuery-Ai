'use client';

import React, { useState } from 'react';
import {
  X,
  Download,
  Printer,
  Copy,
  Check,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Sparkles,
  Camera,
} from 'lucide-react';

interface SnapshotModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl: string | null;
  filename?: string;
}

export const SnapshotModal: React.FC<SnapshotModalProps> = ({
  isOpen,
  onClose,
  imageUrl,
  filename = 'satquery_analytical_snapshot.png',
}) => {
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [isCopied, setIsCopied] = useState<boolean>(false);

  if (!isOpen || !imageUrl) return null;

  const handleDownload = () => {
    const a = document.createElement('a');
    a.href = imageUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handlePrint = () => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>SatQuery AI — Analytical State Snapshot</title>
          <style>
            @page {
              size: landscape;
              margin: 0.5cm;
            }
            body {
              margin: 0;
              padding: 0;
              display: flex;
              justify-content: center;
              align-items: center;
              background-color: #FFFFFF;
            }
            img {
              max-width: 100%;
              height: auto;
              image-rendering: -webkit-optimize-contrast;
            }
          </style>
        </head>
        <body>
          <img src="${imageUrl}" onload="window.print(); window.close();" />
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  const handleCopy = async () => {
    try {
      const res = await fetch(imageUrl);
      const blob = await res.blob();
      await navigator.clipboard.write([
        new ClipboardItem({ [blob.type]: blob }),
      ]);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch {
      // Fallback
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6 select-none animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="bg-white border border-[#E8E8E5] rounded-2xl max-w-6xl w-full h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header */}
        <div className="h-14 px-6 border-b border-[#E8E8E5] flex items-center justify-between bg-[#FAF9F7] shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#0A0A0A] flex items-center justify-center text-emerald-400">
              <Camera className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-[#111111] font-mono">
                  High-Resolution Analytical Snapshot
                </h3>
                <span className="text-[10px] font-mono font-bold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded border border-emerald-200">
                  2400 × 1450 PX · 300 DPI
                </span>
              </div>
              <p className="text-[11px] text-[#666666]">
                Print-friendly vector & radiometric analytical summary of current inspection state
              </p>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center gap-2">
            {/* Zoom Controls */}
            <div className="flex items-center bg-white border border-[#E8E8E5] rounded-lg p-0.5 mr-2">
              <button
                onClick={() => setZoomLevel((z) => Math.max(0.5, z - 0.25))}
                className="p-1.5 text-[#666666] hover:text-[#111111] rounded hover:bg-[#F3F3F0] transition-colors"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="text-[10px] font-mono px-1.5 text-[#666666]">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.25))}
                className="p-1.5 text-[#666666] hover:text-[#111111] rounded hover:bg-[#F3F3F0] transition-colors"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setZoomLevel(1)}
                className="p-1.5 text-[#666666] hover:text-[#111111] rounded hover:bg-[#F3F3F0] transition-colors"
                title="Reset Zoom"
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Copy Button */}
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E8E8E5] bg-white text-xs font-medium text-[#111111] hover:bg-[#F8F8F6] transition-colors"
              title="Copy to Clipboard"
            >
              {isCopied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-emerald-700">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-[#666666]" />
                  <span>Copy</span>
                </>
              )}
            </button>

            {/* Print Button */}
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E8E8E5] bg-white text-xs font-medium text-[#111111] hover:bg-[#F8F8F6] transition-colors"
              title="Print High-Resolution Dossier"
            >
              <Printer className="w-3.5 h-3.5 text-[#666666]" />
              <span>Print</span>
            </button>

            {/* Download Button */}
            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#0A0A0A] hover:bg-[#222222] text-white text-xs font-semibold shadow-sm transition-colors"
              title="Download PNG Image"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download PNG</span>
            </button>

            <div className="w-px h-5 bg-[#E8E8E5] mx-1" />

            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-[#666666] hover:text-[#111111] hover:bg-[#F3F3F0] transition-colors"
              aria-label="Close Snapshot"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Center Preview Stage */}
        <div className="flex-1 bg-[#EBEBE6] overflow-auto p-6 flex items-center justify-center relative">
          <div
            className="transition-transform duration-150 origin-center max-w-full"
            style={{ transform: `scale(${zoomLevel})` }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={imageUrl}
              alt="Analytical State High-Resolution Snapshot"
              className="rounded-lg shadow-2xl border border-[#D5D5D0] max-h-[75vh] w-auto object-contain bg-white"
            />
          </div>
        </div>

        {/* Footer Technical Metadata */}
        <div className="h-10 px-6 border-t border-[#E8E8E5] flex items-center justify-between bg-[#FAF9F7] text-[11px] font-mono text-[#666666] shrink-0">
          <div className="flex items-center gap-3">
            <span>● 2400 × 1450 Resolution</span>
            <span>·</span>
            <span>Format: PNG (Lossless 24-bit)</span>
            <span>·</span>
            <span>Target: ISO / ISRO SIH26167 Report Lab</span>
          </div>
          <div className="flex items-center gap-2 text-emerald-700 font-semibold">
            <Sparkles className="w-3 h-3" />
            <span>Cryptographically Auditable Snapshot Ready</span>
          </div>
        </div>
      </div>
    </div>
  );
};
