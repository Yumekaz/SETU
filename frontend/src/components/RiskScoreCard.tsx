import type { RiskScore } from "../types/generated";

interface Props {
  score: RiskScore;
}

function getTrendBadge(trend: RiskScore["trend_7d"]) {
  switch (trend) {
    case "RISING":
      return <span className="rounded bg-rose-500/10 px-2 py-0.5 text-xs font-bold text-rose-400 border border-rose-500/15">RISING</span>;
    case "FALLING":
      return <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-xs font-bold text-emerald-400 border border-emerald-500/15">FALLING</span>;
    default:
      return <span className="rounded bg-amber-500/10 px-2 py-0.5 text-xs font-bold text-amber-400 border border-amber-500/15">STABLE</span>;
  }
}

export default function RiskScoreCard({ score }: Props) {
  const pct = Math.round(score.score * 100);

  return (
    <article className="rounded-xl bg-glass p-6 shadow-xl shadow-black/25 transition-all duration-300">
      <header className="mb-5 flex items-center justify-between">
        <h2 className="text-lg font-bold tracking-tight text-white uppercase">
          {score.corridor.replace(/_/g, " ")}
        </h2>
        {getTrendBadge(score.trend_7d)}
      </header>

      <div className="mb-5">
        <div className="mb-2 flex justify-between text-xs font-semibold text-slate-400">
          <span className="uppercase tracking-wider">Risk Level</span>
          <span className="font-mono text-sky-400">{pct}%</span>
        </div>
        <div className="h-2.5 overflow-hidden rounded-full bg-slate-950/60 border border-slate-900">
          <div
            className="h-full rounded-full bg-gradient-to-r from-sky-500 to-indigo-500 transition-all duration-500 shadow-md shadow-sky-500/10"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      <dl className="grid grid-cols-2 gap-4 border-t border-slate-900/60 pt-4 text-xs font-semibold text-slate-400">
        <div>
          <dt className="text-[10px] uppercase tracking-wider text-slate-500">Evaluation Date</dt>
          <dd className="mt-1 font-mono text-slate-200">{score.score_date}</dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wider text-slate-500">Active Signals</dt>
          <dd className="mt-1 font-mono text-slate-200">{score.contributing_event_ids.length} Events</dd>
        </div>
      </dl>
    </article>
  );
}