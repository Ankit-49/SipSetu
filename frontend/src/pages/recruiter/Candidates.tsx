import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Search, MapPin, Briefcase, Mail, Loader2 } from "lucide-react";
import axios from "axios";

const API = "http://localhost:5000/api";

type Candidate = {
  ranking_id: string;
  job_id: string;
  job_title: string;
  applicant_id: string;
  applicant_name: string;
  applicant_email: string;
  applicant_location: string;
  matching_score: number;
  resume_skills: string[];
};

export default function RecruiterCandidates() {
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState("all-jobs");
  const [selectedScore, setSelectedScore] = useState("all-scores");
  const [jobs, setJobs] = useState<{ job_id: string; title: string }[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);

  useEffect(() => {
    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setLoading(false);
      return;
    }

    const fetchCandidates = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        params.set("per_page", "50");
        if (selectedJob !== "all-jobs") params.set("job_id", selectedJob);
        if (selectedScore !== "all-scores") params.set("min_score", selectedScore);

        const response = await axios.get(`${API}/recruiters/${userId}/candidates?${params.toString()}`);
        setCandidates(response.data.candidates || []);
        setJobs(response.data.jobs || []);
      } catch (err) {
        console.error("Failed to load recruiter candidates", err);
        setCandidates([]);
      } finally {
        setLoading(false);
      }
    };

    fetchCandidates();
  }, [selectedJob, selectedScore]);

  const filteredCandidates = candidates.filter((c) =>
    c.applicant_name.toLowerCase().includes(search.toLowerCase()) ||
    c.applicant_email.toLowerCase().includes(search.toLowerCase()) ||
    c.job_title.toLowerCase().includes(search.toLowerCase()) ||
    c.resume_skills.some((s) => s.toLowerCase().includes(search.toLowerCase()))
  );

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
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Ranked Candidates</h1>
        <p className="text-slate-500 mt-1">Applicants automatically scored and ranked against your job requirements.</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Sidebar */}
        <div className="w-full lg:w-64 shrink-0 space-y-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-2">
            <h3 className="font-semibold text-slate-900 mb-2">Job Postings</h3>
            <Button 
                variant={selectedJob === "all-jobs" ? "default" : "ghost"} 
                className={`justify-start ${selectedJob === "all-jobs" ? "bg-[#1E3A5F] text-white hover:bg-[#1E3A5F]/90" : ""}`}
                onClick={() => setSelectedJob("all-jobs")}
            >
                All Postings
            </Button>
            {jobs.map((job) => (
                <Button 
                    key={job.job_id} 
                    variant={selectedJob === job.job_id ? "default" : "ghost"} 
                    className={`justify-start text-left truncate w-full ${selectedJob === job.job_id ? "bg-[#1E3A5F] text-white hover:bg-[#1E3A5F]/90" : ""}`}
                    onClick={() => setSelectedJob(job.job_id)}
                    title={job.title}
                >
                    <span className="truncate">{job.title}</span>
                </Button>
            ))}
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-4">
             <h3 className="font-semibold text-slate-900">Filters</h3>
             <div>
                <label className="text-xs font-medium text-slate-500 mb-1 block">Minimum Match Score</label>
                <Select value={selectedScore} onValueChange={setSelectedScore}>
                  <SelectTrigger className="w-full bg-slate-50">
                    <SelectValue placeholder="Min Score" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all-scores">Any Score</SelectItem>
                    <SelectItem value="70">70%+</SelectItem>
                    <SelectItem value="80">80%+</SelectItem>
                    <SelectItem value="90">90%+</SelectItem>
                  </SelectContent>
                </Select>
             </div>
          </div>
        </div>

        {/* Main Content (Candidate List) */}
        <div className="flex-1 space-y-4">
          {selectedJob === "all-jobs" ? (
            <Card className="p-8 text-center text-slate-500 flex flex-col items-center justify-center min-h-[200px]">
              <Briefcase className="h-8 w-8 text-slate-400 mb-2" />
              <p className="font-medium text-slate-700">No Job Selected</p>
              <p className="text-sm mt-1">Please select a job posting from the sidebar to view ranked candidates.</p>
            </Card>
          ) : filteredCandidates.length === 0 ? (
            <Card className="p-8 text-center text-slate-500">No candidates found for the selected filters.</Card>
          ) : filteredCandidates.map((candidate, i) => {
            const score = candidate.matching_score;
            
            const radius = 30;
            const circumference = 2 * Math.PI * radius;
            const strokeDashoffset = circumference - (score / 100) * circumference;
            
            let strokeColor = "text-red-500";
            if (score >= 90) strokeColor = "text-green-500";
            else if (score >= 80) strokeColor = "text-lime-500";
            else if (score >= 70) strokeColor = "text-yellow-500";
            else if (score >= 50) strokeColor = "text-orange-500";

            let rankColor = "text-slate-500 bg-slate-100";
            let rankText = `RANK #${i + 1}`;
            if (i === 0) { rankColor = "text-yellow-700 bg-yellow-100 border-yellow-300"; rankText = "1st Place"; }
            else if (i === 1) { rankColor = "text-slate-700 bg-slate-200 border-slate-400"; rankText = "2nd Place"; }
            else if (i === 2) { rankColor = "text-amber-800 bg-amber-100 border-amber-300"; rankText = "3rd Place"; }

            return (
            <Card key={candidate.ranking_id} className="overflow-hidden hover:shadow-md transition-all duration-300 animate-in fade-in slide-in-from-bottom-2" style={{ animationDelay: `${i * 50}ms` }}>
              <CardContent className="p-0 flex flex-row items-stretch">
                {/* Left: Rank */}
                <div className="w-24 md:w-32 p-4 flex flex-col items-center justify-center bg-slate-50 border-r border-slate-100 shrink-0">
                  {selectedJob !== "all-jobs" ? (
                    <div className={`text-center font-bold px-3 py-1 rounded-full border text-xs md:text-sm ${rankColor}`}>
                      {rankText}
                    </div>
                  ) : (
                    <div className="text-sm font-bold text-slate-400">#{i + 1}</div>
                  )}
                </div>

                {/* Middle: Applicant Details */}
                <div className="flex-1 p-4 md:p-6 flex flex-col justify-center min-w-0">
                  <div className="flex items-start gap-4">
                    <Avatar className="h-12 w-12 border border-slate-200 shrink-0 mt-1">
                      <AvatarFallback className="bg-[#1E3A5F] text-white font-semibold">
                        {candidate.applicant_name.split(' ').map(n => n[0]).join('')}
                      </AvatarFallback>
                    </Avatar>
                    <div className="min-w-0 flex-1">
                      <h3 className="font-bold text-lg text-slate-900 truncate">{candidate.applicant_name}</h3>
                      {(candidate as any).applicant_description && (
                        <p className="text-sm text-slate-600 mt-1 line-clamp-2">
                          {(candidate as any).applicant_description}
                        </p>
                      )}
                      <div className="flex flex-wrap items-center gap-3 text-sm text-slate-500 mt-2">
                        <span className="flex items-center gap-1 text-[#1E3A5F] font-medium"><Mail className="h-3.5 w-3.5" /> {candidate.applicant_email}</span>
                        <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> {candidate.applicant_location || "Not provided"}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right: Match Score */}
                <div className="w-28 md:w-32 p-4 flex flex-col items-center justify-center border-l border-slate-100 shrink-0 bg-white">
                   <div className="relative inline-flex items-center justify-center">
                     <svg className="transform -rotate-90 w-16 h-16 md:w-20 md:h-20">
                       <circle cx="50%" cy="50%" r={radius} stroke="currentColor" strokeWidth="6" fill="transparent" className="text-slate-100" />
                       <circle 
                         cx="50%" cy="50%" r={radius} stroke="currentColor" strokeWidth="6" fill="transparent" 
                         strokeDasharray={circumference} strokeDashoffset={strokeDashoffset} 
                         className={`${strokeColor} transition-all duration-1000 ease-out`} 
                         strokeLinecap="round" 
                       />
                     </svg>
                     <div className="absolute flex flex-col items-center justify-center">
                       <span className="text-sm md:text-lg font-bold text-slate-700">{Math.round(score)}%</span>
                     </div>
                   </div>
                   <div className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-2">Match</div>
                </div>
              </CardContent>
            </Card>
          )})}
        </div>
      </div>
    </div>
  );
}
