import { useState } from "react";
import type { Corridor } from "../types/generated";
import { runForecast, runRecommendations, simulateCascade } from "../api/client";

interface Props {
  corridor: Corridor;
  onComplete: () => void;
}

export default function ScenarioControls({ corridor, onComplete }: Props) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runUnrehearsed = async () => {
    setBusy(true);
    setMessage(null);
    setError(null);
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

  return (
    <div id="scenario-controls" className="rounded-xl bg-glass p-5 shadow-xl shadow-black/20">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h4 className="text-sm font-bold tracking-wider text-slate-200 uppercase">Live Simulation Sandbox</h4>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            Trigger a real-time unrehearsed supply shock cascade on the <strong className="text-sky-400">{corridor.replace(/_/g, " ")}</strong> trade corridor to compute downstream impacts and trigger the decision orchestrator.
          </p>
        </div>
        <button
          type="button"
          disabled={busy}
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