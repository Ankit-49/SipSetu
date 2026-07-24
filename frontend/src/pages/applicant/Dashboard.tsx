import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Briefcase,
  FileText,
  UploadCloud,
  ChevronRight,
  Target,
  Zap,
  Sparkles,
  Loader2,
  Mail,
  X,
  Calendar,
  Clock,
  Video,
  CheckCircle2,
  XCircle
} from "lucide-react";
import { Link } from "react-router";
import { useState, useEffect } from "react";
import { NotificationBell } from "@/components/NotificationBell";
import api from "@/lib/api";
import { useAuth } from "@/app/context/AuthContext";

export default function ApplicantDashboardHome() {
  const { user } = useAuth();
  const date = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    const fetchDashboard = async () => {
      try {
        const response = await api.get(`/applicants/${user.id}/dashboard`);
        setData(response.data);
      } catch (err) {
        console.error("Failed to fetch applicant dashboard", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, [user]);

  const [sendingVerification, setSendingVerification] = useState(false);
  const [verificationSent, setVerificationSent] = useState(false);
  const [dismissVerificationBanner, setDismissVerificationBanner] = useState(false);

  const emailVerified = data?.email_verified;

  const handleResendVerification = async () => {
    setSendingVerification(true);
    setVerificationSent(false);
    try {
      await api.post("/auth/resend-verification");
      setVerificationSent(true);
    } catch (err) {
      console.error("Failed to resend verification", err);
    } finally {
      setSendingVerification(false);
    }
  };

  const userName = data?.name || user?.name || localStorage.getItem("user_name") || "Applicant";
  const firstName = userName.split(" ")[0];
  const recentJobs = data?.recent_jobs || [];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Welcome back, {firstName} 👋</h1>
          <p className="text-slate-500 mt-1">{date}</p>
        </div>
        <div className="flex items-center gap-4">
          <NotificationBell />
        </div>
      </div>

      {/* Email verification banner */}
      {emailVerified === false && !dismissVerificationBanner && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="h-10 w-10 rounded-full bg-amber-100 flex items-center justify-center shrink-0 mt-0.5">
              <Mail className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <h3 className="font-bold text-amber-900 text-sm">Verify your email address</h3>
              <p className="text-xs text-amber-700 mt-0.5">
                Check your inbox for a verification link. Some features may be limited until your email is verified.
              </p>
              {verificationSent && (
                <p className="text-xs text-green-600 font-medium mt-1">✓ Verification email sent! Check your inbox.</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button
              size="sm"
              variant="outline"
              className="border-amber-300 text-amber-800 hover:bg-amber-100 whitespace-nowrap"
              onClick={handleResendVerification}
              disabled={sendingVerification}
            >
              {sendingVerification ? (
                <><Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" /> Sending...</>
              ) : verificationSent ? (
                "Sent!"
              ) : (
                <><Mail className="h-3.5 w-3.5 mr-1.5" /> Resend Email</>
              )}
            </Button>
            <button
              onClick={() => setDismissVerificationBanner(true)}
              className="text-amber-400 hover:text-amber-600 p-1"
              aria-label="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

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
                {Number(data?.avg_match_score ?? 0).toFixed(2)}%
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

      {/* Upcoming Interviews */}
      {data?.upcoming_interviews?.length > 0 && (
        <Card>
          <CardHeader className="pb-3 border-b border-slate-100">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              <Calendar className="h-5 w-5 text-[#1E3A5F]" /> Upcoming Interviews
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100">
              {data.upcoming_interviews.slice(0, 5).map((iv: any) => {
                const dt = new Date(iv.scheduled_at);
                const dateStr = dt.toLocaleDateString("en-US", { weekday: 'short', month: 'short', day: 'numeric' });
                const timeStr = dt.toLocaleTimeString("en-US", { hour: '2-digit', minute: '2-digit' });
                return (
                  <div key={iv.interview_id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                    <div className="flex items-start gap-4">
                      <div className="h-10 w-10 rounded-full bg-[#1E3A5F]/5 flex items-center justify-center shrink-0">
                        <Calendar className="h-5 w-5 text-[#1E3A5F]" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-slate-900">{iv.job_title}</h4>
                        <p className="text-sm text-slate-500">
                          by <span className="font-medium text-slate-700">{iv.recruiter_company || iv.recruiter_name}</span>
                        </p>
                        <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                          <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {dateStr} at {timeStr}</span>
                          <span>{iv.duration_minutes} min</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {iv.status === "pending" && (
                        <Badge className="bg-amber-50 text-amber-700 border-amber-200">Awaiting your response</Badge>
                      )}
                      {iv.status === "confirmed" && (
                        <Badge className="bg-green-50 text-green-700 border-green-200">Confirmed</Badge>
                      )}
                      {iv.meeting_link && iv.status === "confirmed" && (
                        <a href={iv.meeting_link} target="_blank" rel="noopener noreferrer">
                          <Button size="sm" variant="outline" className="h-8 gap-1.5">
                            <Video className="h-3.5 w-3.5" /> Join
                          </Button>
                        </a>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

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
                      {Number(job.matching_score).toFixed(2)}% Match
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
