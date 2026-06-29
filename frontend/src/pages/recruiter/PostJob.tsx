import { useState } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { X, Sparkles } from "lucide-react";

export default function RecruiterPostJob() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [skills, setSkills] = useState<string[]>(["React", "TypeScript", "Git"]);
  const [skillInput, setSkillInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const addSkill = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && skillInput.trim()) {
      e.preventDefault();
      if (!skills.includes(skillInput.trim())) {
        setSkills([...skills, skillInput.trim()]);
      }
      setSkillInput("");
    }
  };

  const removeSkill = (skillToRemove: string) => {
    setSkills(skills.filter(s => s !== skillToRemove));
  };

  const handlePostJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title) {
        alert("Please enter a job title");
        return;
    }
    setIsSubmitting(true);
    try {
      // In a real app, recruiter_id would come from auth context
      const recruiter_id = localStorage.getItem("user_id") || "00000000-0000-0000-0000-000000000000"; 
      await axios.post("http://localhost:5000/api/jobs", {
        recruiter_id,
        title,
        skills
      });
      alert("Job posted successfully!");
      setTitle("");
      setDescription("");
      setSkills([]);
    } catch (err) {
      console.error(err);
      alert("Failed to post job");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Create Job Posting</h1>
        <p className="text-slate-500 mt-1">Our AI will use these details to rank applicants accurately.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Job Details</CardTitle>
          <CardDescription>Be as specific as possible to get better AI matches.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-8" onSubmit={handlePostJob}>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Job Title</Label>
                <Input id="title" value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Senior Frontend Developer" className="h-11" required />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label htmlFor="description">Job Description</Label>
                  <Button type="button" variant="ghost" size="sm" className="h-8 text-indigo-600 gap-1.5 px-2">
                    <Sparkles className="h-3.5 w-3.5" /> Improve with AI
                  </Button>
                </div>
                <Textarea 
                  id="description" 
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Describe the role, responsibilities, and what success looks like..." 
                  className="min-h-[160px] resize-y"
                />
              </div>

              <div className="space-y-3 pt-2">
                <Label htmlFor="skills">Required Skills</Label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {skills.map(skill => (
                    <Badge key={skill} className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 text-white px-3 py-1 gap-1 text-sm font-medium">
                      {skill}
                      <X 
                        className="h-3.5 w-3.5 ml-1 cursor-pointer opacity-70 hover:opacity-100" 
                        onClick={() => removeSkill(skill)}
                      />
                    </Badge>
                  ))}
                </div>
                <Input 
                  id="skills" 
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyDown={addSkill}
                  placeholder="Type a skill and press Enter..." 
                  className="h-11"
                />
                <p className="text-xs text-slate-500">Our AI uses these exact skills to generate the candidate Match Score.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-slate-100">
              <div className="space-y-2">
                <Label>Experience Level</Label>
                <Select>
                  <SelectTrigger className="h-11 bg-white">
                    <SelectValue placeholder="Select experience" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fresher">Fresher</SelectItem>
                    <SelectItem value="1-3">1-3 years</SelectItem>
                    <SelectItem value="3-5">3-5 years</SelectItem>
                    <SelectItem value="5+">5+ years</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Job Type</Label>
                <Select>
                  <SelectTrigger className="h-11 bg-white">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="full">Full-time</SelectItem>
                    <SelectItem value="part">Part-time</SelectItem>
                    <SelectItem value="contract">Contract</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Location</Label>
                <Input placeholder="e.g. Kathmandu, Nepal" className="h-11" />
              </div>

              <div className="space-y-2">
                <Label>Salary Range </Label>
                <div className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 font-medium">₹</span>
                    <Input type="number" placeholder="Min" className="h-11 pl-7" />
                  </div>
                  <span className="text-slate-400">-</span>
                  <div className="relative flex-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 font-medium">₹</span>
                    <Input type="number" placeholder="Max" className="h-11 pl-7" />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 pt-6">
              <Button type="button" variant="outline" className="h-12 sm:flex-1 text-slate-600 bg-white hover:bg-slate-50">
                Save as Draft
              </Button>
              <Button type="submit" disabled={isSubmitting} className="h-12 sm:flex-[2] bg-[#F97316] hover:bg-[#F97316]/90 text-white text-base shadow-lg shadow-orange-500/20">
                {isSubmitting ? "Posting..." : "Post Job Opening"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
