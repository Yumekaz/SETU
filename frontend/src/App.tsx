import { lazy, Suspense, useState } from "react";
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

  const tabs: { id: Tab; label: string }[] = [
    { id: "map", label: "Map" },
    { id: "dashboard", label: "Dashboard" },
    { id: "replay", label: "Backtest Replay" },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 md:px-6">
      <header className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b border-slate-900/60 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-sky-500/10 px-2.5 py-0.5 text-[10px] font-bold tracking-widest text-sky-400 border border-sky-500/20">
              SETU
            </span>
            <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Tactical Monitoring Node</span>
          </div>
          <h1 className="mt-2 text-3xl font-bold bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
            Energy Corridor Resilience Control
          </h1>
        </div>
        <HealthBadge />
      </header>
      <nav className="mb-6 flex gap-2 border-b border-slate-900/60 pb-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`relative px-5 py-2.5 text-sm font-semibold rounded-lg transition-all duration-300 ${
              tab === t.id
                ? "bg-sky-500/10 text-sky-400 border border-sky-500/20 shadow-sm shadow-sky-500/5"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/40"
            }`}
          >
            {t.label}
            {tab === t.id && (
              <span className="absolute bottom-[-10px] left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-sky-400 to-transparent" />
            )}
          </button>
        ))}
      </nav>
      <main className="w-full">
        <Suspense fallback={<p className="text-slate-400">Loading view…</p>}>
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