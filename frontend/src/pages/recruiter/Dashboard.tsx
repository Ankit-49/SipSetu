import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Briefcase, Users, UserCheck, TrendingUp, ChevronRight, FileText } from "lucide-react";
import { Link } from "react-router";
import { useState, useEffect } from "react";
import axios from "axios";

const API = "http://localhost:5000/api";

export default function RecruiterDashboardHome() {
  const date = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setLoading(false);
      return;
    }

    const fetchDashboard = async () => {
      try {
        const response = await axios.get(`${API}/recruiters/${userId}/dashboard`);
        setData(response.data);
      } catch (err) {
        console.error("Failed to fetch recruiter dashboard", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  const topCandidates = data?.top_candidates || [];
  const activeJobs = data?.jobs || [];
  const userName = data?.name || localStorage.getItem("user_name") || "Recruiter";

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#F97316] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Good morning, {userName.split(' ')[0]} 👋</h1>
          <p className="text-slate-500 mt-1">{date}</p>
        </div>
        <Link to="/recruiter/post-job">
          <Button className="bg-[#F97316] hover:bg-[#F97316]/90 text-white shadow-lg shadow-orange-500/20">
            + Post New Job
          </Button>
        </Link>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Active Postings</p>
              <p className="text-3xl font-bold text-slate-900">{data?.active_postings ?? 0}</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-blue-50 flex items-center justify-center">
              <Briefcase className="h-6 w-6 text-[#1E3A5F]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Total Candidates</p>
              <p className="text-3xl font-bold text-slate-900">{data?.total_candidates ?? 0}</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center">
              <Users className="h-6 w-6 text-slate-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Top Match</p>
              <p className="text-3xl font-bold text-[#F97316]">{data?.top_match_score ?? 0}%</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-orange-50 flex items-center justify-center">
              <UserCheck className="h-6 w-6 text-[#F97316]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Recent Jobs</p>
              <div className="flex items-center gap-2">
                <p className="text-3xl font-bold text-slate-900">{activeJobs.length}</p>
                <TrendingUp className="h-4 w-4 text-green-500" />
              </div>
            </div>
            <div className="h-12 w-12 rounded-full bg-green-50 flex items-center justify-center">
              <Users className="h-6 w-6 text-green-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Top Candidates */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2 border-b border-slate-100">
            <CardTitle className="text-lg font-bold">Top Matches (AI Ranked)</CardTitle>
            <Link to="/recruiter/candidates">
              <Button variant="ghost" size="sm" className="text-slate-500 hover:text-[#1E3A5F]">
                View All <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100">
              {topCandidates.length === 0 ? (
                <div className="p-8 text-center text-slate-500">No ranked candidates yet. Upload resumes and create jobs to see matches.</div>
              ) : topCandidates.map((candidate: any) => (
                <div key={`${candidate.applicant_id}-${candidate.job_title}`} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors group">
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-full bg-[#1E3A5F] text-white flex items-center justify-center font-semibold text-sm">
                      {candidate.applicant_name.split(' ').map((n: string) => n[0]).join('')}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-slate-900">{candidate.applicant_name}</h3>
                        <Badge className="bg-green-100 text-green-700 hover:bg-green-100 border-none h-5 text-[10px]">
                          {candidate.matching_score}% Match
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-500">{candidate.job_title}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="hidden md:flex gap-1">
                      {candidate.resume_skills.map((s: string) => <Badge key={s} variant="outline" className="text-xs text-slate-500">{s}</Badge>)}
                    </div>
                    <Button variant="outline" size="sm" className="gap-2">
                      <FileText className="h-3.5 w-3.5" /> Resume
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Postings */}
        <Card>
          <CardHeader className="pb-2 border-b border-slate-100">
            <CardTitle className="text-lg font-bold">Active Job Postings</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100">
              {activeJobs.length === 0 ? (
                <div className="p-8 text-center text-slate-500">No active job postings yet.</div>
              ) : activeJobs.map((post: any) => (
                <div key={post.job_id} className="p-4 hover:bg-slate-50 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-semibold text-slate-900">{post.title}</h4>
                    <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50 border-blue-200">Active</Badge>
                  </div>
                  <div className="flex justify-between items-center text-sm text-slate-500">
                    <span className="flex items-center gap-1.5"><Users className="h-3.5 w-3.5" /> {data?.total_candidates ?? 0} Candidates</span>
                    <span>{post.created_at ? new Date(post.created_at).toLocaleDateString() : "Recent"}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="p-3 bg-slate-50 border-t border-slate-100 text-center rounded-b-xl">
              <Link to="/recruiter/dashboard" className="text-sm font-medium text-[#1E3A5F] hover:underline">
                View all postings
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
