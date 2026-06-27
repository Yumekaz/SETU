import type { CascadeResult } from "../types/generated";

interface Props {
  cascade: CascadeResult | null;
}

function BandRow({
  label,
  band,
  maxVal = 30,
  unit = "%"
}: {
  label: string;
  band: { p10: number; p50: number; p90: number };
  maxVal?: number;
  unit?: string;
}) {
  const p10Pct = Math.min(100, Math.max(0, (band.p10 / maxVal) * 100));
  const p50Pct = Math.min(100, Math.max(0, (band.p50 / maxVal) * 100));
  const p90Pct = Math.min(100, Math.max(0, (band.p90 / maxVal) * 100));

  return (
    <div className="space-y-2 border-b border-slate-900/60 pb-3.5 last:border-0 last:pb-0">
      <div className="flex justify-between items-center text-xs font-semibold">
        <span className="text-slate-400 uppercase tracking-wider">{label}</span>
        <div className="flex gap-2.5 font-mono text-[11px]">
          <span className="text-sky-400 font-medium">p10: {band.p10.toFixed(1)}{unit}</span>
          <span className="text-slate-100 font-bold">p50: {band.p50.toFixed(1)}{unit}</span>
          <span className="text-amber-400 font-medium">p90: {band.p90.toFixed(1)}{unit}</span>
        </div>
      </div>
      
      <div className="relative h-2 w-full rounded-full bg-slate-950/60 border border-slate-900 overflow-hidden">
        <div 
          className="absolute h-full bg-gradient-to-r from-sky-500/20 via-sky-500/40 to-amber-500/20 rounded-full"
          style={{ left: `${p10Pct}%`, width: `${Math.max(4, p90Pct - p10Pct)}%` }}
        />
        <div 
          className="absolute h-full w-1.5 bg-white shadow-md shadow-black/80 rounded-full"
          style={{ left: `calc(${p50Pct}% - 3px)` }}
        />
      </div>
    </div>
  );
}

export default function CascadeBands({ cascade }: Props) {
  if (!cascade) {
    return <p className="text-slate-400 text-sm italic">No cascade simulation results loaded. Run a corridor cascade scenario to view impact bands.</p>;
  }
  return (
    <div id="cascade-bands" className="space-y-4 rounded-xl bg-glass p-5 shadow-xl shadow-black/20">
      <div className="flex justify-between items-center border-b border-slate-900/60 pb-3">
        <h3 className="text-sm font-bold tracking-wider text-slate-200 uppercase">
          {cascade.corridor.replace(/_/g, " ")} CASCADE SENSITIVITY
        </h3>
        <span className="rounded bg-sky-500/10 px-2 py-0.5 text-[10px] font-bold text-sky-400 border border-sky-500/15">
          {cascade.n_simulations} SIMULATIONS
        </span>
      </div>
      <div className="space-y-4">
        <BandRow label="Price Impact" band={cascade.price_impact_pct} maxVal={50} unit="%" />
        <BandRow label="Throughput Decline" band={cascade.refinery_throughput_impact_pct} maxVal={50} unit="%" />
        <BandRow label="SPR Drawdown Period" band={cascade.spr_days_required} maxVal={180} unit=" days" />
      </div>
    </div>
  );
}