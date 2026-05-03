import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, Download, UploadCloud, Edit3, Sparkles } from "lucide-react";

const skills = ["React", "JavaScript", "CSS", "HTML", "Git", "Figma", "REST APIs", "Redux", "Tailwind CSS", "Webpack"];
const resumeFile = { name: "Priya_Sharma_Resume.pdf", uploaded: "Apr 28, 2026", pages: 2 };

export default function ApplicantResume() {
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
              <CardDescription>Your active resume used for matching.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="p-4 border border-slate-200 rounded-xl bg-slate-50 flex items-start gap-4">
                <div className="h-12 w-12 rounded-lg bg-red-100 flex items-center justify-center flex-shrink-0">
                  <FileText className="h-6 w-6 text-red-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-slate-900 truncate">{resumeFile.name}</h4>
                  <p className="text-sm text-slate-500 mt-1">Uploaded {resumeFile.uploaded} • {resumeFile.pages} pages</p>
                </div>
                <Button variant="ghost" size="icon" className="flex-shrink-0 text-slate-400 hover:text-slate-900">
                  <Download className="h-5 w-5" />
                </Button>
              </div>

              <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 flex flex-col items-center justify-center text-center bg-slate-50/50 hover:bg-slate-50 transition-colors cursor-pointer group">
                <div className="h-12 w-12 rounded-full bg-blue-50 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <UploadCloud className="h-6 w-6 text-[#1E3A5F]" />
                </div>
                <h4 className="font-semibold text-slate-900">Replace Resume</h4>
                <p className="text-sm text-slate-500 mt-1 max-w-xs">Drag and drop a new PDF or Word document, or click to browse.</p>
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
                <CardDescription>What our AI found in your document.</CardDescription>
              </div>
              <Button variant="outline" size="sm" className="gap-2">
                <Edit3 className="h-4 w-4" /> Edit
              </Button>
            </CardHeader>
            <CardContent className="pt-6 flex-1">
              <div className="space-y-6">
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3">Verified Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {skills.map((skill, i) => (
                      <Badge key={skill} className={i < 4 ? "bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 text-white px-3 py-1" : "bg-slate-100 text-slate-700 hover:bg-slate-200 px-3 py-1"}>
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="pt-6 border-t border-slate-100">
                  <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3">Experience Summary</h4>
                  <p className="text-slate-600 text-sm leading-relaxed">
                    Frontend developer with 3+ years of experience specializing in React ecosystem. 
                    Strong focus on UI/UX implementation and component architecture. 
                    Demonstrated ability to convert Figma designs into responsive, accessible web applications.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
