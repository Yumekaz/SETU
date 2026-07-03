import { lazy, Suspense, useEffect, useState } from "react";
import type { Corridor } from "./types/generated";
import HealthBadge from "./components/HealthBadge";
import Dashboard from "./components/Dashboard";

const MapView = lazy(() => import("./components/MapView"));
const BacktestReplay = lazy(() => import("./components/BacktestReplay"));

type Tab = "map" | "dashboard" | "replay";

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [corridor, setCorridor] = useState<Corridor>("HORMUZ");
  const [disruption, setDisruption] = useState(false);
  const [utcTime, setUtcTime] = useState("");

  useEffect(() => {
    const updateTime = () => {
      setUtcTime(new Date().toUTCString().replace("GMT", "UTC"));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: "dashboard", label: "Executive Dashboard", icon: "📊" },
    { id: "map", label: "Tactical Maritime Map", icon: "🗺️" },
    { id: "replay", label: "Crisis Backtest Replay", icon: "⏪" },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 md:px-6 space-y-6">
      {/* High-Tech Cyber Header */}
      <header className="rounded-2xl bg-glass-heavy p-6 shadow-2xl border border-slate-800/80 backdrop-blur-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-sky-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-wrap items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="rounded-md bg-gradient-to-r from-sky-500 to-indigo-600 px-3 py-1 text-xs font-black tracking-widest text-white shadow-md shadow-sky-500/20 border border-sky-400/30 font-mono">
                SETU v1.0
              </span>
              <span className="text-[11px] uppercase tracking-widest text-slate-400 font-bold font-mono">
                SOVEREIGN ENERGY SECURITY CONTROL NODE
              </span>
              <span className="hidden md:inline-block h-3 w-px bg-slate-800" />
              <span className="hidden md:inline-block text-[11px] font-mono text-sky-400 font-semibold">
                {utcTime}
              </span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent sm:text-4xl">
              Strategic Energy Trade Uncertainty Engine
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Real-time geopolitical signal intelligence, Monte Carlo cascade simulation, and Pareto-optimal procurement routing for India's maritime crude supply corridors.
            </p>
          </div>
          <div className="flex items-center gap-4">
            <HealthBadge />
          </div>
        </div>
      </header>

      {/* Cyber Tab Switcher */}
      <nav className="flex items-center gap-2 bg-glass p-1.5 rounded-xl border border-slate-800/80 shadow-lg">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`relative flex-1 flex items-center justify-center gap-2 px-5 py-3 text-xs font-bold uppercase tracking-wider rounded-lg transition-all duration-300 ${
              tab === t.id
                ? "bg-gradient-to-r from-sky-500/20 to-indigo-500/20 text-sky-300 border border-sky-500/40 shadow-lg shadow-sky-500/10 font-black"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/40"
            }`}
          >
            <span>{t.icon}</span>
            <span>{t.label}</span>
            {tab === t.id && (
              <span className="absolute bottom-0 left-4 right-4 h-[2px] bg-gradient-to-r from-sky-400 via-indigo-400 to-sky-400 rounded-full shadow-glow" />
            )}
          </button>
        ))}
      </nav>

      {/* Main Content Area */}
      <main className="w-full">
        <Suspense fallback={
          <div className="rounded-xl bg-glass p-12 text-center space-y-3">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-sky-400 border-t-transparent" />
            <p className="text-xs text-slate-400 font-mono">Initializing view module...</p>
          </div>
        }>
          {tab === "map" && (
            <MapView
              selectedCorridor={corridor}
              onCorridorChange={setCorridor}
              showDisruption={disruption}
            />
          )}
          {tab === "dashboard" && (
            <Dashboard
              selectedCorridor={corridor}
              onCorridorChange={setCorridor}
              onScenarioComplete={() => setDisruption(true)}
            />
          )}
          {tab === "replay" && <BacktestReplay />}
        </Suspense>
      </main>
    </div>
  );
}