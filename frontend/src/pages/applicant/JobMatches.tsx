import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, MapPin, Clock, IndianRupee, Bookmark, Send } from "lucide-react";

const jobs = [
  { id: 1, title: "Frontend Developer", company: "TechCorp", match: 92, location: "Remote", type: "Full-time", skills: ["React", "TypeScript", "CSS"], salary: "₹18-24 LPA", posted: "2 days ago" },
  { id: 2, title: "React Engineer", company: "StartupXYZ", match: 87, location: "Bangalore", type: "Full-time", skills: ["React", "Redux", "Node.js"], salary: "₹15-20 LPA", posted: "3 days ago" },
  { id: 3, title: "UI Developer", company: "DesignHub", match: 81, location: "Mumbai", type: "Contract", skills: ["HTML", "CSS", "Figma"], salary: "₹10-14 LPA", posted: "5 days ago" },
  { id: 4, title: "Full Stack Developer", company: "InnovateCo", match: 75, location: "Pune", type: "Full-time", skills: ["React", "Node.js", "PostgreSQL"], salary: "₹20-28 LPA", posted: "1 week ago" },
  { id: 5, title: "JavaScript Developer", company: "CodeBase", match: 71, location: "Remote", type: "Part-time", skills: ["JavaScript", "Vue.js", "REST APIs"], salary: "₹8-12 LPA", posted: "1 week ago" },
  { id: 6, title: "Web Developer", company: "WebWorks", match: 68, location: "Delhi", type: "Full-time", skills: ["HTML", "CSS", "JavaScript", "React"], salary: "₹12-16 LPA", posted: "2 weeks ago" },
];

export default function ApplicantJobMatches() {
  const [search, setSearch] = useState("");

  const filteredJobs = jobs.filter(j => j.title.toLowerCase().includes(search.toLowerCase()) || j.company.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Job Matches</h1>
        <p className="text-slate-500 mt-1">Opportunities ranked by how well they match your extracted skills.</p>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input 
            placeholder="Search roles or companies..." 
            className="pl-9 bg-slate-50 border-slate-200"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-4">
          <Select defaultValue="all">
            <SelectTrigger className="w-[140px] bg-slate-50">
              <SelectValue placeholder="Location" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Locations</SelectItem>
              <SelectItem value="remote">Remote</SelectItem>
              <SelectItem value="bangalore">Bangalore</SelectItem>
              <SelectItem value="mumbai">Mumbai</SelectItem>
            </SelectContent>
          </Select>
          <Select defaultValue="all-types">
            <SelectTrigger className="w-[140px] bg-slate-50">
              <SelectValue placeholder="Job Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all-types">All Types</SelectItem>
              <SelectItem value="full">Full-time</SelectItem>
              <SelectItem value="contract">Contract</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredJobs.map((job, i) => (
          <Card key={job.id} className="hover:shadow-md transition-shadow duration-300 animate-in fade-in zoom-in-95" style={{ animationDelay: `${i * 50}ms`, animationFillMode: 'both' }}>
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center font-bold text-slate-600 text-lg">
                    {job.company.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-bold text-lg text-slate-900">{job.title}</h3>
                    <p className="text-slate-600 text-sm">{job.company}</p>
                  </div>
                </div>
                <Badge className={
                  job.match >= 85 ? "bg-green-100 text-green-700 hover:bg-green-100 border-none px-3 py-1 text-sm font-bold" :
                  job.match >= 70 ? "bg-orange-100 text-orange-700 hover:bg-orange-100 border-none px-3 py-1 text-sm font-bold" :
                  "bg-slate-100 text-slate-700 hover:bg-slate-100 border-none px-3 py-1 text-sm font-bold"
                }>
                  {job.match}% Match
                </Badge>
              </div>

              <div className="flex flex-wrap gap-3 mb-4">
                <div className="flex items-center text-xs text-slate-500 gap-1 bg-slate-50 px-2 py-1 rounded-md">
                  <MapPin className="h-3 w-3" /> {job.location}
                </div>
                <div className="flex items-center text-xs text-slate-500 gap-1 bg-slate-50 px-2 py-1 rounded-md">
                  <Clock className="h-3 w-3" /> {job.type}
                </div>
                <div className="flex items-center text-xs text-slate-500 gap-1 bg-slate-50 px-2 py-1 rounded-md">
                  <IndianRupee className="h-3 w-3" /> {job.salary}
                </div>
              </div>

              <div className="mb-6">
                <p className="text-xs font-semibold text-slate-900 uppercase tracking-wider mb-2">Required Skills</p>
                <div className="flex flex-wrap gap-2">
                  {job.skills.map(skill => (
                    <Badge key={skill} variant="secondary" className="bg-slate-100 text-slate-600 font-normal">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                <span className="text-xs text-slate-400">Posted {job.posted}</span>
                <div className="flex gap-2">
                  <Button variant="ghost" size="icon" className="text-slate-400 hover:text-slate-900">
                    <Bookmark className="h-4 w-4" />
                  </Button>
                  <Button className="bg-[#F97316] hover:bg-[#F97316]/90 text-white gap-2">
                    <Send className="h-4 w-4" /> Apply Now
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
