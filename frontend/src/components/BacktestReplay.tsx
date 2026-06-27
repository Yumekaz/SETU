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
    <div id="backtest-replay-root" className="space-y-6 animate-fadeIn">
      <div className="flex flex-wrap items-center gap-4 bg-glass p-4 rounded-xl border border-slate-900 shadow-lg shadow-black/20">
        <button
          type="button"
          className="btn-primary min-w-[80px]"
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
          className="min-w-[240px] flex-1 accent-sky-500 bg-slate-950/60 rounded-lg cursor-pointer h-2 border border-slate-900 outline-none"
          onChange={(e) => {
            setPlaying(false);
            setIndex(Number(e.target.value));
          }}
        />
        <div className="bg-slate-950/80 border border-slate-900 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-400">
          <span className="font-mono text-slate-300">{currentDate}</span>
          <span className="text-slate-600 mx-2">|</span>
          <span>Risk: </span>
          <span className="font-mono text-sky-400 font-bold">{currentScore.toFixed(4)}</span>
        </div>
      </div>

      <div id="replay-chart" className="h-60 w-full bg-glass p-5 rounded-xl border border-slate-900 shadow-xl shadow-black/20">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points}>
            <CartesianGrid stroke="#1e293b/60" strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 9, fill: "#64748b" }} />
            <YAxis domain={[0, 0.5]} tick={{ fill: "#64748b", fontSize: 9 }} />
            <Tooltip contentStyle={{ background: "#0a0f1d", border: "1px solid #1e293b", borderRadius: "8px" }} />
            <ReferenceLine y={config.risk_threshold} stroke="#ef4444" strokeDasharray="4 4" label={{ value: "Risk Threshold", fill: "#ef4444", fontSize: 10, position: "top" }} />
            <ReferenceLine x={config.reference_point_date} stroke="#a78bfa" strokeDasharray="4 4" label={{ value: "Reference Pt", fill: "#a78bfa", fontSize: 10, position: "insideTopLeft" }} />
            <Line type="monotone" dataKey="score" stroke="#38bdf8" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div
        id="replay-timeline-card"
        className="rounded-xl bg-glass p-5 shadow-xl shadow-black/20"
      >
        <h4 className="text-[10px] font-bold tracking-widest text-slate-400 uppercase mb-3 border-b border-slate-900/60 pb-2">TIMELINE TELEMETRY FEED</h4>
        {event ? (
          <div className="space-y-1">
            <p className="text-xs font-semibold text-slate-400 flex items-center gap-2">
              <span className="font-mono text-slate-300 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-900">{event.date}</span>
              <span className="text-[10px] bg-sky-500/10 text-sky-400 border border-sky-500/15 px-1.5 py-0.5 rounded font-bold uppercase tracking-wider">{(event as TimelineEvent).event_type}</span>
            </p>
            <p className="text-slate-100 text-sm mt-2 leading-relaxed">{(event as TimelineEvent).description}</p>
          </div>
        ) : (
          <p className="text-slate-400 text-sm italic">No timeline telemetry registered on or before {currentDate}</p>
        )}
      </div>

      <div className="bg-glass rounded-xl p-5 shadow-xl shadow-black/20">
        <h4 className="text-xs font-bold tracking-widest text-slate-400 uppercase mb-4">TACTICAL SIMULATION OVERLAY</h4>
        <MapView
          selectedCorridor="HORMUZ"
          onCorridorChange={() => {}}
          showDisruption={currentScore >= 0.15}
          replayScore={currentScore}
        />
      </div>

      <div id="replay-headline" className="rounded-xl bg-glass p-5 shadow-xl shadow-black/20">
        <div className="mb-4 flex items-center justify-between border-b border-slate-900/60 pb-3">
          <span className="text-sm font-bold tracking-wider text-slate-200 uppercase">Backtest Evaluation Summary</span>
          <button type="button" className="text-xs font-semibold text-sky-400 hover:text-sky-300 transition-colors uppercase tracking-wider" onClick={loadHeadline}>
            Refresh run
          </button>
        </div>
        {headline && headline.status !== "empty" ? (
          <div className="grid grid-cols-2 gap-4 text-xs font-semibold text-slate-400">
            <div className="bg-slate-950/40 border border-slate-900 p-3 rounded-lg">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">RUN STATUS</span>
              <span className="mt-1 font-mono text-slate-100 block text-sm">{headline.status}</span>
            </div>
            <div className="bg-slate-950/40 border border-slate-900 p-3 rounded-lg">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">LEAD TIME</span>
              <span className="mt-1 font-mono text-slate-100 block text-sm">{headline.lead_time_days ?? "N/A"} Days</span>
            </div>
            <div className="bg-slate-950/40 border border-slate-900 p-3 rounded-lg">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">TRAJECTORY PEAK</span>
              <span className="mt-1 font-mono text-slate-100 block text-sm">
                {headline.trajectory_peak
                  ? `${headline.trajectory_peak.peak_score.toFixed(4)} [${headline.trajectory_peak.peak_date}]`
                  : "—"}
              </span>
            </div>
            <div className="bg-slate-950/40 border border-slate-900 p-3 rounded-lg">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">ORCHESTRATOR DECISION</span>
              <span className="mt-1 font-mono text-slate-100 block text-sm">{headline.orchestrator_summary?.status ?? "—"}</span>
            </div>
          </div>
        ) : (
          <p className="text-slate-400 text-sm italic">No backtest run registry found. Click refresh to populate telemetry summary.</p>
        )}
      </div>
    </div>
  );
}