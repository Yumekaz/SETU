/** Pure risk-score → display color mapping for map and charts. */

export function scoreToHex(score: number): string {
  const clamped = Math.max(0, Math.min(1, score));
  if (clamped < 0.35) {
    const t = clamped / 0.35;
    const r = Math.round(34 + t * (245 - 34));
    const g = Math.round(197 + t * (158 - 197));
    const b = Math.round(94 + t * (11 - 94));
    return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
  }
  const t = (clamped - 0.35) / 0.65;
  const r = Math.round(245 + t * (239 - 245));
  const g = Math.round(158 + t * (68 - 158));
  const b = Math.round(11 + t * (68 - 11));
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

export function scoreByCorridor(
  scores: Array<{ corridor: string; score: number }>,
): Record<string, number> {
  const out: Record<string, number> = {};
  for (const row of scores) {
    out[row.corridor] = row.score;
  }
  return out;
}

export function timelineEventForDate(
  events: Array<{ date: string }>,
  asOf: string,
): { date: string } | null {
  let best: { date: string } | null = null;
  for (const event of events) {
    if (event.date <= asOf && (!best || event.date > best.date)) {
      best = event;
    }
  }
  return best;
}