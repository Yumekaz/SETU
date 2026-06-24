import type {
  CascadeResult,
  ForecastTrajectoryStep,
  PercentileBand,
  RiskForecast,
} from "../types/generated";

export type { CascadeResult, ForecastTrajectoryStep, PercentileBand, RiskForecast };

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