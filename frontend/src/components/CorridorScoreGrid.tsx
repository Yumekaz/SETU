import type { RiskScore } from "../types/generated";
import { scoreToHex } from "../utils/riskColors";

interface Props {
  scores: RiskScore[];
}

function getTrendBadge(trend: string) {
  switch (trend) {
    case "RISING":
      return <span className="rounded bg-rose-500/10 px-1.5 py-0.5 text-[10px] font-bold text-rose-400 border border-rose-500/15">RISING</span>;
    case "FALLING":
      return <span className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/15">FALLING</span>;
    default:
      return <span className="rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-bold text-amber-400 border border-amber-500/15">STABLE</span>;
  }
}

export default function CorridorScoreGrid({ scores }: Props) {
  if (scores.length === 0) {
    return <p className="text-slate-400 text-sm italic">No risk scores yet — waiting for baseline data telemetry…</p>;
  }
  return (
    <div id="corridor-score-grid" className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {scores.map((s) => (
        <div
          key={s.corridor}
          className="relative overflow-hidden rounded-xl bg-glass p-5 shadow-lg shadow-black/20 hover:scale-[1.01] hover:border-slate-700/80 transition-all duration-300"
          style={{ borderTop: `3px solid ${scoreToHex(s.score)}` }}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold tracking-widest text-slate-400 uppercase">
              {s.corridor.replace(/_/g, " ")}
            </span>
            {getTrendBadge(s.trend_7d)}
          </div>
          
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold tracking-tight font-mono" style={{ color: scoreToHex(s.score) }}>
              {s.score.toFixed(3)}
            </span>
            <span className="text-xs text-slate-500 font-semibold uppercase">Risk Factor</span>
          </div>
          
          <div className="mt-4 flex items-center justify-between text-[10px] text-slate-500">
            <span>LAST EVALUATED</span>
            <span className="font-mono text-slate-400">{s.score_date}</span>
          </div>
        </div>
      ))}
    </div>
  );
}