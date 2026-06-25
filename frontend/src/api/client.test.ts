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

let fetchMock: ReturnType<typeof vi.fn>;

function mockFetch(handlers: Record<string, () => Promise<unknown>>) {
  fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    const method = init?.method ?? "GET";
    const key = `${method} ${url}`;
    for (const [pattern, handler] of Object.entries(handlers)) {
      if (key.includes(pattern) || url.endsWith(pattern)) {
        return handler();
      }
    }
    throw new Error(`unexpected fetch ${key}`);
  });
  vi.stubGlobal("fetch", fetchMock);
}

describe("fetchBacktestTrajectory", () => {
  beforeEach(() => {
    mockFetch({
      "/api/backtest/trajectory": async () => ({
        ok: true,
        json: async () => TRAJECTORY_PAYLOAD,
      }),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns trajectory shape from API", async () => {
    const result = await fetchBacktestTrajectory();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/backtest/trajectory"),
    );
    expect(result.corridor).toBe("HORMUZ");
    expect(result.points).toHaveLength(2);
    expect(result.points[1].score).toBe(0.1);
  });

  it("throws on HTTP error", async () => {
    mockFetch({
      "/api/backtest/trajectory": async () => ({ ok: false, status: 503 }),
    });
    await expect(fetchBacktestTrajectory()).rejects.toThrow("HTTP 503");
  });
});

describe("fetchBacktestTimeline", () => {
  beforeEach(() => {
    mockFetch({
      "/api/backtest/timeline": async () => ({
        ok: true,
        json: async () => TIMELINE_PAYLOAD,
      }),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns cited timeline rows", async () => {
    const rows = await fetchBacktestTimeline();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/backtest/timeline"),
    );
    expect(rows).toHaveLength(1);
    expect(rows[0].source_url).toContain("eia.gov");
    expect(rows[0].date).toBe("2026-03-11");
  });

  it("throws on HTTP error", async () => {
    mockFetch({
      "/api/backtest/timeline": async () => ({ ok: false, status: 500 }),
    });
    await expect(fetchBacktestTimeline()).rejects.toThrow("HTTP 500");
  });
});

describe("ensureBaselineData", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.resetModules();
  });

  it("runs pipeline then forecast when both are empty", async () => {
    const calls: string[] = [];
    mockFetch({
      "/api/risk-scores": async () => {
        calls.push("scores");
        return { ok: true, json: async () => [] };
      },
      "/api/pipeline/run": async () => {
        calls.push("pipeline");
        return { ok: true, json: async () => ({}) };
      },
      "/api/forecast/latest": async () => {
        calls.push("forecast-latest");
        return { ok: true, json: async () => [] };
      },
      "/api/forecast/run": async () => {
        calls.push("forecast-run");
        return { ok: true, json: async () => [{ corridor: "HORMUZ" }] };
      },
    });

    const mod = await import("./client");
    await mod.ensureBaselineData();
    expect(calls).toEqual(["scores", "pipeline", "forecast-latest", "forecast-run"]);
  });

  it("runs forecast only when scores exist but forecasts empty", async () => {
    const calls: string[] = [];
    mockFetch({
      "/api/risk-scores": async () => {
        calls.push("scores");
        return {
          ok: true,
          json: async () => [{ corridor: "HORMUZ", score: 0.1 }],
        };
      },
      "/api/forecast/latest": async () => {
        calls.push("forecast-latest");
        return { ok: true, json: async () => [] };
      },
      "/api/forecast/run": async () => {
        calls.push("forecast-run");
        return { ok: true, json: async () => [{ corridor: "HORMUZ" }] };
      },
    });

    const mod = await import("./client");
    await mod.ensureBaselineData();
    expect(calls).toEqual(["scores", "forecast-latest", "forecast-run"]);
    expect(calls).not.toContain("pipeline");
  });

  it("skips pipeline and forecast when data already present", async () => {
    const calls: string[] = [];
    mockFetch({
      "/api/risk-scores": async () => {
        calls.push("scores");
        return {
          ok: true,
          json: async () => [{ corridor: "HORMUZ", score: 0.1 }],
        };
      },
      "/api/forecast/latest": async () => {
        calls.push("forecast-latest");
        return {
          ok: true,
          json: async () => [{ corridor: "HORMUZ", trajectory: [] }],
        };
      },
    });

    const mod = await import("./client");
    await mod.ensureBaselineData();
    expect(calls).toEqual(["scores", "forecast-latest"]);
  });

  it("retries bootstrap after failure clears promise", async () => {
    let scoreAttempts = 0;
    mockFetch({
      "/api/risk-scores": async () => {
        scoreAttempts += 1;
        if (scoreAttempts === 1) {
          return { ok: false, status: 503 };
        }
        return {
          ok: true,
          json: async () => [{ corridor: "HORMUZ", score: 0.1 }],
        };
      },
      "/api/forecast/latest": async () => ({
        ok: true,
        json: async () => [{ corridor: "HORMUZ", trajectory: [] }],
      }),
    });

    const mod = await import("./client");
    await expect(mod.ensureBaselineData()).rejects.toThrow("HTTP 503");
    await mod.ensureBaselineData();
    expect(scoreAttempts).toBe(2);
  });

  it("deduplicates concurrent bootstrap calls", async () => {
    let scoreCalls = 0;
    mockFetch({
      "/api/risk-scores": async () => {
        scoreCalls += 1;
        return {
          ok: true,
          json: async () => [{ corridor: "HORMUZ", score: 0.1 }],
        };
      },
      "/api/forecast/latest": async () => ({
        ok: true,
        json: async () => [{ corridor: "HORMUZ", trajectory: [] }],
      }),
    });

    const mod = await import("./client");
    await Promise.all([mod.ensureBaselineData(), mod.ensureBaselineData()]);
    expect(scoreCalls).toBe(1);
  });
});