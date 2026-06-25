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

const defaultProps = {
  selectedCorridor: "HORMUZ" as const,
  onCorridorChange: vi.fn(),
  onScenarioComplete: vi.fn(),
};

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