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
  CheckCircle2,
  XCircle,
  Eye,
  Ban,
  ChevronDown,
  Info,
  TrendingUp,
  BookOpen,
  Award,
  Search,
  BarChart3,
} from "lucide-react";
import { Link } from "react-router";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { NotificationBell } from "@/components/NotificationBell";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import api from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { useAuth } from "@/app/context/AuthContext";
import { JoinInterviewButton } from "@/components/JoinInterviewButton";

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

const strengthRows = [
  { key: "content", label: "Content depth", hint: "How much detail your resume contains", max: 30 },
  { key: "skills", label: "Skill coverage", hint: "Number of skills extracted from your resume", max: 25 },
  { key: "match", label: "Match quality", hint: "Average score against your best-matched roles", max: 30 },
  { key: "gaps", label: "Gap closure", hint: "Fewer missing skills for target roles = higher score", max: 15 },
];

export default function ApplicantDashboardHome() {
  const { user } = useAuth();
  const date = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [showStrengthBreakdown, setShowStrengthBreakdown] = useState(false);

  const fetchDashboard = async () => {
    if (!user) return;
    try {
      const response = await api.get(`/applicants/${user.id}/dashboard`);
      setData(response.data);
    } catch (err) {
      console.error("Failed to fetch applicant dashboard", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchDashboard();
  }, [user]);

  const [sendingVerification, setSendingVerification] = useState(false);
  const [verificationSent, setVerificationSent] = useState(false);
  const [dismissedBanner, setDismissedBanner] = useState(false);

  const [respondingId, setRespondingId] = useState<string | null>(null);
  const [selectedInterview, setSelectedInterview] = useState<any>(null);
  const [declineTarget, setDeclineTarget] = useState<any>(null);
  const [declining, setDeclining] = useState(false);

  const respondToInterview = async (iv: any, action: "confirm" | "decline") => {
    setRespondingId(iv.interview_id);
    if (action === "decline") setDeclining(true);
    try {
      await api.patch(`/interviews/${iv.interview_id}/respond`, { action });
      toast({
        title: action === "confirm" ? "Interview confirmed! 🎉" : "Interview declined",
        description:
          action === "confirm"
            ? `You're all set for ${iv.job_title}. The recruiter has been notified.`
            : `You declined the interview for ${iv.job_title}. The recruiter has been notified.`,
      });
      setDeclineTarget(null);
      setSelectedInterview(null);
      fetchDashboard();
    } catch (err: any) {
      const msg = err?.response?.data?.error || "Failed to update interview";
      toast({ title: "Error", description: msg, variant: "destructive" });
    } finally {
      setRespondingId(null);
      setDeclining(false);
    }
  };

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

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#F97316] border-t-transparent" />
      </div>
    );
  }

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-8">
      {/* Header */}
      <motion.div variants={fadeUp} className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Welcome back, {firstName} 👋</h1>
          <p className="text-slate-500 mt-1 flex items-center gap-2">
            <Calendar className="h-4 w-4" /> {date}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <NotificationBell />
        </div>
      </motion.div>

      {/* Email verification banner */}
      {emailVerified === false && !dismissedBanner && (
        <motion.div variants={fadeUp} className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="h-10 w-10 rounded-full bg-amber-100 flex items-center justify-center shrink-0 mt-0.5">
              <Mail className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <h3 className="font-bold text-amber-900 text-sm">Verify your email address</h3>
              <p className="text-xs text-amber-700 mt-0.5">
                Enter the 6-digit verification code we emailed you to unlock all features.
              </p>
              {verificationSent && (
                <p className="text-xs text-green-600 font-medium mt-1">✓ A new verification code has been sent! Check your inbox.</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link to={`/verify-email?email=${encodeURIComponent(user?.email || data?.email || "")}`}>
              <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white whitespace-nowrap gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5" /> Enter Code
              </Button>
            </Link>
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
                <><Mail className="h-3.5 w-3.5 mr-1.5" /> Resend Code</>
              )}
            </Button>
            <button
              onClick={() => setDismissedBanner(true)}
              className="text-amber-400 hover:text-amber-600 p-1"
              aria-label="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </motion.div>
      )}

      {/* No resume prompt */}
      {!data?.has_resume && (
        <motion.div variants={fadeUp} className="group relative overflow-hidden bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200/60 rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
          <div className="flex items-center gap-4">
            <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <UploadCloud className="h-7 w-7 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-blue-900 text-lg">Upload your resume to get started</h3>
              <p className="text-sm text-blue-700">Our AI will extract your skills and match you with top jobs.</p>
            </div>
          </div>
          <Link to="/applicant/resume">
            <Button className="bg-blue-600 hover:bg-blue-700 text-white gap-2 whitespace-nowrap shadow-lg shadow-blue-600/20">
              <UploadCloud className="h-4 w-4" /> Upload Resume
            </Button>
          </Link>
        </motion.div>
      )}

      {/* Stats Row */}
      <motion.div variants={fadeUp} className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Avg Match Score */}
        <Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5">
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Avg. Match Score</p>
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <Target className="h-5 w-5 text-[#F97316]" />
              </div>
            </div>
            <p className="text-3xl font-bold bg-gradient-to-r from-orange-500 to-orange-600 bg-clip-text text-transparent">
              {Number(data?.avg_match_score ?? 0).toFixed(2)}%
            </p>
            <div className="mt-2 flex items-center gap-1 text-xs text-slate-400">
              <TrendingUp className="h-3 w-3" /> Top match score
            </div>
          </CardContent>
        </Card>

        {/* Resume Strength */}
        <Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5">
          <CardContent className="p-6 space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Resume Strength</p>
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <Award className="h-5 w-5 text-[#1E3A5F]" />
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-bold text-2xl text-slate-900">{data?.resume_strength ?? 0}<span className="text-base font-normal text-slate-400">/100</span></span>
                <button
                  onClick={() => setShowStrengthBreakdown(v => !v)}
                  className="inline-flex items-center gap-1 text-xs font-medium text-[#1E3A5F]/70 hover:text-[#F97316] transition-colors cursor-pointer"
                >
                  <Info className="h-3.5 w-3.5" />
                  {showStrengthBreakdown ? "Hide" : "Why?"}
                  <ChevronDown className={`h-3 w-3 transition-transform duration-200 ${showStrengthBreakdown ? "rotate-180" : ""}`} />
                </button>
              </div>
              <Progress value={data?.resume_strength ?? 0} className="h-2 bg-slate-100 rounded-full" indicatorClassName="bg-gradient-to-r from-[#1E3A5F] to-[#2a4f7a]" />
            </div>

            {showStrengthBreakdown && (
              <div className="pt-3 border-t border-slate-100 space-y-3 animate-in fade-in slide-in-from-top-1 duration-200">
                {strengthRows.map((row) => {
                  const val = Number(data?.resume_strength_breakdown?.[row.key] ?? 0);
                  const pct = row.max > 0 ? Math.min(100, (val / row.max) * 100) : 0;
                  return (
                    <div key={row.key} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-medium text-slate-700">{row.label}</span>
                        <span className="font-semibold text-slate-500">{val}/{row.max}</span>
                      </div>
                      <Progress value={pct} className="h-1.5 bg-slate-100 rounded-full" indicatorClassName="bg-[#1E3A5F]" />
                      <p className="text-[11px] text-slate-400 leading-snug">{row.hint}</p>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Skills Detected */}
        <Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5">
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Skills Detected</p>
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <Zap className="h-5 w-5 text-slate-600" />
              </div>
            </div>
            <p className="text-3xl font-bold text-slate-900">{data?.skill_count ?? 0}</p>
            <div className="mt-2 flex items-center gap-1 text-xs text-slate-400">
              <BarChart3 className="h-3 w-3" /> Skills extracted from resume
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Upcoming Interviews */}
      {data?.upcoming_interviews?.length > 0 && (
        <motion.div variants={fadeUp}>
          <Card className="overflow-hidden border-0 shadow-md">
            <CardHeader className="bg-gradient-to-r from-[#1E3A5F] to-[#162d4a] text-white pb-3">
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <Calendar className="h-5 w-5 text-orange-400" /> Upcoming Interviews
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-slate-100">
                {data.upcoming_interviews.slice(0, 5).map((iv: any) => {
                  const dt = new Date(iv.scheduled_at);
                  const dateStr = dt.toLocaleDateString("en-US", { weekday: 'short', month: 'short', day: 'numeric' });
                  const timeStr = dt.toLocaleTimeString("en-US", { hour: '2-digit', minute: '2-digit' });
                  const isResponding = respondingId === iv.interview_id;
                  return (
                    <div key={iv.interview_id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors gap-3 flex-wrap">
                      <div className="flex items-start gap-4 min-w-0">
                        <div className="h-10 w-10 rounded-full bg-[#1E3A5F]/5 flex items-center justify-center shrink-0">
                          <Calendar className="h-5 w-5 text-[#1E3A5F]" />
                        </div>
                        <div className="min-w-0">
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
                      <div className="flex items-center gap-2 flex-wrap">
                        {iv.status === "pending" && (
                          <Badge className="bg-amber-50 text-amber-700 border-amber-200">Awaiting your response</Badge>
                        )}
                        {iv.status === "confirmed" && (
                          <Badge className="bg-green-50 text-green-700 border-green-200">Confirmed</Badge>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8 gap-1.5"
                          onClick={() => setSelectedInterview(iv)}
                        >
                          <Eye className="h-3.5 w-3.5" /> Details
                        </Button>
                        {iv.status === "pending" && (
                          <>
                            <Button
                              size="sm"
                              className="h-8 gap-1.5 bg-green-600 hover:bg-green-700 text-white"
                              onClick={() => respondToInterview(iv, "confirm")}
                              disabled={isResponding}
                            >
                              {isResponding ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />} Accept
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-8 gap-1.5 text-red-600 border-red-200 hover:bg-red-50"
                              onClick={() => setDeclineTarget(iv)}
                              disabled={isResponding}
                            >
                              <XCircle className="h-3.5 w-3.5" /> Decline
                            </Button>
                          </>
                        )}
                        {iv.meeting_link && iv.status === "confirmed" && (
                          <JoinInterviewButton
                            scheduledAt={iv.scheduled_at}
                            durationMinutes={iv.duration_minutes}
                            meetingLink={iv.meeting_link}
                          />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Main Content Grid */}
      <motion.div variants={fadeUp} className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Top Matches */}
        <Card className="lg:col-span-2 flex flex-col hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-slate-100">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-[#1E3A5F] to-[#2a4f7a] flex items-center justify-center">
                <Briefcase className="h-4 w-4 text-white" />
              </div>
              Top Job Matches
            </CardTitle>
            <Link to="/applicant/matches">
              <Button variant="ghost" size="sm" className="text-slate-500 hover:text-[#1E3A5F] gap-1">
                View All <ChevronRight className="h-4 w-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0 flex-1">
            <div className="divide-y divide-slate-100">
              {!data?.top_jobs?.length ? (
                <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
                  <div className="h-16 w-16 rounded-2xl bg-slate-50 flex items-center justify-center mb-4">
                    <Search className="h-8 w-8 text-slate-300" />
                  </div>
                  <h3 className="text-base font-semibold text-slate-700 mb-1">No matches yet</h3>
                  <p className="text-sm text-slate-400 max-w-sm">
                    {data?.has_resume
                      ? "Jobs will appear here once recruiters post openings that match your skills."
                      : "Upload a resume to see personalized job matches."}
                  </p>
                </div>
              ) : data.top_jobs.map((job: any) => (
                <div key={job.job_id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors group">
                  <div className="space-y-1">
                    <h3 className="font-semibold text-slate-900 group-hover:text-[#1E3A5F] transition-colors">{job.title}</h3>
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
        <div className="space-y-6">
          {/* Latest Openings */}
          <Card className="border-0 shadow-md">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-orange-400 to-orange-500 flex items-center justify-center">
                  <Sparkles className="h-4 w-4 text-white" />
                </div>
                Latest Openings
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-slate-100">
                {!recentJobs.length ? (
                  <div className="flex flex-col items-center justify-center py-10 px-6 text-center">
                    <div className="h-12 w-12 rounded-2xl bg-slate-50 flex items-center justify-center mb-3">
                      <Briefcase className="h-6 w-6 text-slate-300" />
                    </div>
                    <p className="text-sm text-slate-400">No jobs available yet.</p>
                  </div>
                ) : recentJobs.slice(0, 4).map((job: any) => (
                  <div key={job.job_id} className="p-4 hover:bg-slate-50 transition-colors group">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-slate-900 group-hover:text-[#1E3A5F] transition-colors">{job.title}</h3>
                        <p className="text-xs text-slate-500">
                          {job.recruiter_company || job.recruiter_name}
                          {job.location ? ` • ${job.location}` : ""}
                        </p>
                      </div>
                      <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50 border-emerald-200 shrink-0">New</Badge>
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
          <Card className="border-0 shadow-md">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-slate-600 to-slate-800 flex items-center justify-center">
                  <BookOpen className="h-4 w-4 text-white" />
                </div>
                Skill Gaps
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-6 space-y-6">
              <p className="text-sm text-slate-600">Top missing skills for roles you're matching with:</p>
              <div className="flex flex-wrap gap-2">
                {data?.missing_skills?.length ? data.missing_skills.map((skill: string) => (
                  <Badge key={skill} variant="secondary" className="bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200">
                    {skill}
                  </Badge>
                )) : (
                  <p className="text-sm text-slate-400">{data?.has_resume ? "No skill gaps found! 🎉" : "Upload a resume to see gaps."}</p>
                )}
              </div>
              <Link to="/applicant/skill-gap">
                <Button variant="outline" className="w-full text-[#1E3A5F] border-[#1E3A5F]/20 hover:bg-blue-50 hover:border-[#1E3A5F]/40 transition-all">
                  View Full Analysis <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Resume Status */}
          <Card className="border-0 shadow-md">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
                  <FileText className="h-4 w-4 text-white" />
                </div>
                Resume Status
              </CardTitle>
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
                  <Link to="/applicant/resume">
                    <Button variant="outline" size="sm" className="w-full text-[#1E3A5F] border-[#1E3A5F]/20 hover:bg-blue-50">
                      Update Resume
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="text-center py-6">
                  <div className="h-12 w-12 rounded-2xl bg-slate-50 flex items-center justify-center mx-auto mb-3">
                    <FileText className="h-6 w-6 text-slate-300" />
                  </div>
                  <p className="text-sm text-slate-500 mb-4">No resume uploaded yet</p>
                  <Link to="/applicant/resume">
                    <Button size="sm" className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 text-white gap-2">
                      <UploadCloud className="h-4 w-4" /> Upload Now
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </motion.div>

      {/* Interview Details Dialog */}
      <Dialog open={!!selectedInterview} onOpenChange={() => setSelectedInterview(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-slate-900">Interview Details</DialogTitle>
            <DialogDescription>
              {selectedInterview?.job_title} with {selectedInterview?.recruiter_company || selectedInterview?.recruiter_name}
            </DialogDescription>
          </DialogHeader>
          {selectedInterview && (() => {
            const dt = new Date(selectedInterview.scheduled_at);
            return (
              <div className="space-y-4 py-2">
                <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="h-10 w-10 rounded-full bg-[#1E3A5F]/10 flex items-center justify-center shrink-0">
                    <Calendar className="h-5 w-5 text-[#1E3A5F]" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">
                      {dt.toLocaleDateString("en-US", { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
                    </p>
                    <p className="text-sm text-slate-500">
                      {dt.toLocaleTimeString("en-US", { hour: '2-digit', minute: '2-digit' })} • {selectedInterview.duration_minutes} minutes
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="p-3 rounded-xl border border-slate-100">
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wide">Recruiter</p>
                    <p className="font-semibold text-slate-800 mt-0.5">{selectedInterview.recruiter_name}</p>
                    <p className="text-slate-500">{selectedInterview.recruiter_company || "—"}</p>
                  </div>
                  <div className="p-3 rounded-xl border border-slate-100">
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wide">Status</p>
                    {selectedInterview.status === "pending" && (
                      <p className="font-semibold text-amber-600 mt-0.5">Awaiting your response</p>
                    )}
                    {selectedInterview.status === "confirmed" && (
                      <p className="font-semibold text-green-600 mt-0.5">Confirmed</p>
                    )}
                    {selectedInterview.status === "declined" && (
                      <p className="font-semibold text-red-500 mt-0.5">Declined</p>
                    )}
                    {selectedInterview.status === "cancelled" && (
                      <p className="font-semibold text-slate-500 mt-0.5">Cancelled</p>
                    )}
                  </div>
                </div>

                {selectedInterview.notes && (
                  <div className="p-3 rounded-xl border border-slate-100">
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Notes from recruiter</p>
                    <p className="text-sm text-slate-700 whitespace-pre-wrap">{selectedInterview.notes}</p>
                  </div>
                )}

                {selectedInterview.meeting_link && (
                  <JoinInterviewButton
                    scheduledAt={selectedInterview.scheduled_at}
                    durationMinutes={selectedInterview.duration_minutes}
                    meetingLink={selectedInterview.meeting_link}
                    label="Join Meeting Link"
                    variant="outline"
                    className="w-full"
                  />
                )}

                {selectedInterview.status === "pending" && (
                  <div className="flex gap-3 pt-2 border-t border-slate-100">
                    <Button
                      className="flex-1 gap-2 bg-green-600 hover:bg-green-700 text-white"
                      onClick={() => respondToInterview(selectedInterview, "confirm")}
                      disabled={respondingId === selectedInterview.interview_id}
                    >
                      {respondingId === selectedInterview.interview_id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <CheckCircle2 className="h-4 w-4" />
                      )} Accept Interview
                    </Button>
                    <Button
                      variant="outline"
                      className="flex-1 gap-2 text-red-600 border-red-200 hover:bg-red-50"
                      onClick={() => {
                        const t = selectedInterview;
                        setSelectedInterview(null);
                        setDeclineTarget(t);
                      }}
                      disabled={respondingId === selectedInterview.interview_id}
                    >
                      <XCircle className="h-4 w-4" /> Decline
                    </Button>
                  </div>
                )}
              </div>
            );
          })()}
        </DialogContent>
      </Dialog>

      {/* Decline Confirmation */}
      <AlertDialog open={!!declineTarget} onOpenChange={() => setDeclineTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="text-lg font-bold text-slate-900">Decline Interview</AlertDialogTitle>
            <AlertDialogDescription className="text-slate-600">
              Are you sure you want to decline the interview for{" "}
              <span className="font-semibold">{declineTarget?.job_title}</span>? The recruiter will be notified
              that you are not available.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={declining}>Keep Interview</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => declineTarget && respondToInterview(declineTarget, "decline")}
              disabled={declining}
              className="bg-red-600 hover:bg-red-700 text-white focus:ring-red-600"
            >
              {declining ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Declining...</>
              ) : (
                <><Ban className="h-4 w-4 mr-2" /> Decline Interview</>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </motion.div>
  );
}