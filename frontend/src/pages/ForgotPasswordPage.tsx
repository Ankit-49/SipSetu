import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { motion } from "framer-motion";
import Lottie from "lottie-react";
import loginAnimation from "@/imports/Login.json";
import { Mail, CheckCircle2, Loader2, Eye, EyeOff } from "lucide-react";
import { VisualBackground } from "@/components/VisualBackground";
import { SipSetuLogo } from "@/components/SipSetuLogo";
import { usePasswordStrength } from "@/hooks/use-password-strength";
import { PasswordStrengthIndicator } from "@/components/PasswordStrengthIndicator";
import api from "@/lib/api";

type Step = "email" | "otp" | "password" | "done";

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [resetToken, setResetToken] = useState("");
  const passwordStrength = usePasswordStrength(password);

  const otpValue = otp.join("");

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email.trim()) {
      setError("Please enter your email address.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/auth/forgot-password", { email });
      setStep("otp");
      // Focus first OTP input after step change
      setTimeout(() => {
        const first = document.getElementById("otp-0");
        first?.focus();
      }, 100);
    } catch (err: any) {
      setError(err.response?.data?.error || "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (otpValue.length !== 6) {
      setError("Please enter the full 6-digit code.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post("/auth/verify-reset-otp", { email, otp: otpValue });
      setResetToken(res.data.reset_token);
      setStep("password");
    } catch (err: any) {
      setError(err.response?.data?.error || "Invalid OTP. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (passwordStrength.score < 40) {
      setError("Please choose a stronger password. Enable at least 3 requirements below.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/auth/reset-password", { token: resetToken, email, password });
      setStep("done");
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to reset password.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleOtpChange = (index: number, value: string) => {
    if (value.length > 1) {
      // Pasted full code
      const digits = value.replace(/\D/g, "").slice(0, 6).split("");
      const newOtp = [...otp];
      digits.forEach((d, i) => { if (i < 6) newOtp[i] = d; });
      setOtp(newOtp);
      const lastIdx = Math.min(digits.length, 5);
      document.getElementById(`otp-${lastIdx}`)?.focus();
      return;
    }
    if (value && !/^\d$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    if (value && index < 5) {
      document.getElementById(`otp-${index + 1}`)?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      document.getElementById(`otp-${index - 1}`)?.focus();
    }
  };

  const handleOtpPaste = (e: React.ClipboardEvent) => {
    const data = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (data.length === 6) {
      e.preventDefault();
      const newOtp = data.split("");
      setOtp(newOtp);
      document.getElementById("otp-5")?.focus();
    }
  };

  const handleResendOtp = async () => {
    setError("");
    setSubmitting(true);
    try {
      await api.post("/auth/forgot-password", { email });
      setOtp(["", "", "", "", "", ""]);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to resend OTP.");
    } finally {
      setSubmitting(false);
    }
  };

  const title = step === "email" ? "Reset your password"
    : step === "otp" ? "Enter verification code"
    : step === "password" ? "Set new password"
    : "Password reset!";

  const description = step === "email" ? "Enter your email address and we'll send you a code."
    : step === "otp" ? `We've sent a 6-digit code to ${email.replace(/(.{3}).+@/, "$1***@")}`
    : step === "password" ? "Choose a strong password for your account."
    : "Your password has been updated successfully.";

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
              <CardTitle className="text-2xl font-bold">{title}</CardTitle>
              <CardDescription>{description}</CardDescription>
            </CardHeader>
            <CardContent>
              {/* Step 1: Email */}
              {step === "email" && (
                <form onSubmit={handleSendOtp} className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input id="email" type="email" placeholder="name@example.com" value={email}
                        onChange={(e) => setEmail(e.target.value)} required className="h-11 pl-9" />
                    </div>
                  </div>
                  {error && <p className="text-red-500 text-sm">{error}</p>}
                  <Button type="submit" disabled={submitting} className="w-full h-11 text-base bg-[#F97316] hover:bg-[#F97316]/90">
                    {submitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Sending...</> : "Send Code"}
                  </Button>
                  <div className="text-center text-sm text-slate-600">
                    Remember your password?{" "}
                    <Link to="/login" className="font-medium text-[#1E3A5F] hover:underline">Sign in</Link>
                  </div>
                </form>
              )}

              {/* Step 2: OTP */}
              {step === "otp" && (
                <form onSubmit={handleVerifyOtp} className="space-y-6">
                  <div className="flex justify-center gap-2">
                    {otp.map((digit, i) => (
                      <Input
                        key={i}
                        id={`otp-${i}`}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={digit}
                        onChange={(e) => handleOtpChange(i, e.target.value)}
                        onKeyDown={(e) => handleOtpKeyDown(i, e)}
                        onPaste={i === 0 ? handleOtpPaste : undefined}
                        className="w-12 h-14 text-center text-xl font-bold border-slate-300 focus:border-[#F97316] focus:ring-[#F97316]"
                        required
                        autoComplete="one-time-code"
                      />
                    ))}
                  </div>
                  {error && <p className="text-red-500 text-sm text-center">{error}</p>}
                  <Button type="submit" disabled={submitting || otpValue.length !== 6} className="w-full h-11 text-base bg-[#F97316] hover:bg-[#F97316]/90">
                    {submitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Verifying...</> : "Verify Code"}
                  </Button>
                  <div className="text-center">
                    <button type="button" onClick={handleResendOtp} disabled={submitting}
                      className="text-sm font-medium text-[#1E3A5F] hover:underline">
                      Resend code
                    </button>
                  </div>
                </form>
              )}

              {/* Step 3: New Password */}
              {step === "password" && (
                <form onSubmit={handleResetPassword} className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="password">New Password</Label>
                    <div className="relative">
                      <Input id="password" type={showPassword ? "text" : "password"} value={password}
                        onChange={(e) => setPassword(e.target.value)} required minLength={8} className="h-11 pr-10" placeholder="Enter your new password" />
                      <button type="button" onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                        tabIndex={-1} aria-label={showPassword ? "Hide password" : "Show password"}>
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                    <PasswordStrengthIndicator strength={passwordStrength} />
                  </div>
                  {error && <p className="text-red-500 text-sm">{error}</p>}
                  <Button type="submit" disabled={submitting} className="w-full h-11 text-base bg-[#F97316] hover:bg-[#F97316]/90">
                    {submitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Resetting...</> : "Reset Password"}
                  </Button>
                </form>
              )}

              {/* Step 4: Done */}
              {step === "done" && (
                <div className="space-y-6 text-center">
                  <div className="flex justify-center">
                    <div className="h-16 w-16 rounded-full bg-green-100 flex items-center justify-center">
                      <CheckCircle2 className="h-8 w-8 text-green-600" />
                    </div>
                  </div>
                  <Button className="w-full h-11 text-base bg-[#1E3A5F] hover:bg-[#1E3A5F]/90"
                    onClick={() => navigate("/login", { replace: true })}>
                    Sign in with new password
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
