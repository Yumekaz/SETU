import { useEffect, useState } from "react";
import type { RouteComparisonResult } from "../api/client";
import { compareRoute } from "../api/client";
import type { Corridor } from "../types/generated";

interface Props {
  corridor: Corridor;
}

export default function MaritimeRouteCard({ corridor }: Props) {
  const [data, setData] = useState<RouteComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    compareRoute(corridor)
      .then((res) => {
        if (active) setData(res);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [corridor]);

  return (
    <div id="maritime-route-card" className="min-w-0 overflow-hidden rounded-xl border border-slate-800 bg-glass p-5 shadow-xl shadow-black/30">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-indigo-400" />
          <h3 className="text-xs font-bold tracking-widest text-slate-300 uppercase">
            DYNAMIC MARITIME ROUTE PATHFINDER ({corridor.replace(/_/g, " ")})
          </h3>
        </div>
        <span className="text-[10px] font-bold font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
          VLCC 300K DWT
        </span>
      </div>

      {loading && <p className="text-xs text-slate-400 animate-pulse py-4">Computing Haversine shortest paths & fuel burn…</p>}
      {error && <p className="text-xs text-rose-400 py-2">Route comparison error: {error}</p>}

      {data && !loading && (
        <div className="space-y-4">
          {/* Comparison Metrics Grid */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg bg-slate-950/60 border border-slate-800/60 p-3 text-center">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">Transit Time</span>
              <span className="text-sm font-bold font-mono text-amber-400">
                +{data.comparison.extra_days.toFixed(1)} Days
              </span>
              <span className="text-[9px] text-slate-500 block mt-0.5">
                ({data.alternative.transit_days.toFixed(1)}d vs {data.normal.transit_days.toFixed(1)}d)
              </span>
            </div>

            <div className="rounded-lg bg-slate-950/60 border border-slate-800/60 p-3 text-center">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">Extra Voyage Cost</span>
              <span className="text-sm font-bold font-mono text-rose-400">
                +${(data.comparison.extra_cost_usd / 1000).toFixed(0)}k
              </span>
              <span className="text-[9px] text-slate-500 block mt-0.5">Fuel & Insurance Delta</span>
            </div>

            <div className="rounded-lg bg-slate-950/60 border border-slate-800/60 p-3 text-center">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">Extra Distance</span>
              <span className="text-sm font-bold font-mono text-sky-400">
                +{data.comparison.extra_distance_nm.toFixed(0)} NM
              </span>
              <span className="text-[9px] text-slate-500 block mt-0.5">Great Circle Delta</span>
            </div>
          </div>

          {/* Reroute Path Waypoints */}
          <div className="rounded-lg bg-slate-900/50 border border-slate-800/40 p-3 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              Alternate Pathfinding Trajectory
            </span>
            <div className="flex flex-wrap items-center gap-1.5 font-mono text-[11px]">
              {data.alternative.path.map((node, i) => (
                <div key={i} className="flex items-center gap-1.5">
                  <span className="bg-slate-950 px-2 py-1 rounded border border-slate-800 text-slate-300 font-medium">
                    {node.replace(/_/g, " ")}
                  </span>
                  {i < data.alternative.path.length - 1 && (
                    <span className="text-sky-400 text-xs">→</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
