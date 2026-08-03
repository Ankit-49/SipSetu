import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  ExternalLink,
  Target,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Loader2,
  UploadCloud,
  MapPin,
  Briefcase,
  GraduationCap,
  DollarSign,
  BookOpen,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { useState, useEffect } from "react";
import { useAuth } from "@/app/context/AuthContext";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Link } from "react-router";
import api from "@/lib/api";

type Resource = { label: string; url: string };

const LEARNING_RESOURCES: Record<string, Resource[]> = {
  "typescript": [
    { label: "TypeScript Handbook (official)", url: "https://www.typescriptlang.org/docs/handbook/intro.html" },
    { label: "YouTube: TypeScript Full Course", url: "https://www.youtube.com/results?search_query=typescript+full+course" },
    { label: "Udemy: TypeScript Bootcamp", url: "https://www.udemy.com/courses/search/?q=typescript+bootcamp" },
  ],
  "node.js": [
    { label: "Node.js official docs", url: "https://nodejs.org/en/docs" },
    { label: "YouTube: Node.js Crash Course", url: "https://www.youtube.com/results?search_query=node.js+crash+course" },
    { label: "The Odin Project: Node.js", url: "https://www.theodinproject.com/paths/full-stack-javascript/courses/nodejs" },
  ],
  "python": [
    { label: "Python official tutorial", url: "https://docs.python.org/3/tutorial/" },
    { label: "Real Python", url: "https://realpython.com/" },
    { label: "CS50 Python (Harvard)", url: "https://cs50.harvard.edu/python/" },
  ],
  "react": [
    { label: "React official docs", url: "https://react.dev/" },
    { label: "YouTube: React Tutorial", url: "https://www.youtube.com/results?search_query=react+full+course" },
    { label: "Frontend Masters: React", url: "https://frontendmasters.com/courses/react/" },
  ],
  "docker": [
    { label: "Docker official docs", url: "https://docs.docker.com/get-started/" },
    { label: "YouTube: Docker for Beginners (Nana)", url: "https://www.youtube.com/results?search_query=docker+techworld+with+nana" },
    { label: "Udemy: Docker & Kubernetes", url: "https://www.udemy.com/courses/search/?q=docker+kubernetes" },
  ],
  "aws": [
    { label: "AWS Skill Builder (free)", url: "https://explore.skillbuilder.aws/" },
    { label: "A Cloud Guru", url: "https://acloudguru.com/" },
    { label: "AWS Solutions Architect cert path", url: "https://aws.amazon.com/certification/certified-solutions-architect-associate/" },
  ],
  "postgresql": [
    { label: "PostgreSQL official docs", url: "https://www.postgresql.org/docs/" },
    { label: "PGExercises", url: "https://pgexercises.com/" },
    { label: "YouTube: SQL & PostgreSQL Course", url: "https://www.youtube.com/results?search_query=postgresql+full+course" },
  ],
  "machine learning": [
    { label: "fast.ai", url: "https://www.fast.ai/" },
    { label: "Coursera ML Specialization", url: "https://www.coursera.org/specializations/machine-learning-introduction" },
    { label: "Kaggle Learn", url: "https://www.kaggle.com/learn" },
  ],
  "system design": [
    { label: "System Design Primer (GitHub)", url: "https://github.com/donnemartin/system-design-primer" },
    { label: "ByteByteGo newsletter", url: "https://blog.bytebytego.com/" },
    { label: "Grokking System Design", url: "https://www.designgurus.io/course/grokking-the-system-design-interview" },
  ],
  "kubernetes": [
    { label: "Kubernetes official docs", url: "https://kubernetes.io/docs/tutorials/" },
    { label: "YouTube: K8s Crash Course (Nana)", url: "https://www.youtube.com/results?search_query=kubernetes+techworld+with+nana" },
    { label: "CKAD certification prep", url: "https://training.linuxfoundation.org/certification/certified-kubernetes-application-developer-ckad/" },
  ],
};

function getResources(skill: string): Resource[] {
  const lower = skill.toLowerCase();
  for (const key of Object.keys(LEARNING_RESOURCES)) {
    if (lower.includes(key) || key.includes(lower)) return LEARNING_RESOURCES[key];
  }
  const q = encodeURIComponent(`${skill} tutorial`);
  return [
    { label: `YouTube: "${skill}" tutorials`, url: `https://www.youtube.com/results?search_query=${q}` },
    { label: `Coursera: "${skill}" courses`, url: `https://www.coursera.org/search?query=${encodeURIComponent(skill)}` },
    { label: `Udemy: "${skill}" courses`, url: `https://www.udemy.com/courses/search/?q=${encodeURIComponent(skill)}` },
  ];
}

const PRIORITY_ORDER: Record<string, number> = { High: 0, Medium: 1, Low: 2 };

export default function ApplicantSkillGap() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [selectedJobId, setSelectedJobId] = useState<string>("all");
  const [gapData, setGapData] = useState<any>(null);
  const [gapLoading, setGapLoading] = useState(false);
  const [hasResume, setHasResume] = useState(true);
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({});

  // Fetch skill gap data (matched jobs come back with it, so no separate call needed)
  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    const fetchGap = async () => {
      setGapLoading(true);
      try {
        const url = selectedJobId === "all"
          ? `/applicants/${user.id}/skill-gap`
          : `/applicants/${user.id}/skill-gap?job_id=${selectedJobId}`;
        const res = await api.get(url);
        setGapData(res.data);
        if (res.data.missing_skills?.length > 0) {
          setOpenItems({ [res.data.missing_skills[0].skill]: true });
        }
        setHasResume(true);
      } catch (err: any) {
        if (err.response?.status === 404) setHasResume(false);
        setGapData(null);
      } finally {
        setGapLoading(false);
        setLoading(false);
      }
    };
    fetchGap();
  }, [selectedJobId, user]);

  const toggleItem = (skill: string) => {
    setOpenItems(prev => ({ ...prev, [skill]: !prev[skill] }));
  };

  const switchJob = (jobId: string) => {
    setSelectedJobId(jobId);
    setOpenItems({});
  };

  const formatSalary = (min: number | null, max: number | null): string => {
    const fmt = (n: number) => `$${n >= 1000 ? `${n / 1000}k` : n}`;
    if (min && max) return `${fmt(min)} – ${fmt(max)}`;
    if (min) return `From ${fmt(min)}`;
    if (max) return `Up to ${fmt(max)}`;
    return "Not disclosed";
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#F97316]" />
      </div>
    );
  }

  const missingCount = gapData?.missing_skills?.length ?? 0;
  const highCount = gapData?.missing_skills?.filter((m: any) => m.priority === "High").length ?? 0;
  const mediumCount = gapData?.missing_skills?.filter((m: any) => m.priority === "Medium").length ?? 0;
  const matchedJobs = gapData?.matched_jobs || [];
  const consideredJobs = gapData?.considered_jobs || [];
  const jobDetail = gapData?.job_detail;

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Skill Gap Analysis</h1>
          <p className="text-slate-500 mt-1">See exactly what's standing between you and your best-matched roles — and how to close the gap.</p>
        </div>
        <div className="w-full md:w-80">
          <p className="text-sm font-medium text-slate-700 mb-2">Analyze skill gap for:</p>
          <Select value={selectedJobId} onValueChange={switchJob} disabled={matchedJobs.length === 0}>
            <SelectTrigger className="bg-white border-slate-200">
              <SelectValue placeholder="Select a job" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">
                {matchedJobs.length > 0 ? `All My Matched Jobs (${matchedJobs.length})` : "All Matched Jobs"}
              </SelectItem>
              {matchedJobs.map((job: any) => (
                <SelectItem key={job.job_id} value={job.job_id}>
                  {job.title} • {job.matching_score}%
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* No resume warning */}
      {!hasResume && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
              <UploadCloud className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-bold text-blue-900">Upload your resume first</h3>
              <p className="text-sm text-blue-700">Skill gap analysis requires a resume to compare against job requirements.</p>
            </div>
          </div>
          <Link to="/applicant/resume">
            <Button className="bg-blue-600 hover:bg-blue-700 text-white gap-2 whitespace-nowrap">
              <UploadCloud className="h-4 w-4" /> Upload Resume
            </Button>
          </Link>
        </div>
      )}

      {gapLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-[#F97316]" />
        </div>
      )}

      {!gapLoading && gapData && matchedJobs.length === 0 && (
        <Card className="p-10 text-center">
          <Target className="h-12 w-12 mx-auto mb-4 text-slate-200" />
          <h3 className="font-bold text-slate-800 text-lg">No matched roles yet</h3>
          <p className="text-slate-500 mt-1 max-w-md mx-auto">
            Once recruiters post jobs that match your skills, they'll appear here with a full gap analysis. Try
            improving your resume to increase your match scores.
          </p>
          <Link to="/applicant/resume" className="inline-block mt-5">
            <Button className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 text-white gap-2">
              <UploadCloud className="h-4 w-4" /> Improve My Resume
            </Button>
          </Link>
        </Card>
      )}

      {!gapLoading && gapData && matchedJobs.length > 0 && (
        <>
          {/* Job detail strip for single-job view */}
          {jobDetail && (
            <Card className="bg-gradient-to-r from-[#1E3A5F] to-[#2a4f7a] text-white border-none shadow-md">
              <CardContent className="p-5 flex flex-col md:flex-row md:items-center gap-4 justify-between">
                <div>
                  <h3 className="font-bold text-lg">{jobDetail.title}</h3>
                  <p className="text-white/70 text-sm">{jobDetail.company}</p>
                </div>
                <div className="flex flex-wrap gap-3 text-sm">
                  {jobDetail.location && (
                    <span className="flex items-center gap-1.5 bg-white/10 rounded-lg px-3 py-1.5">
                      <MapPin className="h-3.5 w-3.5" /> {jobDetail.location}
                    </span>
                  )}
                  {jobDetail.job_type && (
                    <span className="flex items-center gap-1.5 bg-white/10 rounded-lg px-3 py-1.5">
                      <Briefcase className="h-3.5 w-3.5" /> {jobDetail.job_type}
                    </span>
                  )}
                  {jobDetail.experience_level && (
                    <span className="flex items-center gap-1.5 bg-white/10 rounded-lg px-3 py-1.5">
                      <GraduationCap className="h-3.5 w-3.5" /> {jobDetail.experience_level}
                    </span>
                  )}
                  <span className="flex items-center gap-1.5 bg-white/10 rounded-lg px-3 py-1.5">
                    <DollarSign className="h-3.5 w-3.5" /> {formatSalary(jobDetail.salary_min, jobDetail.salary_max)}
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column: Missing Skills */}
            <div className="lg:col-span-2 space-y-6">
              <Card id="missing-skills" className="border-t-4 border-t-[#F97316] scroll-mt-6">
                <CardHeader className="pb-3">
                  <CardTitle className="text-xl flex items-center gap-2">
                    <BookOpen className="h-5 w-5 text-[#F97316]" /> Missing Skills to Learn
                  </CardTitle>
                  <CardDescription>
                    {missingCount > 0
                      ? `${missingCount} skill${missingCount > 1 ? "s" : ""} required for "${gapData.job_title}" that aren't in your profile.`
                      : `Great job! You have all required skills for "${gapData.job_title}".`}
                  </CardDescription>
                  {missingCount > 0 && (
                    <div className="flex flex-wrap gap-2 pt-1">
                      {highCount > 0 && (
                        <Badge className="bg-red-50 text-red-700 border-red-200">{highCount} high priority</Badge>
                      )}
                      {mediumCount > 0 && (
                        <Badge className="bg-orange-50 text-orange-700 border-orange-200">{mediumCount} medium priority</Badge>
                      )}
                      {missingCount - highCount - mediumCount > 0 && (
                        <Badge className="bg-slate-100 text-slate-600 border-slate-200">
                          {missingCount - highCount - mediumCount} low priority
                        </Badge>
                      )}
                    </div>
                  )}
                </CardHeader>
                <CardContent className="p-0">
                  {missingCount === 0 ? (
                    <div className="p-8 text-center">
                      <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-3" />
                      <p className="font-semibold text-green-700">You're a perfect match!</p>
                      <p className="text-sm text-slate-500 mt-1">No skill gaps detected for this role.</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-slate-100">
                      {[...gapData.missing_skills]
                        .sort((a: any, b: any) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority])
                        .map((item: any) => (
                          <Collapsible
                            key={item.skill}
                            open={openItems[item.skill]}
                            onOpenChange={() => toggleItem(item.skill)}
                            className="p-4 bg-white"
                          >
                            <CollapsibleTrigger className="w-full flex items-center justify-between group">
                              <div className="flex items-center gap-3 flex-wrap">
                                <div className={`p-2 rounded-lg ${
                                  item.priority === 'High' ? 'bg-red-50 text-red-600' :
                                  item.priority === 'Medium' ? 'bg-orange-50 text-orange-600' :
                                  'bg-slate-100 text-slate-600'
                                }`}>
                                  <Target className="h-4 w-4" />
                                </div>
                                <span className="font-semibold text-slate-900 capitalize">{item.skill}</span>
                                <Badge variant="outline" className={
                                  item.priority === 'High' ? 'border-red-200 text-red-700 bg-red-50' :
                                  item.priority === 'Medium' ? 'border-orange-200 text-orange-700 bg-orange-50' :
                                  'border-slate-200 text-slate-700 bg-slate-50'
                                }>
                                  {item.priority}
                                </Badge>
                                {item.frequency != null && consideredJobs.length > 1 && (
                                  <Badge variant="secondary" className="bg-blue-50 text-blue-700 border border-blue-200">
                                    Required in {item.frequency} of {consideredJobs.length} roles
                                  </Badge>
                                )}
                              </div>
                              <Button variant="ghost" size="sm" className="text-slate-400 group-hover:text-slate-900">
                                {openItems[item.skill] ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                              </Button>
                            </CollapsibleTrigger>

                            <CollapsibleContent className="pt-4 pl-14">
                              <p className="text-sm font-medium text-slate-900 mb-3 uppercase tracking-wider flex items-center gap-1.5">
                                <Sparkles className="h-3.5 w-3.5 text-[#F97316]" /> Recommended Resources
                              </p>
                              <ul className="space-y-2">
                                {getResources(item.skill).map((res, i) => (
                                  <li key={i}>
                                    <a
                                      href={res.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center text-sm text-[#1E3A5F] hover:underline gap-1.5 p-1.5 -ml-1.5 rounded hover:bg-blue-50 transition-colors"
                                    >
                                      <ExternalLink className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                                      {res.label}
                                    </a>
                                  </li>
                                ))}
                              </ul>
                            </CollapsibleContent>
                          </Collapsible>
                        ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Your Strengths */}
              <Card>
                <CardHeader className="pb-4">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-600" /> Your Strengths
                  </CardTitle>
                  <CardDescription>Skills you already have that match this role.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {gapData.matched_skills?.length > 0 ? gapData.matched_skills.map((skill: string) => (
                      <Badge key={skill} className="bg-green-50 text-green-700 border border-green-200 hover:bg-green-100 px-3 py-1 font-medium gap-1.5 capitalize">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        {skill}
                      </Badge>
                    )) : (
                      <p className="text-sm text-slate-400">
                        {selectedJobId === "all" ? "No matching skills found yet for your target roles." : "No matching skills found for this role."}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Right Column: Readiness + Context */}
            <div className="space-y-6">
              <Card className="bg-[#1E3A5F] text-white border-none shadow-lg">
                <CardContent className="p-8 text-center">
                  <div className="relative w-32 h-32 mx-auto mb-6">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="40" className="text-white/20 stroke-current" strokeWidth="8" fill="none" />
                      <circle cx="50" cy="50" r="40" className="text-[#F97316] stroke-current" strokeWidth="8" fill="none"
                        strokeDasharray="251.2"
                        strokeDashoffset={251.2 - (251.2 * (gapData.readiness_score || 0)) / 100}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center flex-col">
                      <span className="text-white text-4xl font-bold">{gapData.readiness_score || 0}<span className="text-xl">%</span></span>
                    </div>
                  </div>
                  <h3 className="text-white text-xl font-bold mb-2">Role Readiness</h3>
                  <p className="text-white/80 text-sm mb-6">
                    {gapData.readiness_score >= 80
                      ? "You're highly ready for this role! Just a few gaps to fill."
                      : gapData.readiness_score >= 50
                      ? "You have a solid foundation, but addressing skill gaps will boost your chances."
                      : "Focus on learning the missing skills to improve your match significantly."}
                  </p>
                  <div className="flex flex-col gap-2">
                    <a href="#missing-skills" onClick={(e) => {
                      e.preventDefault();
                      document.getElementById("missing-skills")?.scrollIntoView({ behavior: "smooth", block: "start" });
                    }}>
                      <Button className="w-full bg-[#F97316] hover:bg-[#F97316]/90 text-white border-none">
                        <TrendingUp className="h-4 w-4 mr-1.5" /> Close the Gaps
                      </Button>
                    </a>
                    <Link to="/applicant/resume">
                      <Button variant="ghost" className="w-full text-white/80 hover:text-white hover:bg-white/10 border-none">
                        Improve my resume
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>

              {/* Target roles considered */}
              {selectedJobId === "all" && consideredJobs.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Your Target Roles</CardTitle>
                    <CardDescription>Top {consideredJobs.length} roles used for this analysis — click to drill in.</CardDescription>
                  </CardHeader>
                  <CardContent className="p-2">
                    <div className="space-y-1">
                      {consideredJobs.map((job: any) => (
                        <button
                          key={job.job_id}
                          onClick={() => switchJob(job.job_id)}
                          className="w-full flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg hover:bg-blue-50 transition-colors text-left"
                        >
                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-slate-900 truncate">{job.title}</p>
                            <p className="text-xs text-slate-500 truncate">
                              {job.company}{job.location ? ` • ${job.location}` : ""}
                            </p>
                          </div>
                          <Badge className="bg-blue-50 text-blue-700 border-blue-200 shrink-0">{job.matching_score}%</Badge>
                        </button>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* All resume skills */}
              {gapData.resume_skills?.length > 0 && (
                <Card>
                  <CardHeader className="pb-4">
                    <CardTitle className="text-lg">All Resume Skills</CardTitle>
                    <CardDescription>All {gapData.resume_skills.length} skills extracted from your resume.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {gapData.resume_skills.map((skill: string) => (
                        <Badge key={skill} variant="secondary" className="bg-slate-100 text-slate-600 capitalize">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
