import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, Sparkles, Briefcase, MapPin, Building2, RefreshCw } from "lucide-react";
import { Link } from "react-router";
import api from "@/lib/api";

interface SimilarJob {
  job_id: string;
  title: string;
  company: string | null;
  location: string | null;
  similarity_score: number;
  skills: string[];
}

interface SimilarJobsPanelProps {
  resumeId: string;
}

export function SimilarJobsPanel({ resumeId }: SimilarJobsPanelProps) {
  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState<SimilarJob[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const fetchSimilar = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/search/similar-jobs/${resumeId}?limit=10`);
      setResults(res.data.results || []);
      setTotal(res.data.total || 0);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load similar jobs";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (resumeId) fetchSimilar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resumeId]);

  return (
    <Card className="lg:sticky lg:top-6">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Sparkles className="h-4 w-4 text-purple-500" /> Similar Jobs
        </CardTitle>
        <CardDescription>Jobs that match your resume's skills.</CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-8 text-slate-400">
            <Loader2 className="h-5 w-5 animate-spin text-purple-500 mb-2" />
            <span className="text-xs">Finding matches...</span>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-8 text-slate-400">
            <p className="text-xs text-red-500 mb-2">{error}</p>
            <Button variant="ghost" size="sm" onClick={fetchSimilar} className="h-7 text-xs gap-1">
              <RefreshCw className="h-3 w-3" /> Retry
            </Button>
          </div>
        ) : results.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-slate-400">
            <Briefcase className="h-6 w-6 text-slate-300 mb-2" />
            <p className="text-xs font-medium text-slate-600">No matches yet</p>
            <p className="text-[11px] text-slate-400 mt-0.5 text-center">
              Add more skills to improve matching.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
              {results.length} of {total} matches
            </p>

            {results.map((job, i) => {
              const pct = Math.round(job.similarity_score * 100);

              let scoreColor = "bg-slate-100 text-slate-600";
              if (pct >= 80) scoreColor = "bg-green-50 text-green-700 border-green-200";
              else if (pct >= 60) scoreColor = "bg-yellow-50 text-yellow-700 border-yellow-200";
              else if (pct >= 40) scoreColor = "bg-orange-50 text-orange-700 border-orange-200";
              else scoreColor = "bg-red-50 text-red-600 border-red-200";

              return (
                <Link
                  key={job.job_id}
                  to={`/applicant/matches`}
                  className="block"
                >
                  <div
                    className="rounded-lg border border-slate-200 p-3 hover:shadow-md hover:border-purple-200 transition-all duration-200 animate-in fade-in slide-in-from-bottom-1 cursor-pointer"
                    style={{ animationDelay: `${i * 30}ms` }}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <h4 className="text-sm font-semibold text-slate-900 truncate">
                          {job.title}
                        </h4>
                        <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500">
                          {job.company && (
                            <span className="flex items-center gap-0.5">
                              <Building2 className="h-2.5 w-2.5" /> {job.company}
                            </span>
                          )}
                          {job.location && (
                            <span className="flex items-center gap-0.5">
                              <MapPin className="h-2.5 w-2.5" /> {job.location}
                            </span>
                          )}
                        </div>
                        {job.skills.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1.5">
                            {job.skills.slice(0, 3).map((skill) => (
                              <Badge
                                key={skill}
                                variant="outline"
                                className="text-[9px] px-1.5 py-0 text-slate-500 bg-white"
                              >
                                {skill}
                              </Badge>
                            ))}
                            {job.skills.length > 3 && (
                              <span className="text-[9px] text-slate-400 self-center">
                                +{job.skills.length - 3}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="shrink-0 text-right">
                        <div className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full border text-[10px] font-bold ${scoreColor}`}>
                          <Sparkles className="h-2.5 w-2.5" />
                          {pct}%
                        </div>
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}

            <Button
              variant="ghost"
              size="sm"
              onClick={fetchSimilar}
              className="h-7 text-xs w-full text-slate-500 gap-1"
            >
              <RefreshCw className="h-3 w-3" /> Refresh
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
