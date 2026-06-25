import type {
  CascadeResult,
  ForecastTrajectoryStep,
  PercentileBand,
  Recommendation,
  RiskForecast,
} from "../types/generated";

export type {
  CascadeResult,
  ForecastTrajectoryStep,
  PercentileBand,
  Recommendation,
  RiskForecast,
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface HealthResponse {
  status: string;
  version: string;
  phase: number;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/health`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json() as Promise<HealthResponse>;
}

export interface SignalEvent {
  event_id: string;
  corridor: string;
  event_type: string;
  severity: number;
  goldstein_scale: number;
  confidence: number;
  event_date: string;
  ingested_at: string;
  source_url: string;
  raw_text_snippet: string;
}

export interface RiskScore {
  corridor: string;
  score: number;
  score_date: string;
  contributing_event_ids: string[];
  trend_7d: "RISING" | "FALLING" | "STABLE";
}

export async function fetchSignals(): Promise<SignalEvent[]> {
  const response = await fetch(`${API_URL}/api/signals`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<SignalEvent[]>;
}

export async function fetchRiskScores(): Promise<RiskScore[]> {
  const response = await fetch(`${API_URL}/api/risk-scores`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<RiskScore[]>;
}

export async function fetchRiskScoresLatest(): Promise<RiskScore[]> {
  const response = await fetch(`${API_URL}/api/risk-scores/latest`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<RiskScore[]>;
}

export async function runPipeline(): Promise<unknown> {
  const response = await fetch(`${API_URL}/api/pipeline/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source: "cache" }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export interface GraphNode {
  node_id: string;
  node_type: string;
  name: string;
  lat: number;
  lon: number;
  capacity_mbpd: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  flow_mbpd: number;
  corridor_dependency: string;
  alt_route_penalty_days: number;
}

export interface GraphResponse {
  sources: Array<{ name: string; url?: string; note?: string }>;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export async function fetchGraph(): Promise<GraphResponse> {
  const response = await fetch(`${API_URL}/api/graph`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<GraphResponse>;
}

export async function simulateCascade(body: {
  corridor: string;
  seed?: number;
  n_simulations?: number;
}): Promise<CascadeResult> {
  const response = await fetch(`${API_URL}/api/cascade/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<CascadeResult>;
}

export async function fetchCascadeResults(
  corridor?: string,
): Promise<CascadeResult[]> {
  const url = corridor
    ? `${API_URL}/api/cascade/results?corridor=${encodeURIComponent(corridor)}`
    : `${API_URL}/api/cascade/results`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<CascadeResult[]>;
}

export async function fetchCascadeResultsLatest(): Promise<CascadeResult[]> {
  const response = await fetch(`${API_URL}/api/cascade/results/latest`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<CascadeResult[]>;
}

export async function fetchForecasts(corridor?: string): Promise<RiskForecast[]> {
  const url = corridor
    ? `${API_URL}/api/forecast?corridor=${encodeURIComponent(corridor)}`
    : `${API_URL}/api/forecast`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<RiskForecast[]>;
}

export async function fetchForecastsLatest(): Promise<RiskForecast[]> {
  const response = await fetch(`${API_URL}/api/forecast/latest`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<RiskForecast[]>;
}

export async function runForecast(): Promise<RiskForecast[]> {
  const response = await fetch(`${API_URL}/api/forecast/run`, { method: "POST" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<RiskForecast[]>;
}

export async function simulateCascadeFromForecast(params?: {
  seed?: number;
  n_simulations?: number;
}): Promise<CascadeResult & { trigger_forecast: RiskForecast }> {
  const qs = new URLSearchParams();
  if (params?.seed != null) qs.set("seed", String(params.seed));
  if (params?.n_simulations != null) qs.set("n_simulations", String(params.n_simulations));
  const suffix = qs.toString() ? `?${qs}` : "";
  const response = await fetch(`${API_URL}/api/cascade/simulate/from-forecast${suffix}`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<CascadeResult & { trigger_forecast: RiskForecast }>;
}

export async function fetchRecommendations(
  corridor?: string,
): Promise<Recommendation[]> {
  const url = corridor
    ? `${API_URL}/api/recommendations?corridor=${encodeURIComponent(corridor)}`
    : `${API_URL}/api/recommendations`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<Recommendation[]>;
}

export async function fetchRecommendationsLatest(): Promise<Recommendation[]> {
  const response = await fetch(`${API_URL}/api/recommendations/latest`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<Recommendation[]>;
}

export async function runRecommendations(force?: boolean): Promise<Recommendation> {
  const qs = force ? "?force=true" : "";
  const response = await fetch(`${API_URL}/api/recommendations/run${qs}`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<Recommendation>;
}

export async function approveRecommendation(
  id: string,
  operatorNote: string,
): Promise<Recommendation> {
  const response = await fetch(`${API_URL}/api/recommendations/${id}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ operator_note: operatorNote }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<Recommendation>;
}

export async function rejectRecommendation(
  id: string,
  operatorNote: string,
): Promise<Recommendation> {
  const response = await fetch(`${API_URL}/api/recommendations/${id}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ operator_note: operatorNote }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<Recommendation>;
}

export interface BacktestConfig {
  window_start: string;
  window_end: string;
  corridor: string;
  risk_threshold: number;
  reference_point_date: string;
  reference_point_label: string;
  seed: number;
  n_simulations: number;
  ground_truth_compare_date: string;
}

export interface BacktestTrajectoryPoint {
  date: string;
  score: number;
}

export interface BacktestTrajectory {
  corridor: string;
  window_start: string;
  window_end: string;
  points: BacktestTrajectoryPoint[];
}

export interface TimelineEvent {
  date: string;
  event_type: string;
  description: string;
  source_url: string;
  brent_usd?: string;
  notes?: string;
}

export interface BacktestRunResult {
  status: string;
  lead_time_days: number | null;
  reference_point_date: string;
  risk_threshold: number;
  trajectory_peak?: { peak_date: string; peak_score: number };
  orchestrator_summary?: {
    chain_date: string;
    status: string;
    option_ids: string[];
  };
  [key: string]: unknown;
}

export async function fetchBacktestConfig(): Promise<BacktestConfig> {
  const response = await fetch(`${API_URL}/api/backtest/config`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<BacktestConfig>;
}

export async function fetchBacktestTrajectory(): Promise<BacktestTrajectory> {
  const response = await fetch(`${API_URL}/api/backtest/trajectory`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<BacktestTrajectory>;
}

export async function fetchBacktestTimeline(): Promise<TimelineEvent[]> {
  const response = await fetch(`${API_URL}/api/backtest/timeline`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<TimelineEvent[]>;
}

export async function fetchBacktestLatest(): Promise<BacktestRunResult> {
  const response = await fetch(`${API_URL}/api/backtest/latest`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<BacktestRunResult>;
}

export async function runBacktest(): Promise<BacktestRunResult> {
  const response = await fetch(`${API_URL}/api/backtest/run`, { method: "POST" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<BacktestRunResult>;
}

export async function ensureBaselineData(): Promise<void> {
  const scores = await fetchRiskScores();
  if (scores.length === 0) {
    await runPipeline();
  }
  const forecasts = await fetchForecastsLatest();
  if (forecasts.length === 0) {
    await runForecast();
  }
}