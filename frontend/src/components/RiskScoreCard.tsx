import type { RiskScore } from "../types/generated";

interface Props {
  score: RiskScore;
}

function trendColor(trend: RiskScore["trend_7d"]) {
  switch (trend) {
    case "RISING":
      return "text-setu-danger";
    case "FALLING":
      return "text-emerald-400";
    default:
      return "text-setu-warn";
  }
}

export default function RiskScoreCard({ score }: Props) {
  const pct = Math.round(score.score * 100);

  return (
    <article className="rounded-xl border border-slate-700 bg-slate-800/60 p-6 shadow-lg">
      <header className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-setu-accent">
          {score.corridor.replace(/_/g, " ")}
        </h2>
        <span className={`text-sm font-medium ${trendColor(score.trend_7d)}`}>
          {score.trend_7d}
        </span>
      </header>

      <div className="mb-4">
        <div className="mb-1 flex justify-between text-sm text-slate-400">
          <span>Risk score</span>
          <span>{pct}%</span>
        </div>
        <div className="h-3 overflow-hidden rounded-full bg-slate-700">
          <div
            className="h-full rounded-full bg-gradient-to-r from-setu-accent to-setu-warn transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      <dl className="grid grid-cols-2 gap-2 text-sm text-slate-400">
        <div>
          <dt className="text-xs uppercase tracking-wide">Score date</dt>
          <dd className="text-slate-200">{score.score_date}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide">Contributing events</dt>
          <dd className="text-slate-200">{score.contributing_event_ids.length}</dd>
        </div>
      </dl>
    </article>
  );
}