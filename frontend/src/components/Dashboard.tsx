import { useCallback, useEffect, useState } from "react";
import type { CascadeResult, Corridor, Recommendation, RiskForecast, RiskScore } from "../types/generated";
import {
  ensureBaselineData,
  fetchCascadeResultsLatest,
  fetchForecastsLatest,
  fetchRecommendationsLatest,
  fetchRiskScores,
  fetchRiskScoresLatest,
} from "../api/client";
import { usePolling } from "../hooks/usePolling";
import CascadeBands from "./CascadeBands";
import CorridorScoreGrid from "./CorridorScoreGrid";
import IntelligenceBriefingCard from "./IntelligenceBriefingCard";
import MaritimeRouteCard from "./MaritimeRouteCard";
import RecommendationPanel from "./RecommendationPanel";
import RiskTrendChart from "./RiskTrendChart";
import ScenarioControls from "./ScenarioControls";

interface DashboardData {
  latestScores: RiskScore[];
  historyScores: RiskScore[];
  cascades: CascadeResult[];
  forecasts: RiskForecast[];
  recommendations: Recommendation[];
}

async function loadDashboard(): Promise<DashboardData> {
  const [latestScores, historyScores, cascades, forecasts, recommendations] = await Promise.all([
    fetchRiskScoresLatest(),
    fetchRiskScores(),
    fetchCascadeResultsLatest(),
    fetchForecastsLatest(),
    fetchRecommendationsLatest(),
  ]);
  return {
    latestScores: latestScores as RiskScore[],
    historyScores: historyScores as RiskScore[],
    cascades,
    forecasts,
    recommendations,
  };
}

interface Props {
  selectedCorridor: Corridor;
  onCorridorChange: (c: Corridor) => void;
  onScenarioComplete: () => void;
}

export default function Dashboard({
  selectedCorridor,
  onCorridorChange,
  onScenarioComplete,
}: Props) {
  const [bootstrapped, setBootstrapped] = useState(false);
  const [bootstrapError, setBootstrapError] = useState<string | null>(null);

  useEffect(() => {
    ensureBaselineData()
      .then(() => setBootstrapped(true))
      .catch((err: unknown) =>
        setBootstrapError(err instanceof Error ? err.message : String(err)),
      );
  }, []);

  const fetcher = useCallback(() => loadDashboard(), []);
  const { data, error, loading, refresh } = usePolling(fetcher, 30_000, bootstrapped);

  const handleScenario = () => {
    refresh();
    onScenarioComplete();
  };

  if (bootstrapError) {
    return (
      <p id="dashboard-bootstrap-error" className="text-red-300">
        Dashboard bootstrap failed: {bootstrapError}
      </p>
    );
  }

  if (!bootstrapped || (loading && !data)) {
    return <p className="text-slate-400">Loading dashboard baseline…</p>;
  }

  if (error) {
    return <p className="text-red-300">Dashboard error: {error}</p>;
  }

  const corridorCascade =
    data?.cascades.find((c) => c.corridor === selectedCorridor) ?? data?.cascades[0] ?? null;
  const corridorForecast =
    data?.forecasts.find((f) => f.corridor === selectedCorridor) ?? data?.forecasts[0] ?? null;
  const selectedScore = data?.latestScores.find((score) => score.corridor === selectedCorridor);
  const sourceFreshnessDate =
    selectedScore?.score_date ?? corridorForecast?.feature_data_through ?? "awaiting live signal";

  return (
    <div id="dashboard-root" className="space-y-6">
      <section
        id="operational-explainer-card"
        className="relative overflow-hidden rounded-2xl border border-sky-500/20 bg-gradient-to-br from-sky-500/10 via-slate-950/70 to-emerald-500/10 p-5 shadow-2xl shadow-sky-950/20"
      >
        <div className="absolute right-0 top-0 h-32 w-32 rounded-full bg-sky-500/10 blur-3xl" />
        <div className="relative grid gap-5 lg:grid-cols-[1.4fr_1fr] lg:items-center">
          <div>
            <div className="mb-3 flex flex-wrap gap-2">
              <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-emerald-300">
                PS 2 · Energy supply-chain resilience
              </span>
              <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-sky-300">
                Source-grounded decision intelligence
              </span>
            </div>
            <h2 className="text-xl font-black leading-tight text-slate-50 md:text-2xl">
              SETU detects geopolitical supply-chain shocks from live news, maps the affected crude corridor, forecasts risk, simulates downstream impact, and recommends mitigation.
            </h2>
            <p className="mt-3 max-w-4xl text-sm leading-relaxed text-slate-300">
              This is not a news summarizer. It converts evidence into an operator workflow:
              signal extraction, corridor scoring, maritime rerouting, Monte Carlo impact analysis,
              and Pareto-ranked response options for import-dependent economies.
            </p>
          </div>

          <div className="grid gap-2 rounded-xl border border-slate-800/70 bg-slate-950/50 p-4">
            {[
              ["Live source", "AP/GDELT URL evidence"],
              ["Extraction", "Corridor + event type + confidence"],
              ["Forecast basis", `Features through ${sourceFreshnessDate}`],
              ["Decision layer", "Cascade + Pareto mitigation"],
            ].map(([label, value]) => (
              <div key={label} className="flex items-center justify-between gap-3 border-b border-slate-800/60 pb-2 last:border-0 last:pb-0">
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
                  {label}
                </span>
                <span className="text-right text-[11px] font-semibold text-slate-200">{value}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xs font-bold tracking-widest text-slate-400 uppercase">Live Global Corridor Risk Metrics</h2>
          <span className="text-[10px] font-mono text-slate-500">Auto-refresh: 30s</span>
        </div>
        <CorridorScoreGrid scores={data?.latestScores ?? []} />
      </section>

      {/* Grounded XAI Briefing & Dynamic Maritime Route Pathfinder */}
      <section className="grid gap-6 lg:grid-cols-2">
        <IntelligenceBriefingCard corridor={selectedCorridor} />
        <MaritimeRouteCard corridor={selectedCorridor} />
      </section>
      
      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl bg-glass p-5 shadow-xl shadow-black/20">
          <h2 className="mb-4 text-xs font-bold tracking-widest text-slate-400 uppercase">Risk History & Progression</h2>
          <RiskTrendChart scores={data?.historyScores ?? []} />
        </div>
        
        <div id="forecast-panel" className="rounded-xl bg-glass p-5 shadow-xl shadow-black/20 flex flex-col justify-between">
          <div>
            <h3 className="mb-4 text-xs font-bold tracking-widest text-slate-400 uppercase">GRU Forecast Telemetry ({selectedCorridor.replace(/_/g, " ")})</h3>
            {corridorForecast ? (
              <div className="space-y-2">
                {corridorForecast.trajectory.map((step) => (
                  <div key={step.forecast_date} className="flex justify-between items-center border-b border-slate-900/60 pb-2 last:border-0 last:pb-0">
                    <span className="font-mono text-slate-400 text-xs">{step.forecast_date}</span>
                    <div className="flex items-center gap-3 text-xs">
                      <span className="text-sky-400 font-bold font-mono bg-sky-500/5 px-2 py-0.5 rounded border border-sky-500/10">
                        p50: {step.score_band.p50.toFixed(3)}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        p10–p90: {step.score_band.p10.toFixed(3)}–{step.score_band.p90.toFixed(3)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-400 text-sm italic">No forecast telemetry available — run pipeline/forecast triggers first.</p>
            )}
          </div>
        </div>
      </section>
      
      <section className="grid gap-6 lg:grid-cols-2">
        <CascadeBands cascade={corridorCascade} />
        <RecommendationPanel recommendations={data?.recommendations ?? []} onUpdated={refresh} />
      </section>

      <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-slate-900/60">
        <div className="flex items-center gap-3 bg-glass px-4 py-2.5 rounded-lg border border-slate-900">
          <label htmlFor="scenario-corridor-select" className="text-xs font-bold uppercase tracking-wider text-slate-400">Tactical Target Corridor</label>
          <select
            id="scenario-corridor-select"
            className="bg-slate-950/80 border border-slate-900/80 rounded px-2.5 py-1 text-xs text-sky-400 font-bold outline-none focus:border-sky-500 transition-all cursor-pointer"
            value={selectedCorridor}
            onChange={(e) => onCorridorChange(e.target.value as Corridor)}
          >
            <option value="HORMUZ">HORMUZ</option>
            <option value="BAB_EL_MANDEB">BAB EL MANDEB</option>
            <option value="MALACCA">MALACCA</option>
          </select>
        </div>
      </div>
      
      <ScenarioControls corridor={selectedCorridor} onComplete={handleScenario} />
    </div>
  );
}
