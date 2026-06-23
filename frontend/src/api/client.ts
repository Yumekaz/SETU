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