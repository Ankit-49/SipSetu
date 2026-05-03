import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Briefcase, Users, UserCheck, TrendingUp, ChevronRight, FileText } from "lucide-react";
import { Link } from "react-router";

const stats = { activePostings: 5, totalApplicants: 143, shortlisted: 28, hiresThisMonth: 3 };
const topCandidates = [
  { id: 1, name: "Priya Sharma", role: "Frontend Developer", match: 92, skills: ["React", "TypeScript"], status: "Shortlisted" },
  { id: 2, name: "Arjun Nair", role: "Full Stack Developer", match: 88, skills: ["Node.js", "React", "PostgreSQL"], status: "In Review" },
  { id: 3, name: "Sneha Patel", role: "UI Developer", match: 84, skills: ["CSS", "Figma", "HTML"], status: "Applied" },
];
const recentPostings = [
  { id: 1, title: "Frontend Developer", applicants: 47, posted: "3 days ago", status: "Active" },
  { id: 2, title: "Backend Engineer", applicants: 31, posted: "5 days ago", status: "Active" },
  { id: 3, title: "DevOps Engineer", applicants: 22, posted: "1 week ago", status: "Active" },
];

export default function RecruiterDashboardHome() {
  const date = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Good morning, Rahul 👋</h1>
          <p className="text-slate-500 mt-1">{date}</p>
        </div>
        <Link to="/recruiter/post-job">
          <Button className="bg-[#F97316] hover:bg-[#F97316]/90 text-white shadow-lg shadow-orange-500/20">
            + Post New Job
          </Button>
        </Link>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Active Postings</p>
              <p className="text-3xl font-bold text-slate-900">{stats.activePostings}</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-blue-50 flex items-center justify-center">
              <Briefcase className="h-6 w-6 text-[#1E3A5F]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Total Applicants</p>
              <p className="text-3xl font-bold text-slate-900">{stats.totalApplicants}</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center">
              <Users className="h-6 w-6 text-slate-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Shortlisted</p>
              <p className="text-3xl font-bold text-[#F97316]">{stats.shortlisted}</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-orange-50 flex items-center justify-center">
              <UserCheck className="h-6 w-6 text-[#F97316]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Hires This Month</p>
              <div className="flex items-center gap-2">
                <p className="text-3xl font-bold text-slate-900">{stats.hiresThisMonth}</p>
                <TrendingUp className="h-4 w-4 text-green-500" />
              </div>
            </div>
            <div className="h-12 w-12 rounded-full bg-green-50 flex items-center justify-center">
              <Users className="h-6 w-6 text-green-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Top Candidates */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2 border-b border-slate-100">
            <CardTitle className="text-lg font-bold">Top Matches (AI Ranked)</CardTitle>
            <Link to="/recruiter/candidates">
              <Button variant="ghost" size="sm" className="text-slate-500 hover:text-[#1E3A5F]">
                View All <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100">
              {topCandidates.map((candidate) => (
                <div key={candidate.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors group">
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-full bg-[#1E3A5F] text-white flex items-center justify-center font-semibold text-sm">
                      {candidate.name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-slate-900">{candidate.name}</h3>
                        <Badge className="bg-green-100 text-green-700 hover:bg-green-100 border-none h-5 text-[10px]">
                          {candidate.match}% Match
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-500">{candidate.role}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="hidden md:flex gap-1">
                      {candidate.skills.map(s => <Badge key={s} variant="outline" className="text-xs text-slate-500">{s}</Badge>)}
                    </div>
                    <Badge variant="secondary" className={
                      candidate.status === 'Shortlisted' ? 'bg-green-50 text-green-700' :
                      candidate.status === 'In Review' ? 'bg-blue-50 text-blue-700' :
                      'bg-slate-100 text-slate-700'
                    }>
                      {candidate.status}
                    </Badge>
                    <Button variant="outline" size="sm" className="gap-2">
                      <FileText className="h-3.5 w-3.5" /> Resume
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Postings */}
        <Card>
          <CardHeader className="pb-2 border-b border-slate-100">
            <CardTitle className="text-lg font-bold">Active Job Postings</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100">
              {recentPostings.map(post => (
                <div key={post.id} className="p-4 hover:bg-slate-50 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-semibold text-slate-900">{post.title}</h4>
                    <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50 border-blue-200">Active</Badge>
                  </div>
                  <div className="flex justify-between items-center text-sm text-slate-500">
                    <span className="flex items-center gap-1.5"><Users className="h-3.5 w-3.5" /> {post.applicants} Applicants</span>
                    <span>{post.posted}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="p-3 bg-slate-50 border-t border-slate-100 text-center rounded-b-xl">
              <Link to="/recruiter/dashboard" className="text-sm font-medium text-[#1E3A5F] hover:underline">
                View all postings
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
