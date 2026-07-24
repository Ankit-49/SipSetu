import { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, MapPin, Clock, Briefcase, Send, Loader2, UploadCloud, SlidersHorizontal, X, DollarSign, TrendingUp, FilterX, Bookmark, BookmarkCheck } from "lucide-react";
import { Link } from "react-router";
import api from "@/lib/api";
import { useAuth } from "@/app/context/AuthContext";
import { useToast } from "@/hooks/use-toast";

const JOB_TYPE_OPTIONS = [
  { value: "full", label: "Full-time" },
  { value: "part", label: "Part-time" },
  { value: "contract", label: "Contract" },
];

const EXP_LEVEL_OPTIONS = [
  { value: "fresher", label: "Fresher" },
  { value: "1-3", label: "1-3 years" },
  { value: "3-5", label: "3-5 years" },
  { value: "5+", label: "5+ years" },
];

export default function ApplicantJobMatches() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [search, setSearch] = useState("");
  const [locationFilter, setLocationFilter] = useState("all");
  const [jobTypeFilter, setJobTypeFilter] = useState("all");
  const [expLevelFilter, setExpLevelFilter] = useState("all");
  const [salaryMin, setSalaryMin] = useState("");
  const [salaryMax, setSalaryMax] = useState("");
  const [skillFilter, setSkillFilter] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loading, setLoading] = useState(true);
  const [applyingJobId, setApplyingJobId] = useState<string | null>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [hasResume, setHasResume] = useState(true);
  const [appliedJobIds, setAppliedJobIds] = useState<string[]>([]);
  const [savedJobIds, setSavedJobIds] = useState<string[]>([]);
  const [savingJobId, setSavingJobId] = useState<string | null>(null);

  const buildQuery = useCallback(() => {
    const params = new URLSearchParams({ per_page: "100" });
    if (search) params.set("search", search);
    if (locationFilter !== "all") params.set("location", locationFilter);
    if (jobTypeFilter !== "all") params.set("job_type", jobTypeFilter);
    if (expLevelFilter !== "all") params.set("experience_level", expLevelFilter);
    if (salaryMin) params.set("salary_min", salaryMin);
    if (salaryMax) params.set("salary_max", salaryMax);
    if (skillFilter) params.set("skill", skillFilter);
    return params.toString();
  }, [search, locationFilter, jobTypeFilter, expLevelFilter, salaryMin, salaryMax, skillFilter]);

  const fetchMatches = useCallback(async () => {
    if (!user) { setLoading(false); return; }
    try {
      const params = buildQuery();
      const matchesRes = await api.get(`/applicants/${user.id}/matched-jobs?${params}`);
      const jobsData = matchesRes.data.matched_jobs || [];
      setJobs(jobsData.map((job: any) => ({ ...job, applied: Boolean(job.applied) })));
      setAppliedJobIds(jobsData.filter((j: any) => j.applied).map((j: any) => String(j.job_id)));
      if (matchesRes.data.resume_id === null) setHasResume(false);
    } catch (err) {
      console.error("Failed to load job matches", err);
      setHasResume(false);
    } finally {
      setLoading(false);
    }
  }, [user, buildQuery]);

  // Fetch saved job IDs
  const fetchSavedIds = useCallback(async () => {
    if (!user) return;
    try {
      const res = await api.get(`/applicants/${user.id}/saved-job-ids`);
      setSavedJobIds(res.data.saved_job_ids || []);
    } catch (err) {
      console.error("Failed to load saved job IDs", err);
    }
  }, [user]);

  useEffect(() => {
    if (!user) { setLoading(false); return; }
    setLoading(true);
    const timer = setTimeout(() => {
      Promise.all([fetchMatches(), fetchSavedIds()]);
    }, 150);
    return () => clearTimeout(timer);
  }, [user, fetchMatches, fetchSavedIds]);

  // Count active non-search filters
  const advancedFilterCount = [
    jobTypeFilter !== "all",
    expLevelFilter !== "all",
    !!salaryMin,
    !!salaryMax,
    !!skillFilter,
  ].filter(Boolean).length;

  const clearAllFilters = () => {
    setSearch("");
    setLocationFilter("all");
    setJobTypeFilter("all");
    setExpLevelFilter("all");
    setSalaryMin("");
    setSalaryMax("");
    setSkillFilter("");
  };

  const locations = Array.from(new Set(jobs.map(j => j.location).filter(Boolean)));

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
    if (days < 14) return "1 week ago";
    return `${Math.floor(days / 7)} weeks ago`;
  };

  const handleApply = async (jobId: string) => {
    if (!user || applyingJobId === jobId || appliedJobIds.includes(jobId)) {
      return;
    }

    setApplyingJobId(jobId);
    try {
      await api.post(`/jobs/${jobId}/apply`, { applicant_id: user.id });
      setAppliedJobIds((prev) => [...prev, jobId]);
      const job = jobs.find(j => String(j.job_id) === String(jobId));
      toast({
        title: "Application sent!",
        description: `You applied to "${job?.title || "the job"}".`,
      });
    } catch (err) {
      console.error("Failed to apply for job", err);
      toast({
        title: "Could not apply",
        description: "Please try again in a moment.",
        variant: "destructive",
      });
    } finally {
      setApplyingJobId(null);
    }
  };

  const handleToggleSave = async (jobId: string) => {
    if (!user || savingJobId === jobId) return;
    const isSaved = savedJobIds.includes(jobId);
    setSavingJobId(jobId);
    try {
      if (isSaved) {
        await api.delete(`/jobs/${jobId}/save`);
        setSavedJobIds((prev) => prev.filter(id => id !== jobId));
      } else {
        await api.post(`/jobs/${jobId}/save`);
        setSavedJobIds((prev) => [...prev, jobId]);
      }
    } catch (err) {
      console.error("Failed to toggle save", err);
    } finally {
      setSavingJobId(null);
    }
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
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Job Matches</h1>
        <p className="text-slate-500 mt-1">Opportunities ranked by how well they match your extracted skills.</p>
      </div>

      {!hasResume && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
              <UploadCloud className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-bold text-blue-900">Upload your resume to see matches</h3>
              <p className="text-sm text-blue-700">Our AI will calculate your match score for each job.</p>
            </div>
          </div>
          <Link to="/applicant/resume">
            <Button className="bg-blue-600 hover:bg-blue-700 text-white gap-2 whitespace-nowrap">
              <UploadCloud className="h-4 w-4" /> Upload Resume
            </Button>
          </Link>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Primary filter row */}
        <div className="p-4 flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search roles or companies..."
              className="pl-9 bg-slate-50 border-slate-200"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="flex gap-3">
            <Select value={locationFilter} onValueChange={setLocationFilter}>
              <SelectTrigger className="w-[150px] bg-slate-50">
                <SelectValue placeholder="Location" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Locations</SelectItem>
                {locations.map(loc => (
                  <SelectItem key={loc} value={loc}>{loc}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant={advancedFilterCount > 0 ? "default" : "outline"}
              size="sm"
              className={`gap-2 h-10 ${advancedFilterCount > 0 ? 'bg-[#F97316] hover:bg-[#e8630e] text-white' : 'text-slate-600'}`}
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              <SlidersHorizontal className="h-4 w-4" />
              Filters
              {advancedFilterCount > 0 && (
                <span className="inline-flex items-center justify-center h-5 min-w-[20px] rounded-full bg-white/20 text-xs font-bold px-1">
                  {advancedFilterCount}
                </span>
              )}
            </Button>
          </div>
        </div>

        {/* Advanced filters (collapsible) */}
        {showAdvanced && (
          <div className="px-4 pb-4 border-t border-slate-100 pt-4 animate-in fade-in slide-in-from-top-2 duration-200">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Job Type */}
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-slate-500 flex items-center gap-1.5">
                  <Briefcase className="h-3 w-3" /> Job Type
                </Label>
                <Select value={jobTypeFilter} onValueChange={setJobTypeFilter}>
                  <SelectTrigger className="h-9 bg-slate-50 text-sm">
                    <SelectValue placeholder="All types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    {JOB_TYPE_OPTIONS.map(o => (
                      <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Experience Level */}
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-slate-500 flex items-center gap-1.5">
                  <TrendingUp className="h-3 w-3" /> Experience
                </Label>
                <Select value={expLevelFilter} onValueChange={setExpLevelFilter}>
                  <SelectTrigger className="h-9 bg-slate-50 text-sm">
                    <SelectValue placeholder="All levels" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Levels</SelectItem>
                    {EXP_LEVEL_OPTIONS.map(o => (
                      <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Salary Range */}
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-slate-500 flex items-center gap-1.5">
                  <DollarSign className="h-3 w-3" /> Salary (LPA)
                </Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    placeholder="Min"
                    value={salaryMin}
                    onChange={(e) => setSalaryMin(e.target.value)}
                    className="h-9 bg-slate-50 text-sm"
                  />
                  <span className="text-slate-300 text-sm">-</span>
                  <Input
                    type="number"
                    placeholder="Max"
                    value={salaryMax}
                    onChange={(e) => setSalaryMax(e.target.value)}
                    className="h-9 bg-slate-50 text-sm"
                  />
                </div>
              </div>

              {/* Skill Filter */}
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-slate-500 flex items-center gap-1.5">
                  <Search className="h-3 w-3" /> Skills
                </Label>
                <Input
                  placeholder="e.g. python, react (comma-sep)"
                  value={skillFilter}
                  onChange={(e) => setSkillFilter(e.target.value)}
                  className="h-9 bg-slate-50 text-sm"
                />
              </div>
            </div>

            {/* Active filter badges */}
            <div className="flex flex-wrap items-center gap-2 mt-4 pt-3 border-t border-slate-100">
              {jobTypeFilter !== "all" && (
                <Badge variant="secondary" className="bg-orange-50 text-orange-700 border-orange-200 gap-1 px-2.5 py-1">
                  {JOB_TYPE_OPTIONS.find(o => o.value === jobTypeFilter)?.label || jobTypeFilter}
                  <X className="h-3 w-3 cursor-pointer" onClick={() => setJobTypeFilter("all")} />
                </Badge>
              )}
              {expLevelFilter !== "all" && (
                <Badge variant="secondary" className="bg-orange-50 text-orange-700 border-orange-200 gap-1 px-2.5 py-1">
                  {EXP_LEVEL_OPTIONS.find(o => o.value === expLevelFilter)?.label || expLevelFilter}
                  <X className="h-3 w-3 cursor-pointer" onClick={() => setExpLevelFilter("all")} />
                </Badge>
              )}
              {salaryMin && (
                <Badge variant="secondary" className="bg-orange-50 text-orange-700 border-orange-200 gap-1 px-2.5 py-1">
                  Min: NPR {salaryMin} LPA
                  <X className="h-3 w-3 cursor-pointer" onClick={() => setSalaryMin("")} />
                </Badge>
              )}
              {salaryMax && (
                <Badge variant="secondary" className="bg-orange-50 text-orange-700 border-orange-200 gap-1 px-2.5 py-1">
                  Max: NPR {salaryMax} LPA
                  <X className="h-3 w-3 cursor-pointer" onClick={() => setSalaryMax("")} />
                </Badge>
              )}
              {skillFilter && (
                <Badge variant="secondary" className="bg-orange-50 text-orange-700 border-orange-200 gap-1 px-2.5 py-1">
                  Skills: {skillFilter}
                  <X className="h-3 w-3 cursor-pointer" onClick={() => setSkillFilter("")} />
                </Badge>
              )}
              {advancedFilterCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs text-slate-500 hover:text-red-600 gap-1"
                  onClick={clearAllFilters}
                >
                  <FilterX className="h-3 w-3" /> Clear all
                </Button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Grid */}
      {jobs.length === 0 ? (
        <div className="text-center py-16 text-slate-500">
          <Briefcase className="h-12 w-12 mx-auto text-slate-200 mb-4" />
          <p className="font-medium">{hasResume ? "No job matches found." : "Upload a resume to unlock job matches."}</p>
          <p className="text-sm mt-1">
            {hasResume ? "Try adjusting your filters or check back when new jobs are posted." : ""}
          </p>
        </div>
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
                  <Badge className={
                    job.matching_score >= 85 ? "bg-green-100 text-green-700 hover:bg-green-100 border-none px-3 py-1 text-sm font-bold" :
                    job.matching_score >= 70 ? "bg-orange-100 text-orange-700 hover:bg-orange-100 border-none px-3 py-1 text-sm font-bold" :
                    "bg-slate-100 text-slate-700 hover:bg-slate-100 border-none px-3 py-1 text-sm font-bold"
                  }>
                    {Number(job.matching_score).toFixed(2)}% Match
                  </Badge>
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
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className={`p-1.5 h-auto transition-colors ${
                        savedJobIds.includes(job.job_id)
                          ? "text-[#F97316] hover:text-[#e8630e]"
                          : "text-slate-300 hover:text-slate-500"
                      }`}
                      onClick={() => handleToggleSave(job.job_id)}
                      disabled={savingJobId === job.job_id}
                      title={savedJobIds.includes(job.job_id) ? "Remove from saved" : "Save for later"}
                    >
                      {savingJobId === job.job_id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : savedJobIds.includes(job.job_id) ? (
                        <BookmarkCheck className="h-4 w-4" />
                      ) : (
                        <Bookmark className="h-4 w-4" />
                      )}
                    </Button>
                    <span className="text-xs text-slate-400">{formatPosted(job.created_at)}</span>
                  </div>
                  <Button
                    className="bg-[#F97316] hover:bg-[#F97316]/90 text-white gap-2"
                    onClick={() => handleApply(job.job_id)}
                    disabled={applyingJobId === job.job_id || appliedJobIds.includes(job.job_id)}
                  >
                    {appliedJobIds.includes(job.job_id) ? (
                      "Applied"
                    ) : applyingJobId === job.job_id ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" /> Applying...
                      </>
                    ) : (
                      <>
                        <Send className="h-4 w-4" /> Apply Now
                      </>
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
