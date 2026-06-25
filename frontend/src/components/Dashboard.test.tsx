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
      expect(screen.getByText(/p50 0\.150/)).toBeTruthy();
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

  it("renders bootstrap error for non-Error rejection", async () => {
    vi.mocked(ensureBaselineData).mockRejectedValueOnce("string failure");

    render(<Dashboard {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/Dashboard bootstrap failed: string failure/)).toBeTruthy();
    });
  });
});