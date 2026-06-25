import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { RiskScore } from "../types/generated";

interface Props {
  scores: RiskScore[];
}

export default function RiskTrendChart({ scores }: Props) {
  const byCorridor = new Map<string, RiskScore[]>();
  for (const s of scores) {
    const list = byCorridor.get(s.corridor) ?? [];
    list.push(s);
    byCorridor.set(s.corridor, list);
  }

  const corridors = [...byCorridor.keys()];
  if (corridors.length === 0) {
    return <p className="text-slate-400">No score history for trends.</p>;
  }

  const primary = corridors[0];
  const data = (byCorridor.get(primary) ?? [])
    .slice()
    .sort((a, b) => a.score_date.localeCompare(b.score_date))
    .map((s) => ({ date: s.score_date, score: s.score }));

  return (
    <div id="risk-trend-chart" className="h-64 w-full min-h-[200px]">
      <p className="mb-2 text-xs uppercase text-slate-400">{primary} score history</p>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={data}>
          <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 10 }} />
          <YAxis domain={[0, 1]} tick={{ fill: "#94a3b8", fontSize: 10 }} />
          <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #475569" }} />
          <Line type="monotone" dataKey="score" stroke="#0ea5e9" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}