import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle2, XCircle, Mail } from "lucide-react";
import { Link, useSearchParams } from "react-router";
import { useState, useEffect } from "react";
import { SipSetuLogo } from "@/components/SipSetuLogo";
import api from "@/lib/api";

type VerifyState = "loading" | "success" | "error";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [state, setState] = useState<VerifyState>("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setState("error");
      setMessage("No verification token found. Please check the link you received in your email.");
      return;
    }

    const verify = async () => {
      try {
        const response = await api.post("/auth/verify-email", { token });
        setState("success");
        setMessage(response.data.message || "Email verified successfully!");
      } catch (err: any) {
        setState("error");
        setMessage(err?.response?.data?.error || "Verification failed. The link may be expired or invalid.");
      }
    };
    verify();
  }, [token]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-orange-50 flex flex-col items-center justify-center p-4">
      <div className="mb-8">
        <SipSetuLogo className="text-3xl font-bold text-[#1E3A5F]" />
      </div>

      <Card className="w-full max-w-md shadow-xl border-0">
        <CardContent className="p-8 text-center">
          {state === "loading" && (
            <div className="py-8 space-y-6">
              <div className="mx-auto h-16 w-16 rounded-full bg-blue-50 flex items-center justify-center">
                <Loader2 className="h-8 w-8 text-[#1E3A5F] animate-spin" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">Verifying your email...</h2>
                <p className="text-sm text-slate-500">Please wait while we confirm your email address.</p>
              </div>
            </div>
          )}

          {state === "success" && (
            <div className="py-8 space-y-6">
              <div className="mx-auto h-16 w-16 rounded-full bg-green-50 flex items-center justify-center">
                <CheckCircle2 className="h-8 w-8 text-green-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">Email Verified! 🎉</h2>
                <p className="text-sm text-slate-500">{message}</p>
              </div>
              <div className="pt-2 space-y-3">
                <Link to="/login">
                  <Button className="w-full bg-[#F97316] hover:bg-[#e8630e] text-white">
                    Sign In
                  </Button>
                </Link>
              </div>
            </div>
          )}

          {state === "error" && (
            <div className="py-8 space-y-6">
              <div className="mx-auto h-16 w-16 rounded-full bg-red-50 flex items-center justify-center">
                <XCircle className="h-8 w-8 text-red-500" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">Verification Failed</h2>
                <p className="text-sm text-slate-500">{message}</p>
              </div>
              <div className="pt-2 space-y-3">
                <Link to="/login">
                  <Button variant="outline" className="w-full gap-2">
                    <Mail className="h-4 w-4" /> Go to Login
                  </Button>
                </Link>
                <p className="text-xs text-slate-400">
                  Need a new verification link? Sign in and use the option to resend verification.
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
