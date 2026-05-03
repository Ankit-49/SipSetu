import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Search, MapPin, Briefcase, ChevronDown, FileText, Mail } from "lucide-react";

const candidates = [
  { id: 1, name: "Priya Sharma", email: "priya@email.com", appliedFor: "Frontend Developer", match: 92, skills: ["React", "TypeScript", "CSS", "Git"], experience: "3 years", location: "Mumbai", status: "Shortlisted" },
  { id: 2, name: "Arjun Nair", email: "arjun@email.com", appliedFor: "Full Stack Developer", match: 88, skills: ["Node.js", "React", "PostgreSQL", "Docker"], experience: "4 years", location: "Bangalore", status: "In Review" },
  { id: 3, name: "Sneha Patel", email: "sneha@email.com", appliedFor: "UI Developer", match: 84, skills: ["CSS", "Figma", "HTML", "JavaScript"], experience: "2 years", location: "Pune", status: "Applied" },
  { id: 4, name: "Vikram Singh", email: "vikram@email.com", appliedFor: "Frontend Developer", match: 79, skills: ["React", "JavaScript", "Webpack"], experience: "2 years", location: "Delhi", status: "Applied" },
  { id: 5, name: "Meera Krishnan", email: "meera@email.com", appliedFor: "Backend Engineer", match: 76, skills: ["Node.js", "Express", "MongoDB"], experience: "3 years", location: "Chennai", status: "Rejected" },
  { id: 6, name: "Rohit Gupta", email: "rohit@email.com", appliedFor: "Full Stack Developer", match: 73, skills: ["React", "Node.js", "MySQL"], experience: "2 years", location: "Hyderabad", status: "Applied" },
];

export default function RecruiterCandidates() {
  const [search, setSearch] = useState("");

  const filteredCandidates = candidates.filter(c => 
    c.name.toLowerCase().includes(search.toLowerCase()) || 
    c.skills.some(s => s.toLowerCase().includes(search.toLowerCase()))
  );

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Shortlisted': return <Badge className="bg-green-100 text-green-700 hover:bg-green-100 border-none">Shortlisted</Badge>;
      case 'In Review': return <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100 border-none">In Review</Badge>;
      case 'Rejected': return <Badge className="bg-red-100 text-red-700 hover:bg-red-100 border-none">Rejected</Badge>;
      default: return <Badge className="bg-slate-100 text-slate-700 hover:bg-slate-100 border-none">Applied</Badge>;
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Ranked Candidates</h1>
        <p className="text-slate-500 mt-1">Applicants automatically scored and ranked against your job requirements.</p>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input 
            placeholder="Search candidates or skills..." 
            className="pl-9 bg-slate-50 border-slate-200"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-4">
          <Select defaultValue="all-jobs">
            <SelectTrigger className="w-[180px] bg-slate-50">
              <SelectValue placeholder="Filter by Job" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all-jobs">All Postings</SelectItem>
              <SelectItem value="frontend">Frontend Developer</SelectItem>
              <SelectItem value="fullstack">Full Stack Developer</SelectItem>
            </SelectContent>
          </Select>
          <Select defaultValue="all-status">
            <SelectTrigger className="w-[150px] bg-slate-50">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all-status">Any Status</SelectItem>
              <SelectItem value="applied">Applied</SelectItem>
              <SelectItem value="review">In Review</SelectItem>
              <SelectItem value="shortlisted">Shortlisted</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Candidate List */}
      <div className="space-y-4">
        {filteredCandidates.map((candidate, i) => (
          <Card key={candidate.id} className="overflow-hidden hover:shadow-md transition-all duration-300 animate-in fade-in slide-in-from-bottom-2" style={{ animationDelay: `${i * 50}ms` }}>
            <CardContent className="p-0">
              <div className="flex flex-col md:flex-row items-stretch">
                {/* Rank & Score (Left Sidebar) */}
                <div className="flex md:flex-col items-center justify-between md:justify-center md:w-32 p-4 md:p-6 bg-slate-50 border-b md:border-b-0 md:border-r border-slate-100 shrink-0">
                  <div className="text-sm font-bold text-slate-400 mb-1">RANK #{i + 1}</div>
                  <div className={`text-3xl font-extrabold ${candidate.match >= 85 ? 'text-green-600' : candidate.match >= 75 ? 'text-orange-500' : 'text-slate-600'}`}>
                    {candidate.match}<span className="text-base">%</span>
                  </div>
                  <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mt-1">Match</div>
                </div>

                {/* Main Content */}
                <div className="flex-1 p-4 md:p-6 flex flex-col justify-center">
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
                    <div className="flex items-center gap-4">
                      <Avatar className="h-12 w-12 border border-slate-200">
                        <AvatarFallback className="bg-[#1E3A5F] text-white font-semibold">
                          {candidate.name.split(' ').map(n => n[0]).join('')}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <h3 className="font-bold text-lg text-slate-900">{candidate.name}</h3>
                        <div className="flex flex-wrap items-center gap-3 text-sm text-slate-500 mt-1">
                          <span className="flex items-center gap-1"><Briefcase className="h-3.5 w-3.5" /> {candidate.appliedFor}</span>
                          <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> {candidate.location}</span>
                          <span className="flex items-center gap-1 text-[#1E3A5F] font-medium">{candidate.experience} exp.</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between md:justify-end md:w-auto gap-3">
                      {getStatusBadge(candidate.status)}
                    </div>
                  </div>

                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mt-auto">
                    <div className="flex flex-wrap gap-2">
                      {candidate.skills.map(skill => (
                        <Badge key={skill} variant="secondary" className="bg-slate-100 text-slate-700 font-normal border border-slate-200/50">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                    
                    <div className="flex items-center gap-2 shrink-0">
                      <Button variant="outline" size="icon" className="h-9 w-9 text-slate-500 border-slate-200" title="Email Candidate">
                        <Mail className="h-4 w-4" />
                      </Button>
                      <Button className="h-9 bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 text-white gap-2">
                        <FileText className="h-4 w-4" /> View Resume
                      </Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="outline" className="h-9 gap-1 text-slate-700 border-slate-200">
                            Status <ChevronDown className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem className="text-slate-700">Mark as Applied</DropdownMenuItem>
                          <DropdownMenuItem className="text-blue-600 font-medium">Move to Review</DropdownMenuItem>
                          <DropdownMenuItem className="text-green-600 font-medium">Shortlist</DropdownMenuItem>
                          <DropdownMenuItem className="text-red-600">Reject</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
