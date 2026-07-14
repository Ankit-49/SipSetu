import { useState } from "react";
import { Link, useNavigate } from "react-router";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import React from "react";
import { motion } from "framer-motion";
import Lottie from "lottie-react";
import loginAnimation from "@/imports/Login.json";
import { VisualBackground } from "@/components/VisualBackground";
import { SipSetuLogo } from "@/components/SipSetuLogo";

export default function RegisterPage() {
  const navigate = useNavigate();
  const searchParams = new URLSearchParams(window.location.search);
  const initialRole = searchParams.get('role') || 'applicant';
  const [role, setRole] = React.useState(initialRole);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    try {
      const response = await axios.post("http://127.0.0.1:5000/api/auth/register", {
        name,
        email,
        password,
        role
      });
      
      const userId = response.data.user_id;
      if (userId) {
        localStorage.setItem("user_id", userId);
        localStorage.setItem("user_role", role);
        localStorage.setItem("user_name", name);
      }
      
      // Auto-login after registration could go here
      // For now just redirect
      if (role === "applicant") {
        navigate("/applicant/dashboard");
      } else {
        navigate("/recruiter/dashboard");
      }
    } catch (err: any) {
      console.error("Registration error:", err);
      const message = err.response?.data?.error || err.message || "Registration failed. Please check if the backend is running.";
      setError(message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden selection:bg-[#F97316] selection:text-white">
      <VisualBackground />
      
      <div className="w-full max-w-5xl flex items-center justify-between gap-12 relative z-10">
        {/* Animation Side (Hidden on small screens) */}
        <motion.div 
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="flex-1 hidden md:flex items-center justify-center"
        >
          <div className="w-full max-w-lg drop-shadow-2xl">
            <Lottie
              animationData={loginAnimation}
              loop={true}
              autoplay={true}
              style={{ width: '100%', height: 'auto', transform: 'scaleX(-1)' }} // Mirror it for variety
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
          <Card className="shadow-2xl border-none bg-white/95 backdrop-blur-sm">
            <CardHeader className="space-y-3 text-center pb-6">
              <div className="flex justify-center mb-2">
                <SipSetuLogo className="text-4xl font-black tracking-tighter text-[#1E3A5F]" />
              </div>
              <CardTitle className="text-2xl font-bold">Create an account</CardTitle>
              <CardDescription>Join SipSetu to start your journey</CardDescription>
            </CardHeader>
            <CardContent>
          <form onSubmit={handleRegister} className="space-y-6">
            <div className="space-y-2">
              <Label className="text-slate-600 text-xs uppercase tracking-wider font-semibold">I am a</Label>
              <ToggleGroup 
                type="single" 
                value={role} 
                onValueChange={(v) => v && setRole(v)}
                className="justify-start w-full bg-slate-100 p-1 rounded-xl"
              >
                <ToggleGroupItem 
                  value="applicant" 
                  className={`flex-1 rounded-lg data-[state=on]:bg-[#1E3A5F] data-[state=on]:text-black ${role !== 'applicant' && 'hover:bg-slate-200 text-slate-600'}`}
                >
                  Job Seeker
                </ToggleGroupItem>
                <ToggleGroupItem 
                  value="recruiter" 
                  className={`flex-1 rounded-lg data-[state=on]:bg-[#1E3A5F] data-[state=on]:text-black ${role !== 'recruiter' && 'hover:bg-slate-200 text-slate-600'}`}
                >
                  Recruiter
                </ToggleGroupItem>
              </ToggleGroup>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input id="name" type="text" placeholder="John Doe" value={name} onChange={(e) => setName(e.target.value)} required className="h-11" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="name@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required className="h-11" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} className="h-11" />
              </div>
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}

            <Button type="submit" className="w-full h-11 text-base bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
              Create Account
            </Button>

            <div className="text-center text-sm text-slate-600">
              Already have an account?{" "}
              <Link to={`/login`} className="font-medium text-[#1E3A5F] hover:underline">
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
