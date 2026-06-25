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
        <h2 className="mb-3 text-lg font-semibold text-slate-100">Baseline risk (live)</h2>
        <CorridorScoreGrid scores={data?.latestScores ?? []} />
      </section>
      <section className="grid gap-6 lg:grid-cols-2">
        <RiskTrendChart scores={data?.historyScores ?? []} />
        <div id="forecast-panel" className="rounded-lg border border-slate-700 bg-slate-800/40 p-4">
          <h3 className="mb-2 text-sm font-semibold text-slate-200">Forecast bands</h3>
          {corridorForecast ? (
            <ul className="space-y-1 text-sm text-slate-300">
              {corridorForecast.trajectory.map((step) => (
                <li key={step.forecast_date}>
                  {step.forecast_date}: p50 {step.score_band.p50.toFixed(3)} (p10–p90{" "}
                  {step.score_band.p10.toFixed(3)}–{step.score_band.p90.toFixed(3)})
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-400">No forecasts — run pipeline/forecast first.</p>
          )}
        </div>
      </section>
      <section className="grid gap-6 lg:grid-cols-2">
        <CascadeBands cascade={corridorCascade} />
        <RecommendationPanel recommendations={data?.recommendations ?? []} onUpdated={refresh} />
      </section>
      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm text-slate-400">Scenario corridor</label>
        <select
          id="scenario-corridor-select"
          className="rounded bg-slate-800 px-3 py-2 text-sm"
          value={selectedCorridor}
          onChange={(e) => onCorridorChange(e.target.value as Corridor)}
        >
          <option value="HORMUZ">HORMUZ</option>
          <option value="BAB_EL_MANDEB">BAB_EL_MANDEB</option>
          <option value="MALACCA">MALACCA</option>
        </select>
      </div>
      <ScenarioControls corridor={selectedCorridor} onComplete={handleScenario} />
    </div>
  );
}