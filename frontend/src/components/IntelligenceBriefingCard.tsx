import { useEffect, useState } from "react";
import type { IntelligenceBriefing } from "../api/client";
import { fetchLatestBriefing } from "../api/client";
import type { Corridor } from "../types/generated";

interface Props {
  corridor: Corridor;
}

export default function IntelligenceBriefingCard({ corridor }: Props) {
  const [briefing, setBriefing] = useState<IntelligenceBriefing | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    fetchLatestBriefing(corridor)
      .then((data) => {
        if (active) setBriefing(data);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [corridor]);

  const levelBadgeClass = (level: string) => {
    switch (level) {
      case "CRITICAL":
        return "badge-critical";
      case "HIGH":
        return "badge-high";
      case "MODERATE":
        return "badge-moderate";
      default:
        return "badge-low";
    }
  };

  const prioritizedFactors =
    briefing?.contributing_factors
      .filter(
        (factor) =>
          factor.contribution_pct > 0 ||
          factor.source_url.includes("apnews.com") ||
          factor.source_url.includes("reuters.com"),
      )
      .slice(0, 3) ?? [];

  const hiddenFactorCount = Math.max(
    0,
    (briefing?.contributing_factors.length ?? 0) - prioritizedFactors.length,
  );

  return (
    <div id="intelligence-briefing-card" className="bg-glass rounded-xl p-5 shadow-xl shadow-black/30 border border-slate-800/80 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-sky-400 animate-ping" />
            <h3 className="text-xs font-bold tracking-widest text-slate-300 uppercase">
              GROUNDED XAI BRIEFING ({corridor.replace(/_/g, " ")})
            </h3>
          </div>
          {briefing && (
            <span className={levelBadgeClass(briefing.risk_level)}>
              {briefing.risk_level} THREAT · {(briefing.score * 100).toFixed(0)}%
            </span>
          )}
        </div>

        {loading && <p className="text-xs text-slate-400 animate-pulse py-4">Generating grounded intelligence report…</p>}
        {error && <p className="text-xs text-rose-400 py-2">Briefing unavailable: {error}</p>}

        {briefing && !loading && (
          <div className="space-y-4">
            {/* Headline Narrative */}
            <div className="rounded-lg bg-slate-950/60 border border-slate-800/60 p-3.5">
              <p className="text-xs text-slate-200 leading-relaxed font-medium">
                {briefing.headline}
              </p>
            </div>

            {/* Contributing Signals Breakdown */}
            {prioritizedFactors.length > 0 ? (
              <div className="space-y-2.5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Source-grounded risk drivers
                  </span>
                  <span className="rounded border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest text-emerald-300">
                    noisy seed rows de-emphasized
                  </span>
                </div>
                <div className="space-y-2">
                  {prioritizedFactors.map((factor, idx) => (
                    <div key={idx} className="rounded bg-slate-900/50 border border-slate-800/40 p-2.5 text-xs space-y-1.5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-sky-400 text-[11px]">{factor.event_type}</span>
                          <span className="text-[10px] text-slate-500 font-mono">{factor.event_date}</span>
                        </div>
                        <span className="font-mono text-[10px] font-semibold text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                          {factor.contribution_pct}% share
                        </span>
                      </div>
                      
                      {/* Breakdown Bar */}
                      <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-sky-500 to-indigo-500 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(100, factor.contribution_pct)}%` }}
                        />
                      </div>

                      {factor.source_url && (
                        <a
                          href={factor.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[10px] text-slate-400 hover:text-sky-300 underline truncate block font-mono"
                        >
                          Source: {factor.source_url}
                        </a>
                      )}
                    </div>
                  ))}
                </div>
                {hiddenFactorCount > 0 && (
                  <p className="text-[10px] text-slate-500">
                    {hiddenFactorCount} lower-confidence or zero-contribution historical rows are de-emphasized in the operational view.
                  </p>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No active threat signals contributing to risk score.</p>
            )}
          </div>
        )}
      </div>

      {/* Recommended Posture Box */}
      {briefing && (
        <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-start gap-2.5">
          <span className="text-xs font-bold text-sky-400 uppercase shrink-0 mt-0.5">POSTURE:</span>
          <p className="text-xs text-slate-300 font-medium leading-relaxed">{briefing.recommended_posture}</p>
        </div>
      )}
    </div>
  );
}
