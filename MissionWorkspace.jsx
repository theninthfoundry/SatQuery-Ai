import { useState, useRef, useEffect } from "react";
import {
  ZoomIn,
  ZoomOut,
  Crosshair,
  Layers,
  Ruler,
  ArrowUp,
  ChevronDown,
  ChevronRight,
  Check,
  Circle,
  Loader2,
  Download,
  Cpu,
  X,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Static mission data (would come from the orchestrator / evidence engine)
// ---------------------------------------------------------------------------

const MISSION_STEPS = [
  { n: "01", key: "data", label: "Data" },
  { n: "02", key: "query", label: "Query" },
  { n: "03", key: "analysis", label: "Analysis" },
  { n: "04", key: "evidence", label: "Evidence" },
  { n: "05", key: "trace", label: "Trace" },
  { n: "06", key: "export", label: "Export" },
];

const DATASETS = [
  { label: "Optical", sensor: "Sentinel-2", res: "10 m · EPSG:32643", dims: "10980 × 10980", status: "Valid" },
  { label: "SAR", sensor: "Sentinel-1 · C-band", res: "10 m", dims: "10680 × 10680", status: "Compatible" },
];

const LENS_OPTIONS = ["True color", "NIR", "SAR", "Change", "Evidence"];

const LAYERS_DEFAULT = [
  { key: "optical", label: "Optical", on: true },
  { key: "sar", label: "SAR", on: false },
  { key: "change", label: "Change mask", on: false },
  { key: "grounding", label: "Grounding", on: false },
  { key: "geojson", label: "GeoJSON", on: false },
];

const TRACE_STEPS = [
  { key: "understand", label: "Understanding query" },
  { key: "validate", label: "Validating inputs" },
  { key: "select", label: "Selecting analysis" },
  { key: "change", label: "Running ChangeNet" },
  { key: "evidence", label: "Generating spatial evidence" },
  { key: "measure", label: "Calculating area" },
  { key: "synthesize", label: "Synthesizing result" },
];

const REGIONS = [
  { id: "04", top: "34%", left: "42%", w: "18%", h: "14%", area: "1.82 ha", type: "Built-up development", confidence: 84 },
  { id: "07", top: "58%", left: "22%", w: "10%", h: "9%", area: "0.51 ha", type: "Built-up development", confidence: 76 },
  { id: "11", top: "20%", left: "64%", w: "8%", h: "7%", area: "0.23 ha", type: "Built-up development", confidence: 69 },
];

const SUGGESTED_PROMPTS = [
  "Has built-up area increased, and where?",
  "Highlight the water body.",
  "Compare optical and SAR evidence.",
];

const EVIDENCE_ITEMS = [
  { key: "optical", label: "Optical", detail: "Spectral evidence" },
  { key: "sar", label: "SAR", detail: "Structural evidence" },
  { key: "change", label: "Change model", detail: "Temporal difference" },
  { key: "geometry", label: "Geometry", detail: "Deterministic area" },
];

// ---------------------------------------------------------------------------

export default function MissionWorkspace() {
  const [activeStep, setActiveStep] = useState("data");
  const [lens, setLens] = useState("Change");
  const [layers, setLayers] = useState(LAYERS_DEFAULT);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("idle"); // idle | analyzing | complete
  const [traceIndex, setTraceIndex] = useState(-1);
  const [traceExpanded, setTraceExpanded] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [why, setWhy] = useState(false);
  const [toast, setToast] = useState(null);
  const timerRef = useRef(null);

  useEffect(() => {
    return () => clearTimeout(timerRef.current);
  }, []);

  function toggleLayer(key) {
    setLayers((prev) => prev.map((l) => (l.key === key ? { ...l, on: !l.on } : l)));
  }

  function runAnalysis(text) {
    const q = (text ?? query).trim();
    if (!q) return;
    clearTimeout(timerRef.current);
    setQuery(q);
    setStatus("analyzing");
    setActiveStep("analysis");
    setSelectedRegion(null);
    setWhy(false);
    setTraceIndex(0);

    let i = 0;
    const step = () => {
      i += 1;
      if (i < TRACE_STEPS.length) {
        setTraceIndex(i);
        timerRef.current = setTimeout(step, 480);
      } else {
        setStatus("complete");
        setLayers((prev) =>
          prev.map((l) => (l.key === "change" ? { ...l, on: true } : l))
        );
      }
    };
    timerRef.current = setTimeout(step, 480);
  }

  function exportMission() {
    setToast("Mission dossier exported");
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => setToast(null), 2200);
  }

  return (
    <div className="w-full h-screen min-h-[640px] bg-neutral-950 text-neutral-200 flex flex-col font-sans">
      {/* ---------------------------------------------------------------- */}
      {/* Header                                                          */}
      {/* ---------------------------------------------------------------- */}
      <header className="h-14 shrink-0 flex items-center justify-between px-4 border-b border-neutral-800 bg-neutral-950">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span className="font-semibold tracking-wide text-neutral-100">SATQUERY</span>
          </div>
          <span className="hidden sm:block text-xs text-neutral-500 border-l border-neutral-800 pl-3">
            Multimodal Earth Observation Intelligence
          </span>
        </div>

        <div className="flex items-center gap-4">
          <span className="hidden md:flex items-center gap-1.5 text-xs text-neutral-500 font-mono">
            MISSION <span className="text-neutral-300">0247</span>
          </span>
          <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-mono">
            <Circle className="w-2 h-2 fill-emerald-400 stroke-none" />
            SYSTEM READY
          </span>
          <span className="hidden sm:flex items-center gap-1.5 text-xs text-neutral-400 font-mono border border-neutral-800 rounded px-2 py-1">
            <Cpu className="w-3.5 h-3.5" />
            RTX 4060 · 7.2/8 GB
          </span>
          <button
            onClick={exportMission}
            className="flex items-center gap-1.5 text-xs text-neutral-300 border border-neutral-800 rounded px-2.5 py-1.5 hover:bg-neutral-900 hover:border-neutral-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            Export
          </button>
        </div>
      </header>

      {/* ---------------------------------------------------------------- */}
      {/* Main three-panel layout                                         */}
      {/* ---------------------------------------------------------------- */}
      <div className="flex-1 flex min-h-0">
        {/* ---------------- LEFT: Mission ---------------- */}
        <aside className="w-56 shrink-0 border-r border-neutral-800 flex flex-col overflow-y-auto">
          <nav className="py-2">
            {MISSION_STEPS.map((s) => {
              const active = activeStep === s.key;
              return (
                <button
                  key={s.key}
                  onClick={() => setActiveStep(s.key)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 text-left text-sm border-l-2 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-cyan-400 ${
                    active
                      ? "border-cyan-400 text-neutral-100 bg-neutral-900"
                      : "border-transparent text-neutral-500 hover:text-neutral-300 hover:bg-neutral-900/60"
                  }`}
                >
                  <span className="font-mono text-[11px] text-neutral-600">{s.n}</span>
                  {s.label}
                </button>
              );
            })}
          </nav>

          <div className="mt-2 px-4 pb-4 space-y-3">
            <p className="text-[11px] tracking-wide text-neutral-600 uppercase">Datasets</p>
            {DATASETS.map((d) => (
              <div key={d.label} className="border border-neutral-800 rounded-md p-3 bg-neutral-900/50">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-neutral-200">{d.label}</span>
                  <span className="flex items-center gap-1 text-[11px] text-emerald-400">
                    <Check className="w-3 h-3" />
                    {d.status}
                  </span>
                </div>
                <p className="text-[11px] text-neutral-500 mt-1">{d.sensor}</p>
                <p className="text-[11px] font-mono text-neutral-500">{d.res}</p>
              </div>
            ))}
          </div>
        </aside>

        {/* ---------------- CENTER: Geo workspace ---------------- */}
        <main className="flex-1 min-w-0 flex flex-col relative bg-neutral-950">
          {/* Analysis lens tabs */}
          <div className="flex items-center gap-1 px-4 py-2 border-b border-neutral-800 overflow-x-auto">
            {LENS_OPTIONS.map((l) => (
              <button
                key={l}
                onClick={() => setLens(l)}
                className={`px-2.5 py-1 rounded text-xs whitespace-nowrap transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
                  lens === l
                    ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/40"
                    : "text-neutral-500 border border-transparent hover:text-neutral-300"
                }`}
              >
                {l}
              </button>
            ))}
          </div>

          {/* Canvas */}
          <div className="flex-1 relative overflow-hidden">
            <div
              className="absolute inset-0"
              style={{
                backgroundImage:
                  "linear-gradient(135deg, #14201c 0%, #101a1f 40%, #0c1418 100%)",
              }}
            >
              <div
                className="absolute inset-0 opacity-[0.15]"
                style={{
                  backgroundImage:
                    "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
                  backgroundSize: "48px 48px",
                }}
              />
            </div>

            {/* Change regions (visible once analysis completes) */}
            {status === "complete" &&
              REGIONS.map((r) => {
                const selected = selectedRegion === r.id;
                return (
                  <button
                    key={r.id}
                    onClick={() => setSelectedRegion(selected ? null : r.id)}
                    style={{ top: r.top, left: r.left, width: r.w, height: r.h }}
                    className={`absolute rounded-sm border transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
                      selected
                        ? "border-red-400 bg-red-500/20"
                        : "border-red-500/60 bg-red-500/10 hover:bg-red-500/20"
                    }`}
                  >
                    <span className="absolute -top-5 left-0 text-[10px] font-mono text-red-300 bg-neutral-950/80 px-1 rounded">
                      {r.id}
                    </span>
                  </button>
                );
              })}

            {/* Analyzing overlay trace card */}
            {status === "analyzing" && (
              <div className="absolute top-4 left-4 w-64 border border-neutral-800 bg-neutral-900/90 backdrop-blur-sm rounded-md p-3">
                <p className="text-[11px] tracking-wide text-neutral-500 uppercase mb-2">SatQuery analyst</p>
                <ul className="space-y-1.5">
                  {TRACE_STEPS.map((s, i) => {
                    const done = i < traceIndex;
                    const active = i === traceIndex;
                    return (
                      <li key={s.key} className="flex items-center gap-2 text-xs">
                        {done ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        ) : active ? (
                          <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin shrink-0" />
                        ) : (
                          <Circle className="w-3.5 h-3.5 text-neutral-700 shrink-0" />
                        )}
                        <span className={done || active ? "text-neutral-300" : "text-neutral-600"}>
                          {s.label}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* Floating zoom controls */}
            <div className="absolute bottom-4 left-4 flex flex-col border border-neutral-800 bg-neutral-900/80 backdrop-blur-sm rounded-md overflow-hidden">
              <button className="p-2 hover:bg-neutral-800 text-neutral-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400" aria-label="Zoom in">
                <ZoomIn className="w-4 h-4" />
              </button>
              <button className="p-2 hover:bg-neutral-800 text-neutral-400 border-t border-neutral-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400" aria-label="Zoom out">
                <ZoomOut className="w-4 h-4" />
              </button>
              <button className="p-2 hover:bg-neutral-800 text-neutral-400 border-t border-neutral-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400" aria-label="Recenter">
                <Crosshair className="w-4 h-4" />
              </button>
              <button className="p-2 hover:bg-neutral-800 text-neutral-400 border-t border-neutral-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400" aria-label="Measure">
                <Ruler className="w-4 h-4" />
              </button>
            </div>

            {/* Layers control */}
            <div className="absolute bottom-4 right-4 border border-neutral-800 bg-neutral-900/80 backdrop-blur-sm rounded-md p-3 w-44">
              <p className="flex items-center gap-1.5 text-[11px] tracking-wide text-neutral-500 uppercase mb-2">
                <Layers className="w-3 h-3" />
                Layers
              </p>
              <div className="space-y-1.5">
                {layers.map((l) => (
                  <label key={l.key} className="flex items-center gap-2 text-xs text-neutral-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={l.on}
                      onChange={() => toggleLayer(l.key)}
                      className="w-3.5 h-3.5 accent-cyan-500"
                    />
                    {l.label}
                  </label>
                ))}
              </div>
            </div>

            {/* Execution trace toggle (post-completion) */}
            {status === "complete" && (
              <div className="absolute top-4 left-4">
                <button
                  onClick={() => setTraceExpanded((v) => !v)}
                  className="flex items-center gap-2 text-xs text-neutral-300 border border-neutral-800 bg-neutral-900/90 backdrop-blur-sm rounded-md px-3 py-2 hover:border-neutral-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400"
                >
                  {traceExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                  Analysis complete · 7 operations
                </button>
                {traceExpanded && (
                  <div className="mt-1 w-64 border border-neutral-800 bg-neutral-900/95 backdrop-blur-sm rounded-md p-3">
                    <p className="text-[11px] tracking-wide text-neutral-500 uppercase mb-2">Execution trace</p>
                    <ul className="space-y-1.5">
                      {TRACE_STEPS.map((s) => (
                        <li key={s.key} className="flex items-center gap-2 text-xs text-neutral-300">
                          <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                          {s.label}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>

        {/* ---------------- RIGHT: Intelligence ---------------- */}
        <aside className="w-80 shrink-0 border-l border-neutral-800 overflow-y-auto">
          {status === "idle" && (
            <div className="p-4 text-sm text-neutral-500">
              Ask a question below to begin analysis. Findings, evidence, and
              measurements will appear here.
            </div>
          )}

          {status === "analyzing" && (
            <div className="p-4">
              <p className="text-[11px] tracking-wide text-neutral-500 uppercase mb-3">Analyzing</p>
              <ul className="space-y-2">
                {TRACE_STEPS.map((s, i) => {
                  const done = i < traceIndex;
                  const active = i === traceIndex;
                  return (
                    <li key={s.key} className="flex items-center gap-2 text-sm">
                      {done ? (
                        <Check className="w-4 h-4 text-emerald-400 shrink-0" />
                      ) : active ? (
                        <Loader2 className="w-4 h-4 text-cyan-400 animate-spin shrink-0" />
                      ) : (
                        <Circle className="w-4 h-4 text-neutral-700 shrink-0" />
                      )}
                      <span className={done || active ? "text-neutral-300" : "text-neutral-600"}>
                        {s.label}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {status === "complete" && (
            <div className="p-4 space-y-4">
              <div>
                <p className="text-[11px] tracking-wide text-neutral-500 uppercase mb-1">Finding</p>
                <p className="text-base text-neutral-100 leading-snug">
                  Built-up area increased
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="border border-neutral-800 rounded-md p-3">
                  <p className="text-[11px] text-neutral-500 uppercase">Area</p>
                  <p className="text-xl font-mono text-neutral-100 mt-1">2.56 ha</p>
                </div>
                <div className="border border-neutral-800 rounded-md p-3">
                  <p className="text-[11px] text-neutral-500 uppercase">Confidence</p>
                  <p className="text-xl font-mono text-amber-400 mt-1">87%</p>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] text-neutral-500 uppercase">Confidence</span>
                  <span className="text-[11px] font-mono text-neutral-400">87%</span>
                </div>
                <div className="h-1.5 bg-neutral-800 rounded-full overflow-hidden">
                  <div className="h-full bg-cyan-400 rounded-full" style={{ width: "87%" }} />
                </div>
                <p className="text-[11px] text-neutral-600 mt-1">
                  Heuristic score — not yet calibration-validated. See methodology notes.
                </p>
              </div>

              <p className="text-sm text-neutral-400 leading-relaxed">
                A new built-up region was detected in the north-western portion
                of the scene, corroborated across optical and SAR evidence.
              </p>

              <div>
                <p className="text-[11px] tracking-wide text-neutral-500 uppercase mb-2">Evidence</p>
                <div className="space-y-1.5">
                  {EVIDENCE_ITEMS.map((e) => (
                    <div
                      key={e.key}
                      className="flex items-center justify-between border border-neutral-800 rounded-md px-3 py-2"
                    >
                      <div>
                        <p className="text-xs text-neutral-200">{e.label}</p>
                        <p className="text-[11px] text-neutral-600">{e.detail}</p>
                      </div>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    </div>
                  ))}
                </div>
              </div>

              <button
                onClick={() => setWhy((v) => !v)}
                className="w-full flex items-center justify-between text-xs text-neutral-300 border border-neutral-800 rounded-md px-3 py-2 hover:border-neutral-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400"
              >
                Why this answer?
                {why ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              </button>
              {why && (
                <div className="border border-neutral-800 rounded-md p-3 text-xs text-neutral-400 leading-relaxed space-y-2">
                  <p>
                    SatQuery detected spatial differences between two temporal
                    observations and polygonized 14 altered regions.
                  </p>
                  <p className="font-mono text-neutral-500">
                    Polygonized change mask → CRS-aware surface-area calculation.
                  </p>
                </div>
              )}

              <div>
                <p className="text-[11px] tracking-wide text-neutral-500 uppercase mb-2">Change regions</p>
                <div className="space-y-1.5">
                  {REGIONS.map((r) => {
                    const selected = selectedRegion === r.id;
                    return (
                      <button
                        key={r.id}
                        onClick={() => setSelectedRegion(selected ? null : r.id)}
                        className={`w-full text-left border rounded-md px-3 py-2 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
                          selected
                            ? "border-cyan-500/50 bg-cyan-500/5"
                            : "border-neutral-800 hover:border-neutral-700"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono text-neutral-300">Region {r.id}</span>
                          <span className="text-xs font-mono text-neutral-400">{r.area}</span>
                        </div>
                        <p className="text-[11px] text-neutral-600 mt-0.5">{r.type} · {r.confidence}% confidence</p>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </aside>
      </div>

      {/* ---------------------------------------------------------------- */}
      {/* Bottom: query bar                                                */}
      {/* ---------------------------------------------------------------- */}
      <div className="shrink-0 border-t border-neutral-800 px-4 py-3 bg-neutral-950">
        {status === "idle" && (
          <div className="flex flex-wrap gap-2 mb-2">
            {SUGGESTED_PROMPTS.map((p) => (
              <button
                key={p}
                onClick={() => runAnalysis(p)}
                className="text-xs text-neutral-500 border border-neutral-800 rounded-full px-3 py-1 hover:text-neutral-300 hover:border-neutral-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400"
              >
                {p}
              </button>
            ))}
          </div>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            runAnalysis();
          }}
          className="flex items-center gap-2"
        >
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask SatQuery anything about this scene..."
            className="flex-1 bg-neutral-900 border border-neutral-800 rounded-md px-3 py-2.5 text-sm text-neutral-200 placeholder-neutral-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400"
          />
          <button
            type="submit"
            disabled={status === "analyzing"}
            className="shrink-0 flex items-center justify-center w-10 h-10 rounded-md bg-cyan-500 text-neutral-950 hover:bg-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
            aria-label="Run analysis"
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-20 right-4 flex items-center gap-2 bg-neutral-900 border border-neutral-800 text-neutral-200 text-sm rounded-md px-3 py-2 shadow-lg">
          <Check className="w-4 h-4 text-emerald-400" />
          {toast}
          <button onClick={() => setToast(null)} className="ml-1 text-neutral-500 hover:text-neutral-300" aria-label="Dismiss">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
