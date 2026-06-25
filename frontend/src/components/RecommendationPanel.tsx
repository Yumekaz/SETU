import { useState } from "react";
import type { Recommendation } from "../types/generated";
import { approveRecommendation, rejectRecommendation } from "../api/client";

interface Props {
  recommendations: Recommendation[];
  onUpdated: () => void;
}

export default function RecommendationPanel({ recommendations, onUpdated }: Props) {
  const [note, setNote] = useState("Demo operator review");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pending = recommendations.filter((r) => r.status === "PENDING_APPROVAL");
  const latest = pending[0] ?? recommendations[0];

  const act = async (action: "approve" | "reject") => {
    if (!latest) return;
    setBusy(true);
    setError(null);
    try {
      if (action === "approve") {
        await approveRecommendation(latest.recommendation_id, note);
      } else {
        await rejectRecommendation(latest.recommendation_id, note);
      }
      onUpdated();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (!latest) {
    return <p className="text-slate-400">No recommendations yet.</p>;
  }

  return (
    <div id="recommendation-panel" className="space-y-3 rounded-lg border border-slate-700 bg-slate-800/50 p-4">
      <div className="flex items-center justify-between">
        <p className="font-semibold text-slate-100">{latest.trigger_corridor}</p>
        <span className="rounded bg-slate-700 px-2 py-0.5 text-xs">{latest.status}</span>
      </div>
      <ul className="space-y-2 text-sm">
        {latest.options.map((o) => (
          <li key={o.option_id} className="rounded bg-slate-900/60 p-2">
            <span className="font-medium text-sky-300">{o.option_id}</span>
            <p className="text-slate-400">{o.description}</p>
            <p className="text-xs text-slate-500">
              risk {o.risk_score.toFixed(2)} · time {o.time_score.toFixed(2)}
              {o.is_pareto_optimal ? " · Pareto" : ""}
            </p>
          </li>
        ))}
      </ul>
      {latest.status === "PENDING_APPROVAL" && (
        <div className="space-y-2">
          <input
            className="w-full rounded bg-slate-900 px-3 py-2 text-sm"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Operator note"
          />
          <div className="flex gap-2">
            <button
              type="button"
              disabled={busy}
              className="rounded bg-emerald-700 px-3 py-1.5 text-sm hover:bg-emerald-600 disabled:opacity-50"
              onClick={() => act("approve")}
            >
              Approve
            </button>
            <button
              type="button"
              disabled={busy}
              className="rounded bg-red-800 px-3 py-1.5 text-sm hover:bg-red-700 disabled:opacity-50"
              onClick={() => act("reject")}
            >
              Reject
            </button>
          </div>
        </div>
      )}
      {error && <p className="text-sm text-red-300">{error}</p>}
    </div>
  );
}