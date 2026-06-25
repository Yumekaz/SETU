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
        `Scenario ${corridor}: cascade ${cascade.scenario_id.slice(0, 8)}… → ${rec.options.length} options`,
      );
      onComplete();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div id="scenario-controls" className="rounded-lg border border-slate-700 bg-slate-800/40 p-4">
      <p className="mb-2 text-sm text-slate-300">Unrehearsed live scenario</p>
      <button
        type="button"
        disabled={busy}
        onClick={runUnrehearsed}
        className="rounded bg-setu-accent px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
      >
        Run {corridor} cascade + orchestrator
      </button>
      {message && <p className="mt-2 text-sm text-emerald-300">{message}</p>}
      {error && <p className="mt-2 text-sm text-red-300">{error}</p>}
    </div>
  );
}