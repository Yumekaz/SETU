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
  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: "dashboard", label: "Overview", icon: "01" },
    { id: "map", label: "Maritime network", icon: "02" },
    { id: "replay", label: "Scenario replay", icon: "03" },
  ];

  return (
    <div className="mx-auto max-w-screen-2xl px-4 py-5 sm:px-6 lg:px-8 space-y-5">
      <header className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/80 px-5 py-6 shadow-[0_18px_60px_-30px_rgba(15,23,42,0.9)] sm:px-7">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-sky-400/50 to-transparent" />
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <div className="mb-3 flex items-center gap-3">
              <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-sky-300">SETU</span>
              <span className="h-3 w-px bg-slate-700" />
              <span className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-500">Energy supply resilience</span>
            </div>
            <h1 className="max-w-3xl text-3xl font-bold tracking-tight text-slate-50 sm:text-4xl">
              Strategic energy trade intelligence
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-slate-400">
              Evidence-led risk intelligence and response planning for India's maritime crude supply corridors.
            </p>
          </div>
          <div className="flex items-center">
            <HealthBadge />
          </div>
        </div>
      </header>

      <nav className="grid grid-cols-3 rounded-xl border border-slate-800 bg-slate-950/70 p-1.5 shadow-sm">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`relative flex min-w-0 items-center justify-center gap-2 rounded-lg px-2 py-3 text-[11px] font-semibold transition-colors sm:px-4 sm:text-xs ${
              tab === t.id
                ? "bg-slate-800 text-slate-100 shadow-sm"
                : "text-slate-500 hover:bg-slate-900/70 hover:text-slate-200"
            }`}
          >
            <span className={`font-mono text-[10px] ${tab === t.id ? "text-sky-300" : "text-slate-600"}`}>{t.icon}</span>
            <span className="truncate">{t.label}</span>
          </button>
        ))}
      </nav>

      {/* Main Content Area */}
      <main className="w-full">
        <Suspense fallback={
          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-12 text-center space-y-3">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-sky-400 border-t-transparent" />
            <p className="text-sm text-slate-400">Preparing workspace…</p>
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
