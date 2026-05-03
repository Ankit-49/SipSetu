import { useState } from "react";
import { Link, useLocation } from "react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import React from "react";

export default function RegisterPage() {
  const [, setLocation] = useLocation();
  const searchParams = new URLSearchParams(window.location.search);
  const initialRole = searchParams.get('role') || 'applicant';
  const [role, setRole] = React.useState(initialRole);

  const handleRegister = (e: React.FormEvent) => {
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
          <CardTitle className="text-2xl">Create an account</CardTitle>
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
                <Label htmlFor="name">Full Name</Label>
                <Input id="name" type="text" placeholder="John Doe" required className="h-11" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="name@example.com" required className="h-11" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" required className="h-11" />
              </div>
            </div>

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
    </div>
  );
}
