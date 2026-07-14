import { useEffect, useState } from "react";
import { Link } from "react-router";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Target, TrendingUp, Award, ArrowRight, User, Briefcase, Sparkles, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { VisualBackground } from "@/components/VisualBackground";
import { SipSetuLogo } from "@/components/SipSetuLogo";

const API = "http://localhost:5000/api";

interface PreviewStats {
  jobs: number;
  recruiters: number;
  applicants: number;
  resumes: number;
}

interface PreviewJob {
  job_id: string;
  title: string;
  recruiter_company: string;
  recruiter_name: string;
  location: string;
  skills: string[];
  created_at: string | null;
}

interface PreviewCandidate {
  ranking_id: string;
  job_id: string;
  job_title: string;
  applicant_id: string;
  applicant_name: string;
  matching_score: number;
  resume_skills: string[];
}

// Display caps for the landing page — show the platform's reach in real
// units rather than inflating with marketing numbers.
const formatStat = (n: number | undefined): string => {
  if (n === undefined || n === null) return "0";
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}K+`;
  return `${n}+`;
};

export default function LandingPage() {
  const [stats, setStats] = useState<PreviewStats>({
    jobs: 0,
    recruiters: 0,
    applicants: 0,
    resumes: 0,
  });
  const [recentJobs, setRecentJobs] = useState<PreviewJob[]>([]);
  const [topCandidates, setTopCandidates] = useState<PreviewCandidate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPreview = async () => {
      try {
        const res = await axios.get(`${API}/public/preview`);
        setStats(res.data?.stats ?? { jobs: 0, recruiters: 0, applicants: 0, resumes: 0 });
        setRecentJobs(res.data?.recent_jobs ?? []);
        setTopCandidates(res.data?.top_candidates ?? []);
      } catch (err) {
        console.error("Failed to load landing page stats", err);
      } finally {
        setLoading(false);
      }
    };
    fetchPreview();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 font-sans selection:bg-[#F97316] selection:text-white">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <SipSetuLogo className="text-2xl font-bold tracking-tight text-[#1E3A5F]" />
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm font-medium text-slate-600 hover:text-[#1E3A5F] transition-colors">Features</a>
            <a href="#how-it-works" className="text-sm font-medium text-slate-600 hover:text-[#1E3A5F] transition-colors">How it Works</a>
            <a href="#live-data" className="text-sm font-medium text-slate-600 hover:text-[#1E3A5F] transition-colors">Live Activity</a>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/preview">
              <Button variant="ghost" className="hover:text-[#1E3A5F]">Preview</Button>
            </Link>
            <Link to="/login">
              <Button variant="ghost" className="hover:text-[#6aacde]" >Sign In</Button>
            </Link>
            <Link to="/register">
              <Button className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-48 pb-32 px-6 overflow-hidden relative">
        <VisualBackground />

        <div className="max-w-5xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="mb-6 inline-block px-4 py-1.5 rounded-full bg-white/10 border border-white/20 backdrop-blur-sm"
          >
            <span className="text-blue-100 text-sm font-medium uppercase tracking-widest">Bridging Talent & Opportunity</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-6xl md:text-8xl font-black tracking-tighter text-white mb-8 leading-[0.9]"
          >
            NO SKILL <br />
            <span className="text-blue-200">LEFT BEHIND</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-xl md:text-2xl text-blue-50 mb-12 max-w-2xl mx-auto leading-relaxed font-light"
          >
            SipSetu is the AI-powered recruitment platform bridging job seekers and recruiters. Discover where you truly stand, or find the signal through the noise.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-6"
          >
            <Link to="/preview">
              <Button size="lg" className="w-full sm:w-auto h-16 px-10 text-lg bg-[#F97316] hover:bg-[#F97316]/90 text-white shadow-xl shadow-orange-500/30 rounded-2xl font-bold transition-all hover:scale-105">
                Preview the platform <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link to="/register?role=applicant">
              <Button size="lg" className="w-full sm:w-auto h-16 px-10 text-lg bg-[#F97316] hover:bg-[#F97316]/90 text-white shadow-xl shadow-orange-500/30 rounded-2xl font-bold transition-all hover:scale-105">
                I'm a Job Seeker <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link to="/register?role=recruiter">
              <Button size="lg" className="w-full sm:w-auto h-16 px-10 text-lg bg-[#F97316] hover:bg-[#F97316]/90 text-white shadow-xl shadow-orange-500/30 rounded-2xl font-bold transition-all hover:scale-105">
                I'm a Recruiter <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Stats Bar — live data from /api/public/preview */}
      <section className="border-y border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-10">
          {loading ? (
            <div className="flex items-center justify-center h-20">
              <Loader2 className="h-6 w-6 animate-spin text-[#1E3A5F]" />
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center divide-x divide-slate-100">
              <div className="flex flex-col">
                <span className="text-3xl font-bold text-[#1E3A5F]" data-testid="stat-applicants">
                  {formatStat(stats.applicants)}
                </span>
                <span className="text-sm font-medium text-slate-500 mt-1">Job Seekers</span>
              </div>
              <div className="flex flex-col">
                <span className="text-3xl font-bold text-[#1E3A5F]" data-testid="stat-recruiters">
                  {formatStat(stats.recruiters)}
                </span>
                <span className="text-sm font-medium text-slate-500 mt-1">Companies Hiring</span>
              </div>
              <div className="flex flex-col">
                <span className="text-3xl font-bold text-[#F97316]" data-testid="stat-jobs">
                  {formatStat(stats.jobs)}
                </span>
                <span className="text-sm font-medium text-slate-500 mt-1">Open Roles</span>
              </div>
              <div className="flex flex-col">
                <span className="text-3xl font-bold text-[#1E3A5F]" data-testid="stat-resumes">
                  {formatStat(stats.resumes)}
                </span>
                <span className="text-sm font-medium text-slate-500 mt-1">Resumes Analyzed</span>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-6 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-[#1E3A5F] mb-4">Intelligence at every step</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">Our precision instruments give you the clarity needed to make the right career or hiring moves.</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { title: "Resume Analysis", icon: FileText, desc: "Deep extraction of skills, experience, and intent from any format." },
              { title: "Intelligent Matching", icon: Target, desc: "Context-aware scoring that goes beyond keyword bingo." },
              { title: "Skill Gap Detection", icon: TrendingUp, desc: "See exactly what you're missing for your dream role." },
              { title: "Candidate Ranking", icon: Award, desc: "Find the strongest signals in a sea of applications instantly." }
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
              >
                <Card className="h-full border-slate-200 shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1">
                  <CardContent className="p-6">
                    <div className="h-12 w-12 rounded-xl bg-blue-50 text-[#1E3A5F] flex items-center justify-center mb-6">
                      <feature.icon className="h-6 w-6" />
                    </div>
                    <h3 className="text-xl font-semibold text-slate-900 mb-2">{feature.title}</h3>
                    <p className="text-slate-600 text-sm leading-relaxed">{feature.desc}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-24 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-[#1E3A5F] mb-4">How SipSetu Works</h2>
          </div>

          <div className="grid md:grid-cols-2 gap-16">
            {/* Applicants */}
            <div>
              <h3 className="text-2xl font-bold text-[#F97316] mb-8 flex items-center gap-3">
                <User className="h-6 w-6" /> For Job Seekers
              </h3>
              <div className="space-y-8">
                {[
                  { title: "Build or Upload Resume", desc: "Drop your PDF or build one inline — our AI extracts your profile either way." },
                  { title: "Discover Matches", desc: "See jobs ranked by your actual skill overlap, not just keywords." },
                  { title: "Bridge the Gap", desc: "Get targeted learning resources for skills you're missing." }
                ].map((step, i) => (
                  <div key={i} className="flex gap-4">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-orange-100 text-[#F97316] font-bold flex items-center justify-center">
                      {i + 1}
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-slate-900 mb-1">{step.title}</h4>
                      <p className="text-slate-600">{step.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recruiters */}
            <div>
              <h3 className="text-2xl font-bold text-[#1E3A5F] mb-8 flex items-center gap-3">
                <Briefcase className="h-6 w-6" /> For Recruiters
              </h3>
              <div className="space-y-8">
                {[
                  { title: "Post Requirements", desc: "Define what you actually need with weighted skill tags." },
                  { title: "Review Ranked Talent", desc: "Candidates are auto-scored against your exact needs." },
                  { title: "Make Confident Hires", desc: "Look past the resume noise to find true capability." }
                ].map((step, i) => (
                  <div key={i} className="flex gap-4">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-50 text-[#1E3A5F] font-bold flex items-center justify-center">
                      {i + 1}
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-slate-900 mb-1">{step.title}</h4>
                      <p className="text-slate-600">{step.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Live Activity — real jobs and candidates from the database */}
      <section id="live-data" className="py-24 px-6 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 text-[#F97316] text-sm font-semibold mb-4">
              <Sparkles className="h-4 w-4" /> Live from our platform
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-[#1E3A5F] mb-4">What's happening right now</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Real roles posted and real candidate matches happening on SipSetu. No staging data.
            </p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-40">
              <Loader2 className="h-6 w-6 animate-spin text-[#1E3A5F]" />
            </div>
          ) : (
            <div className="grid lg:grid-cols-2 gap-8">
              {/* Recent jobs */}
              <Card className="border-slate-200 shadow-sm">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
                      <Briefcase className="h-5 w-5 text-[#1E3A5F]" /> Latest Roles
                    </h3>
                    <Badge variant="secondary" className="bg-slate-100 text-slate-700">
                      {recentJobs.length} {recentJobs.length === 1 ? "job" : "jobs"}
                    </Badge>
                  </div>
                  {recentJobs.length === 0 ? (
                    <p className="text-sm text-slate-500 py-8 text-center">
                      No jobs posted yet. Be the first to <Link to="/register?role=recruiter" className="text-[#1E3A5F] font-semibold hover:underline">post one</Link>.
                    </p>
                  ) : (
                    <div className="space-y-4">
                      {recentJobs.slice(0, 4).map((job) => (
                        <div
                          key={job.job_id}
                          className="rounded-xl border border-slate-200 p-4 bg-white hover:border-[#1E3A5F]/30 transition-colors"
                          data-testid="landing-recent-job"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <h4 className="font-semibold text-slate-900 truncate">{job.title}</h4>
                              <p className="text-sm text-slate-500 mt-0.5 truncate">
                                {job.recruiter_company || job.recruiter_name || "Hiring team"}
                                {job.location ? ` • ${job.location}` : ""}
                              </p>
                            </div>
                          </div>
                          {job.skills && job.skills.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-3">
                              {job.skills.slice(0, 4).map((skill) => (
                                <Badge key={skill} variant="secondary" className="bg-slate-100 text-slate-700 hover:bg-slate-100 text-xs">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Top candidates */}
              <Card className="border-slate-200 shadow-sm">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
                      <Award className="h-5 w-5 text-[#F97316]" /> Top Matches
                    </h3>
                    <Badge variant="secondary" className="bg-orange-50 text-[#F97316]">
                      {topCandidates.length} {topCandidates.length === 1 ? "match" : "matches"}
                    </Badge>
                  </div>
                  {topCandidates.length === 0 ? (
                    <p className="text-sm text-slate-500 py-8 text-center">
                      No ranked candidates yet. <Link to="/register?role=applicant" className="text-[#1E3A5F] font-semibold hover:underline">Apply to a role</Link> to appear here.
                    </p>
                  ) : (
                    <div className="space-y-4">
                      {topCandidates.slice(0, 4).map((c) => (
                        <div
                          key={c.ranking_id}
                          className="rounded-xl border border-slate-200 p-4 bg-white hover:border-[#F97316]/30 transition-colors"
                          data-testid="landing-top-candidate"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <h4 className="font-semibold text-slate-900 truncate">{c.applicant_name}</h4>
                              <p className="text-sm text-slate-500 mt-0.5 truncate">For: {c.job_title}</p>
                            </div>
                            <Badge className="bg-[#F97316]/10 text-[#F97316] hover:bg-[#F97316]/10 border-none flex-shrink-0">
                              {Number(c.matching_score).toFixed(1)}%
                            </Badge>
                          </div>
                          {c.resume_skills && c.resume_skills.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-3">
                              {c.resume_skills.slice(0, 4).map((skill) => (
                                <Badge key={skill} variant="secondary" className="bg-slate-100 text-slate-700 hover:bg-slate-100 text-xs">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#1E3A5F] text-slate-300 py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <SipSetuLogo className="text-2xl font-bold text-white tracking-tight" />
          </div>
          <div className="text-sm">
            © {new Date().getFullYear()} SipSetu Inc. No skill left behind.
          </div>
          <div className="flex gap-6 text-sm">
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Terms</a>
            <a href="#" className="hover:text-white transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
