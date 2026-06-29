import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, MapPin, Clock, Briefcase, Send, Loader2, UploadCloud } from "lucide-react";
import { Link } from "react-router";
import axios from "axios";

const API = "http://localhost:5000/api";

export default function ApplicantJobMatches() {
  const [search, setSearch] = useState("");
  const [locationFilter, setLocationFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [jobs, setJobs] = useState<any[]>([]);
  const [hasResume, setHasResume] = useState(true);

  useEffect(() => {
    const userId = localStorage.getItem("user_id");
    if (!userId) { setLoading(false); return; }

    const fetchMatches = async () => {
      try {
        const res = await axios.get(`${API}/applicants/${userId}/matched-jobs?per_page=50`);
        setJobs(res.data.matched_jobs || []);
        if (res.data.resume_id === null) setHasResume(false);
      } catch (err) {
        console.error("Failed to load job matches", err);
        setHasResume(false);
      } finally {
        setLoading(false);
      }
    };
    fetchMatches();
  }, []);

  const filteredJobs = jobs.filter(j => {
    const matchesSearch = j.title.toLowerCase().includes(search.toLowerCase())
      || (j.recruiter_company || "").toLowerCase().includes(search.toLowerCase());
    const matchesLocation = locationFilter === "all"
      || (j.location || "").toLowerCase().includes(locationFilter.toLowerCase());
    return matchesSearch && matchesLocation;
  });

  const locations = Array.from(new Set(jobs.map(j => j.location).filter(Boolean)));

  const formatSalary = (job: any) => {
    if (job.salary_min && job.salary_max) return `Rs.${Math.round(job.salary_min)}-${Math.round(job.salary_max)} LPA`;
    if (job.salary_min) return `Rs.${Math.round(job.salary_min)}+ LPA`;
    return null;
  };

  const formatPosted = (dateStr: string) => {
    if (!dateStr) return "";
    const diff = Date.now() - new Date(dateStr).getTime();
    const days = Math.floor(diff / 86400000);
    if (days === 0) return "Today";
    if (days === 1) return "1 day ago";
    if (days < 7) return `${days} days ago`;
    if (days < 14) return "1 week ago";
    return `${Math.floor(days / 7)} weeks ago`;
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#F97316]" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Job Matches</h1>
        <p className="text-slate-500 mt-1">Opportunities ranked by how well they match your extracted skills.</p>
      </div>

      {!hasResume && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
              <UploadCloud className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-bold text-blue-900">Upload your resume to see matches</h3>
              <p className="text-sm text-blue-700">Our AI will calculate your match score for each job.</p>
            </div>
          </div>
          <Link to="/applicant/resume">
            <Button className="bg-blue-600 hover:bg-blue-700 text-white gap-2 whitespace-nowrap">
              <UploadCloud className="h-4 w-4" /> Upload Resume
            </Button>
          </Link>
        </div>
      )}

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
          <Select value={locationFilter} onValueChange={setLocationFilter}>
            <SelectTrigger className="w-[160px] bg-slate-50">
              <SelectValue placeholder="Location" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Locations</SelectItem>
              {locations.map(loc => (
                <SelectItem key={loc} value={loc}>{loc}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Grid */}
      {filteredJobs.length === 0 ? (
        <div className="text-center py-16 text-slate-500">
          <Briefcase className="h-12 w-12 mx-auto text-slate-200 mb-4" />
          <p className="font-medium">{hasResume ? "No job matches found." : "Upload a resume to unlock job matches."}</p>
          <p className="text-sm mt-1">
            {hasResume ? "Try adjusting your filters or check back when new jobs are posted." : ""}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredJobs.map((job, i) => (
            <Card key={job.job_id} className="hover:shadow-md transition-shadow duration-300 animate-in fade-in zoom-in-95" style={{ animationDelay: `${i * 50}ms`, animationFillMode: 'both' }}>
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center font-bold text-slate-600 text-lg">
                      {(job.recruiter_company || job.recruiter_name || "?").charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-bold text-lg text-slate-900">{job.title}</h3>
                      <p className="text-slate-600 text-sm">{job.recruiter_company || job.recruiter_name}</p>
                    </div>
                  </div>
                  <Badge className={
                    job.matching_score >= 85 ? "bg-green-100 text-green-700 hover:bg-green-100 border-none px-3 py-1 text-sm font-bold" :
                    job.matching_score >= 70 ? "bg-orange-100 text-orange-700 hover:bg-orange-100 border-none px-3 py-1 text-sm font-bold" :
                    "bg-slate-100 text-slate-700 hover:bg-slate-100 border-none px-3 py-1 text-sm font-bold"
                  }>
                    {job.matching_score}% Match
                  </Badge>
                </div>

                <div className="flex flex-wrap gap-3 mb-4">
                  {job.location && (
                    <div className="flex items-center text-xs text-slate-500 gap-1 bg-slate-50 px-2 py-1 rounded-md">
                      <MapPin className="h-3 w-3" /> {job.location}
                    </div>
                  )}
                  {job.job_type && (
                    <div className="flex items-center text-xs text-slate-500 gap-1 bg-slate-50 px-2 py-1 rounded-md">
                      <Clock className="h-3 w-3" /> {job.job_type}
                    </div>
                  )}
                  {formatSalary(job) && (
                    <div className="flex items-center text-xs text-slate-500 gap-1 bg-slate-50 px-2 py-1 rounded-md">
                      {formatSalary(job)}
                    </div>
                  )}
                </div>

                <div className="mb-6">
                  <p className="text-xs font-semibold text-slate-900 uppercase tracking-wider mb-2">Required Skills</p>
                  <div className="flex flex-wrap gap-2">
                    {job.skills.length > 0 ? job.skills.map((skill: string) => (
                      <Badge key={skill} variant="secondary" className="bg-slate-100 text-slate-600 font-normal">
                        {skill}
                      </Badge>
                    )) : <span className="text-xs text-slate-400">No skills listed</span>}
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                  <span className="text-xs text-slate-400">{formatPosted(job.created_at)}</span>
                  <Button className="bg-[#F97316] hover:bg-[#F97316]/90 text-white gap-2">
                    <Send className="h-4 w-4" /> Apply Now
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
