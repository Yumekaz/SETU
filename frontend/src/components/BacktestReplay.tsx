import { useEffect, useMemo, useRef, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  fetchBacktestConfig,
  fetchBacktestLatest,
  fetchBacktestTimeline,
  fetchBacktestTrajectory,
  runBacktest,
  type BacktestConfig,
  type BacktestRunResult,
  type BacktestTrajectory,
  type TimelineEvent,
} from "../api/client";
import { timelineEventForDate } from "../utils/riskColors";
import MapView from "./MapView";

const PLAY_MS = 200;

export default function BacktestReplay() {
  const [config, setConfig] = useState<BacktestConfig | null>(null);
  const [trajectory, setTrajectory] = useState<BacktestTrajectory | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [headline, setHeadline] = useState<BacktestRunResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    Promise.all([
      fetchBacktestConfig(),
      fetchBacktestTrajectory(),
      fetchBacktestTimeline(),
      fetchBacktestLatest().catch(() => null),
    ])
      .then(([cfg, traj, tl, latest]) => {
        setConfig(cfg);
        setTrajectory(traj);
        setTimeline(tl);
        if (latest && latest.status !== "empty") setHeadline(latest);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const points = trajectory?.points ?? [];
  const current = points[index];
  const currentDate = current?.date ?? trajectory?.window_start ?? "";
  const currentScore = current?.score ?? 0;
  const event = useMemo(
    () => timelineEventForDate(timeline, currentDate),
    [timeline, currentDate],
  );

  useEffect(() => {
    if (!playing || points.length === 0) return;
    timer.current = window.setInterval(() => {
      setIndex((i) => {
        if (i >= points.length - 1) {
          setPlaying(false);
          return i;
        }
        return i + 1;
      });
    }, PLAY_MS);
    return () => {
      if (timer.current) window.clearInterval(timer.current);
    };
  }, [playing, points.length]);

  const loadHeadline = async () => {
    try {
      const result = await runBacktest();
      setHeadline(result);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  if (error) return <p className="text-red-300">Replay error: {error}</p>;
  if (!trajectory || !config) return <p className="text-slate-400">Loading replay data…</p>;

  return (
    <div id="backtest-replay-root" className="space-y-6">
      <div className="flex flex-wrap items-center gap-4">
        <button
          type="button"
          className="rounded bg-setu-accent px-4 py-2 text-sm"
          onClick={() => setPlaying((p) => !p)}
        >
          {playing ? "Pause" : "Play"}
        </button>
        <input
          id="replay-scrub"
          type="range"
          min={0}
          max={Math.max(0, points.length - 1)}
          value={index}
          className="min-w-[240px] flex-1"
          onChange={(e) => {
            setPlaying(false);
            setIndex(Number(e.target.value));
          }}
        />
        <span className="font-mono text-sm text-sky-300">
          {currentDate} · score {currentScore.toFixed(4)}
        </span>
      </div>
      <div id="replay-chart" className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points}>
            <CartesianGrid stroke="#334155" />
            <XAxis dataKey="date" tick={{ fontSize: 9, fill: "#94a3b8" }} />
            <YAxis domain={[0, 0.5]} tick={{ fill: "#94a3b8" }} />
            <Tooltip />
            <ReferenceLine y={config.risk_threshold} stroke="#ef4444" strokeDasharray="4 4" />
            <ReferenceLine x={config.reference_point_date} stroke="#a78bfa" strokeDasharray="4 4" />
            <Line type="monotone" dataKey="score" stroke="#38bdf8" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div
        id="replay-timeline-card"
        className="rounded-lg border border-slate-700 bg-slate-800/50 p-4"
      >
        {event ? (
          <>
            <p className="text-xs text-slate-400">
              {event.date} · {(event as TimelineEvent).event_type}
            </p>
            <p className="text-slate-100">{(event as TimelineEvent).description}</p>
          </>
        ) : (
          <p className="text-slate-400">No timeline event on or before {currentDate}</p>
        )}
      </div>
      <MapView
        selectedCorridor="HORMUZ"
        onCorridorChange={() => {}}
        showDisruption={currentScore >= 0.15}
        replayScore={currentScore}
      />
      <div id="replay-headline" className="rounded-lg border border-slate-600 bg-slate-900/60 p-4 text-sm">
        <div className="mb-2 flex items-center justify-between">
          <span className="font-semibold text-slate-200">Phase 5 headline result (honest)</span>
          <button type="button" className="text-xs text-sky-400 underline" onClick={loadHeadline}>
            Refresh run
          </button>
        </div>
        {headline && headline.status !== "empty" ? (
          <dl className="grid grid-cols-2 gap-2 text-slate-300">
            <dt>status</dt>
            <dd>{headline.status}</dd>
            <dt>lead_time_days</dt>
            <dd>{headline.lead_time_days ?? "null"}</dd>
            <dt>peak</dt>
            <dd>
              {headline.trajectory_peak
                ? `${headline.trajectory_peak.peak_score} on ${headline.trajectory_peak.peak_date}`
                : "—"}
            </dd>
            <dt>orchestrator</dt>
            <dd>{headline.orchestrator_summary?.status ?? "—"}</dd>
          </dl>
        ) : (
          <p className="text-slate-400">Run backtest to populate headline panel.</p>
        )}
      </div>
    </div>
  );
}