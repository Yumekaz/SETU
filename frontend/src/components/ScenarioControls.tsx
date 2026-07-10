import { useState } from "react";
import { ingestLiveUrl, runForecast, runPipeline, runRecommendations, simulateCascade } from "../api/client";
import type { IngestUrlResponse } from "../api/client";
import type { Corridor } from "../types/generated";

const REFERENCE_INCIDENT_URL = "https://apnews.com/article/4732228810c9839a1258309ad43b8289";

interface Props {
  corridor: Corridor;
  onComplete: () => void;
}

type WorkflowStepStatus = "pending" | "running" | "done" | "failed";

interface WorkflowStep {
  id: string;
  label: string;
  status: WorkflowStepStatus;
}

const initialWorkflowSteps: WorkflowStep[] = [
  { id: "source", label: "Ingest reference incident source", status: "pending" },
  { id: "risk", label: "Extract HORMUZ military event + update risk", status: "pending" },
  { id: "forecast", label: "Run live-signal forecast", status: "pending" },
  { id: "cascade", label: "Simulate downstream cascade", status: "pending" },
  { id: "mitigation", label: "Generate Pareto mitigation options", status: "pending" },
];

export default function ScenarioControls({ corridor, onComplete }: Props) {
  const [busy, setBusy] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [urlBusy, setUrlBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [liveEvidence, setLiveEvidence] = useState<IngestUrlResponse | null>(null);
  const [gdeltBusy, setGdeltBusy] = useState(false);
  const [gdeltMessage, setGdeltMessage] = useState<string | null>(null);
  const [workflowBusy, setWorkflowBusy] = useState(false);
  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>(initialWorkflowSteps);

  const updateWorkflowStep = (id: string, status: WorkflowStepStatus) => {
    setWorkflowSteps((steps) =>
      steps.map((step) => (step.id === id ? { ...step, status } : step)),
    );
  };

  const runUnrehearsed = async () => {
    setBusy(true);
    setMessage(null);
    setError(null);
    setLiveEvidence(null);
    try {
      const cascade = await simulateCascade({ corridor, n_simulations: 50 });
      await runForecast();
      const rec = await runRecommendations(true);
      setMessage(
        `Scenario executed successfully: cascade simulation [${cascade.scenario_id.slice(0, 8)}] initialized. Generated ${rec.options.length} options.`,
      );
      onComplete();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const runIncidentWorkflow = async () => {
    setWorkflowBusy(true);
    setMessage(null);
    setError(null);
    setGdeltMessage(null);
    setLiveEvidence(null);
    setWorkflowSteps(initialWorkflowSteps.map((step) => ({ ...step, status: "pending" })));

    try {
      updateWorkflowStep("source", "running");
      const evidence = await ingestLiveUrl(REFERENCE_INCIDENT_URL);
      if (evidence.status !== "accepted") {
        updateWorkflowStep("source", "failed");
        throw new Error(evidence.rejection_reason || "Reference incident source was rejected");
      }
      setLiveEvidence(evidence);
      updateWorkflowStep("source", "done");

      updateWorkflowStep("risk", "running");
      if (evidence.corridor !== "HORMUZ" || evidence.event_type !== "MILITARY") {
        updateWorkflowStep("risk", "failed");
        throw new Error(
          `Unexpected extraction: ${evidence.corridor ?? "UNKNOWN"} / ${evidence.event_type ?? "UNKNOWN"}`,
        );
      }
      updateWorkflowStep("risk", "done");

      updateWorkflowStep("forecast", "running");
      const forecasts = await runForecast();
      const hormuzForecast = forecasts.find((forecast) => forecast.corridor === "HORMUZ");
      if (!hormuzForecast) {
        updateWorkflowStep("forecast", "failed");
        throw new Error("Forecast did not return HORMUZ telemetry");
      }
      updateWorkflowStep("forecast", "done");

      updateWorkflowStep("cascade", "running");
      const cascade = await simulateCascade({ corridor: "HORMUZ", n_simulations: 50 });
      updateWorkflowStep("cascade", "done");

      updateWorkflowStep("mitigation", "running");
      const rec = await runRecommendations(true);
      updateWorkflowStep("mitigation", "done");

      setMessage(
        `Incident workflow complete: source evidence → HORMUZ risk ${(evidence.risk_score_after ?? 0).toFixed(3)} → forecast through ${hormuzForecast.feature_data_through} → cascade ${cascade.scenario_id.slice(0, 8)} → ${rec.options.length} mitigation options.`,
      );
      setUrlInput("");
      onComplete();
    } catch (err) {
      setError(`Incident workflow failed: ${(err as Error).message}`);
    } finally {
      setWorkflowBusy(false);
    }
  };

  const handleIngestUrl = async () => {
    if (!urlInput.trim()) return;
    setUrlBusy(true);
    setMessage(null);
    setError(null);
    try {
      const res = await ingestLiveUrl(urlInput.trim());
      if (res.status === "accepted") {
        setLiveEvidence(res);
        setMessage(
          `Live URL ingested successfully! Corridor [${res.corridor}], Event Type [${res.event_type}], Severity [${res.severity?.toFixed(2)}]. Updated risk score: ${(res.risk_score_after ?? 0).toFixed(3)}.`
        );
        setUrlInput("");
        onComplete();
      } else {
        setError(`URL Ingestion Rejected: ${res.rejection_reason || "Extraction filter rejected article content"}`);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUrlBusy(false);
    }
  };

  const refreshGdelt = async () => {
    setGdeltBusy(true);
    setGdeltMessage(null);
    setError(null);
    try {
      const result = await runPipeline("gdelt_live");
      setGdeltMessage(
        `GDELT refreshed at ${result.refreshed_at}: ${result.stats.input_rows} relevant rows, ${result.stats.accepted_events} accepted, ${result.stats.dedup_dropped} duplicates.`,
      );
      onComplete();
    } catch (err) {
      setError(`GDELT refresh failed: ${(err as Error).message}`);
    } finally {
      setGdeltBusy(false);
    }
  };

  return (
    <div id="scenario-controls" className="rounded-xl bg-glass p-5 shadow-xl shadow-black/20 space-y-6">
      {/* Guided incident-response workflow */}
      <div className="rounded-2xl border border-emerald-500/25 bg-gradient-to-br from-emerald-500/10 via-sky-500/5 to-indigo-500/10 p-4 shadow-lg shadow-emerald-950/20">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2.5 py-1 text-[9px] font-black uppercase tracking-widest text-emerald-300">
                Incident Workflow
              </span>
              <span className="rounded-full border border-sky-400/20 bg-sky-400/10 px-2.5 py-1 text-[9px] font-bold uppercase tracking-widest text-sky-300">
                Guided response sequence
              </span>
            </div>
            <h4 className="text-base font-black tracking-tight text-slate-100">
              Run SETU’s complete source-to-decision workflow
            </h4>
            <p className="max-w-3xl text-xs leading-relaxed text-slate-300">
              Uses a reference incident source to execute the full chain: source evidence → HORMUZ risk update → forecast → cascade simulation → mitigation recommendation.
            </p>
          </div>
          <button
            type="button"
            disabled={workflowBusy || busy || urlBusy || gdeltBusy}
            onClick={runIncidentWorkflow}
            className="btn-primary min-w-56"
          >
            {workflowBusy ? "Running Incident Workflow..." : "Run Incident Response Workflow"}
          </button>
        </div>

        <ol className="mt-4 grid gap-2 md:grid-cols-5">
          {workflowSteps.map((step, index) => (
            <li
              key={step.id}
              className={`rounded-lg border p-3 text-[10px] transition-all ${
                step.status === "done"
                  ? "border-emerald-500/35 bg-emerald-500/10 text-emerald-200"
                  : step.status === "running"
                    ? "border-sky-500/40 bg-sky-500/10 text-sky-200 animate-pulse"
                    : step.status === "failed"
                      ? "border-rose-500/40 bg-rose-500/10 text-rose-200"
                      : "border-slate-800 bg-slate-950/40 text-slate-400"
              }`}
            >
              <div className="mb-1 font-mono text-[9px] uppercase tracking-widest opacity-70">
                Step {index + 1}
              </div>
              <div className="font-bold leading-snug">{step.label}</div>
              <div className="mt-2 font-mono uppercase tracking-widest">
                {step.status === "done" ? "✓ Done" : step.status}
              </div>
            </li>
          ))}
        </ol>
      </div>

      {/* Simulation Trigger */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-900/60 pb-5">
        <div>
          <h4 className="text-sm font-bold tracking-wider text-slate-200 uppercase">Live Simulation Sandbox</h4>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            Trigger a real-time unrehearsed supply shock cascade on the <strong className="text-sky-400">{corridor.replace(/_/g, " ")}</strong> trade corridor to compute downstream impacts and trigger the decision orchestrator.
          </p>
        </div>
        <button
          type="button"
          disabled={busy || urlBusy || gdeltBusy}
          onClick={runUnrehearsed}
          className={`flex items-center justify-center gap-2 px-5 py-3 text-xs font-bold uppercase tracking-wider rounded-lg shadow-md transition-all duration-300 shrink-0 ${
            busy 
              ? "bg-slate-800 text-slate-500 cursor-not-allowed" 
              : "bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 hover:shadow-sky-500/20 text-white active:scale-[0.98]"
          }`}
        >
          {busy && (
            <svg className="animate-spin h-4 w-4 text-sky-400" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          )}
          {busy ? "Executing Simulation..." : "Simulate Supply Disruption"}
        </button>
      </div>

      {/* Live URL Intelligence Ingest */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h4 className="text-xs font-bold tracking-wider text-slate-300 uppercase">
            Analyze Live Geopolitical News Link
          </h4>
          <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[9px] font-black tracking-widest text-emerald-300">
            LIVE WEB · SOURCE GROUNDED
          </span>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-sky-500/15 bg-sky-500/5 p-3">
          <p className="text-[11px] text-slate-400">
            Pull the latest 15-minute GDELT export and merge relevant corridor events without deleting existing evidence.
          </p>
          <button
            type="button"
            disabled={gdeltBusy || busy || urlBusy}
            onClick={refreshGdelt}
            className="btn-secondary whitespace-nowrap text-xs py-2 px-3"
          >
            {gdeltBusy ? "Refreshing GDELT..." : "Refresh GDELT Live"}
          </button>
        </div>
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <input
            type="url"
            className="input-premium flex-1"
            placeholder="Paste news article URL (e.g. https://www.reuters.com/...)"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            disabled={urlBusy || busy || gdeltBusy}
          />
          <button
            type="button"
            disabled={urlBusy || busy || gdeltBusy || !urlInput.trim()}
            onClick={handleIngestUrl}
            className="btn-secondary whitespace-nowrap text-xs py-2.5 px-4"
          >
            {urlBusy ? "Scraping & Scoring..." : "Ingest & Score Live URL"}
          </button>
        </div>
      </div>

      {liveEvidence && (
        <div id="live-evidence-card" className="rounded-xl border border-emerald-500/25 bg-emerald-500/5 p-4 space-y-3">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-emerald-300">Verified source evidence</p>
              <p className="mt-1 text-sm font-bold text-slate-100">{liveEvidence.article_title || "Untitled article"}</p>
              <p className="mt-1 text-[11px] text-slate-400">
                {liveEvidence.source_domain} · Published {liveEvidence.published_at || "timestamp unavailable"} · Scraped {liveEvidence.scraped_at}
              </p>
            </div>
            <span className="rounded border border-sky-500/30 bg-sky-500/10 px-2 py-1 text-[10px] font-bold text-sky-300">
              Confidence {((liveEvidence.confidence ?? 0) * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {liveEvidence.evidence_terms.map((term) => (
              <span key={term} className="rounded bg-slate-950/70 px-2 py-1 text-[10px] font-mono text-slate-300 border border-slate-800">
                {term}
              </span>
            ))}
          </div>
          <a href={liveEvidence.source_url} target="_blank" rel="noreferrer" className="block truncate text-[11px] text-sky-400 hover:text-sky-300">
            {liveEvidence.source_url}
          </a>
        </div>
      )}

      {gdeltMessage && (
        <div id="gdelt-refresh-result" className="rounded-lg border border-sky-500/25 bg-sky-500/10 p-3 text-xs font-semibold text-sky-300">
          {gdeltMessage}
        </div>
      )}
      
      {message && (
        <div className="mt-4 rounded-lg bg-emerald-500/10 border border-emerald-500/25 p-3 text-xs font-semibold text-emerald-400 animate-fadeIn">
          {message}
        </div>
      )}
      {error && (
        <div className="mt-4 rounded-lg bg-rose-500/10 border border-rose-500/25 p-3 text-xs font-semibold text-rose-400 animate-fadeIn">
          Error: {error}
        </div>
      )}
    </div>
  );
}
