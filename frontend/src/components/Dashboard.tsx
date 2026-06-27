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

  return (
    <div id="dashboard-root" className="space-y-6">
      <section>
        <h2 className="mb-4 text-xs font-bold tracking-widest text-slate-400 uppercase">Live Global Corridor Risk Metrics</h2>
        <CorridorScoreGrid scores={data?.latestScores ?? []} />
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