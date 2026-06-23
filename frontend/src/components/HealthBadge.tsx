import { useEffect, useState } from "react";

interface HealthResponse {
  status: string;
  version: string;
  phase: number;
}

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function HealthBadge() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: HealthResponse) => {
        setHealth(data);
        setError(null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-slate-700 px-3 py-1 text-sm">
        <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
        Checking backend…
      </span>
    );
  }

  if (error) {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-red-900/50 px-3 py-1 text-sm text-red-300">
        <span className="h-2 w-2 rounded-full bg-red-500" />
        Backend unreachable: {error}
      </span>
    );
  }

  const ok = health?.status === "ok";

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm ${
        ok ? "bg-emerald-900/50 text-emerald-300" : "bg-red-900/50 text-red-300"
      }`}
    >
      <span
        className={`h-2 w-2 rounded-full ${ok ? "bg-emerald-400" : "bg-red-500"}`}
      />
      {ok ? "Backend OK" : "Backend Error"} — v{health?.version} · Phase{" "}
      {health?.phase}
    </span>
  );
}