import type { RiskScore } from "../types/generated";
import { scoreToHex } from "../utils/riskColors";

interface Props {
  scores: RiskScore[];
}

function getTrendBadge(trend: string) {
  switch (trend) {
    case "RISING":
      return <span className="rounded bg-rose-500/15 px-2 py-0.5 text-[10px] font-bold text-rose-300 border border-rose-500/30 shadow-sm shadow-rose-500/20">▲ RISING</span>;
    case "FALLING":
      return <span className="rounded bg-emerald-500/15 px-2 py-0.5 text-[10px] font-bold text-emerald-300 border border-emerald-500/30 shadow-sm shadow-emerald-500/20">▼ FALLING</span>;
    default:
      return <span className="rounded bg-amber-500/15 px-2 py-0.5 text-[10px] font-bold text-amber-300 border border-amber-500/30 shadow-sm shadow-amber-500/20">● STABLE</span>;
  }
}

export default function CorridorScoreGrid({ scores }: Props) {
  if (scores.length === 0) {
    return <p className="text-slate-400 text-sm italic">No risk scores yet — waiting for baseline data telemetry…</p>;
  }

  return (
    <div id="corridor-score-grid" className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {scores.map((s) => {
        const hex = scoreToHex(s.score);
        return (
          <div
            key={s.corridor}
            className="relative overflow-hidden rounded-2xl bg-glass p-5 shadow-xl shadow-black/30 border border-slate-800/80 transition-all duration-300 hover:-translate-y-1 hover:border-slate-700 hover:shadow-2xl group"
            style={{ borderTop: `4px solid ${hex}` }}
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-extrabold tracking-widest text-slate-300 uppercase font-mono">
                {s.corridor.replace(/_/g, " ")}
              </span>
              {getTrendBadge(s.trend_7d)}
            </div>
            
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-3xl font-black tracking-tight font-mono" style={{ color: hex }}>
                {s.score.toFixed(3)}
              </span>
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                THREAT INDEX
              </span>
            </div>

            {/* Visual Threat Meter Bar */}
            <div className="mt-3 h-2 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800/80">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${Math.min(100, Math.max(8, s.score * 100))}%`, backgroundColor: hex }}
              />
            </div>
            
            <div className="mt-4 flex items-center justify-between text-[10px] text-slate-400 font-mono pt-2 border-t border-slate-900">
              <span className="text-slate-500">AS OF DATE:</span>
              <span className="text-slate-300 font-bold">{s.score_date}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}