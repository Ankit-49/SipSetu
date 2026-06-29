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
          <Select value={selectedJob} onValueChange={setSelectedJob}>
            <SelectTrigger className="w-[180px] bg-slate-50">
              <SelectValue placeholder="Filter by Job" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all-jobs">All Postings</SelectItem>
              {jobs.map((job) => (
                <SelectItem key={job.job_id} value={job.job_id}>{job.title}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={selectedScore} onValueChange={setSelectedScore}>
            <SelectTrigger className="w-[150px] bg-slate-50">
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

      {/* Candidate List */}
      <div className="space-y-4">
        {filteredCandidates.length === 0 ? (
          <Card className="p-8 text-center text-slate-500">No candidates found for the selected filters.</Card>
        ) : filteredCandidates.map((candidate, i) => (
          <Card key={candidate.ranking_id} className="overflow-hidden hover:shadow-md transition-all duration-300 animate-in fade-in slide-in-from-bottom-2" style={{ animationDelay: `${i * 50}ms` }}>
            <CardContent className="p-0">
              <div className="flex flex-col md:flex-row items-stretch">
                {/* Rank & Score (Left Sidebar) */}
                <div className="flex md:flex-col items-center justify-between md:justify-center md:w-32 p-4 md:p-6 bg-slate-50 border-b md:border-b-0 md:border-r border-slate-100 shrink-0">
                  <div className="text-sm font-bold text-slate-400 mb-1">RANK #{i + 1}</div>
                  <div className={`text-3xl font-extrabold ${candidate.matching_score >= 85 ? 'text-green-600' : candidate.matching_score >= 75 ? 'text-orange-500' : 'text-slate-600'}`}>
                    {candidate.matching_score}<span className="text-base">%</span>
                  </div>
                  <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mt-1">Match</div>
                </div>

                {/* Main Content */}
                <div className="flex-1 p-4 md:p-6 flex flex-col justify-center">
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
                    <div className="flex items-center gap-4">
                      <Avatar className="h-12 w-12 border border-slate-200">
                        <AvatarFallback className="bg-[#1E3A5F] text-white font-semibold">
                          {candidate.applicant_name.split(' ').map(n => n[0]).join('')}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <h3 className="font-bold text-lg text-slate-900">{candidate.applicant_name}</h3>
                        <div className="flex flex-wrap items-center gap-3 text-sm text-slate-500 mt-1">
                          <span className="flex items-center gap-1"><Briefcase className="h-3.5 w-3.5" /> {candidate.job_title}</span>
                          <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> {candidate.applicant_location || "Location not provided"}</span>
                          <span className="flex items-center gap-1 text-[#1E3A5F] font-medium">{candidate.applicant_email}</span>
                        </div>
                      </div>
                    </div>
                    <Badge className={candidate.matching_score >= 85 ? 'bg-green-100 text-green-700 hover:bg-green-100 border-none' : candidate.matching_score >= 75 ? 'bg-orange-100 text-orange-700 hover:bg-orange-100 border-none' : 'bg-slate-100 text-slate-700 hover:bg-slate-100 border-none'}>
                      {candidate.matching_score}% Match
                    </Badge>
                  </div>

                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mt-auto">
                    <div className="flex flex-wrap gap-2">
                      {candidate.resume_skills.map(skill => (
                        <Badge key={skill} variant="secondary" className="bg-slate-100 text-slate-700 font-normal border border-slate-200/50">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                    
                    <div className="flex items-center gap-2 shrink-0">
                      <Button variant="outline" size="icon" className="h-9 w-9 text-slate-500 border-slate-200" title="Email Candidate" onClick={() => window.location.href = `mailto:${candidate.applicant_email}`}>
                        <Mail className="h-4 w-4" />
                      </Button>
                      <Button className="h-9 bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 text-white gap-2">
                        <Briefcase className="h-4 w-4" /> {candidate.resume_skills.length} Skills
                      </Button>
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
