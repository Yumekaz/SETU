import HealthBadge from "./components/HealthBadge";
import RiskScoreCard from "./components/RiskScoreCard";
import type { RiskScore } from "./types/generated";
import riskScoresFixture from "@fixtures/risk_scores.json";

export default function App() {
  const mockScore = (riskScoresFixture as RiskScore[])[0];

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <header className="mb-10">
        <p className="mb-2 text-sm uppercase tracking-widest text-setu-accent">
          Strategic Energy Trade Uncertainty
        </p>
        <h1 className="mb-4 text-3xl font-bold text-white">SETU — Phase 0</h1>
        <HealthBadge />
      </header>

      <section>
        <h2 className="mb-4 text-xl font-semibold text-slate-200">
          Mock Risk Score (fixture)
        </h2>
        {mockScore ? (
          <RiskScoreCard score={mockScore} />
        ) : (
          <p className="text-slate-400">
            No fixture found — run{" "}
            <code className="rounded bg-slate-800 px-1">python scripts/generate_mocks.py</code>
          </p>
        )}
      </section>

      <footer className="mt-12 text-center text-xs text-slate-500">
        Contracts frozen per SETU SRS Section 6 · No modeling logic in Phase 0
      </footer>
    </div>
  );
}