import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Target, FileText, Briefcase, Eye, ChevronRight } from "lucide-react";
import { Link } from "react-router";

const matchScore = 78;
const topJobs = [
  { id: 1, title: "Frontend Developer", company: "TechCorp", match: 92, location: "Remote" },
  { id: 2, title: "React Engineer", company: "StartupXYZ", match: 87, location: "Bangalore" },
  { id: 3, title: "UI Developer", company: "DesignHub", match: 81, location: "Mumbai" },
  { id: 4, title: "Full Stack Dev", company: "InnovateCo", match: 75, location: "Pune" },
];
const resumeStrength = 65;
const skillGaps = ["TypeScript", "Node.js", "System Design"];

export default function ApplicantDashboardHome() {
  const date = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Welcome back, Priya 👋</h1>
        <p className="text-slate-500 mt-1">{date}</p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Avg. Match Score</p>
              <p className="text-3xl font-bold text-[#F97316]">{matchScore}%</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-orange-50 flex items-center justify-center">
              <Target className="h-6 w-6 text-[#F97316]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex flex-col justify-center space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-500">Resume Strength</p>
              <FileText className="h-5 w-5 text-blue-500" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-bold text-slate-900">{resumeStrength}/100</span>
              </div>
              <Progress value={resumeStrength} className="h-2 bg-slate-100" indicatorClassName="bg-[#1E3A5F]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Jobs Applied</p>
              <p className="text-3xl font-bold text-slate-900">12</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center">
              <Briefcase className="h-6 w-6 text-slate-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Profile Views</p>
              <p className="text-3xl font-bold text-slate-900">48</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center">
              <Eye className="h-6 w-6 text-slate-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Top Matches */}
        <Card className="lg:col-span-2 flex flex-col">
          <CardHeader className="flex flex-row items-center justify-between pb-2 border-b border-slate-100">
            <CardTitle className="text-lg font-bold">Top Job Matches</CardTitle>
            <Link to="/applicant/matches">
              <Button variant="ghost" size="sm" className="text-slate-500 hover:text-[#1E3A5F]">
                View All <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0 flex-1">
            <div className="divide-y divide-slate-100">
              {topJobs.map((job) => (
                <div key={job.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                  <div className="space-y-1">
                    <h3 className="font-semibold text-slate-900">{job.title}</h3>
                    <p className="text-sm text-slate-500">{job.company} • {job.location}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge className={job.match >= 85 ? 'bg-green-100 text-green-700 hover:bg-green-100' : 'bg-orange-100 text-orange-700 hover:bg-orange-100'}>
                      {job.match}% Match
                    </Badge>
                    <Button variant="outline" size="sm">View</Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Right Column */}
        <div className="space-y-8">
          {/* Skill Gap */}
          <Card>
            <CardHeader className="pb-2 border-b border-slate-100">
              <CardTitle className="text-lg font-bold">Critical Skill Gaps</CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-6 space-y-6">
              <p className="text-sm text-slate-600">Top missing skills for roles you're matching with:</p>
              <div className="flex flex-wrap gap-2">
                {skillGaps.map(skill => (
                  <Badge key={skill} variant="secondary" className="bg-slate-100 text-slate-700 hover:bg-slate-200">
                    {skill}
                  </Badge>
                ))}
              </div>
              <Link to="/applicant/skill-gap">
                <Button variant="outline" className="w-full text-[#1E3A5F] border-[#1E3A5F]/20 hover:bg-blue-50">
                  View Full Analysis
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Activity */}
          <Card>
            <CardHeader className="pb-2 border-b border-slate-100">
              <CardTitle className="text-lg font-bold">Recent Activity</CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-6">
              <div className="space-y-4">
                <div className="flex gap-3 items-start">
                  <div className="h-8 w-8 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Briefcase className="h-4 w-4 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">Applied for Frontend Developer</p>
                    <p className="text-xs text-slate-500">TechCorp • 2 days ago</p>
                  </div>
                </div>
                <div className="flex gap-3 items-start">
                  <div className="h-8 w-8 rounded-full bg-green-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Eye className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">Profile viewed</p>
                    <p className="text-xs text-slate-500">StartupXYZ • 3 days ago</p>
                  </div>
                </div>
                <div className="flex gap-3 items-start">
                  <div className="h-8 w-8 rounded-full bg-orange-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <FileText className="h-4 w-4 text-orange-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">Resume updated</p>
                    <p className="text-xs text-slate-500">1 week ago</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
