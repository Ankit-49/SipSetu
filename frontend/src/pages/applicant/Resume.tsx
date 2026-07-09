import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, UploadCloud, Edit3, Sparkles, Loader2, CheckCircle2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import axios from "axios";

const API = "http://localhost:5000/api";

export default function ApplicantResume() {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [resume, setResume] = useState<any>(null);

  const fetchResume = async () => {
    const userId = localStorage.getItem("user_id");
    if (!userId) { setLoading(false); return; }
    try {
      const res = await axios.get(`${API}/resumes?applicant_id=${userId}`);
      if (res.data.length > 0) {
        setResume(res.data[0]); // latest resume
      }
    } catch (err) {
      console.error("Failed to load resume", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchResume(); }, []);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const userId = localStorage.getItem("user_id");
    if (!userId) {
      toast({ title: "Not logged in", variant: "destructive" });
      return;
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      toast({ title: "Invalid file", description: "Please upload a PDF file.", variant: "destructive" });
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('applicant_id', userId);

      const res = await axios.post(`${API}/resumes/upload-pdf`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      toast({
        title: "Resume uploaded!",
        description: `${res.data.skill_count} skills extracted successfully.`,
      });
      await fetchResume();
    } catch (err: any) {
      toast({
        title: "Upload failed",
        description: err.response?.data?.error || "Failed to upload resume.",
        variant: "destructive"
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#1E3A5F]" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">My Resume</h1>
        <p className="text-slate-500 mt-1">Manage your document and extracted skills profile.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: File Management */}
        <div className="space-y-8">
          <Card>
            <CardHeader>
              <CardTitle>Current Document</CardTitle>
              <CardDescription>Your active resume used for job matching.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {resume ? (
                <div className="p-4 border border-slate-200 rounded-xl bg-slate-50 flex items-start gap-4">
                  <div className="h-12 w-12 rounded-lg bg-red-100 flex items-center justify-center flex-shrink-0">
                    <FileText className="h-6 w-6 text-red-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-slate-900 truncate">
                      {resume.file_path || "Uploaded Resume"}
                    </h4>
                    <p className="text-sm text-slate-500 mt-1">
                      Uploaded {new Date(resume.uploaded_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      {" • "}{resume.skills.length} skills detected
                    </p>
                    <div className="flex items-center gap-1.5 mt-1">
                      <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                      <span className="text-xs text-green-600 font-medium">Active for matching</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 border border-dashed border-slate-200 rounded-xl bg-slate-50/50 text-center">
                  <p className="text-sm text-slate-500">No resume uploaded yet.</p>
                </div>
              )}

              {/* Upload drop zone */}
              <div
                className="border-2 border-dashed border-slate-200 rounded-xl p-8 flex flex-col items-center justify-center text-center bg-slate-50/50 hover:bg-slate-50 transition-colors cursor-pointer group"
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="h-12 w-12 rounded-full bg-blue-50 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  {uploading ? (
                    <Loader2 className="h-6 w-6 text-[#1E3A5F] animate-spin" />
                  ) : (
                    <UploadCloud className="h-6 w-6 text-[#1E3A5F]" />
                  )}
                </div>
                <h4 className="font-semibold text-slate-900">
                  {uploading ? "Analyzing your resume..." : resume ? "Replace Resume" : "Upload Resume"}
                </h4>
                <p className="text-sm text-slate-500 mt-1 max-w-xs">
                  {uploading ? "Extracting skills and building your profile..." : "Click to browse and upload your PDF resume."}
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={handleFileSelect}
                  disabled={uploading}
                />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-indigo-50 to-blue-50 border-indigo-100 shadow-sm">
            <CardContent className="p-6 flex items-start gap-4">
              <div className="h-10 w-10 rounded-full bg-white shadow-sm flex items-center justify-center flex-shrink-0">
                <Sparkles className="h-5 w-5 text-indigo-600" />
              </div>
              <div>
                <h4 className="font-bold text-indigo-900 mb-1">Build a resume with AI</h4>
                <p className="text-sm text-indigo-700/80 mb-4">Don't have a solid resume yet? Use our AI builder to craft one tailored for tech roles.</p>
                <Button className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm">
                  Start Building
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Extracted Profile */}
        <div className="space-y-8">
          <Card className="h-full flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between pb-2 border-b border-slate-100">
              <div>
                <CardTitle>Extracted Profile</CardTitle>
                <CardDescription>Skills our AI found in your document.</CardDescription>
              </div>
              <Button variant="outline" size="sm" className="gap-2">
                <Edit3 className="h-4 w-4" /> Edit
              </Button>
            </CardHeader>
            <CardContent className="pt-6 flex-1">
              {resume && resume.skills.length > 0 ? (
                <div className="space-y-6">
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3">Verified Skills</h4>
                    <div className="flex flex-wrap gap-2">
                      {resume.skills.map((skill: string, i: number) => (
                        <Badge
                          key={skill}
                          className={i < 4
                            ? "bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 text-white px-3 py-1"
                            : "bg-slate-100 text-slate-700 hover:bg-slate-200 px-3 py-1"
                          }
                        >
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="pt-6 border-t border-slate-100">
                    <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3">Upload Details</h4>
                    <div className="space-y-2 text-sm text-slate-600">
                      <p><span className="font-medium text-slate-700">File:</span> {resume.file_path || "Resume"}</p>
                      <p><span className="font-medium text-slate-700">Uploaded:</span> {new Date(resume.uploaded_at).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</p>
                      <p><span className="font-medium text-slate-700">Skills found:</span> {resume.skills.length}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-48 text-center">
                  <FileText className="h-12 w-12 text-slate-200 mb-4" />
                  <p className="text-slate-500 font-medium">No resume uploaded yet</p>
                  <p className="text-sm text-slate-400 mt-1">Upload a PDF to extract your skills profile.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
