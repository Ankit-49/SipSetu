import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Loader2, Sparkles, RefreshCw } from "lucide-react";
import api from "@/lib/api";

interface SimilarResume {
  resume_id: string;
  applicant_id: string;
  applicant_name: string | null;
  similarity_score: number;
  skills: string[];
}

interface SimilarResumesPanelProps {
  jobId: string;
  jobTitle?: string;
}

export function SimilarResumesPanel({ jobId, jobTitle: _jobTitle }: SimilarResumesPanelProps) {
  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState<SimilarResume[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const fetchSimilar = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/search/similar-resumes/${jobId}?limit=10`);
      setResults(res.data.results || []);
      setTotal(res.data.total || 0);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load similar resumes";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (jobId) fetchSimilar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-slate-400">
        <Loader2 className="h-6 w-6 animate-spin text-[#F97316] mb-3" />
        <span className="text-sm">Finding similar resumes...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-slate-400">
        <p className="text-sm text-red-500 mb-3">{error}</p>
        <Button variant="outline" size="sm" onClick={fetchSimilar} className="gap-1.5">
          <RefreshCw className="h-3.5 w-3.5" /> Retry
        </Button>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-slate-400">
        <Sparkles className="h-8 w-8 text-slate-300 mb-3" />
        <p className="text-sm font-medium text-slate-600">No similar resumes found</p>
        <p className="text-xs text-slate-400 mt-1">
          Try adding more skills or a detailed job description for better matching.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs text-slate-500">
          Showing {results.length} of {total} semantically similar resumes
        </p>
        <Button variant="ghost" size="sm" onClick={fetchSimilar} className="h-7 text-xs gap-1">
          <RefreshCw className="h-3 w-3" /> Refresh
        </Button>
      </div>

      {results.map((r, i) => {
        const score = r.similarity_score;
        const pct = Math.round(score * 100);

        let scoreColor = "bg-slate-100 text-slate-600";
        let scoreBorder = "border-slate-200";
        if (pct >= 80) { scoreColor = "bg-green-50 text-green-700"; scoreBorder = "border-green-200"; }
        else if (pct >= 60) { scoreColor = "bg-yellow-50 text-yellow-700"; scoreBorder = "border-yellow-200"; }
        else if (pct >= 40) { scoreColor = "bg-orange-50 text-orange-700"; scoreBorder = "border-orange-200"; }
        else { scoreColor = "bg-red-50 text-red-600"; scoreBorder = "border-red-200"; }

        const initials = (r.applicant_name || "?")
          .split(" ")
          .map((w) => w[0])
          .join("")
          .toUpperCase()
          .slice(0, 2);

        return (
          <Card
            key={r.resume_id}
            className="hover:shadow-md transition-shadow animate-in fade-in slide-in-from-bottom-1"
            style={{ animationDelay: `${i * 40}ms` }}
          >
            <CardContent className="p-4 flex items-center gap-4">
              {/* Rank badge */}
              <div className="text-[10px] font-bold text-slate-400 w-5 text-center shrink-0">
                #{i + 1}
              </div>

              {/* Avatar */}
              <Avatar className="h-9 w-9 border border-slate-200 shrink-0">
                <AvatarFallback className="bg-[#1E3A5F] text-white text-xs font-semibold">
                  {initials}
                </AvatarFallback>
              </Avatar>

              {/* Name + skills */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-slate-900 truncate">
                    {r.applicant_name || "Unknown applicant"}
                  </h4>
                </div>
                {r.skills.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {r.skills.slice(0, 5).map((skill) => (
                      <Badge
                        key={skill}
                        variant="outline"
                        className="text-[10px] px-1.5 py-0 text-slate-500 bg-white"
                      >
                        {skill}
                      </Badge>
                    ))}
                    {r.skills.length > 5 && (
                      <span className="text-[10px] text-slate-400 self-center">
                        +{r.skills.length - 5}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Similarity score */}
              <div className="shrink-0 text-right">
                <div className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full border text-xs font-bold ${scoreColor} ${scoreBorder}`}>
                  <Sparkles className="h-3 w-3" />
                  {pct}%
                </div>
                <p className="text-[9px] text-slate-400 mt-0.5 uppercase tracking-wider">Similarity</p>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

/**
 * Compact inline trigger button — renders a small "Similar Resumes" button
 * with a badge showing the result count.
 */
export function SimilarResumesTrigger({
  jobId,
  jobTitle,
  onOpen,
}: {
  jobId: string;
  jobTitle?: string;
  onOpen: (jobId: string, jobTitle: string) => void;
}) {
  const [count, setCount] = useState<number | null>(null);
  const [fetching, setFetching] = useState(false);

  const handleClick = async () => {
    onOpen(jobId, jobTitle || "");
    // Optionally pre-fetch count
    if (count === null && !fetching) {
      setFetching(true);
      try {
        const res = await api.get(`/search/similar-resumes/${jobId}?limit=1`);
        setCount(res.data.total || 0);
      } catch {
        // silently ignore
      } finally {
        setFetching(false);
      }
    }
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      className="text-slate-500 hover:text-purple-600 hover:bg-purple-50 gap-1.5"
      onClick={handleClick}
    >
      <Sparkles className="h-3.5 w-3.5" />
      Similar
      {count !== null && count > 0 && (
        <span className="ml-0.5 inline-flex items-center justify-center h-4 min-w-[16px] rounded-full bg-purple-100 text-purple-700 text-[10px] font-bold px-1">
          {count}
        </span>
      )}
    </Button>
  );
}
