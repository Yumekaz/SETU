import { describe, expect, it } from "vitest";
import { scoreByCorridor, scoreToHex, timelineEventForDate } from "./riskColors";

describe("riskColors", () => {
  it("maps zero score to greenish tone", () => {
    expect(scoreToHex(0)).toMatch(/^#[0-9a-f]{6}$/i);
  });

  it("builds corridor score map", () => {
    const map = scoreByCorridor([
      { corridor: "HORMUZ", score: 0.25 },
      { corridor: "MALACCA", score: 0.1 },
    ]);
    expect(map.HORMUZ).toBe(0.25);
    expect(map.MALACCA).toBe(0.1);
  });

  it("picks nearest prior timeline event", () => {
    const events = [
      { date: "2026-02-07" },
      { date: "2026-03-11" },
    ];
    expect(timelineEventForDate(events, "2026-03-05")?.date).toBe("2026-02-07");
    expect(timelineEventForDate(events, "2026-03-11")?.date).toBe("2026-03-11");
  });
});