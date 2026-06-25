import type { RiskScore } from "../types/generated";
import { scoreToHex } from "../utils/riskColors";

interface Props {
  scores: RiskScore[];
}

export default function CorridorScoreGrid({ scores }: Props) {
  if (scores.length === 0) {
    return <p className="text-slate-400">No risk scores yet — pipeline will populate baseline.</p>;
  }
  return (
    <div id="corridor-score-grid" className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {scores.map((s) => (
        <div
          key={s.corridor}
          className="rounded-lg border border-slate-700 bg-slate-800/60 p-4"
          style={{ borderLeftColor: scoreToHex(s.score), borderLeftWidth: 4 }}
        >
          <p className="text-xs uppercase tracking-wide text-slate-400">{s.corridor}</p>
          <p className="text-2xl font-bold" style={{ color: scoreToHex(s.score) }}>
            {s.score.toFixed(3)}
          </p>
          <p className="text-xs text-slate-500">
            {s.score_date} · {s.trend_7d}
          </p>
        </div>
      ))}
    </div>
  );
}