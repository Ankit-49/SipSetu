import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { motion } from "framer-motion";
import Lottie from "lottie-react";
import loginAnimation from "@/imports/Login.json";
import { Eye, EyeOff, Loader2, CheckCircle2, AlertCircle, ArrowLeft } from "lucide-react";
import { VisualBackground } from "@/components/VisualBackground";
import { SipSetuLogo } from "@/components/SipSetuLogo";
import { usePasswordStrength } from "@/hooks/use-password-strength";
import { PasswordStrengthIndicator } from "@/components/PasswordStrengthIndicator";
import api from "@/lib/api";

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [tokenError, setTokenError] = useState(false);
  const passwordStrength = usePasswordStrength(password);

  useEffect(() => {
    if (!token) {
      setTokenError(true);
      setError("No reset token found. Please request a new password reset link.");
    }
  }, [token]);

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!token) {
      setTokenError(true);
      setError("No reset token found. Please request a new password reset link.");
      return;
    }
    if (passwordStrength.score < 40) {
      setError("Please choose a stronger password. Enable at least 3 requirements below.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/auth/reset-password", { token, password });
      setSuccess(true);
    } catch (err: any) {
      const message = err.response?.data?.error || "Failed to reset password. The link may have expired.";
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
            <Lottie animationData={loginAnimation} loop autoplay style={{ width: '100%', height: 'auto', transform: 'scaleX(-1)' }} />
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
              <CardTitle className="text-2xl font-bold">
                {success ? "Password reset!" : tokenError ? "Invalid link" : "Set new password"}
              </CardTitle>
              <CardDescription>
                {success
                  ? "Your password has been updated successfully."
                  : tokenError
                  ? "This password reset link is invalid or has expired."
                  : "Choose a strong password for your account."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {success ? (
                <div className="space-y-6 text-center">
                  <div className="flex justify-center">
                    <div className="h-16 w-16 rounded-full bg-green-100 flex items-center justify-center">
                      <CheckCircle2 className="h-8 w-8 text-green-600" />
                    </div>
                  </div>
                  <Button
                    className="w-full h-11 text-base bg-[#1E3A5F] hover:bg-[#1E3A5F]/90"
                    onClick={() => navigate("/login", { replace: true })}
                  >
                    Sign in with new password
                  </Button>
                </div>
              ) : tokenError ? (
                <div className="space-y-6 text-center">
                  <div className="flex justify-center">
                    <div className="h-16 w-16 rounded-full bg-red-100 flex items-center justify-center">
                      <AlertCircle className="h-8 w-8 text-red-500" />
                    </div>
                  </div>
                  <Link
                    to="/forgot-password"
                    className="inline-flex items-center text-sm font-medium text-[#F97316] hover:underline gap-1"
                  >
                    <ArrowLeft className="h-4 w-4" /> Request a new reset link
                  </Link>
                </div>
              ) : (
                <form onSubmit={handleReset} className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="password">New Password</Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        minLength={8}
                        className="h-11 pr-10"
                        placeholder="Enter your new password"
                      />
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

                  {error && <p className="text-red-500 text-sm">{error}</p>}

                  <Button
                    type="submit"
                    disabled={submitting}
                    className="w-full h-11 text-base bg-[#F97316] hover:bg-[#F97316]/90"
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Resetting...
                      </>
                    ) : (
                      "Reset Password"
                    )}
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
