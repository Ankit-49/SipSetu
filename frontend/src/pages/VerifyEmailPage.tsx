import { useState, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, CheckCircle2, XCircle, Mail, ArrowLeft } from "lucide-react";
import { SipSetuLogo } from "@/components/SipSetuLogo";
import api from "@/lib/api";
import { useAuth } from "@/app/context/AuthContext";

type PageState = "form" | "loading" | "success" | "error";

export default function VerifyEmailPage() {
  const navigate = useNavigate();
  const { user, markEmailVerified } = useAuth();
  const [searchParams] = useSearchParams();
  const prefillEmail = searchParams.get("email") || "";

  const [email, setEmail] = useState(prefillEmail);
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [state, setState] = useState<PageState>(prefillEmail ? "form" : "form");
  const [message, setMessage] = useState("");
  const [resending, setResending] = useState(false);

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleOtpChange = (index: number, value: string) => {
    if (value && !/^\d$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const code = otp.join("");
    if (code.length !== 6) {
      setMessage("Please enter the full 6-digit verification code.");
      return;
    }
    if (!email) {
      setMessage("Please enter your email address.");
      return;
    }

    setState("loading");
    try {
      const response = await api.post("/auth/verify-email", { email, otp: code });
      markEmailVerified();
      setState("success");
      setMessage(response.data.message || "Email verified successfully!");
    } catch (err: any) {
      setState("error");
      setMessage(err?.response?.data?.error || "Verification failed. Please check your code and try again.");
    }
  };

  const handleResend = async () => {
    if (!email) return;
    setResending(true);
    try {
      // Resend needs auth — if the user isn't logged in, redirect to login
      await api.post("/auth/resend-verification");
      setOtp(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
      setMessage("A new verification code has been sent to your email.");
      setState("form");
    } catch (err: any) {
      if (err?.response?.status === 401) {
        setMessage("Session expired. Please log in to request a new code.");
      } else {
        setMessage(err?.response?.data?.error || "Failed to resend code.");
      }
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-orange-50 flex flex-col items-center justify-center p-4">
      <div className="mb-8">
        <SipSetuLogo className="text-3xl font-bold text-[#1E3A5F]" />
      </div>

      <Card className="w-full max-w-md shadow-xl border-0">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto h-14 w-14 rounded-full bg-orange-50 flex items-center justify-center mb-3">
            <Mail className="h-7 w-7 text-[#F97316]" />
          </div>
          <CardTitle className="text-xl font-bold text-slate-900">Verify your email</CardTitle>
          <CardDescription className="text-sm text-slate-500">
            Enter the 6-digit code sent to your email address
          </CardDescription>
        </CardHeader>

        <CardContent className="p-6 pt-2">
          {state === "success" && (
            <div className="py-8 space-y-6 text-center">
              <div className="mx-auto h-16 w-16 rounded-full bg-green-50 flex items-center justify-center">
                <CheckCircle2 className="h-8 w-8 text-green-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">Email Verified! 🎉</h2>
                <p className="text-sm text-slate-500">{message}</p>
              </div>
              <div className="pt-2">
                <Button
                  className="w-full bg-[#F97316] hover:bg-[#e8630e] text-white"
                  onClick={() =>
                    navigate(user?.role === "recruiter" ? "/recruiter/dashboard" : "/applicant/dashboard")
                  }
                >
                  Go to Dashboard
                </Button>
              </div>
            </div>
          )}

          {state === "loading" && (
            <div className="py-8 text-center space-y-6">
              <div className="mx-auto h-16 w-16 rounded-full bg-blue-50 flex items-center justify-center">
                <Loader2 className="h-8 w-8 text-[#1E3A5F] animate-spin" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">Verifying...</h2>
                <p className="text-sm text-slate-500">Please wait while we verify your code.</p>
              </div>
            </div>
          )}

          {(state === "form" || state === "error") && (
            <form onSubmit={handleSubmit} className="space-y-5 pt-2">
              {/* Email input */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-700">Email address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-9"
                    required
                    disabled={state === "loading"}
                  />
                </div>
              </div>

              {/* OTP input row */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-700">Verification code</label>
                <div className="flex gap-2 justify-center">
                  {otp.map((digit, i) => (
                    <Input
                      key={i}
                      ref={(el) => { inputRefs.current[i] = el; }}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleOtpChange(i, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(i, e)}
                      className="w-11 h-12 text-center text-lg font-bold [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                      disabled={state === "loading"}
                      autoFocus={i === 0}
                    />
                  ))}
                </div>
              </div>

              {/* Error message */}
              {state === "error" && message && (
                <div className="flex items-start gap-2 p-3 rounded-lg bg-red-50 border border-red-200">
                  <XCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                  <p className="text-sm text-red-700">{message}</p>
                </div>
              )}

              {/* Submit button */}
              <Button
                type="submit"
                className="w-full bg-[#F97316] hover:bg-[#e8630e] text-white gap-2"
                disabled={state === "loading"}
              >
                {state === "loading" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <CheckCircle2 className="h-4 w-4" />
                )}
                Verify Email
              </Button>

              {/* Resend / back links */}
              <div className="flex items-center justify-between text-sm pt-1">
                <button
                  type="button"
                  onClick={() =>
                    navigate(user
                      ? (user.role === "recruiter" ? "/recruiter/dashboard" : "/applicant/dashboard")
                      : "/login")
                  }
                  className="text-slate-500 hover:text-slate-700 flex items-center gap-1"
                >
                  <ArrowLeft className="h-3 w-3" /> Back to dashboard
                </button>
                <button
                  type="button"
                  onClick={handleResend}
                  disabled={resending || !email}
                  className="text-[#F97316] hover:text-[#e8630e] font-medium disabled:text-slate-300 disabled:cursor-not-allowed"
                >
                  {resending ? "Sending..." : "Resend code"}
                </button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
