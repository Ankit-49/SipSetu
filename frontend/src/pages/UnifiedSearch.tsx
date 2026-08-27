import { useState, useEffect, useCallback, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Search,
  Sparkles,
  Briefcase,
  MapPin,
  Clock,
  Loader2,
  X,
  SlidersHorizontal,
  TrendingUp,
  Building2,
  Heart,
  RotateCcw,
  User,
} from "lucide-react";
import { Link } from "react-router";
import api from "@/lib/api";
import { useAuth } from "@/app/context/AuthContext";
import { SimilarJobsPanel } from "@/components/SimilarJobsPanel";
import { SimilarResumesPanel } from "@/components/SimilarResumesPanel";

// ---- Types ----

interface Job {
  job_id: string;
  title: string;
  description?: string;
  location?: string;
  job_type?: string;
  experience_level?: string;
  salary_min?: number;
  salary_max?: number;
  skills?: string[];
  created_at?: string;
  recruiter_name?: string;
  match_score?: number;
  applied?: boolean;
}

interface SemanticResult {
  job_id?: string;
  resume_id?: string;
  title?: string;
  applicant_name?: string;
  company?: string;
  location?: string;
  similarity_score: number;
  skills: string[];
}

const EXPERIENCE_MAP: Record<string, string> = {
  fresher: "Fresher",
  "1-3": "1-3 years",
  "3-5": "3-5 years",
  "5+": "5+ years",
  Entry: "Entry",
  Mid: "Mid",
  Senior: "Senior",
  Lead: "Lead",
};

// ---- Component ----

export default function UnifiedSearch() {
  const { user } = useAuth();
  const isRecruiter = user?.role === "recruiter";

  // Core search state
  const [query, setQuery] = useState("");
  const [activeTab, setActiveTab] = useState(isRecruiter ? "keyword" : "keyword");
  const [loading, setLoading] = useState(false);

  // Filter state
  const [showFilters, setShowFilters] = useState(false);
  const [jobTypeFilter, setJobTypeFilter] = useState("all");
  const [expLevelFilter, setExpLevelFilter] = useState("all");
  const [locationFilter, setLocationFilter] = useState("all");
  const [salaryMin, setSalaryMin] = useState("");
  const [salaryMax, setSalaryMax] = useState("");
  const [skillFilter, setSkillFilter] = useState("");

  // Results
  const [keywordResults, setKeywordResults] = useState<Job[]>([]);
  const [semanticResults, setSemanticResults] = useState<SemanticResult[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [recruiterJobs, setRecruiterJobs] = useState<{ job_id: string; title: string }[]>([]);

  // ---- Fetch keyword search results ----
  const fetchKeywordResults = useCallback(async (overrides?: { search?: string }) => {
    setLoading(true);
    const q = overrides?.search ?? query;
    try {
      const params = new URLSearchParams({ limit: "30" });
      if (q) params.set("search", q);
      if (jobTypeFilter !== "all") params.set("job_type", jobTypeFilter);
      if (expLevelFilter !== "all") params.set("experience_level", expLevelFilter);
      if (locationFilter !== "all") params.set("location", locationFilter);
      if (salaryMin) params.set("salary_min", salaryMin);
      if (salaryMax) params.set("salary_max", salaryMax);
      if (skillFilter) params.set("skill", skillFilter);

      const res = await api.get(`/jobs?${params.toString()}`);
      const data = res.data?.data ?? res.data?.jobs ?? [];
      setKeywordResults(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Search failed", err);
      setKeywordResults([]);
    } finally {
      setLoading(false);
    }
  }, [jobTypeFilter, expLevelFilter, locationFilter, salaryMin, salaryMax, skillFilter]);

  // ---- Fetch semantic job matches (for applicants) ----
  const fetchSemanticResults = useCallback(async () => {
    if (!user || isRecruiter) return;
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: "30" });
      if (jobTypeFilter !== "all") params.set("job_type", jobTypeFilter);
      if (expLevelFilter !== "all") params.set("experience_level", expLevelFilter);
      if (locationFilter !== "all") params.set("location", locationFilter);
      if (salaryMin) params.set("salary_min", salaryMin);
      if (salaryMax) params.set("salary_max", salaryMax);
      if (skillFilter) params.set("skill", skillFilter);

      const res = await api.get(`/applicants/${user.id}/matched-jobs?${params.toString()}`);
      const data = res.data?.data || [];
      setSemanticResults(data.map((j: Job) => ({
        job_id: j.job_id,
        title: j.title,
        company: j.recruiter_name,
        location: j.location,
        similarity_score: (j.match_score || 0) / 100,
        skills: j.skills || [],
      })));
    } catch (err) {
      console.error("Semantic search failed", err);
      setSemanticResults([]);
    } finally {
      setLoading(false);
    }
  }, [user, isRecruiter, jobTypeFilter, expLevelFilter, locationFilter, salaryMin, salaryMax, skillFilter]);

  // ---- Fetch recruiter's jobs for similar-resumes tab ----
  const fetchRecruiterJobs = useCallback(async () => {
    if (!user || !isRecruiter) return;
    try {
      const res = await api.get(`/jobs?recruiter_id=${user.id}&limit=50`);
      const data = res.data?.data ?? res.data?.jobs ?? [];
      setRecruiterJobs(Array.isArray(data) ? data.map((j: Job) => ({ job_id: j.job_id, title: j.title })) : []);
    } catch {
      // silent
    }
  }, [user, isRecruiter]);

  // Initial loads
  useEffect(() => {
    fetchKeywordResults();
    if (isRecruiter) fetchRecruiterJobs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-fetch on tab change
  useEffect(() => {
    if (activeTab === "keyword") fetchKeywordResults();
    else if (activeTab === "semantic") fetchSemanticResults();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  // Ref to track the current search query for the input handler
  const queryRef = useRef(query);
  queryRef.current = query;

  // ---- Helpers ----
  const activeFilterCount = [
    jobTypeFilter !== "all",
    expLevelFilter !== "all",
    locationFilter !== "all",
    !!salaryMin,
    !!salaryMax,
    !!skillFilter,
  ].filter(Boolean).length;

  const clearFilters = () => {
    setJobTypeFilter("all");
    setExpLevelFilter("all");
    setLocationFilter("all");
    setSalaryMin("");
    setSalaryMax("");
    setSkillFilter("");
  };

  const formatSalary = (job: Job) => {
    if (job.salary_min && job.salary_max)
      return `NPR ${Math.round(job.salary_min)} - ${Math.round(job.salary_max)} LPA`;
    if (job.salary_min) return `NPR ${Math.round(job.salary_min)}+ LPA`;
    if (job.salary_max) return `Up to NPR ${Math.round(job.salary_max)} LPA`;
    return null;
  };

  const locations = Array.from(
    new Set(keywordResults.map((j) => j.location).filter(Boolean))
  );

  // ---- Shared filter bar ----
  const renderFilters = () => (
    <div className="space-y-4">
      {/* Primary row */}
      <div className="flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder={isRecruiter ? "Search jobs by title, skill, or location..." : "Search roles, companies, or skills..."}
            className="pl-9 bg-slate-50 border-slate-200"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && fetchKeywordResults({ search: e.currentTarget.value })}
          />
        </div>
        <Button
          variant="outline"
          className="gap-2 shrink-0"
          onClick={() => setShowFilters(!showFilters)}
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filters
          {activeFilterCount > 0 && (
            <Badge className="ml-1 h-5 min-w-[20px] px-1 bg-[#F97316] text-white text-[10px]">
              {activeFilterCount}
            </Badge>
          )}
        </Button>
        <Button onClick={() => fetchKeywordResults()} className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
          Search
        </Button>
      </div>

      {/* Advanced filters */}
      {showFilters && (
        <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">Job Type</label>
              <Select value={jobTypeFilter} onValueChange={setJobTypeFilter}>
                <SelectTrigger className="bg-white"><SelectValue placeholder="All types" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="Full-time">Full-time</SelectItem>
                  <SelectItem value="Part-time">Part-time</SelectItem>
                  <SelectItem value="Contract">Contract</SelectItem>
                  <SelectItem value="Internship">Internship</SelectItem>
                  <SelectItem value="Remote">Remote</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">Experience</label>
              <Select value={expLevelFilter} onValueChange={setExpLevelFilter}>
                <SelectTrigger className="bg-white"><SelectValue placeholder="All levels" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="Entry">Entry</SelectItem>
                  <SelectItem value="Mid">Mid</SelectItem>
                  <SelectItem value="Senior">Senior</SelectItem>
                  <SelectItem value="Lead">Lead</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">Location</label>
              <Select value={locationFilter} onValueChange={setLocationFilter}>
                <SelectTrigger className="bg-white"><SelectValue placeholder="All locations" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Locations</SelectItem>
                  {locations.map((loc) => (
                    <SelectItem key={loc} value={loc!}>{loc}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">Skill</label>
              <Input
                placeholder="e.g. Python, React"
                className="bg-white"
                value={skillFilter}
                onChange={(e) => setSkillFilter(e.target.value)}
              />
            </div>
          </div>
          <div className="flex items-center gap-3 mt-3">
            <div className="flex items-center gap-2">
              <label className="text-xs text-slate-500">Salary (LPA):</label>
              <Input
                type="number"
                placeholder="Min"
                className="w-24 bg-white h-8 text-xs"
                value={salaryMin}
                onChange={(e) => setSalaryMin(e.target.value)}
              />
              <span className="text-slate-400">-</span>
              <Input
                type="number"
                placeholder="Max"
                className="w-24 bg-white h-8 text-xs"
                value={salaryMax}
                onChange={(e) => setSalaryMax(e.target.value)}
              />
            </div>
            {activeFilterCount > 0 && (
              <Button variant="ghost" size="sm" onClick={clearFilters} className="text-xs gap-1 text-slate-500">
                <RotateCcw className="h-3 w-3" /> Clear all
              </Button>
            )}
          </div>
          {/* Active filter badges */}
          {activeFilterCount > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-slate-200">
              {jobTypeFilter !== "all" && (
                <Badge variant="secondary" className="bg-orange-50 text-orange-700 border-orange-200 text-[10px] gap-1">
                  {jobTypeFilter} <X className="h-2.5 w-2.5 cursor-pointer" onClick={() => setJobTypeFilter("all")} />
                </Badge>
              )}
              {expLevelFilter !== "all" && (
                <Badge variant="secondary" className="bg-blue-50 text-blue-700 border-blue-200 text-[10px] gap-1">
                  {expLevelFilter} <X className="h-2.5 w-2.5 cursor-pointer" onClick={() => setExpLevelFilter("all")} />
                </Badge>
              )}
              {locationFilter !== "all" && (
                <Badge variant="secondary" className="bg-green-50 text-green-700 border-green-200 text-[10px] gap-1">
                  {locationFilter} <X className="h-2.5 w-2.5 cursor-pointer" onClick={() => setLocationFilter("all")} />
                </Badge>
              )}
              {skillFilter && (
                <Badge variant="secondary" className="bg-purple-50 text-purple-700 border-purple-200 text-[10px] gap-1">
                  {skillFilter} <X className="h-2.5 w-2.5 cursor-pointer" onClick={() => setSkillFilter("")} />
                </Badge>
              )}
              {(salaryMin || salaryMax) && (
                <Badge variant="secondary" className="bg-amber-50 text-amber-700 border-amber-200 text-[10px] gap-1">
                  NPR {salaryMin || "0"}-{salaryMax || "∞"} LPA <X className="h-2.5 w-2.5 cursor-pointer" onClick={() => { setSalaryMin(""); setSalaryMax(""); }} />
                </Badge>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );

  // ---- Shared job card ----
  const renderJobCard = (job: Job, extra?: { score?: number; scoreLabel?: string }) => {
    const createdDate = job.created_at
      ? new Date(job.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
      : "";

    return (
      <Card key={job.job_id} className="hover:shadow-md transition-shadow group">
        <CardContent className="p-4">
          <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-start gap-3">
                <div className="h-9 w-9 rounded-lg bg-[#1E3A5F]/5 flex items-center justify-center shrink-0 mt-0.5">
                  <Briefcase className="h-4 w-4 text-[#1E3A5F]" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-slate-900 text-sm">{job.title}</h3>
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-1 text-[11px] text-slate-500">
                    {job.location && (
                      <span className="flex items-center gap-0.5"><MapPin className="h-2.5 w-2.5" /> {job.location}</span>
                    )}
                    {job.job_type && (
                      <span className="flex items-center gap-0.5"><Briefcase className="h-2.5 w-2.5" /> {job.job_type}</span>
                    )}
                    {job.experience_level && (
                      <span className="flex items-center gap-0.5"><TrendingUp className="h-2.5 w-2.5" /> {EXPERIENCE_MAP[job.experience_level] || job.experience_level}</span>
                    )}
                    {createdDate && (
                      <span className="flex items-center gap-0.5"><Clock className="h-2.5 w-2.5" /> {createdDate}</span>
                    )}
                  </div>
                  {job.skills && job.skills.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {job.skills.slice(0, 5).map((s: string) => (
                        <Badge key={s} variant="outline" className="text-[10px] px-1.5 py-0 text-slate-500 bg-white">{s}</Badge>
                      ))}
                      {job.skills.length > 5 && (
                        <span className="text-[10px] text-slate-400 self-center">+{job.skills.length - 5}</span>
                      )}
                    </div>
                  )}
                  {job.description && (
                    <p className="text-[11px] text-slate-400 mt-2 line-clamp-1">{job.description}</p>
                  )}
                </div>
              </div>
            </div>
            <div className="flex flex-row lg:flex-col items-center lg:items-end gap-2 shrink-0">
              {formatSalary(job) && (
                <Badge variant="secondary" className="bg-green-50 text-green-700 border-green-200 text-[10px] whitespace-nowrap">
                  {formatSalary(job)}
                </Badge>
              )}
              {extra?.score !== undefined && (
                <Badge
                  variant="secondary"
                  className={`text-[10px] whitespace-nowrap font-bold ${
                    extra.score >= 80 ? "bg-green-50 text-green-700 border-green-200"
                    : extra.score >= 60 ? "bg-yellow-50 text-yellow-700 border-yellow-200"
                    : "bg-orange-50 text-orange-700 border-orange-200"
                  }`}
                >
                  <Sparkles className="h-2.5 w-2.5 mr-0.5" />
                  {Math.round(extra.score)}% {extra.scoreLabel || "match"}
                </Badge>
              )}
              {!isRecruiter && (
                <Link to="/applicant/matches">
                  <Button variant="ghost" size="sm" className="h-7 text-[10px] text-[#1E3A5F] gap-1">
                    View Details
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  // ---- Tab definitions ----
  const applicantTabs = [
    { value: "keyword", label: "All Jobs", icon: Briefcase },
    { value: "semantic", label: "Best Matches", icon: Sparkles },
  ];

  const recruiterTabs = [
    { value: "keyword", label: "All Jobs", icon: Briefcase },
    { value: "resumes", label: "Similar Resumes", icon: User },
  ];

  const tabs = isRecruiter ? recruiterTabs : applicantTabs;

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Search</h1>
        <p className="text-slate-500 mt-1">
          {isRecruiter
            ? "Search job postings and find semantically similar candidates."
            : "Explore job opportunities with keyword and AI-powered semantic matching."}
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Main content */}
        <div className="flex-1 space-y-5">
          {/* Filter bar */}
          {renderFilters()}

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="bg-slate-100">
              {tabs.map((tab) => (
                <TabsTrigger key={tab.value} value={tab.value} className="gap-1.5">
                  <tab.icon className="h-3.5 w-3.5" />
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>

            {/* ---- Keyword Search Tab ---- */}
            <TabsContent value="keyword" className="mt-4">
              {loading ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="h-6 w-6 animate-spin text-[#F97316]" />
                </div>
              ) : keywordResults.length === 0 ? (
                <Card className="p-12 text-center">
                  <Search className="h-10 w-10 mx-auto text-slate-300 mb-3" />
                  <p className="font-medium text-slate-700">No jobs found</p>
                  <p className="text-sm text-slate-400 mt-1">Try adjusting your search or filters.</p>
                </Card>
              ) : (
                <div className="space-y-3">
                  <p className="text-xs text-slate-400">{keywordResults.length} jobs found</p>
                  {keywordResults.map((job) => renderJobCard(job))}
                </div>
              )}
            </TabsContent>

            {/* ---- Semantic Matches Tab (Applicant) ---- */}
            {!isRecruiter && (
              <TabsContent value="semantic" className="mt-4">
                {loading ? (
                  <div className="flex items-center justify-center py-16">
                    <Loader2 className="h-6 w-6 animate-spin text-purple-500" />
                  </div>
                ) : semanticResults.length === 0 ? (
                  <Card className="p-12 text-center">
                    <Sparkles className="h-10 w-10 mx-auto text-slate-300 mb-3" />
                    <p className="font-medium text-slate-700">No semantic matches</p>
                    <p className="text-sm text-slate-400 mt-1">Upload a resume to unlock AI-powered job matching.</p>
                  </Card>
                ) : (
                  <div className="space-y-3">
                    <p className="text-xs text-slate-400">{semanticResults.length} jobs ranked by semantic similarity to your resume</p>
                    {semanticResults.map((r, i) => (
                      <Card key={r.job_id || i} className="hover:shadow-md transition-shadow">
                        <CardContent className="p-4 flex items-center gap-4">
                          <div className="text-[10px] font-bold text-slate-400 w-5 text-center shrink-0">#{i + 1}</div>
                          <div className="h-9 w-9 rounded-lg bg-purple-50 flex items-center justify-center shrink-0">
                            <Briefcase className="h-4 w-4 text-purple-600" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-semibold text-slate-900 truncate">{r.title}</h4>
                            <div className="flex items-center gap-2 mt-0.5 text-[11px] text-slate-500">
                              {r.company && <span className="flex items-center gap-0.5"><Building2 className="h-2.5 w-2.5" /> {r.company}</span>}
                              {r.location && <span className="flex items-center gap-0.5"><MapPin className="h-2.5 w-2.5" /> {r.location}</span>}
                            </div>
                            {r.skills.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-1.5">
                                {r.skills.slice(0, 4).map((s) => (
                                  <Badge key={s} variant="outline" className="text-[10px] px-1.5 py-0 text-slate-500 bg-white">{s}</Badge>
                                ))}
                                {r.skills.length > 4 && <span className="text-[10px] text-slate-400 self-center">+{r.skills.length - 4}</span>}
                              </div>
                            )}
                          </div>
                          <div className={`shrink-0 inline-flex items-center gap-1 px-2.5 py-1 rounded-full border text-xs font-bold ${
                            Math.round(r.similarity_score * 100) >= 80 ? "bg-green-50 text-green-700 border-green-200"
                            : Math.round(r.similarity_score * 100) >= 60 ? "bg-yellow-50 text-yellow-700 border-yellow-200"
                            : "bg-orange-50 text-orange-700 border-orange-200"
                          }`}>
                            <Sparkles className="h-3 w-3" /> {Math.round(r.similarity_score * 100)}%
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </TabsContent>
            )}

            {/* ---- Similar Resumes Tab (Recruiter) ---- */}
            {isRecruiter && (
              <TabsContent value="resumes" className="mt-4">
                {recruiterJobs.length === 0 ? (
                  <Card className="p-12 text-center">
                    <Briefcase className="h-10 w-10 mx-auto text-slate-300 mb-3" />
                    <p className="font-medium text-slate-700">No jobs posted yet</p>
                    <p className="text-sm text-slate-400 mt-1">Post a job first to find similar candidates.</p>
                  </Card>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="text-xs font-medium text-slate-500 mb-1.5 block">Select a job to find similar resumes</label>
                      <Select value={selectedJobId || ""} onValueChange={(v) => setSelectedJobId(v)}>
                        <SelectTrigger className="bg-white">
                          <SelectValue placeholder="Choose a job..." />
                        </SelectTrigger>
                        <SelectContent>
                          {recruiterJobs.map((j) => (
                            <SelectItem key={j.job_id} value={j.job_id}>{j.title}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    {selectedJobId && (
                      <SimilarResumesPanel
                        jobId={selectedJobId}
                        jobTitle={recruiterJobs.find((j) => j.job_id === selectedJobId)?.title}
                      />
                    )}
                  </div>
                )}
              </TabsContent>
            )}
          </Tabs>
        </div>

        {/* Right sidebar — Similar Jobs for applicants */}
        {!isRecruiter && (
          <div className="w-full lg:w-72 shrink-0">
            {/* We'll show a placeholder — the real panel needs a resumeId, which we fetch */}
            <ApplicantSidebar />
          </div>
        )}
      </div>
    </div>
  );
}

// ---- Small helper component to fetch resume ID and show SimilarJobsPanel ----
function ApplicantSidebar() {
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const userId = localStorage.getItem("user_id");
    if (!userId) { setChecking(false); return; }
    api.get(`/resumes?applicant_id=${userId}`)
      .then((res) => {
        const list = res.data?.data || [];
        if (list.length > 0) setResumeId(list[0].resume_id);
      })
      .catch(() => {})
      .finally(() => setChecking(false));
  }, []);

  if (checking) {
    return (
      <Card className="p-8 text-center">
        <Loader2 className="h-5 w-5 animate-spin text-purple-500 mx-auto mb-2" />
        <p className="text-xs text-slate-400">Loading matches...</p>
      </Card>
    );
  }

  if (!resumeId) {
    return (
      <Card className="p-6 text-center">
        <Heart className="h-8 w-8 mx-auto text-slate-300 mb-2" />
        <p className="text-sm font-medium text-slate-700">No resume uploaded</p>
        <p className="text-xs text-slate-400 mt-1">Upload a resume to see similar jobs.</p>
        <Link to="/applicant/resume">
          <Button size="sm" className="mt-3 bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 text-xs">Upload Resume</Button>
        </Link>
      </Card>
    );
  }

  return <SimilarJobsPanel resumeId={resumeId} />;
}
