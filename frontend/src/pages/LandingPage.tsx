import { useEffect, useState } from "react";
import { Link } from "react-router";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Target, TrendingUp, Award, ArrowRight, User, Briefcase, Sparkles, Loader2, ChevronDown, Star, Zap, Shield, BarChart3 } from "lucide-react";
import { motion, useScroll, useTransform, type Variants } from "framer-motion";
import { VisualBackground } from "@/components/VisualBackground";
import { SipSetuLogo } from "@/components/SipSetuLogo";

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

// Animated counter component
function AnimatedCounter({ value, label, color = "text-[#1E3A5F]", icon: Icon }: { value: number; label: string; color?: string; icon?: any }) {
  const [count, setCount] = useState(0);
  const target = value || 0;

  useEffect(() => {
    if (!target) return;
    const duration = 2000;
    const steps = 30;
    const increment = target / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        setCount(target);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [target]);

  return (
    <motion.div
      className="flex flex-col items-center gap-2"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
    >
      {Icon && (
        <div className="h-10 w-10 rounded-full bg-white/10 flex items-center justify-center">
          <Icon className="h-5 w-5 text-white" />
        </div>
      )}
      <span className={`text-4xl font-black tracking-tight ${color}`}>
        {count}{target >= 1000 ? "+" : "+"}
      </span>
      <span className="text-sm font-medium text-slate-400">{label}</span>
    </motion.div>
  );
}

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 }
  }
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } }
};

export default function LandingPage() {
  const [stats, setStats] = useState<PreviewStats>({ jobs: 0, recruiters: 0, applicants: 0, resumes: 0 });
  const [recentJobs, setRecentJobs] = useState<PreviewJob[]>([]);
  const [topCandidates, setTopCandidates] = useState<PreviewCandidate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPreview = async () => {
      try {
        const res = await api.get("/public/preview");
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

  const { scrollYProgress } = useScroll();
  const heroOpacity = useTransform(scrollYProgress, [0, 0.15], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 0.15], [1, 0.95]);

  return (
    <div className="min-h-screen bg-slate-50 font-sans selection:bg-[#F97316] selection:text-white overflow-x-hidden">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-lg border-b border-slate-200/60 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <SipSetuLogo className="text-2xl font-bold tracking-tight text-[#1E3A5F]" />
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm font-medium text-slate-600 hover:text-[#1E3A5F] transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 after:bg-[#F97316] after:transition-all hover:after:w-full">Features</a>
            <a href="#how-it-works" className="text-sm font-medium text-slate-600 hover:text-[#1E3A5F] transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 after:bg-[#F97316] after:transition-all hover:after:w-full">How it Works</a>
            <a href="#live-data" className="text-sm font-medium text-slate-600 hover:text-[#1E3A5F] transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 after:bg-[#F97316] after:transition-all hover:after:w-full">Live Activity</a>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/preview">
              <Button variant="ghost" className="text-slate-600 hover:text-[#1E3A5F] hover:bg-slate-100">Preview</Button>
            </Link>
            <Link to="/login">
              <Button variant="ghost" className="text-slate-600 hover:text-[#1E3A5F] hover:bg-slate-100">Sign In</Button>
            </Link>
            <Link to="/register">
              <Button className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 text-white shadow-lg shadow-[#1E3A5F]/20">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <motion.section style={{ opacity: heroOpacity, scale: heroScale }} className="pt-48 pb-32 px-6 overflow-hidden relative">
        <VisualBackground />
        <div className="max-w-5xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-6 inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 border border-white/20 backdrop-blur-sm"
          >
            <Star className="h-3.5 w-3.5 text-yellow-300" />
            <span className="text-blue-100 text-sm font-medium uppercase tracking-widest">AI-Powered Recruitment Platform</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-6xl md:text-8xl font-black tracking-tighter text-white mb-8 leading-[0.9]"
          >
            NO SKILL <br />
            <span className="bg-gradient-to-r from-blue-200 via-blue-100 to-white bg-clip-text text-transparent">LEFT BEHIND</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.35 }}
            className="text-xl md:text-2xl text-blue-50/90 mb-12 max-w-2xl mx-auto leading-relaxed font-light"
          >
            SipSetu is the AI-powered recruitment platform bridging job seekers and recruiters. Discover where you truly stand, or find the signal through the noise.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.5 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link to="/preview">
              <Button size="lg" className="w-full sm:w-auto h-14 px-8 text-base bg-white text-[#1E3A5F] hover:bg-blue-50 shadow-xl shadow-white/20 rounded-xl font-bold transition-all duration-300 hover:scale-105 hover:shadow-2xl">
                Explore Platform <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link to="/register?role=applicant">
              <Button size="lg" className="w-full sm:w-auto h-14 px-8 text-base bg-[#F97316] hover:bg-[#e8630e] text-white shadow-xl shadow-orange-500/30 rounded-xl font-bold transition-all duration-300 hover:scale-105">
                I'm a Job Seeker <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link to="/register?role=recruiter">
              <Button size="lg" className="w-full sm:w-auto h-14 px-8 text-base bg-[#1E3A5F] hover:bg-[#162d4a] text-white shadow-xl shadow-[#1E3A5F]/30 rounded-xl font-bold transition-all duration-300 hover:scale-105">
                I'm a Recruiter <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </motion.div>

          {/* Scroll indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5 }}
            className="mt-20"
          >
            <motion.div
              animate={{ y: [0, 8, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="inline-flex items-center gap-2 text-blue-200/60 text-xs"
            >
              <span>Scroll to explore</span>
              <ChevronDown className="h-4 w-4" />
            </motion.div>
          </motion.div>
        </div>
      </motion.section>

      {/* Stats Bar */}
      <section className="border-y border-slate-200 bg-white relative">
        <div className="max-w-7xl mx-auto px-6 py-12">
          {loading ? (
            <div className="flex items-center justify-center h-20">
              <Loader2 className="h-6 w-6 animate-spin text-[#1E3A5F]" />
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              <AnimatedCounter value={stats.applicants} label="Job Seekers" color="text-[#1E3A5F]" icon={User} />
              <AnimatedCounter value={stats.recruiters} label="Companies Hiring" color="text-[#1E3A5F]" icon={Briefcase} />
              <AnimatedCounter value={stats.jobs} label="Open Roles" color="text-[#F97316]" icon={BarChart3} />
              <AnimatedCounter value={stats.resumes} label="Resumes Analyzed" color="text-[#1E3A5F]" icon={FileText} />
            </div>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-28 px-6 bg-gradient-to-b from-slate-50 to-white">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-[#1E3A5F] text-sm font-semibold mb-4">
              <Zap className="h-4 w-4" /> Powerful Features
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-[#1E3A5F] mb-4 tracking-tight">Intelligence at every step</h2>
            <p className="text-lg text-slate-500 max-w-2xl mx-auto">Our precision instruments give you the clarity needed to make the right career or hiring moves.</p>
          </motion.div>

          <motion.div
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="grid md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {[
              { title: "Resume Analysis", icon: FileText, desc: "Deep extraction of skills, experience, and intent from any format." },
              { title: "Intelligent Matching", icon: Target, desc: "Context-aware scoring that goes beyond keyword bingo." },
              { title: "Skill Gap Detection", icon: TrendingUp, desc: "See exactly what you're missing for your dream role." },
              { title: "Candidate Ranking", icon: Award, desc: "Find the strongest signals in a sea of applications instantly." }
            ].map((feature, i) => (
              <motion.div key={i} variants={itemVariants}>
                <Card className="h-full border-slate-200 hover:border-[#1E3A5F]/20 shadow-sm hover:shadow-xl transition-all duration-500 hover:-translate-y-2 group cursor-default">
                  <CardContent className="p-6">
                    <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100 text-[#1E3A5F] flex items-center justify-center mb-6 group-hover:scale-110 group-hover:shadow-lg transition-all duration-300">
                      <feature.icon className="h-6 w-6" />
                    </div>
                    <h3 className="text-xl font-semibold text-slate-900 mb-2 group-hover:text-[#1E3A5F] transition-colors">{feature.title}</h3>
                    <p className="text-slate-500 text-sm leading-relaxed">{feature.desc}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-28 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 text-[#F97316] text-sm font-semibold mb-4">
              <Shield className="h-4 w-4" /> How It Works
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-[#1E3A5F] mb-4 tracking-tight">Your journey, simplified</h2>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-16">
            {/* Applicants */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <div className="p-8 rounded-2xl bg-gradient-to-br from-orange-50 to-orange-50/50 border border-orange-100">
                <h3 className="text-2xl font-bold text-[#F97316] mb-8 flex items-center gap-3">
                  <User className="h-6 w-6" /> For Job Seekers
                </h3>
                <div className="space-y-8">
                  {[
                    { title: "Build or Upload Resume", desc: "Drop your PDF or build one inline — our AI extracts your profile either way." },
                    { title: "Discover Matches", desc: "See jobs ranked by your actual skill overlap, not just keywords." },
                    { title: "Bridge the Gap", desc: "Get targeted learning resources for skills you're missing." }
                  ].map((step, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true }}
                      transition={{ delay: i * 0.15 }}
                      className="flex gap-4 group"
                    >
                      <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-orange-100 text-[#F97316] font-bold flex items-center justify-center group-hover:scale-110 group-hover:shadow-md transition-all duration-300">
                        {i + 1}
                      </div>
                      <div>
                        <h4 className="text-lg font-semibold text-slate-900 mb-1">{step.title}</h4>
                        <p className="text-slate-500">{step.desc}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>

            {/* Recruiters */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <div className="p-8 rounded-2xl bg-gradient-to-br from-blue-50 to-blue-50/50 border border-blue-100">
                <h3 className="text-2xl font-bold text-[#1E3A5F] mb-8 flex items-center gap-3">
                  <Briefcase className="h-6 w-6" /> For Recruiters
                </h3>
                <div className="space-y-8">
                  {[
                    { title: "Post Requirements", desc: "Define what you actually need with weighted skill tags." },
                    { title: "Review Ranked Talent", desc: "Candidates are auto-scored against your exact needs." },
                    { title: "Make Confident Hires", desc: "Look past the resume noise to find true capability." }
                  ].map((step, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true }}
                      transition={{ delay: i * 0.15 }}
                      className="flex gap-4 group"
                    >
                      <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-blue-50 text-[#1E3A5F] font-bold flex items-center justify-center group-hover:scale-110 group-hover:shadow-md transition-all duration-300">
                        {i + 1}
                      </div>
                      <div>
                        <h4 className="text-lg font-semibold text-slate-900 mb-1">{step.title}</h4>
                        <p className="text-slate-500">{step.desc}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Live Activity */}
      <section id="live-data" className="py-28 px-6 bg-gradient-to-b from-slate-50 to-white">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 text-[#F97316] text-sm font-semibold mb-4">
              <Sparkles className="h-4 w-4" /> Live from our platform
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-[#1E3A5F] mb-4 tracking-tight">What's happening right now</h2>
            <p className="text-lg text-slate-500 max-w-2xl mx-auto">
              Real roles posted and real candidate matches happening on SipSetu. No staging data.
            </p>
          </motion.div>

          {loading ? (
            <div className="flex items-center justify-center h-40">
              <Loader2 className="h-6 w-6 animate-spin text-[#1E3A5F]" />
            </div>
          ) : (
            <div className="grid lg:grid-cols-2 gap-8 stagger-children">
              {/* Recent jobs */}
              <Card className="border-slate-200 shadow-sm hover:shadow-lg transition-all duration-300">
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
                    <div className="space-y-3">
                      {recentJobs.slice(0, 4).map((job, i) => (
                        <motion.div
                          key={job.job_id}
                          initial={{ opacity: 0, x: -10 }}
                          whileInView={{ opacity: 1, x: 0 }}
                          viewport={{ once: true }}
                          transition={{ delay: i * 0.1 }}
                          className="rounded-xl border border-slate-200 p-4 bg-white hover:border-[#1E3A5F]/30 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
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
                        </motion.div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Top candidates */}
              <Card className="border-slate-200 shadow-sm hover:shadow-lg transition-all duration-300">
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
                    <div className="space-y-3">
                      {topCandidates.slice(0, 4).map((c, i) => (
                        <motion.div
                          key={c.ranking_id}
                          initial={{ opacity: 0, x: 10 }}
                          whileInView={{ opacity: 1, x: 0 }}
                          viewport={{ once: true }}
                          transition={{ delay: i * 0.1 }}
                          className="rounded-xl border border-slate-200 p-4 bg-white hover:border-[#F97316]/30 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
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
                        </motion.div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 bg-[#1E3A5F] relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-[#1E3A5F] via-[#1E3A5F]/90 to-[#F97316]/10" />
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">Ready to transform your hiring?</h2>
            <p className="text-xl text-blue-200 mb-10 max-w-2xl mx-auto">
              Join thousands of job seekers and recruiters already using SipSetu to make better career and hiring decisions.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/register?role=applicant">
                <Button size="lg" className="h-14 px-10 text-base bg-[#F97316] hover:bg-[#e8630e] text-white shadow-xl shadow-orange-500/30 rounded-xl font-bold transition-all duration-300 hover:scale-105">
                  Get Started Free <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Link to="/preview">
                <Button size="lg" className="h-14 px-10 text-base bg-white/10 hover:bg-white/20 text-white border border-white/20 rounded-xl font-bold transition-all duration-300 hover:scale-105">
                  See Live Demo
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#0f2440] text-slate-400 py-16 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            <div className="md:col-span-2">
              <SipSetuLogo className="text-2xl font-bold text-white tracking-tight mb-4" />
              <p className="text-sm text-slate-400 max-w-md leading-relaxed">
                AI-powered recruitment platform bridging the gap between talent and opportunity. No skill left behind.
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">Platform</h4>
              <div className="space-y-3">
                <a href="#features" className="block text-sm hover:text-white transition-colors">Features</a>
                <a href="#how-it-works" className="block text-sm hover:text-white transition-colors">How it Works</a>
                <a href="#live-data" className="block text-sm hover:text-white transition-colors">Live Activity</a>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">Company</h4>
              <div className="space-y-3">
                <a href="#" className="block text-sm hover:text-white transition-colors">Privacy</a>
                <a href="#" className="block text-sm hover:text-white transition-colors">Terms</a>
                <a href="#" className="block text-sm hover:text-white transition-colors">Contact</a>
              </div>
            </div>
          </div>
          <div className="border-t border-white/10 pt-8 text-center text-sm">
            © {new Date().getFullYear()} SipSetu Inc. No skill left behind.
          </div>
        </div>
      </footer>
    </div>
  );
}
