import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MapPin, Clock, Briefcase, Send, Loader2, BookmarkCheck, Bookmark, Trash2, Heart } from "lucide-react";
import { Link } from "react-router";
import api from "@/lib/api";
import { useAuth } from "@/app/context/AuthContext";
import { useToast } from "@/hooks/use-toast";

export default function ApplicantSavedJobs() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [jobs, setJobs] = useState<any[]>([]);
  const [applyingJobId, setApplyingJobId] = useState<string | null>(null);
  const [appliedJobIds, setAppliedJobIds] = useState<string[]>([]);
  const [unsavingId, setUnsavingId] = useState<string | null>(null);

  useEffect(() => {
    if (!user) { setLoading(false); return; }
    fetchSavedJobs();
  }, [user]);

  const fetchSavedJobs = async () => {
    if (!user) return;
    try {
      const res = await api.get(`/applicants/${user.id}/saved-jobs`);
      setJobs(res.data.saved_jobs || []);
      setAppliedJobIds(res.data.saved_jobs.filter((j: any) => j.applied).map((j: any) => String(j.job_id)));
    } catch (err) {
      console.error("Failed to load saved jobs", err);
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async (jobId: string) => {
    if (!user || applyingJobId === jobId || appliedJobIds.includes(jobId)) return;
    setApplyingJobId(jobId);
    try {
      await api.post(`/jobs/${jobId}/apply`, { applicant_id: user.id });
      setAppliedJobIds((prev) => [...prev, jobId]);
      const job = jobs.find(j => String(j.job_id) === String(jobId));
      toast({ title: "Application sent!", description: `You applied to "${job?.title || "the job"}".` });
    } catch (err) {
      toast({ title: "Could not apply", description: "Please try again.", variant: "destructive" });
    } finally {
      setApplyingJobId(null);
    }
  };

  const handleUnsave = async (jobId: string) => {
    setUnsavingId(jobId);
    try {
      await api.delete(`/jobs/${jobId}/save`);
      setJobs((prev) => prev.filter(j => String(j.job_id) !== String(jobId)));
      toast({ title: "Removed from saved jobs" });
    } catch (err) {
      toast({ title: "Failed to remove", variant: "destructive" });
    } finally {
      setUnsavingId(null);
    }
  };

  const formatSalary = (job: any) => {
    if (job.salary_min && job.salary_max) return `NPR ${Math.round(job.salary_min)} - ${Math.round(job.salary_max)} LPA`;
    if (job.salary_min) return `NPR ${Math.round(job.salary_min)}+ LPA`;
    return null;
  };

  const formatPosted = (dateStr: string) => {
    if (!dateStr) return "";
    const diff = Date.now() - new Date(dateStr).getTime();
    const days = Math.floor(diff / 86400000);
    if (days === 0) return "Today";
    if (days === 1) return "1 day ago";
    if (days < 7) return `${days} days ago`;
    return `${Math.floor(days / 7)} weeks ago`;
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#F97316]" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            <Heart className="h-7 w-7 text-[#F97316]" /> Saved Jobs
          </h1>
          <p className="text-slate-500 mt-1">Jobs you've bookmarked for later. Apply before they're gone!</p>
        </div>
      </div>

      {jobs.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <div className="h-16 w-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4">
              <Bookmark className="h-8 w-8 text-slate-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">No saved jobs yet</h3>
            <p className="text-slate-500 mb-6 max-w-md mx-auto">
              Browse job matches and bookmark the ones you're interested in. They'll appear here for quick access.
            </p>
            <Link to="/applicant/matches">
              <Button className="bg-[#F97316] hover:bg-[#e8630e] text-white gap-2">
                <Briefcase className="h-4 w-4" /> Browse Jobs
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {jobs.map((job, i) => (
            <Card key={job.job_id} className="hover:shadow-md transition-shadow duration-300 animate-in fade-in zoom-in-95" style={{ animationDelay: `${i * 50}ms`, animationFillMode: 'both' }}>
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center font-bold text-slate-600 text-lg">
                      {(job.recruiter_company || job.recruiter_name || "?").charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-bold text-lg text-slate-900">{job.title}</h3>
                      <p className="text-slate-600 text-sm">{job.recruiter_company || job.recruiter_name}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {job.matching_score > 0 && (
                      <Badge className={
                        job.matching_score >= 85 ? "bg-green-100 text-green-700 hover:bg-green-100 border-none px-3 py-1 text-sm font-bold" :
                        job.matching_score >= 70 ? "bg-orange-100 text-orange-700 hover:bg-orange-100 border-none px-3 py-1 text-sm font-bold" :
                        "bg-slate-100 text-slate-700 hover:bg-slate-100 border-none px-3 py-1 text-sm font-bold"
                      }>
                        {Number(job.matching_score).toFixed(2)}% Match
                      </Badge>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="p-1.5 h-auto text-slate-300 hover:text-red-500"
                      onClick={() => handleUnsave(job.job_id)}
                      disabled={unsavingId === job.job_id}
                      title="Remove from saved"
                    >
                      {unsavingId === job.job_id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

                <div className="flex flex-wrap gap-3 mb-4">
                  {job.location && (
                    <div className="flex items-center text-xs text-slate-500 gap-1 bg-slate-50 px-2 py-1 rounded-md">
                      <MapPin className="h-3 w-3" /> {job.location}
                    </div>
                  )}
                  {job.job_type && (
                    <div className="flex items-center text-xs text-slate-500 gap-1 bg-slate-50 px-2 py-1 rounded-md">
                      <Clock className="h-3 w-3" /> {job.job_type}
                    </div>
                  )}
                  {formatSalary(job) && (
                    <div className="flex items-center text-xs text-slate-500 gap-1 bg-slate-50 px-2 py-1 rounded-md">
                      {formatSalary(job)}
                    </div>
                  )}
                </div>

                <div className="mb-6">
                  <p className="text-xs font-semibold text-slate-900 uppercase tracking-wider mb-2">Required Skills</p>
                  <div className="flex flex-wrap gap-2">
                    {job.skills.length > 0 ? job.skills.map((skill: string) => (
                      <Badge key={skill} variant="secondary" className="bg-slate-100 text-slate-600 font-normal">
                        {skill}
                      </Badge>
                    )) : <span className="text-xs text-slate-400">No skills listed</span>}
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                  <span className="text-xs text-slate-400">{formatPosted(job.created_at)}</span>
                  <Button
                    className="bg-[#F97316] hover:bg-[#F97316]/90 text-white gap-2"
                    onClick={() => handleApply(job.job_id)}
                    disabled={applyingJobId === job.job_id || appliedJobIds.includes(job.job_id)}
                  >
                    {appliedJobIds.includes(job.job_id) ? (
                      "Applied"
                    ) : applyingJobId === job.job_id ? (
                      <><Loader2 className="h-4 w-4 animate-spin" /> Applying...</>
                    ) : (
                      <><Send className="h-4 w-4" /> Apply Now</>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
