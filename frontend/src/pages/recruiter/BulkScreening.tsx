import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { 
  UploadCloud, 
  Trash2, 
  Sparkles, 
  AlertCircle, 
  FileText, 
  ChevronRight, 
  Award,
  BookOpen,
  Briefcase,
  AlertTriangle,
  UserCheck,
  RefreshCw
} from "lucide-react";
import api, { API_BASE } from "@/lib/api";
import confetti from "canvas-confetti";

interface CandidateResult {
  filename: string;
  candidate_name: string;
  match_score: number;
  skills_score: number;
  content_score: number;
  extracted_skills: string[];
  matched_skills: string[];
  missing_skills: string[];
  text_snippet: string;
  raw_text: string;
  error?: string;
}

interface JobPosting {
  job_id: string;
  title: string;
  skills: string[];
  experience_level?: string;
}

export default function RecruiterBulkScreening() {
  // Mode selection
  const [jobMode, setJobMode] = useState<"posted" | "custom">("posted");
  const [activeJobs, setActiveJobs] = useState<JobPosting[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  
  // Custom job fields
  const [customTitle, setCustomTitle] = useState("");
  const [customSkills, setCustomSkills] = useState("");
  const [customDescription, setCustomDescription] = useState("");

  // File upload state
  const [files, setFiles] = useState<File[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Analysis / Process state
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState("");
  const [results, setResults] = useState<CandidateResult[]>([]);
  const [jobTitleResult, setJobTitleResult] = useState("");
  const [jobSkillsResult, setJobSkillsResult] = useState<string[]>([]);
  const [showResults, setShowResults] = useState(false);

  // Modal / Detail view
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateResult | null>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);

  // Error handling
  const [error, setError] = useState<string | null>(null);

  // Fetch posted jobs on mount
  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const userId = localStorage.getItem("user_id");
        const response = await api.get("/jobs", {
          params: {
            recruiter_id: userId,
            per_page: 100
          }
        });
        const myJobs = response.data.jobs || [];
        setActiveJobs(myJobs);
        if (myJobs.length > 0) {
          setSelectedJobId((current) => current || myJobs[0].job_id);
        }
      } catch (err) {
        console.error("Failed to load active jobs", err);
      }
    };
    fetchJobs();
  }, []);

  // Drag and drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(Array.from(e.target.files));
    }
  };

  const addFiles = (newFiles: File[]) => {
    const pdfs = newFiles.filter(file => file.type === "application/pdf" || file.name.endsWith(".pdf"));
    
    if (pdfs.length !== newFiles.length) {
      setError("Only PDF files are supported for bulk resume screening.");
    } else {
      setError(null);
    }

    setFiles(prev => {
      const combined = [...prev, ...pdfs];
      // Keep only unique files by name + size
      const unique = combined.filter((file, index, self) =>
        index === self.findIndex((f) => f.name === file.name && f.size === file.size)
      );
      
      if (unique.length > 50) {
        setError("Maximum limit of 50 resumes reached. Only the first 50 resumes will be uploaded.");
        return unique.slice(0, 50);
      }
      return unique;
    });
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
    if (files.length <= 50) {
      setError(null);
    }
  };

  const clearAllFiles = () => {
    setFiles([]);
    setError(null);
  };

  // Perform bulk screen matching
  const handleScreenResumes = async () => {
    if (files.length === 0) {
      setError("Please select at least one resume PDF to analyze.");
      return;
    }
    if (files.length > 50) {
      setError("You cannot upload more than 50 resumes at once.");
      return;
    }
    if (jobMode === "custom" && !customTitle.trim()) {
      setError("Please enter a job title for the custom screening.");
      return;
    }
    if (jobMode === "custom" && !customDescription.trim() && !customSkills.trim()) {
      setError("Please provide either custom skills or a job description to match against.");
      return;
    }
    if (jobMode === "posted" && !selectedJobId) {
      setError("Please select one of your posted jobs before screening resumes.");
      return;
    }

    setError(null);
    setIsProcessing(true);
    setProgress(5);
    setProgressText("Initializing text extractor pipeline...");

    // Setup form data
    const formData = new FormData();
    files.forEach(file => {
      formData.append("files", file);
    });

    if (jobMode === "posted") {
      formData.append("job_id", selectedJobId);
    } else {
      formData.append("custom_title", customTitle);
      formData.append("custom_skills", customSkills);
      formData.append("custom_description", customDescription);
    }

    // Simulate progressive load to look premium and give state feedback
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 85) {
          clearInterval(progressInterval);
          return 85;
        }
        
        // Dynamic step texts
        const nextVal = prev + Math.floor(Math.random() * 8) + 2;
        if (nextVal > 25 && nextVal < 45) {
          setProgressText(`Reading PDF streams & extracting text from ${files.length} document(s)...`);
        } else if (nextVal >= 45 && nextVal < 70) {
          setProgressText("Applying TF-IDF content modeling & matching skills matrices...");
        } else if (nextVal >= 70) {
          setProgressText("Synthesizing final cosine similarity rankings...");
        }
        return nextVal;
      });
    }, 450);

    try {
      const response = await api.post("/recruiters/bulk-screen", formData, {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      });

      clearInterval(progressInterval);
      setProgress(100);
      setProgressText("Screening complete!");
      
      setTimeout(() => {
        setResults(response.data.results);
        setJobTitleResult(response.data.job_title);
        setJobSkillsResult(response.data.job_skills);
        setIsProcessing(false);
        setShowResults(true);
        
        // Trigger celebratory confetti if we have successful high matches (>75%)
        const topScore = response.data.results[0]?.match_score || 0;
        if (topScore >= 70) {
          confetti({
            particleCount: 80,
            spread: 60,
            origin: { y: 0.6 }
          });
        }
      }, 500);

    } catch (err: any) {
      clearInterval(progressInterval);
      setIsProcessing(false);
      const errMsg = err.response?.data?.error || "Failed to screen resumes. Please make sure files are valid PDFs and the backend is running.";
      setError(errMsg);
      console.error(err);
    }
  };

  const handleReset = () => {
    setFiles([]);
    setResults([]);
    setShowResults(false);
    setProgress(0);
    setProgressText("");
    setError(null);
  };

  const openCandidateDetails = (candidate: CandidateResult) => {
    setSelectedCandidate(candidate);
    setDetailModalOpen(true);
  };

  // Best match is index 0 since results are sorted desc
  const bestCandidate = results[0];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-16">
      {/* Page Title & Back link */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Sparkles className="h-7 w-7 text-orange-500 animate-pulse" /> Bulk Resume Matcher
          </h1>
          <p className="text-slate-500 mt-1">
            Upload up to 50 resumes to instantly extract text, extract skills, and rank best fits.
          </p>
        </div>
        {showResults && (
          <Button variant="outline" onClick={handleReset} className="border-slate-200">
            <RefreshCw className="h-4 w-4 mr-2" /> Start New Screen
          </Button>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-3 text-sm shadow-sm">
          <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Error occurred</p>
            <p className="mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* 1. INPUT SCREEN */}
      {!showResults && !isProcessing && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* LEFT: JOB TARGETING CONFIGURATION */}
          <div className="lg:col-span-1 space-y-6">
            <Card className="shadow-sm border-slate-200">
              <CardHeader className="pb-4">
                <CardTitle className="text-lg font-bold flex items-center gap-2 text-slate-800">
                  <Briefcase className="h-5 w-5 text-[#1E3A5F]" /> Job Parameters
                </CardTitle>
                <CardDescription>
                  Define the criteria to match resumes against.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                
                {/* Toggle Buttons */}
                <div className="grid grid-cols-2 p-1 bg-slate-100 rounded-lg">
                  <button
                    type="button"
                    onClick={() => { setJobMode("posted"); setError(null); }}
                    className={`py-2 px-3 text-xs font-semibold rounded-md transition-all ${
                      jobMode === "posted" 
                        ? "bg-white text-slate-900 shadow-sm" 
                        : "text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    Select Active Job
                  </button>
                  <button
                    type="button"
                    onClick={() => { setJobMode("custom"); setError(null); }}
                    className={`py-2 px-3 text-xs font-semibold rounded-md transition-all ${
                      jobMode === "custom" 
                        ? "bg-white text-slate-900 shadow-sm" 
                        : "text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    Define Custom Job
                  </button>
                </div>

                {jobMode === "posted" ? (
                  <div className="space-y-4">
                    <label className="text-sm font-semibold text-slate-700">Choose Job Posting</label>
                    {activeJobs.length === 0 ? (
                      <div className="text-xs text-amber-600 bg-amber-50 border border-amber-100 p-3 rounded-lg flex items-start gap-2">
                        <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                        <span>No active jobs found. Switch to "Define Custom Job" or create a posting first.</span>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <Select value={selectedJobId} onValueChange={setSelectedJobId}>
                          <SelectTrigger className="w-full bg-slate-50 border-slate-200">
                            <SelectValue placeholder="Select a job" />
                          </SelectTrigger>
                          <SelectContent>
                            {activeJobs.map(job => (
                              <SelectItem key={job.job_id} value={job.job_id}>
                                {job.title}{job.experience_level ? ` • ${job.experience_level}` : ""}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        {/* Selected Job Skills Preview */}
                        {selectedJobId && (
                          <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg space-y-2">
                            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Target Skills</span>
                            <div className="flex flex-wrap gap-1.5 pt-1">
                              {activeJobs.find(j => j.job_id === selectedJobId)?.skills.map(s => (
                                <Badge key={s} variant="secondary" className="bg-[#1E3A5F]/5 text-[#1E3A5F] border-none text-[10px] px-2">
                                  {s}
                                </Badge>
                              )) || <span className="text-xs text-slate-500">No skills defined</span>}
                            </div>
                            {activeJobs.find(j => j.job_id === selectedJobId)?.experience_level && (
                              <div className="text-[11px] text-slate-500">
                                Experience target: {activeJobs.find(j => j.job_id === selectedJobId)?.experience_level}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4 animate-in fade-in slide-in-from-top-1 duration-200">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-700">Job Title</label>
                      <Input
                        placeholder="e.g. Senior Frontend Engineer"
                        value={customTitle}
                        onChange={(e) => setCustomTitle(e.target.value)}
                        className="bg-slate-50 border-slate-200"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-700">Target Skills (comma-separated)</label>
                      <Input
                        placeholder="e.g. React, TypeScript, Tailwind, Git"
                        value={customSkills}
                        onChange={(e) => setCustomSkills(e.target.value)}
                        className="bg-slate-50 border-slate-200"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-700">Job Description (for Cosine Context)</label>
                      <Textarea
                        placeholder="Paste job description details to enable semantic content matching..."
                        value={customDescription}
                        onChange={(e) => setCustomDescription(e.target.value)}
                        className="bg-slate-50 border-slate-200 min-h-[140px] text-xs"
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* RIGHT: DRAG & DROP MULTIPLE UPLOAD */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="shadow-sm border-slate-200 h-full flex flex-col">
              <CardHeader className="pb-4">
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle className="text-lg font-bold text-slate-800">Upload Resumes</CardTitle>
                    <CardDescription>Select up to 50 PDF resumes to match against targets.</CardDescription>
                  </div>
                  {files.length > 0 && (
                    <Button variant="ghost" size="sm" onClick={clearAllFiles} className="text-red-500 hover:text-red-600">
                      <Trash2 className="h-4 w-4 mr-1.5" /> Clear All
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-6 flex-1 flex flex-col justify-between">
                
                {/* Drag and Drop Zone */}
                <div
                  onDragEnter={handleDrag}
                  onDragOver={handleDrag}
                  onDragLeave={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all flex flex-col items-center justify-center min-h-[220px] ${
                    dragActive 
                      ? "border-orange-500 bg-orange-50/50 scale-[0.99]" 
                      : "border-slate-300 hover:border-orange-500/70 hover:bg-slate-50/70 bg-slate-50/20"
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <div className="h-12 w-12 rounded-full bg-orange-50 flex items-center justify-center mb-4 text-[#F97316]">
                    <UploadCloud className="h-6 w-6" />
                  </div>
                  <h4 className="font-bold text-slate-800 text-sm">Drag and drop resume PDFs here</h4>
                  <p className="text-xs text-slate-400 mt-1">Or click to browse from files (limit 50 resumes)</p>
                  <Badge variant="outline" className="mt-3 text-slate-500 bg-white">
                    {files.length} / 50 Selected
                  </Badge>
                </div>

                {/* Selected Files List */}
                {files.length > 0 && (
                  <div className="border border-slate-100 rounded-lg p-3 bg-slate-50/60 max-h-[240px] overflow-y-auto space-y-2 mt-4">
                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">Selected PDF Documents</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {files.map((file, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 rounded bg-white border border-slate-100 text-xs shadow-sm hover:border-slate-200">
                          <div className="flex items-center gap-2 truncate pr-2">
                            <FileText className="h-4 w-4 text-red-500 shrink-0" />
                            <span className="font-medium text-slate-700 truncate" title={file.name}>
                              {file.name}
                            </span>
                            <span className="text-[10px] text-slate-400 shrink-0">
                              ({(file.size / 1024).toFixed(0)} KB)
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); removeFile(idx); }}
                            className="text-slate-400 hover:text-red-500 transition-colors"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Screening Action Button */}
                <div className="pt-6 border-t border-slate-100 flex justify-end mt-auto">
                  <Button
                    onClick={handleScreenResumes}
                    disabled={files.length === 0}
                    className="w-full md:w-auto bg-[#F97316] hover:bg-[#F97316]/90 text-white font-semibold py-2 px-6 shadow-lg shadow-orange-500/20"
                  >
                    <Sparkles className="h-4 w-4 mr-2" /> Screen & Rank {files.length > 0 ? `(${files.length})` : ""} Resumes
                  </Button>
                </div>

              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* 2. PROCESSING STATE VIEW */}
      {isProcessing && (
        <Card className="shadow-lg border-slate-200/60 max-w-2xl mx-auto p-12 text-center flex flex-col items-center justify-center space-y-6">
          <div className="relative h-20 w-20 flex items-center justify-center">
            {/* Pulsing outer rings */}
            <div className="absolute inset-0 rounded-full bg-orange-100 animate-ping opacity-75"></div>
            <div className="absolute h-16 w-16 rounded-full bg-orange-200 opacity-50 animate-pulse"></div>
            <div className="relative h-12 w-12 rounded-full bg-gradient-to-br from-[#F97316] to-[#1E3A5F] flex items-center justify-center text-white">
              <Sparkles className="h-6 w-6 animate-spin duration-3000" />
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="text-xl font-bold text-slate-800">Processing Resumes</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">{progressText}</p>
          </div>

          <div className="w-full max-w-md mx-auto space-y-1">
            <Progress value={progress} className="h-2 bg-slate-100" />
            <div className="flex justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              <span>Extracting Text</span>
              <span>{progress}%</span>
            </div>
          </div>
        </Card>
      )}

      {/* 3. SCREENED RESULTS SCREEN */}
      {showResults && (
        <div className="space-y-8 animate-in fade-in zoom-in-95 duration-400">
          
          {/* Target Job Indicator Header */}
          <div className="p-4 bg-[#1E3A5F]/5 border border-[#1E3A5F]/10 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-[#1E3A5F] flex items-center justify-center text-white">
                <Briefcase className="h-5 w-5" />
              </div>
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-[#1E3A5F]/60">Target Profile Position</div>
                <h3 className="font-bold text-lg text-slate-800">{jobTitleResult}</h3>
              </div>
            </div>
            
            {jobSkillsResult.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-xs text-slate-500 font-medium mr-1.5">Target Skills:</span>
                {jobSkillsResult.map(s => (
                  <Badge key={s} variant="secondary" className="bg-[#1E3A5F] text-white hover:bg-[#1E3A5F] border-none text-[10px]">
                    {s}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* SPOTLIGHT: BEST MATCH (Absolute Top Candidate) */}
          {bestCandidate && (
            <div className="relative group">
              {/* Glowing decorative gradient borders */}
              <div className="absolute -inset-0.5 bg-gradient-to-r from-orange-500 to-indigo-600 rounded-2xl blur opacity-30 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
              
              <Card className="relative shadow-md border-orange-500/20 bg-gradient-to-br from-white via-white to-orange-50/15 overflow-hidden">
                <div className="absolute top-0 right-0 h-28 w-28 bg-gradient-to-bl from-orange-200/30 to-transparent rounded-bl-full pointer-events-none"></div>
                
                <CardContent className="p-6 md:p-8">
                  <div className="flex flex-col md:flex-row justify-between items-start gap-6">
                    <div className="space-y-4 flex-1">
                      
                      {/* Spotlight Badge */}
                      <Badge className="bg-orange-500 hover:bg-orange-500 text-white font-bold tracking-wider px-3 py-1 flex items-center gap-1.5 w-fit border-none animate-bounce">
                        <Award className="h-4 w-4" /> Best Fit Match
                      </Badge>

                      <div className="space-y-1.5">
                        <h2 className="text-2xl font-black text-slate-900 leading-none">
                          {bestCandidate.candidate_name}
                        </h2>
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          <FileText className="h-3.5 w-3.5 text-red-500" />
                          <span>{bestCandidate.filename}</span>
                        </div>
                      </div>

                      {/* Summary text snippet */}
                      <p className="text-sm text-slate-600 leading-relaxed max-w-3xl pt-2">
                        "{bestCandidate.text_snippet}"
                      </p>

                      {/* Skills breakdown */}
                      <div className="space-y-2 pt-2">
                        <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Key Matching Skills</span>
                        <div className="flex flex-wrap gap-1.5">
                          {bestCandidate.matched_skills.map(s => (
                            <Badge key={s} className="bg-green-500 hover:bg-green-500 border-none text-white px-2 py-0.5 text-xs font-semibold">
                              {s}
                            </Badge>
                          ))}
                          {bestCandidate.missing_skills.length > 0 && (
                            <span className="text-xs text-slate-400 pl-1 self-center">
                              Missing: {bestCandidate.missing_skills.join(", ")}
                            </span>
                          )}
                        </div>
                      </div>

                    </div>

                    {/* Circular Score display on right */}
                    <div className="flex flex-col items-center justify-center bg-white border border-slate-100 rounded-xl p-6 shadow-sm min-w-[150px] shrink-0 self-center md:self-start">
                      <div className="relative flex items-center justify-center">
                        {/* Radial progress mockup using simple circle outline styles */}
                        <svg className="w-20 h-20">
                          <circle className="text-slate-100" strokeWidth="6" stroke="currentColor" fill="transparent" r="34" cx="40" cy="40"/>
                          <circle className="text-orange-500" strokeWidth="6" strokeDasharray={2 * Math.PI * 34} strokeDashoffset={2 * Math.PI * 34 * (1 - bestCandidate.match_score / 100)} strokeLinecap="round" stroke="currentColor" fill="transparent" r="34" cx="40" cy="40"/>
                        </svg>
                        <span className="absolute text-2xl font-black text-slate-800">
                          {bestCandidate.match_score}<span className="text-xs font-bold">%</span>
                        </span>
                      </div>
                      
                      <div className="text-[10px] font-bold uppercase text-slate-400 tracking-widest mt-3">Match Score</div>
                      
                      <Button
                        onClick={() => openCandidateDetails(bestCandidate)}
                        className="mt-4 w-full bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 text-white text-xs font-bold py-1.5 h-8 gap-1.5 shadow"
                      >
                        Analyze Fit <ChevronRight className="h-3.5 w-3.5" />
                      </Button>
                    </div>

                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* CANDIDATES TABLE / LIST */}
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-lg font-bold text-slate-800">All Screened Resumes ({results.length})</CardTitle>
              <CardDescription>Ranked matches from highest to lowest matching index.</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-slate-100">
                {results.map((candidate, index) => {
                  const isTop = index === 0;
                  return (
                    <div 
                      key={index} 
                      className={`p-4 md:p-6 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 transition-colors hover:bg-slate-50/70 ${
                        isTop ? "bg-orange-50/10" : ""
                      }`}
                    >
                      {/* Left Block: Rank, Info & Skills */}
                      <div className="flex items-center gap-4 flex-1">
                        {/* Rank Circle */}
                        <div className={`h-9 w-9 rounded-full flex items-center justify-center font-bold text-sm shrink-0 border ${
                          isTop 
                            ? "bg-orange-500 text-white border-orange-500" 
                            : "bg-slate-100 text-slate-600 border-slate-200"
                        }`}>
                          #{index + 1}
                        </div>

                        <div className="space-y-1.5 min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-bold text-slate-800 truncate text-sm md:text-base">
                              {candidate.candidate_name}
                            </h4>
                            {isTop && (
                              <Badge className="bg-orange-100 hover:bg-orange-100 text-orange-700 text-[9px] h-4 uppercase font-bold border-none px-1.5">
                                Top Match
                              </Badge>
                            )}
                            {candidate.error && (
                              <Badge className="bg-red-100 text-red-700 text-[9px] h-4 uppercase font-bold border-none px-1.5 flex items-center gap-0.5">
                                <AlertCircle className="h-2.5 w-2.5" /> Failed
                              </Badge>
                            )}
                          </div>
                          
                          {candidate.error ? (
                            <span className="text-xs text-red-500 block">{candidate.error}</span>
                          ) : (
                            <div className="flex flex-wrap gap-1">
                              {candidate.matched_skills.map(s => (
                                <Badge key={s} className="bg-green-50 text-green-700 hover:bg-green-50 border-green-200/50 text-[9px] px-1.5 py-0">
                                  {s}
                                </Badge>
                              ))}
                              {candidate.missing_skills.map(s => (
                                <Badge key={s} variant="outline" className="text-slate-400 border-slate-200 text-[9px] px-1.5 py-0 line-through">
                                  {s}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Right Block: Score Breakdown & Analyze Button */}
                      <div className="flex items-center justify-between md:justify-end gap-6 shrink-0 border-t md:border-t-0 pt-3 md:pt-0 border-slate-100">
                        
                        {!candidate.error && (
                          <div className="text-right flex md:flex-col items-center md:items-end justify-between w-full md:w-auto gap-4 md:gap-0.5">
                            <span className="text-xs text-slate-400 font-medium">Match Fit:</span>
                            <div className="flex items-baseline gap-0.5">
                              <span className={`text-xl font-black ${
                                candidate.match_score >= 75 ? 'text-green-600' : candidate.match_score >= 50 ? 'text-orange-500' : 'text-slate-500'
                              }`}>
                                {candidate.match_score}
                              </span>
                              <span className="text-xs font-bold text-slate-400">%</span>
                            </div>
                            {/* Small metric tags */}
                            <span className="hidden md:inline text-[9px] text-slate-400 font-semibold">
                              (Skills: {candidate.skills_score}% • Experience: {candidate.experience_score}% • Context: {candidate.content_score}%)
                            </span>
                          </div>
                        )}

                        <Button
                          variant="outline"
                          size="sm"
                          disabled={!!candidate.error}
                          onClick={() => openCandidateDetails(candidate)}
                          className="h-9 text-slate-700 border-slate-200 font-semibold"
                        >
                          <BookOpen className="h-4 w-4 mr-1.5" /> Analyze Fit
                        </Button>
                      </div>

                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 4. DETAILS SIDE MODAL / SHEET */}
      {selectedCandidate && (
        <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
          <DialogContent className="max-w-3xl overflow-hidden flex flex-col max-h-[85vh] p-0 border-slate-200 shadow-2xl">
            
            {/* Header with gradient strip */}
            <div className="h-2 bg-gradient-to-r from-orange-500 to-indigo-600"></div>
            
            <div className="p-6 border-b border-slate-100">
              <div className="flex justify-between items-start gap-4">
                <div className="space-y-1">
                  <DialogTitle className="text-2xl font-black text-slate-900">
                    {selectedCandidate.candidate_name}
                  </DialogTitle>
                  <DialogDescription className="flex items-center gap-1.5 text-xs text-slate-400">
                    <FileText className="h-3.5 w-3.5 text-red-500" />
                    <span>{selectedCandidate.filename}</span>
                  </DialogDescription>
                </div>
                
                <div className="text-right shrink-0">
                  <Badge className="bg-orange-100 hover:bg-orange-100 text-orange-700 font-bold border-none px-2.5 py-1 text-sm">
                    {selectedCandidate.match_score}% Match Score
                  </Badge>
                  <div className="text-[10px] text-slate-400 font-semibold mt-1">
                    Skills: {selectedCandidate.skills_score}% • Experience: {selectedCandidate.experience_score}% • Cosine: {selectedCandidate.content_score}%
                  </div>
                </div>
              </div>
            </div>

            {/* Scrollable details content */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1 text-slate-700">
              
              {/* Skills Analysis Block */}
              <div className="space-y-3">
                <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <UserCheck className="h-4 w-4 text-green-500" /> Skills Evaluation
                </h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Matching Skills */}
                  <div className="p-4 bg-green-50/40 border border-green-100 rounded-xl space-y-2">
                    <span className="text-xs font-bold text-green-800">Matched Target Skills ({selectedCandidate.matched_skills.length})</span>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {selectedCandidate.matched_skills.length === 0 ? (
                        <span className="text-xs text-slate-400 italic">No matching skills found</span>
                      ) : selectedCandidate.matched_skills.map(s => (
                        <Badge key={s} className="bg-green-500 hover:bg-green-500 border-none text-white text-[10px]">
                          {s}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Missing Skills */}
                  <div className="p-4 bg-red-50/30 border border-red-100 rounded-xl space-y-2">
                    <span className="text-xs font-bold text-red-800">Missing Target Skills ({selectedCandidate.missing_skills.length})</span>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {selectedCandidate.missing_skills.length === 0 ? (
                        <span className="text-xs text-green-600 font-medium">None! Perfect skills match.</span>
                      ) : selectedCandidate.missing_skills.map(s => (
                        <Badge key={s} variant="outline" className="text-red-600 border-red-200 text-[10px]">
                          {s}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Extra extracted skills */}
                {selectedCandidate.extracted_skills.filter(s => !selectedCandidate.matched_skills.includes(s)).length > 0 && (
                  <div className="p-4 bg-slate-50 border border-slate-100 rounded-xl space-y-2">
                    <span className="text-xs font-bold text-slate-500">Other Extracted Skills</span>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {selectedCandidate.extracted_skills
                        .filter(s => !selectedCandidate.matched_skills.includes(s))
                        .map(s => (
                          <Badge key={s} variant="secondary" className="bg-slate-200 text-slate-600 hover:bg-slate-200 border-none text-[10px]">
                            {s}
                          </Badge>
                        ))
                      }
                    </div>
                  </div>
                )}
              </div>

              {/* Parsed Text Viewer Block */}
              <div className="space-y-3">
                <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <FileText className="h-4 w-4 text-[#1E3A5F]" /> Full Resume Extracted Text
                </h4>
                
                <div className="p-4 border border-slate-200 rounded-xl bg-slate-50 max-h-[300px] overflow-y-auto">
                  <pre className="text-xs font-mono text-slate-600 whitespace-pre-wrap leading-relaxed select-all">
                    {selectedCandidate.raw_text}
                  </pre>
                </div>
              </div>

            </div>

            {/* Footer buttons */}
            <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end gap-2 rounded-b-lg">
              <Button
                variant="outline"
                onClick={() => setDetailModalOpen(false)}
                className="border-slate-200"
              >
                Close Analysis
              </Button>
            </div>

          </DialogContent>
        </Dialog>
      )}

    </div>
  );
}
