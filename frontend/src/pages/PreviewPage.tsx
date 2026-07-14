import { useEffect, useState } from "react";
import axios from "axios";
import { Link } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Briefcase, Users, FileText, Sparkles, ArrowRight, Loader2, Target } from "lucide-react";

const API = "http://localhost:5000/api";

export default function PreviewPage() {
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState<any>(null);

  useEffect(() => {
    const fetchPreview = async () => {
      try {
        const response = await axios.get(`${API}/public/preview`);
        setPreview(response.data);
      } catch (error) {
        console.error("Failed to load preview data", error);
      } finally {
        setLoading(false);
      }
    };

    fetchPreview();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="h-8 w-8 animate-spin text-[#F97316]" />
      </div>
    );
  }

  const stats = preview?.stats || {};
  const recentJobs = preview?.recent_jobs || [];
  const topCandidates = preview?.top_candidates || [];

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="bg-[#1E3A5F] text-white">
        <div className="max-w-7xl mx-auto px-6 py-16 md:py-20">
          <div className="max-w-3xl">
            <p className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-sm font-medium mb-6">
              <Sparkles className="h-4 w-4" /> Guest Preview
            </p>
            <h1 className="text-4xl md:text-6xl font-black tracking-tight leading-tight mb-4">
              See the platform before you sign in.
            </h1>
            <p className="text-lg md:text-xl text-slate-200 max-w-2xl">
              This preview is powered by live database records so non-users can explore the experience without creating an account.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 mt-8">
            <Link to="/login">
              <Button className="bg-[#F97316] hover:bg-[#F97316]/90 text-white gap-2">
                Sign In <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link to="/register">
              <Button variant="outline" className="border-white/20 text-white bg-white/5 hover:bg-white/10 hover:text-white">
                Create Account
              </Button>
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-12 space-y-8">
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="p-6 flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Jobs</p>
                <p className="text-3xl font-bold text-slate-900">{stats.jobs ?? 0}</p>
              </div>
              <Briefcase className="h-8 w-8 text-[#1E3A5F]" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6 flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Recruiters</p>
                <p className="text-3xl font-bold text-slate-900">{stats.recruiters ?? 0}</p>
              </div>
              <Users className="h-8 w-8 text-[#F97316]" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6 flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Applicants</p>
                <p className="text-3xl font-bold text-slate-900">{stats.applicants ?? 0}</p>
              </div>
              <Target className="h-8 w-8 text-[#1E3A5F]" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6 flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Resumes</p>
                <p className="text-3xl font-bold text-slate-900">{stats.resumes ?? 0}</p>
              </div>
              <FileText className="h-8 w-8 text-[#F97316]" />
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-8 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Recent Jobs</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {recentJobs.length === 0 ? (
                <p className="text-sm text-slate-500">No jobs are available yet.</p>
              ) : recentJobs.map((job: any) => (
                <div key={job.job_id} className="rounded-xl border border-slate-200 p-4 bg-slate-50/70">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="font-semibold text-slate-900">{job.title}</h3>
                      <p className="text-sm text-slate-500">
                        {job.recruiter_company || job.recruiter_name}
                        {job.location ? ` • ${job.location}` : ""}
                      </p>
                    </div>
                    <Badge className="bg-slate-100 text-slate-700 hover:bg-slate-100 border-none">
                      {job.matching_score ?? "Live"}
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {(job.skills || []).slice(0, 4).map((skill: string) => (
                      <Badge key={skill} variant="secondary" className="bg-white text-slate-700">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Top Ranked Candidates</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {topCandidates.length === 0 ? (
                <p className="text-sm text-slate-500">No ranked candidates are available yet.</p>
              ) : topCandidates.map((candidate: any) => (
                <div key={candidate.ranking_id} className="rounded-xl border border-slate-200 p-4 bg-slate-50/70">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="font-semibold text-slate-900">{candidate.applicant_name}</h3>
                      <p className="text-sm text-slate-500">{candidate.job_title}</p>
                    </div>
                    <Badge className="bg-[#F97316]/10 text-[#F97316] hover:bg-[#F97316]/10 border-none">
                      {candidate.matching_score.toFixed(2)}% Match
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {(candidate.resume_skills || []).slice(0, 4).map((skill: string) => (
                      <Badge key={skill} variant="secondary" className="bg-white text-slate-700">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
