import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ExternalLink, Target, CheckCircle2, ChevronDown, ChevronUp, Loader2, UploadCloud } from "lucide-react";
import { useState, useEffect } from "react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Link } from "react-router";
import axios from "axios";

const API = "http://localhost:5000/api";

const LEARNING_RESOURCES: Record<string, string[]> = {
  "typescript": ["TypeScript Handbook (official)", "Udemy: TypeScript Bootcamp", "Frontend Masters: TypeScript"],
  "node.js": ["Node.js official docs", "The Odin Project: Node.js", "Udemy: Node.js Complete Guide"],
  "python": ["Python.org tutorial", "Real Python", "CS50 Python (Harvard)"],
  "react": ["React official docs", "Scrimba React Course", "Frontend Masters: React"],
  "docker": ["Docker official docs", "TechWorld with Nana (YouTube)", "Docker & Kubernetes Udemy"],
  "aws": ["AWS Skill Builder (free)", "A Cloud Guru", "AWS Certified Solutions Architect"],
  "postgresql": ["PostgreSQL official docs", "pgExercises", "Udemy: SQL Bootcamp"],
  "machine learning": ["fast.ai", "Coursera ML Specialization", "Kaggle Learn"],
  "system design": ["Grokking System Design", "YouTube: System Design Primer", "ByteByteGo newsletter"],
  "kubernetes": ["Kubernetes official docs", "TechWorld with Nana (YouTube)", "CKAD certification prep"],
};

function getResources(skill: string): string[] {
  const lower = skill.toLowerCase();
  for (const key of Object.keys(LEARNING_RESOURCES)) {
    if (lower.includes(key) || key.includes(lower)) return LEARNING_RESOURCES[key];
  }
  return [`Search "${skill} tutorial" on YouTube`, `"${skill}" on Coursera`, `"${skill}" on Udemy`];
}

export default function ApplicantSkillGap() {
  const [loading, setLoading] = useState(true);
  const [jobs, setJobs] = useState<any[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>("all");
  const [gapData, setGapData] = useState<any>(null);
  const [gapLoading, setGapLoading] = useState(false);
  const [hasResume, setHasResume] = useState(true);
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({});

  const userId = localStorage.getItem("user_id");

  // Fetch all jobs for dropdown
  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const res = await axios.get(`${API}/jobs?per_page=50`);
        setJobs(res.data.jobs || []);
      } catch (err) {
        console.error("Failed to load jobs", err);
      } finally {
        setLoading(false);
      }
    };
    fetchJobs();
  }, []);

  // Fetch skill gap data
  useEffect(() => {
    if (!userId) return;
    const fetchGap = async () => {
      setGapLoading(true);
      try {
        const url = selectedJobId === "all"
          ? `${API}/applicants/${userId}/skill-gap`
          : `${API}/applicants/${userId}/skill-gap?job_id=${selectedJobId}`;
        const res = await axios.get(url);
        setGapData(res.data);
        // Auto-open first item
        if (res.data.missing_skills?.length > 0) {
          setOpenItems({ [res.data.missing_skills[0].skill]: true });
        }
        setHasResume(true);
      } catch (err: any) {
        if (err.response?.status === 404) setHasResume(false);
        setGapData(null);
      } finally {
        setGapLoading(false);
      }
    };
    fetchGap();
  }, [selectedJobId, userId]);

  const toggleItem = (skill: string) => {
    setOpenItems(prev => ({ ...prev, [skill]: !prev[skill] }));
  };

  const selectedJob = jobs.find(j => j.job_id === selectedJobId);
  const jobLabel = selectedJobId === "all"
    ? "All Matched Jobs"
    : selectedJob ? `${selectedJob.title} @ ${selectedJob.recruiter_company || selectedJob.recruiter_name}` : "";

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#F97316]" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Skill Gap Analysis</h1>
          <p className="text-slate-500 mt-1">See exactly what's standing between you and your target roles.</p>
        </div>
        <div className="w-full md:w-80">
          <p className="text-sm font-medium text-slate-700 mb-2">Analyze skill gap for:</p>
          <Select value={selectedJobId} onValueChange={setSelectedJobId}>
            <SelectTrigger className="bg-white border-slate-200">
              <SelectValue placeholder="Select a job" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Matched Jobs</SelectItem>
              {jobs.map(job => (
                <SelectItem key={job.job_id} value={job.job_id}>
                  {job.title} @ {job.recruiter_company || job.recruiter_name}
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

      {!gapLoading && gapData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Missing Skills */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="border-t-4 border-t-[#F97316]">
              <CardHeader>
                <CardTitle className="text-xl">Missing Skills to Learn</CardTitle>
                <CardDescription>
                  {gapData.missing_skills?.length > 0
                    ? `${gapData.missing_skills.length} skill${gapData.missing_skills.length > 1 ? "s" : ""} required for "${gapData.job_title}" that aren't in your profile.`
                    : `Great job! You have all required skills for "${gapData.job_title}".`
                  }
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {gapData.missing_skills?.length === 0 ? (
                  <div className="p-8 text-center">
                    <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-3" />
                    <p className="font-semibold text-green-700">You're a perfect match!</p>
                    <p className="text-sm text-slate-500 mt-1">No skill gaps detected for this role.</p>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {gapData.missing_skills.map((item: any) => (
                      <Collapsible
                        key={item.skill}
                        open={openItems[item.skill]}
                        onOpenChange={() => toggleItem(item.skill)}
                        className="p-4 bg-white"
                      >
                        <CollapsibleTrigger className="w-full flex items-center justify-between group">
                          <div className="flex items-center gap-3">
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
                              {item.priority} Priority
                            </Badge>
                          </div>
                          <Button variant="ghost" size="sm" className="text-slate-400 group-hover:text-slate-900">
                            {openItems[item.skill] ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                          </Button>
                        </CollapsibleTrigger>

                        <CollapsibleContent className="pt-4 pl-14">
                          <p className="text-sm font-medium text-slate-900 mb-3 uppercase tracking-wider">Recommended Resources</p>
                          <ul className="space-y-2">
                            {getResources(item.skill).map((res, i) => (
                              <li key={i}>
                                <a href="#" className="inline-flex items-center text-sm text-[#1E3A5F] hover:underline gap-1.5 p-1.5 -ml-1.5 rounded hover:bg-blue-50 transition-colors">
                                  <ExternalLink className="h-3.5 w-3.5 text-slate-400" />
                                  {res}
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
          </div>

          {/* Right Column: Readiness & Strengths */}
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
                    <span className="text-4xl font-bold">{gapData.readiness_score || 0}<span className="text-xl">%</span></span>
                  </div>
                </div>
                <h3 className="text-xl font-bold mb-2">Role Readiness</h3>
                <p className="text-blue-100 text-sm mb-6">
                  {gapData.readiness_score >= 80
                    ? "You're highly ready for this role! Just a few gaps to fill."
                    : gapData.readiness_score >= 50
                    ? "You have a solid foundation, but addressing skill gaps will boost your chances."
                    : "Focus on learning the missing skills to improve your match significantly."}
                </p>
                <Button className="w-full bg-[#F97316] hover:bg-[#F97316]/90 text-white border-none">
                  Boost Your Profile
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-4">
                <CardTitle className="text-lg">Your Strengths</CardTitle>
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
                      {selectedJobId === "all" ? "Select a job to see matching skills." : "No matching skills found for this role."}
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

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
      )}

      {!gapLoading && !gapData && hasResume && (
        <div className="text-center py-16 text-slate-400">
          <Target className="h-12 w-12 mx-auto mb-4 text-slate-200" />
          <p className="font-medium">Select a job above to see your skill gap analysis.</p>
        </div>
      )}
    </div>
  );
}
