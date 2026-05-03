import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FileText, Target, TrendingUp, Award, ArrowRight, User, Briefcase } from "lucide-react";
import { motion } from "framer-motion";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans selection:bg-[#F97316] selection:text-white">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="text-2xl font-bold tracking-tight text-[#1E3A5F]">SipSetu</div>
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm font-medium text-slate-600 hover:text-[#1E3A5F] transition-colors">Features</a>
            <a href="#how-it-works" className="text-sm font-medium text-slate-600 hover:text-[#1E3A5F] transition-colors">How it Works</a>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost" className="font-medium">Sign In</Button>
            </Link>
            <Link to="/register">
              <Button className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 overflow-hidden relative">
        <div className="absolute inset-0 z-0">
          <motion.div 
            animate={{ 
              y: [0, -20, 0],
              opacity: [0.5, 0.8, 0.5]
            }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
            className="absolute top-20 right-20 w-64 h-64 bg-orange-300 rounded-full mix-blend-multiply filter blur-3xl opacity-50"
          />
          <motion.div 
            animate={{ 
              y: [0, 20, 0],
              opacity: [0.3, 0.6, 0.3]
            }}
            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
            className="absolute bottom-20 left-20 w-72 h-72 bg-blue-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30"
          />
        </div>

        <div className="max-w-4xl mx-auto text-center relative z-10">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-5xl md:text-7xl font-extrabold tracking-tight text-[#1E3A5F] mb-6"
          >
            No Skill Left Behind
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-xl text-slate-600 mb-10 max-w-2xl mx-auto leading-relaxed"
          >
            SipSetu is the AI-powered recruitment platform bridging job seekers and recruiters. Discover where you truly stand, or find the signal through the noise.
          </motion.p>
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link to="/register?role=applicant">
              <Button size="lg" className="w-full sm:w-auto h-14 px-8 text-lg bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 shadow-lg shadow-blue-900/20 rounded-xl">
                I'm a Job Seeker <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link to="/register?role=recruiter">
              <Button size="lg" className="w-full sm:w-auto h-14 px-8 text-lg bg-[#F97316] hover:bg-[#F97316]/90 text-white shadow-lg shadow-orange-500/20 rounded-xl">
                I'm a Recruiter <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="border-y border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center divide-x divide-slate-100">
            <div className="flex flex-col">
              <span className="text-3xl font-bold text-[#1E3A5F]">10,000+</span>
              <span className="text-sm font-medium text-slate-500 mt-1">Job Seekers</span>
            </div>
            <div className="flex flex-col">
              <span className="text-3xl font-bold text-[#1E3A5F]">500+</span>
              <span className="text-sm font-medium text-slate-500 mt-1">Companies</span>
            </div>
            <div className="flex flex-col">
              <span className="text-3xl font-bold text-[#F97316]">85%</span>
              <span className="text-sm font-medium text-slate-500 mt-1">Match Accuracy</span>
            </div>
            <div className="flex flex-col">
              <span className="text-3xl font-bold text-[#1E3A5F]">72hrs</span>
              <span className="text-sm font-medium text-slate-500 mt-1">Avg. Time-to-Hire</span>
            </div>
          </div>
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
                  { title: "Upload Resume", desc: "Drop your PDF and let our AI extract your profile instantly." },
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

      {/* Footer */}
      <footer className="bg-[#1E3A5F] text-slate-300 py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <span className="text-2xl font-bold text-white tracking-tight">SipSetu</span>
          </div>
          <div className="text-sm">
            © 2026 SipSetu Inc. No skill left behind.
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
