import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ExternalLink, Target, CheckCircle2, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

const jobOptions = ["Frontend Developer @ TechCorp", "React Engineer @ StartupXYZ", "Full Stack Developer @ InnovateCo"];
const missingSkills = [
  { skill: "TypeScript", priority: "High", resources: ["TypeScript Handbook (official)", "Udemy: TypeScript Bootcamp", "Frontend Masters: TypeScript"] },
  { skill: "Node.js", priority: "Medium", resources: ["Node.js official docs", "The Odin Project: Node.js", "Udemy: Node.js Complete Guide"] },
  { skill: "System Design", priority: "Medium", resources: ["Grokking System Design", "YouTube: System Design Primer", "ByteByteGo newsletter"] },
  { skill: "Testing (Jest)", priority: "Low", resources: ["Jest official docs", "Testing Library docs"] },
];
const strengths = ["React", "JavaScript", "CSS", "HTML", "Git", "REST APIs"];

export default function ApplicantSkillGap() {
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({"TypeScript": true});

  const toggleItem = (skill: string) => {
    setOpenItems(prev => ({ ...prev, [skill]: !prev[skill] }));
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Skill Gap Analysis</h1>
          <p className="text-slate-500 mt-1">See exactly what's standing between you and your target roles.</p>
        </div>
        <div className="w-full md:w-80">
          <p className="text-sm font-medium text-slate-700 mb-2">Analyze skill gap for:</p>
          <Select defaultValue="Frontend Developer @ TechCorp">
            <SelectTrigger className="bg-white border-slate-200">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {jobOptions.map(opt => (
                <SelectItem key={opt} value={opt}>{opt}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Missing Skills */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-t-4 border-t-[#F97316]">
            <CardHeader>
              <CardTitle className="text-xl">Missing Skills to Learn</CardTitle>
              <CardDescription>We've identified {missingSkills.length} critical skills required for this role that aren't in your profile.</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-slate-100">
                {missingSkills.map((item) => (
                  <Collapsible 
                    key={item.skill} 
                    open={openItems[item.skill]} 
                    onOpenChange={() => toggleItem(item.skill)}
                    className="p-4 bg-white"
                  >
                    <CollapsibleTrigger className="w-full flex items-center justify-between group">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${
                          item.priority === 'High' ? 'bg-red-50 text-red-600' :
                          item.priority === 'Medium' ? 'bg-orange-50 text-orange-600' :
                          'bg-slate-100 text-slate-600'
                        }`}>
                          <Target className="h-4 w-4" />
                        </div>
                        <span className="font-semibold text-slate-900">{item.skill}</span>
                        <Badge variant="outline" className={
                          item.priority === 'High' ? 'border-red-200 text-red-700 bg-red-50' :
                          item.priority === 'Medium' ? 'border-orange-200 text-orange-700 bg-orange-50' :
                          'border-slate-200 text-slate-700 bg-slate-50'
                        }>
                          {item.priority} Priority
                        </Badge>
                      </div>
                      <Button variant="ghost" size="sm" className="text-slate-400 group-hover:text-slate-900">
                        {openItems[item.skill] ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </Button>
                    </CollapsibleTrigger>
                    
                    <CollapsibleContent className="pt-4 pl-14">
                      <p className="text-sm font-medium text-slate-900 mb-3 uppercase tracking-wider">Recommended Resources</p>
                      <ul className="space-y-2">
                        {item.resources.map((res, i) => (
                          <li key={i}>
                            <a href="#" className="inline-flex items-center text-sm text-[#1E3A5F] hover:underline gap-1.5 p-1.5 -ml-1.5 rounded hover:bg-blue-50 transition-colors">
                              <ExternalLink className="h-3.5 w-3.5 text-slate-400" />
                              {res}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </CollapsibleContent>
                  </Collapsible>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Strengths & Readiness */}
        <div className="space-y-6">
          <Card className="bg-[#1E3A5F] text-white border-none shadow-lg">
            <CardContent className="p-8 text-center">
              <div className="relative w-32 h-32 mx-auto mb-6">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="40" className="text-white/20 stroke-current" strokeWidth="8" fill="none" />
                  <circle cx="50" cy="50" r="40" className="text-[#F97316] stroke-current" strokeWidth="8" fill="none" strokeDasharray="251.2" strokeDashoffset={251.2 - (251.2 * 78) / 100} strokeLinecap="round" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center flex-col">
                  <span className="text-4xl font-bold">78<span className="text-xl">%</span></span>
                </div>
              </div>
              <h3 className="text-xl font-bold mb-2">Role Readiness</h3>
              <p className="text-blue-100 text-sm mb-6">You have a strong foundation for this role, but addressing high-priority gaps will significantly boost your chances.</p>
              <Button className="w-full bg-[#F97316] hover:bg-[#F97316]/90 text-white border-none">
                Boost Your Profile
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-lg">Your Strengths</CardTitle>
              <CardDescription>Matching skills you already possess.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {strengths.map(skill => (
                  <Badge key={skill} className="bg-green-50 text-green-700 border border-green-200 hover:bg-green-100 px-3 py-1 font-medium gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    {skill}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
