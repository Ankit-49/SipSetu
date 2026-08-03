import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Briefcase, Users, UserCheck, TrendingUp, ChevronRight, FileText, Plus, ExternalLink, Calendar, Clock, Loader2, Mail, X, CheckCircle2, Ban, BarChart3, Search, Sparkles } from "lucide-react";
import { Link } from "react-router";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { NotificationBell } from "@/components/NotificationBell";
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
    transition: { staggerChildren: 0.07 },
  },
};

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export default function RecruiterDashboardHome() {
  const { user } = useAuth();
  const date = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchDashboard();
  }, [user]);

  const fetchDashboard = async () => {
    if (!user) return;
    try {
      const response = await api.get(`/recruiters/${user.id}/dashboard`);
      setData(response.data);
    } catch (err) {
      console.error("Failed to fetch recruiter dashboard", err);
    } finally {
      setLoading(false);
    }
  };

  const topCandidates = data?.top_candidates || [];
  const activeJobs = data?.jobs || [];

  const [sendingVerification, setSendingVerification] = useState(false);
  const [verificationSent, setVerificationSent] = useState(false);
  const [dismissedBanner, setDismissedBanner] = useState(false);

  const [cancelTarget, setCancelTarget] = useState<any>(null);
  const [cancelling, setCancelling] = useState(false);

  const handleCancelInterview = async () => {
    if (!cancelTarget) return;
    setCancelling(true);
    try {
      await api.patch(`/interviews/${cancelTarget.interview_id}/cancel`);
      toast({
        title: "Interview cancelled",
        description: `The interview for ${cancelTarget.job_title} has been cancelled and the candidate has been notified.`,
      });
      setCancelTarget(null);
      fetchDashboard();
    } catch (err: any) {
      const msg = err?.response?.data?.error || "Failed to cancel interview";
      toast({ title: "Error", description: msg, variant: "destructive" });
    } finally {
      setCancelling(false);
    }
  };

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

  const userName = data?.name || user?.name || localStorage.getItem("user_name") || "Recruiter";

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
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Good morning, {userName.split(' ')[0]} 👋</h1>
          <p className="text-slate-500 mt-1 flex items-center gap-2">
            <Calendar className="h-4 w-4" /> {date}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <NotificationBell />
        </div>
      </motion.div>

      {/* Email verification banner */}
      {user?.emailVerified === false && !dismissedBanner && (
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
            <Link to={`/verify-email?email=${encodeURIComponent(user?.email || "")}`}>
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

      {/* Stats Row */}
      <motion.div variants={fadeUp} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5">
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Active Postings</p>
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <Briefcase className="h-5 w-5 text-[#1E3A5F]" />
              </div>
            </div>
            <p className="text-3xl font-bold text-slate-900">{data?.active_postings ?? 0}</p>
            <div className="mt-2 flex items-center gap-1 text-xs text-slate-400">
              <TrendingUp className="h-3 w-3" /> Active job listings
            </div>
          </CardContent>
        </Card>
        <Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5">
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Candidates</p>
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <Users className="h-5 w-5 text-slate-600" />
              </div>
            </div>
            <p className="text-3xl font-bold text-slate-900">{data?.total_candidates ?? 0}</p>
            <div className="mt-2 flex items-center gap-1 text-xs text-slate-400">
              <BarChart3 className="h-3 w-3" /> Across all postings
            </div>
          </CardContent>
        </Card>
        <Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5">
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Top Match</p>
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <UserCheck className="h-5 w-5 text-[#F97316]" />
              </div>
            </div>
            <p className="text-3xl font-bold bg-gradient-to-r from-orange-500 to-orange-600 bg-clip-text text-transparent">{Number(data?.top_match_score ?? 0).toFixed(2)}%</p>
            <div className="mt-2 flex items-center gap-1 text-xs text-slate-400">
              <TrendingUp className="h-3 w-3" /> Highest candidate score
            </div>
          </CardContent>
        </Card>
        <Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5">
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Recent Jobs</p>
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-green-50 to-green-100 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <Sparkles className="h-5 w-5 text-green-600" />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <p className="text-3xl font-bold text-slate-900">{activeJobs.length}</p>
              <TrendingUp className="h-5 w-5 text-green-500" />
            </div>
            <div className="mt-2 flex items-center gap-1 text-xs text-slate-400">
              <Briefcase className="h-3 w-3" /> Jobs posted this month
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
                  return (
                    <div key={iv.interview_id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors gap-3 flex-wrap">
                      <div className="flex items-start gap-4 min-w-0">
                        <div className="h-10 w-10 rounded-full bg-[#1E3A5F]/5 flex items-center justify-center shrink-0">
                          <Calendar className="h-5 w-5 text-[#1E3A5F]" />
                        </div>
                        <div className="min-w-0">
                          <h4 className="font-semibold text-slate-900">{iv.job_title}</h4>
                          <p className="text-sm text-slate-500">
                            with <span className="font-medium text-slate-700">{iv.applicant_name}</span>
                          </p>
                          <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                            <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {dateStr} at {timeStr}</span>
                            <span>{iv.duration_minutes} min</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-wrap">
                        {iv.status === "pending" && (
                          <Badge className="bg-amber-50 text-amber-700 border-amber-200">Awaiting Response</Badge>
                        )}
                        {iv.status === "confirmed" && (
                          <Badge className="bg-green-50 text-green-700 border-green-200">Confirmed</Badge>
                        )}
                        {iv.meeting_link && (
                          <JoinInterviewButton
                            scheduledAt={iv.scheduled_at}
                            durationMinutes={iv.duration_minutes}
                            meetingLink={iv.meeting_link}
                          />
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-8 gap-1.5 text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => setCancelTarget(iv)}
                        >
                          <Ban className="h-3.5 w-3.5" /> Cancel
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      <motion.div variants={fadeUp} className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Top Candidates */}
        <Card className="lg:col-span-2 flex flex-col hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-slate-100">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-[#1E3A5F] to-[#2a4f7a] flex items-center justify-center">
                <Users className="h-4 w-4 text-white" />
              </div>
              Top Matches (AI Ranked)
            </CardTitle>
            <Link to="/recruiter/candidates">
              <Button variant="ghost" size="sm" className="text-slate-500 hover:text-[#1E3A5F] gap-1">
                View All <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0 flex-1">
            <div className="divide-y divide-slate-100">
              {topCandidates.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
                  <div className="h-16 w-16 rounded-2xl bg-slate-50 flex items-center justify-center mb-4">
                    <Search className="h-8 w-8 text-slate-300" />
                  </div>
                  <h3 className="text-base font-semibold text-slate-700 mb-1">No candidates yet</h3>
                  <p className="text-sm text-slate-400 max-w-sm">
                    Upload resumes and create jobs to see ranked matches here.
                  </p>
                </div>
              ) : topCandidates.map((candidate: any, idx: number) => (
                <motion.div
                  key={`${candidate.applicant_id}-${candidate.job_title}`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="p-4 flex items-center justify-between gap-4 hover:bg-slate-50 transition-colors group min-w-0"
                >
                  <div className="flex items-start gap-4 min-w-0 flex-1">
                    <div className="h-10 w-10 rounded-full bg-gradient-to-br from-[#1E3A5F] to-[#2a4f7a] text-white flex items-center justify-center font-semibold text-sm shrink-0 mt-0.5 shadow-sm">
                      {candidate.applicant_name.split(' ').map((n: string) => n[0]).join('')}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-semibold text-slate-900 group-hover:text-[#1E3A5F] transition-colors">{candidate.applicant_name}</h3>
                        <Badge className="bg-green-100 text-green-700 hover:bg-green-100 border-none h-5 text-[10px] shrink-0">
                          {Number(candidate.matching_score).toFixed(2)}% Match
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-500 truncate">{candidate.job_title}</p>
                      {candidate.resume_skills?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {candidate.resume_skills.slice(0, 4).map((s: string) => (
                            <Badge key={s} variant="outline" className="text-[11px] px-2 py-0.5 text-slate-500 bg-white border-slate-200">
                              {s}
                            </Badge>
                          ))}
                          {candidate.resume_skills.length > 4 && (
                            <span className="text-[11px] text-slate-400 self-center">+{candidate.resume_skills.length - 4}</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-4 shrink-0">
                    <Button variant="outline" size="sm" className="gap-2">
                      <FileText className="h-3.5 w-3.5" /> Resume
                    </Button>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Active Job Postings */}
        <Card className="flex flex-col hover:shadow-lg transition-all duration-300 border-0 shadow-md">
          <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-orange-400 to-orange-500 flex items-center justify-center">
                <Briefcase className="h-4 w-4 text-white" />
              </div>
              Active Jobs
            </CardTitle>
            <Link to="/recruiter/post-job">
              <Button size="sm" className="bg-[#F97316] hover:bg-[#e8630e] text-white gap-1.5 shadow-sm hover:shadow-md transition-all">
                <Plus className="h-4 w-4" /> New
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0 flex-1">
            <div className="divide-y divide-slate-100">
              {activeJobs.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 px-6 text-center">
                  <div className="h-12 w-12 rounded-2xl bg-slate-50 flex items-center justify-center mb-3">
                    <Briefcase className="h-6 w-6 text-slate-300" />
                  </div>
                  <p className="text-sm text-slate-500 mb-1">No active job postings yet.</p>
                  <p className="text-xs text-slate-400">Create your first posting to start receiving candidates.</p>
                </div>
              ) : activeJobs.slice(0, 5).map((post: any) => (
                <div key={post.job_id} className="p-4 hover:bg-slate-50 transition-colors group">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-semibold text-slate-900 group-hover:text-[#1E3A5F] transition-colors">{post.title}</h4>
                    <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50 border-blue-200 shrink-0">Active</Badge>
                  </div>
                  <div className="flex justify-between items-center text-sm text-slate-500">
                    <span className="flex items-center gap-1.5"><Users className="h-3.5 w-3.5" /> {data?.total_candidates ?? 0} Candidates</span>
                    <span className="text-xs">{post.created_at ? new Date(post.created_at).toLocaleDateString() : "Recent"}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="p-3 bg-slate-50 border-t border-slate-100 text-center rounded-b-xl">
              <Link to="/recruiter/jobs" className="text-sm font-medium text-[#1E3A5F] hover:text-[#F97316] transition-colors inline-flex items-center gap-1 underline-offset-2 hover:underline">
                Manage Jobs <ExternalLink className="h-3 w-3" />
              </Link>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Cancel Interview Confirmation */}
      <AlertDialog open={!!cancelTarget} onOpenChange={() => setCancelTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="text-lg font-bold text-slate-900">Cancel Interview</AlertDialogTitle>
            <AlertDialogDescription className="text-slate-600">
              Are you sure you want to cancel the interview for{" "}
              <span className="font-semibold">{cancelTarget?.job_title}</span> with{" "}
              <span className="font-semibold">{cancelTarget?.applicant_name}</span>?
              The candidate will be notified immediately.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={cancelling}>Keep Interview</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleCancelInterview}
              disabled={cancelling}
              className="bg-red-600 hover:bg-red-700 text-white focus:ring-red-600"
            >
              {cancelling ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Cancelling...</>
              ) : (
                <><Ban className="h-4 w-4 mr-2" /> Cancel Interview</>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </motion.div>
  );
}