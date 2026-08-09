import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Sparkles,
  Activity,
  ArrowDownRight,
  ArrowUpRight,
} from "lucide-react";

type Contribution = {
  feature: string;
  label: string;
  description: string;
  value: number;
  baseline: number;
  contribution: number;
  direction: "up" | "down" | "neutral";
};

type Explanation = {
  available: boolean;
  model_score?: number | null;
  blended_score?: number | null;
  alpha?: number | null;
  heuristic?: { skills_score?: number; experience_score?: number; content_score?: number } | null;
  contributions?: Contribution[];
  error?: string;
};

function HeuristicBlock({ heuristic }: { heuristic: NonNullable<Explanation["heuristic"]> }) {
  const rows = [
    { key: "skills_score", label: "Skill coverage", hint: "Share of required skills matched", color: "from-[#1E3A5F] to-[#2a4f7a]" },
    { key: "experience_score", label: "Experience fit", hint: "Years of experience vs. target", color: "from-orange-400 to-orange-500" },
    { key: "content_score", label: "Content match", hint: "Text similarity with the job", color: "from-emerald-400 to-emerald-500" },
  ] as const;

  return (
    <div className="space-y-3">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
        <Activity className="h-3.5 w-3.5" /> Heuristic breakdown
      </p>
      {rows.map((row) => {
        const val = Number(heuristic?.[row.key] ?? 0);
        return (
          <div key={row.key} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-slate-700">{row.label}</span>
              <span className="font-semibold text-slate-500">{val.toFixed(1)}%</span>
            </div>
            <Progress value={val} className="h-1.5 bg-slate-100 rounded-full" indicatorClassName={`bg-gradient-to-r ${row.color}`} />
            <p className="text-[11px] text-slate-400">{row.hint}</p>
          </div>
        );
      })}
    </div>
  );
}

export default function ScoreExplanation({ explanation }: { explanation: Explanation | null }) {
  if (!explanation) return null;

  if (!explanation.available) {
    return (
      <div className="space-y-4">
        {explanation.error ? (
          <p className="text-sm text-slate-500">{explanation.error}</p>
        ) : explanation.heuristic ? (
          <HeuristicBlock heuristic={explanation.heuristic} />
        ) : (
          <p className="text-sm text-slate-500">No explanation available for this score yet.</p>
        )}
      </div>
    );
  }

  const contributions = explanation.contributions || [];
  const up = contributions.filter((c) => c.direction === "up");
  const down = contributions.filter((c) => c.direction === "down");
  const neutral = contributions.filter((c) => c.direction === "neutral");

  return (
    <div className="space-y-5">
      {/* Model summary */}
      <div className="flex flex-wrap items-center gap-2">
        <Badge className="bg-violet-50 text-violet-700 border-violet-200 gap-1">
          <Sparkles className="h-3 w-3" /> AI model score: {explanation.model_score?.toFixed(1) ?? "—"}
        </Badge>
        {explanation.blended_score != null && (
          <Badge className="bg-slate-50 text-slate-600 border-slate-200 gap-1">
            Final score: {explanation.blended_score.toFixed(1)}
          </Badge>
        )}
        {explanation.alpha != null && (
          <Badge className="bg-slate-50 text-slate-500 border-slate-200 gap-1">blend α {explanation.alpha.toFixed(2)}</Badge>
        )}
      </div>

      {contributions.length === 0 ? (
        <p className="text-sm text-slate-500">No feature contributions computed for this candidate.</p>
      ) : (
        <>
          {/* Positive contributors */}
          {up.length > 0 && (
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-green-600 flex items-center gap-1.5">
                <TrendingUp className="h-3.5 w-3.5" /> Pushed the score up
              </p>
              <div className="space-y-1.5">
                {up.slice(0, 6).map((c) => (
                  <div key={c.feature} className="flex items-start gap-2 p-2.5 rounded-lg bg-green-50/60 border border-green-100">
                    <ArrowUpRight className="h-4 w-4 text-green-600 shrink-0 mt-0.5" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-semibold text-slate-800">{c.label}</p>
                        <span className="text-sm font-bold text-green-700 shrink-0">+{c.contribution.toFixed(1)}</span>
                      </div>
                      <p className="text-[11px] text-slate-500">{c.description}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Value {c.value.toFixed(1)} vs. avg {c.baseline.toFixed(1)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Negative contributors */}
          {down.length > 0 && (
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-red-500 flex items-center gap-1.5">
                <TrendingDown className="h-3.5 w-3.5" /> Pulled the score down
              </p>
              <div className="space-y-1.5">
                {down.slice(0, 6).map((c) => (
                  <div key={c.feature} className="flex items-start gap-2 p-2.5 rounded-lg bg-red-50/60 border border-red-100">
                    <ArrowDownRight className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-semibold text-slate-800">{c.label}</p>
                        <span className="text-sm font-bold text-red-500 shrink-0">{c.contribution.toFixed(1)}</span>
                      </div>
                      <p className="text-[11px] text-slate-500">{c.description}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Value {c.value.toFixed(1)} vs. avg {c.baseline.toFixed(1)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Neutral note */}
          {neutral.length > 0 && (
            <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
              <Minus className="h-3 w-3" /> {neutral.length} feature{neutral.length === 1 ? "" : "s"} had little effect on this score.
            </p>
          )}
        </>
      )}

      {explanation.heuristic && (
        <div className="pt-4 border-t border-slate-100">
          <HeuristicBlock heuristic={explanation.heuristic} />
        </div>
      )}
    </div>
  );
}
