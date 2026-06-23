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