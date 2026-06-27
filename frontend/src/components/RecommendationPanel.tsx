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
    return <p className="text-slate-400 text-sm italic">No routing recommendation logs found. Populate with a live scenario cascade.</p>;
  }

  const isPending = latest.status === "PENDING_APPROVAL";

  return (
    <div id="recommendation-panel" className="space-y-4 rounded-xl bg-glass p-5 shadow-xl shadow-black/20">
      <div className="flex items-center justify-between border-b border-slate-900/60 pb-3">
        <h3 className="text-sm font-bold tracking-wider text-slate-200 uppercase">
          {latest.trigger_corridor.replace(/_/g, " ")} MITIGATION
        </h3>
        <span 
          className={`rounded px-2.5 py-0.5 text-[10px] font-bold border transition-all duration-300 ${
            isPending 
              ? "bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse" 
              : latest.status === "APPROVED"
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : "bg-slate-800 text-slate-400 border-slate-700/50"
          }`}
        >
          {latest.status.replace(/_/g, " ")}
        </span>
      </div>

      <ul className="space-y-3 text-sm">
        {latest.options.map((o) => (
          <li key={o.option_id} className="relative rounded-lg bg-slate-950/40 border border-slate-900 p-4 transition-all duration-300 hover:border-slate-800/80">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-bold font-mono text-sky-400">{o.option_id}</span>
              {o.is_pareto_optimal && (
                <span className="rounded bg-sky-500/10 px-1.5 py-0.5 text-[9px] font-bold text-sky-400 border border-sky-500/15 uppercase tracking-wide">
                  Pareto Optimal
                </span>
              )}
            </div>
            <p className="text-slate-300 text-xs leading-relaxed">{o.description}</p>
            
            <div className="mt-3 flex gap-4 text-[10px] text-slate-500 font-semibold border-t border-slate-900/60 pt-2.5">
              <div>
                <span>RISK PENALTY: </span>
                <span className="font-mono text-slate-300">{o.risk_score.toFixed(3)}</span>
              </div>
              <div>
                <span>TRANSIT TIME: </span>
                <span className="font-mono text-slate-300">{o.time_score.toFixed(3)}</span>
              </div>
            </div>
          </li>
        ))}
      </ul>

      {isPending && (
        <div className="space-y-3 border-t border-slate-900/60 pt-4">
          <input
            className="input-premium"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Review authorization notes..."
          />
          <div className="flex gap-2">
            <button
              type="button"
              disabled={busy}
              className="btn-success flex-1"
              onClick={() => act("approve")}
            >
              Approve mitigation
            </button>
            <button
              type="button"
              disabled={busy}
              className="btn-danger"
              onClick={() => act("reject")}
            >
              Reject
            </button>
          </div>
        </div>
      )}
      {error && <p className="text-xs text-rose-400 font-semibold bg-rose-500/5 border border-rose-500/10 p-2.5 rounded-lg">{error}</p>}
    </div>
  );
}