/**
 * @vitest-environment jsdom
 */
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Dashboard from "./Dashboard";

vi.mock("../api/client", () => ({
  ensureBaselineData: vi.fn(),
  fetchRiskScoresLatest: vi.fn(),
  fetchRiskScores: vi.fn(),
  fetchCascadeResultsLatest: vi.fn(),
  fetchForecastsLatest: vi.fn(),
  fetchRecommendationsLatest: vi.fn(),
  fetchLatestBriefing: vi.fn().mockResolvedValue({
    corridor: "HORMUZ",
    risk_level: "LOW",
    score: 0.12,
    trend: "STABLE",
    headline: "No active threat signals detected.",
    contributing_factors: [],
    recommended_posture: "Maintain standard procurement schedule.",
    generated_at: "2026-06-01T00:00:00Z",
  }),
  compareRoute: vi.fn().mockResolvedValue({
    corridor: "HORMUZ",
    origin: "persian_gulf",
    destination: "jamnagar",
    normal: { path: ["persian_gulf", "hormuz", "jamnagar"], distance_nm: 1, transit_days: 1, cost_usd: 1 },
    alternative: { path: ["persian_gulf", "cape_of_good_hope", "jamnagar"], distance_nm: 2, transit_days: 2, cost_usd: 2 },
    comparison: { extra_days: 1, extra_cost_usd: 1, extra_distance_nm: 1 },
  }),
}));

vi.mock("../hooks/usePolling", () => ({
  usePolling: vi.fn(() => ({
    data: null,
    error: null,
    loading: false,
    refresh: vi.fn(),
  })),
}));

import { ensureBaselineData } from "../api/client";
import { usePolling } from "../hooks/usePolling";

const defaultProps = {
  selectedCorridor: "HORMUZ" as const,
  onCorridorChange: vi.fn(),
  onScenarioComplete: vi.fn(),
};

const populatedDashboard = {
  latestScores: [
    { corridor: "HORMUZ", score: 0.12, as_of: "2026-06-01" },
    { corridor: "MALACCA", score: 0.08, as_of: "2026-06-01" },
    { corridor: "BAB_EL_MANDEB", score: 0.05, as_of: "2026-06-01" },
  ],
  historyScores: [],
  cascades: [],
  forecasts: [
    {
      corridor: "HORMUZ",
      trajectory: [
        {
          forecast_date: "2026-06-02",
          score_band: { p10: 0.1, p50: 0.15, p90: 0.2 },
        },
      ],
    },
  ],
  recommendations: [],
};

describe("Dashboard forecast bootstrap", () => {
  it("shows forecast bands after ensureBaselineData populates data", async () => {
    vi.mocked(ensureBaselineData).mockResolvedValueOnce(undefined);
    vi.mocked(usePolling).mockReturnValue({
      data: populatedDashboard,
      error: null,
      loading: false,
      refresh: vi.fn(),
    });

    render(<Dashboard {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/p50:\s*0\.150/)).toBeTruthy();
    });
    expect(screen.queryByText(/No forecasts/)).toBeNull();
    expect(document.querySelector("#forecast-panel")?.textContent).toContain("p10–p90");
  });
});

describe("Dashboard bootstrap error", () => {
  it("renders #dashboard-bootstrap-error when ensureBaselineData rejects Error", async () => {
    vi.mocked(ensureBaselineData).mockRejectedValueOnce(new Error("pipeline failed"));

    render(<Dashboard {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/Dashboard bootstrap failed: pipeline failed/)).toBeTruthy();
    });
    expect(document.querySelector("#dashboard-bootstrap-error")).toBeTruthy();
  });

  it("shows polling error when fetcher fails after bootstrap", async () => {
    vi.mocked(ensureBaselineData).mockResolvedValueOnce(undefined);
    vi.mocked(usePolling).mockReturnValue({
      data: null,
      error: "Network unreachable",
      loading: false,
      refresh: vi.fn(),
    });

    render(<Dashboard {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/Dashboard error: Network unreachable/)).toBeTruthy();
    });
  });

  it("renders bootstrap error for non-Error rejection", async () => {
    vi.mocked(ensureBaselineData).mockRejectedValueOnce("string failure");

    render(<Dashboard {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/Dashboard bootstrap failed: string failure/)).toBeTruthy();
    });
  });
});
