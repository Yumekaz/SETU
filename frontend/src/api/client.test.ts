import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fetchBacktestTimeline, fetchBacktestTrajectory } from "./client";

const TRAJECTORY_PAYLOAD = {
  corridor: "HORMUZ",
  window_start: "2026-02-01",
  window_end: "2026-06-30",
  points: [
    { date: "2026-02-01", score: 0 },
    { date: "2026-02-02", score: 0.1 },
  ],
};

const TIMELINE_PAYLOAD = [
  {
    date: "2026-03-11",
    event_type: "MILITARY",
    description: "Hormuz restriction",
    source_url: "https://www.eia.gov/todayinenergy/",
    brent_usd: "85.10",
  },
];

describe("fetchBacktestTrajectory", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url.endsWith("/api/backtest/trajectory")) {
          return {
            ok: true,
            json: async () => TRAJECTORY_PAYLOAD,
          };
        }
        throw new Error(`unexpected url ${url}`);
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns trajectory shape from API", async () => {
    const result = await fetchBacktestTrajectory();
    expect(result.corridor).toBe("HORMUZ");
    expect(result.points).toHaveLength(2);
    expect(result.points[1].score).toBe(0.1);
  });
});

describe("fetchBacktestTimeline", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url.endsWith("/api/backtest/timeline")) {
          return {
            ok: true,
            json: async () => TIMELINE_PAYLOAD,
          };
        }
        throw new Error(`unexpected url ${url}`);
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns cited timeline rows", async () => {
    const rows = await fetchBacktestTimeline();
    expect(rows).toHaveLength(1);
    expect(rows[0].source_url).toContain("eia.gov");
    expect(rows[0].date).toBe("2026-03-11");
  });
});