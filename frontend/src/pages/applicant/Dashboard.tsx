import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Target, FileText, Briefcase, ChevronRight, Loader2, UploadCloud, Zap, Sparkles } from "lucide-react";
import { Link } from "react-router";
import { useState, useEffect } from "react";
import axios from "axios";

const API = "http://localhost:5000/api";

export default function ApplicantDashboardHome() {
  const date = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const userId = localStorage.getItem("user_id");
    if (!userId) { setLoading(false); return; }

    const fetchDashboard = async () => {
      try {
        const res = await axios.get(`${API}/applicants/${userId}/dashboard`);
        setData(res.data);
      } catch (err) {
        console.error("Failed to fetch dashboard data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  const userName = data?.name || localStorage.getItem("user_name") || "there";
  const firstName = userName.split(" ")[0];
  const recentJobs = data?.recent_jobs || [];

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
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Welcome back, {firstName} 👋</h1>
        <p className="text-slate-500 mt-1">{date}</p>
      </div>

      {/* No resume prompt */}
      {!data?.has_resume && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
              <UploadCloud className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-bold text-blue-900">Upload your resume to get started</h3>
              <p className="text-sm text-blue-700">Our AI will extract your skills and match you with top jobs.</p>
            </div>
          </div>
          <Link to="/applicant/resume">
            <Button className="bg-blue-600 hover:bg-blue-700 text-white gap-2 whitespace-nowrap">
              <UploadCloud className="h-4 w-4" /> Upload Resume
            </Button>
          </Link>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Avg. Match Score</p>
              <p className="text-3xl font-bold text-[#F97316]">
                {data?.avg_match_score ?? 0}%
              </p>
            </div>
            <div className="h-12 w-12 rounded-full bg-orange-50 flex items-center justify-center">
              <Target className="h-6 w-6 text-[#F97316]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex flex-col justify-center space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-500">Resume Strength</p>
              <FileText className="h-5 w-5 text-blue-500" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-bold text-slate-900">{data?.resume_strength ?? 0}/100</span>
              </div>
              <Progress value={data?.resume_strength ?? 0} className="h-2 bg-slate-100" indicatorClassName="bg-[#1E3A5F]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Skills Detected</p>
              <p className="text-3xl font-bold text-slate-900">{data?.skill_count ?? 0}</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center">
              <Zap className="h-6 w-6 text-slate-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Top Matches */}
        <Card className="lg:col-span-2 flex flex-col">
          <CardHeader className="flex flex-row items-center justify-between pb-2 border-b border-slate-100">
            <CardTitle className="text-lg font-bold">Top Job Matches</CardTitle>
            <Link to="/applicant/matches">
              <Button variant="ghost" size="sm" className="text-slate-500 hover:text-[#1E3A5F]">
                View All <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0 flex-1">
            <div className="divide-y divide-slate-100">
              {!data?.top_jobs?.length ? (
                <div className="p-8 text-center text-slate-500">
                  {data?.has_resume
                    ? "No job matches yet. Jobs will appear here once recruiters post openings."
                    : "Upload a resume to see job matches."}
                </div>
              ) : data.top_jobs.map((job: any) => (
                <div key={job.job_id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                  <div className="space-y-1">
                    <h3 className="font-semibold text-slate-900">{job.title}</h3>
                    <p className="text-sm text-slate-500">
                      {job.recruiter_company || job.recruiter_name}
                      {job.location ? ` • ${job.location}` : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge className={job.matching_score >= 85 ? 'bg-green-100 text-green-700 hover:bg-green-100' : 'bg-orange-100 text-orange-700 hover:bg-orange-100'}>
                      {job.matching_score}% Match
                    </Badge>
                    <Link to="/applicant/matches">
                      <Button variant="outline" size="sm">View</Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Right Column */}
        <div className="space-y-8">
          <Card>
            <CardHeader className="pb-2 border-b border-slate-100">
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-[#F97316]" /> Latest Openings
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-slate-100">
                {!recentJobs.length ? (
                  <div className="p-6 text-sm text-slate-500">No jobs are available yet.</div>
                ) : recentJobs.slice(0, 4).map((job: any) => (
                  <div key={job.job_id} className="p-4 hover:bg-slate-50 transition-colors">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-slate-900">{job.title}</h3>
                        <p className="text-xs text-slate-500">
                          {job.recruiter_company || job.recruiter_name}
                          {job.location ? ` • ${job.location}` : ""}
                        </p>
                      </div>
                      <Badge className="bg-slate-100 text-slate-700 hover:bg-slate-100 border-none">New</Badge>
                    </div>
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {(job.skills || []).slice(0, 3).map((skill: string) => (
                        <Badge key={skill} variant="secondary" className="bg-white text-slate-700 border border-slate-200">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Skill Gap */}
          <Card>
            <CardHeader className="pb-2 border-b border-slate-100">
              <CardTitle className="text-lg font-bold">Critical Skill Gaps</CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-6 space-y-6">
              <p className="text-sm text-slate-600">Top missing skills for roles you're matching with:</p>
              <div className="flex flex-wrap gap-2">
                {data?.missing_skills?.length ? data.missing_skills.map((skill: string) => (
                  <Badge key={skill} variant="secondary" className="bg-slate-100 text-slate-700 hover:bg-slate-200">
                    {skill}
                  </Badge>
                )) : (
                  <p className="text-sm text-slate-400">{data?.has_resume ? "No skill gaps found!" : "Upload a resume to see gaps."}</p>
                )}
              </div>
              <Link to="/applicant/skill-gap">
                <Button variant="outline" className="w-full text-[#1E3A5F] border-[#1E3A5F]/20 hover:bg-blue-50">
                  View Full Analysis
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Resume Status */}
          <Card>
            <CardHeader className="pb-2 border-b border-slate-100">
              <CardTitle className="text-lg font-bold">Resume Status</CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-6">
              {data?.has_resume ? (
                <div className="space-y-4">
                  <div className="flex gap-3 items-start">
                    <div className="h-8 w-8 rounded-full bg-orange-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <FileText className="h-4 w-4 text-orange-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900">
                        {data.resume_filename || "Resume uploaded"}
                      </p>
                      <p className="text-xs text-slate-500">
                        {data.resume_uploaded_at
                          ? new Date(data.resume_uploaded_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                          : "Recently uploaded"}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-3 items-start">
                    <div className="h-8 w-8 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Briefcase className="h-4 w-4 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900">{data.skill_count} skills extracted</p>
                      <p className="text-xs text-slate-500">Used for job matching</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-sm text-slate-500 mb-3">No resume uploaded yet</p>
                  <Link to="/applicant/resume">
                    <Button size="sm" className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 text-white">Upload Now</Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
