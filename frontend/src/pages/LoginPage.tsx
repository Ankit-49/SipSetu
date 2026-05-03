import { useState } from "react";
import { Link, useLocation } from "react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import React from "react";

export default function LoginPage() {
  const [, setLocation] = useLocation();
  const [role, setRole] = React.useState("applicant");

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (role === "applicant") {
      setLocation("/applicant/dashboard");
    } else {
      setLocation("/recruiter/dashboard");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4 selection:bg-[#F97316] selection:text-white">
      <Card className="w-full max-w-md shadow-xl border-slate-200">
        <CardHeader className="space-y-3 text-center pb-6">
          <div className="flex justify-center mb-2">
            <Link to="/" className="text-3xl font-bold tracking-tight text-[#1E3A5F]">SipSetu</Link>
          </div>
          <CardTitle className="text-2xl">Welcome back</CardTitle>
          <CardDescription>Enter your details to sign in to your account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-6">
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
                  className={`flex-1 rounded-lg data-[state=on]:bg-[#1E3A5F] data-[state=on]:text-white ${role !== 'applicant' && 'hover:bg-slate-200 text-slate-600'}`}
                >
                  Job Seeker
                </ToggleGroupItem>
                <ToggleGroupItem 
                  value="recruiter" 
                  className={`flex-1 rounded-lg data-[state=on]:bg-[#1E3A5F] data-[state=on]:text-white ${role !== 'recruiter' && 'hover:bg-slate-200 text-slate-600'}`}
                >
                  Recruiter
                </ToggleGroupItem>
              </ToggleGroup>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="name@example.com" required className="h-11" />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Password</Label>
                  <a href="#" className="text-sm font-medium text-[#F97316] hover:underline">Forgot password?</a>
                </div>
                <Input id="password" type="password" required className="h-11" />
              </div>
            </div>

            <Button type="submit" className="w-full h-11 text-base bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
              Sign In
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
    </div>
  );
}
