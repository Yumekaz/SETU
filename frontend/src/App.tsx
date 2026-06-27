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
    <div className="min-h-screen bg-setu-navy px-6 py-8">
      <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-setu-accent">SETU</p>
          <h1 className="text-2xl font-bold text-white">
            Energy Corridor Resilience — Demo
          </h1>
        </div>
        <HealthBadge />
      </header>
      <nav className="mb-6 flex gap-2 border-b border-slate-700 pb-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-t px-4 py-2 text-sm font-medium ${
              tab === t.id
                ? "bg-slate-800 text-sky-300"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <main className="min-w-[1280px]">
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