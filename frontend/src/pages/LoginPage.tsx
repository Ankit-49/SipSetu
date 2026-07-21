import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import React from "react";
import { motion } from "framer-motion";
import Lottie from "lottie-react";
import loginAnimation from "@/imports/Login.json";
import { Eye, EyeOff } from "lucide-react";
import { VisualBackground } from "@/components/VisualBackground";
import { SipSetuLogo } from "@/components/SipSetuLogo";
import { useAuth } from "@/app/context/AuthContext";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const from = (location.state as { from?: string })?.from || undefined;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    setSubmitting(true);
    try {
      await login(email, password);
      // After successful login, the AuthContext sets localStorage + user state
      const role = localStorage.getItem("user_role");
      if (from && (from.startsWith("/applicant") || from.startsWith("/recruiter"))) {
        navigate(from, { replace: true });
      } else if (role === "applicant") {
        navigate("/applicant/dashboard", { replace: true });
      } else {
        navigate("/recruiter/dashboard", { replace: true });
      }
    } catch (err: any) {
      console.error("Login error:", err);
      const message = err.response?.data?.error || err.message || "Login failed. Please check if the backend is running.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const role = "applicant"; // default for registration link

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
            <Lottie animationData={loginAnimation} loop autoplay style={{ width: '100%', height: 'auto' }} />
          </div>
        </motion.div>

        {/* Card Side */}
        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="w-full max-w-md"
        >
          <Card className="shadow-2xl border-none bg-white/95 backdrop-blur-sm">
            <CardHeader className="space-y-3 text-center pb-6">
              <div className="flex justify-center mb-2">
                <SipSetuLogo className="text-4xl font-black tracking-tighter text-[#1E3A5F]" />
              </div>
              <CardTitle className="text-2xl font-bold">Welcome back</CardTitle>
              <CardDescription>Enter your details to sign in to your account</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleLogin} className="space-y-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" type="email" placeholder="name@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required className="h-11" />
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="password">Password</Label>
                      <Link to="/forgot-password" className="text-sm font-medium text-[#F97316] hover:underline">Forgot password?</Link>
                    </div>
                    <div className="relative">
                      <Input id="password" type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} className="h-11 pr-10" />
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
                  </div>
                </div>

                {error && <p className="text-red-500 text-sm">{error}</p>}

                <Button type="submit" disabled={submitting} className="w-full h-11 text-base bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
                  {submitting ? "Signing in..." : "Sign In"}
                </Button>

                <div className="text-center text-sm text-slate-600">
                  Don't have an account?{" "}
                  <Link to={`/register?role=${role}`} className="font-medium text-[#1E3A5F] hover:underline">
                    Register
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
