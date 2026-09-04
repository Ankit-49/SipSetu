import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import React from "react";
import { motion } from "framer-motion";
import Lottie from "lottie-react";
import loginAnimation from "@/imports/Login.json";
import { Eye, EyeOff, ArrowRight, Mail, Lock, User, UserCircle, Building } from "lucide-react";
import { VisualBackground } from "@/components/VisualBackground";
import { SipSetuLogo } from "@/components/SipSetuLogo";
import { useAuth } from "@/app/context/AuthContext";
import { usePasswordStrength } from "@/hooks/use-password-strength";
import { PasswordStrengthIndicator } from "@/components/PasswordStrengthIndicator";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const searchParams = new URLSearchParams(window.location.search);
  const initialRole = searchParams.get('role') || 'applicant';
  const [role, setRole] = React.useState(initialRole);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const passwordStrength = usePasswordStrength(password);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (passwordStrength.score < 40) {
      setError("Please choose a stronger password. Enable at least 3 requirements below.");
      return;
    }
    setSubmitting(true);
    try {
      const regResult = await register(name, email, password, role as "applicant" | "recruiter");
      if (regResult?.email_verified === false) {
        navigate(`/verify-email?email=${encodeURIComponent(email)}`, { replace: true });
      } else {
        const dashPath = role === "recruiter" ? "/recruiter/dashboard" : "/applicant/dashboard";
        navigate(dashPath, { replace: true });
      }
    } catch (err: any) {
      console.error("Registration error:", err);
      const message = err.response?.data?.error || err.message || "Registration failed. Please check if the backend is running.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden selection:bg-[#F97316] selection:text-white">
      <VisualBackground />

      <div className="w-full max-w-5xl flex items-center justify-between gap-12 relative z-10">
        {/* Animation Side */}
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="flex-1 hidden md:flex items-center justify-center"
        >
          <div className="w-full max-w-lg drop-shadow-2xl">
            <Lottie
              animationData={loginAnimation}
              loop
              autoplay
              style={{ width: '100%', height: 'auto', transform: 'scaleX(-1)' }}
            />
          </div>
        </motion.div>

        {/* Card Side */}
        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="w-full max-w-md"
        >
          <Card className="shadow-2xl border-none bg-white/95 backdrop-blur-lg rounded-2xl overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#F97316] via-[#1E3A5F] to-[#F97316]" />
            <CardHeader className="space-y-3 text-center pb-6 pt-8">
              <div className="flex justify-center mb-2">
                <SipSetuLogo className="text-4xl font-black tracking-tighter text-[#1E3A5F]" />
              </div>
              <CardTitle className="text-2xl font-bold">Create an account</CardTitle>
              <CardDescription className="text-slate-500">Join SipSetu to start your journey</CardDescription>
            </CardHeader>
            <CardContent className="pb-8 px-8">
              <form onSubmit={handleRegister} className="space-y-5">
                {/* Role toggle */}
                <div className="space-y-2">
                  <Label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">I am a</Label>
                  <ToggleGroup
                    type="single"
                    value={role}
                    onValueChange={(v) => v && setRole(v)}
                    className="justify-start w-full bg-slate-100 p-1 rounded-xl gap-1"
                  >
                    <ToggleGroupItem value="applicant"
                      className={`flex-1 rounded-lg data-[state=on]:bg-[#1E3A5F] data-[state=on]:text-white data-[state=on]:shadow-md transition-all duration-200 ${role !== 'applicant' ? 'hover:bg-slate-200 text-slate-600' : 'text-white'}`}>
                      <UserCircle className={`h-4 w-4 mr-1.5 ${role === 'applicant' ? 'text-white' : 'text-slate-400'}`} />
                      Job Seeker
                    </ToggleGroupItem>
                    <ToggleGroupItem value="recruiter"
                      className={`flex-1 rounded-lg data-[state=on]:bg-[#1E3A5F] data-[state=on]:text-white data-[state=on]:shadow-md transition-all duration-200 ${role !== 'recruiter' ? 'hover:bg-slate-200 text-slate-600' : 'text-white'}`}>
                      <Building className={`h-4 w-4 mr-1.5 ${role === 'recruiter' ? 'text-white' : 'text-slate-400'}`} />
                      Recruiter
                    </ToggleGroupItem>
                  </ToggleGroup>
                </div>

                <div className="space-y-3">
                  <div className="space-y-2">
                    <Label htmlFor="name" className="text-sm font-medium text-slate-700">Full Name</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input id="name" type="text" placeholder="John Doe" value={name} onChange={(e) => setName(e.target.value)} required className="h-11 pl-10 bg-slate-50 border-slate-200 focus:bg-white transition-all" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-sm font-medium text-slate-700">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input id="email" type="email" placeholder="name@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required className="h-11 pl-10 bg-slate-50 border-slate-200 focus:bg-white transition-all" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-sm font-medium text-slate-700">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input id="password" data-testid="password-input" type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} className="h-11 pl-10 pr-10 bg-slate-50 border-slate-200 focus:bg-white transition-all" />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                        tabIndex={-1}
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                    <PasswordStrengthIndicator strength={passwordStrength} />
                  </div>
                </div>

                {error && (
                  <motion.p
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-red-500 text-sm bg-red-50 border border-red-100 rounded-lg p-3"
                  >
                    {error}
                  </motion.p>
                )}

                <Button type="submit" disabled={submitting} className="w-full h-11 text-base bg-gradient-to-r from-[#1E3A5F] to-[#2a4f7a] hover:from-[#1E3A5F]/90 hover:to-[#2a4f7a]/90 shadow-lg shadow-[#1E3A5F]/20 transition-all duration-300">
                  {submitting ? (
                    <span className="flex items-center gap-2">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      Creating account...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      Create Account <ArrowRight className="h-4 w-4" />
                    </span>
                  )}
                </Button>

                <div className="text-center text-sm text-slate-500">
                  Already have an account?{" "}
                  <Link to="/login" className="font-semibold text-[#1E3A5F] hover:text-[#F97316] transition-colors">
                    Sign in
                  </Link>
                </div>
              </form>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
