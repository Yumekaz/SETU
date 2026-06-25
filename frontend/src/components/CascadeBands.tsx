import type { CascadeResult } from "../types/generated";

interface Props {
  cascade: CascadeResult | null;
}

function BandRow({
  label,
  band,
}: {
  label: string;
  band: { p10: number; p50: number; p90: number };
}) {
  return (
    <div className="text-sm">
      <span className="text-slate-400">{label}: </span>
      <span className="text-sky-300">p10 {band.p10.toFixed(1)}</span>
      <span className="mx-1 text-slate-500">|</span>
      <span className="text-white">p50 {band.p50.toFixed(1)}</span>
      <span className="mx-1 text-slate-500">|</span>
      <span className="text-amber-300">p90 {band.p90.toFixed(1)}</span>
    </div>
  );
}

export default function CascadeBands({ cascade }: Props) {
  if (!cascade) {
    return <p className="text-slate-400">No cascade results — run a scenario to populate bands.</p>;
  }
  return (
    <div id="cascade-bands" className="space-y-2 rounded-lg border border-slate-700 bg-slate-800/50 p-4">
      <p className="text-sm font-semibold text-slate-200">
        {cascade.corridor} · {cascade.n_simulations} sims
      </p>
      <BandRow label="Price impact %" band={cascade.price_impact_pct} />
      <BandRow label="Throughput impact %" band={cascade.refinery_throughput_impact_pct} />
      <BandRow label="SPR days" band={cascade.spr_days_required} />
    </div>
  );
}