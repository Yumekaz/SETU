import { useEffect, useState } from "react";
import { fetchHealth, type HealthResponse } from "../api/client";

export default function HealthBadge() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHealth()
      .then((data) => {
        setHealth(data);
        setError(null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <span className="inline-flex items-center gap-2.5 rounded-lg border border-slate-800 bg-slate-900/40 px-3.5 py-1.5 text-xs font-semibold text-slate-400 shadow-sm">
        <span className="h-2 w-2 animate-pulse rounded-full bg-slate-500" />
        CHECKING TELEMETRY…
      </span>
    );
  }

  if (error) {
    return (
      <span className="inline-flex items-center gap-2.5 rounded-lg border border-red-500/20 bg-red-500/10 px-3.5 py-1.5 text-xs font-semibold text-red-400 shadow-sm shadow-red-500/5">
        <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
        TELEMETRY FAILURE: {error}
      </span>
    );
  }

  const ok = health?.status === "ok";

  return (
    <span
      className={`inline-flex items-center gap-2.5 rounded-lg border px-3.5 py-1.5 text-xs font-semibold backdrop-blur-md shadow-sm transition-all duration-300 ${
        ok 
          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-sm shadow-emerald-500/5" 
          : "bg-red-500/10 text-red-400 border-red-500/20 shadow-sm shadow-red-500/5"
      }`}
    >
      <span className="relative flex h-2 w-2">
        {ok && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${ok ? "bg-emerald-400" : "bg-red-500"}`} />
      </span>
      <span>
        {ok ? "BACKEND ONLINE" : "CONNECTION LOST"}
      </span>
      <span className="text-slate-700 font-normal">|</span>
      <span className="text-[10px] text-slate-400 font-medium">v{health?.version || "1.0.0"} · P{health?.phase || 8}</span>
    </span>
  );
}