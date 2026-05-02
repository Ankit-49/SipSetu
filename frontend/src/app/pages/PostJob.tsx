import { useState } from "react";
import { useNavigate } from "react-router";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { X, Sparkles } from "lucide-react";

export default function PostJob() {
  const navigate = useNavigate();
  const [jobTitle, setJobTitle] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [skills, setSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState('');
  const [experienceLevel, setExperienceLevel] = useState('');
  const [jobType, setJobType] = useState('');
  const [location, setLocation] = useState('');
  const [salaryMin, setSalaryMin] = useState('');
  const [salaryMax, setSalaryMax] = useState('');

  const handleAddSkill = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && skillInput.trim()) {
      e.preventDefault();
      if (!skills.includes(skillInput.trim())) {
        setSkills([...skills, skillInput.trim()]);
        setSkillInput('');
      }
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setSkills(skills.filter(skill => skill !== skillToRemove));
  };

  const handleSubmit = (isDraft: boolean) => {
    const jobData = {
      id: Math.random().toString(36).substring(7),
      title: jobTitle,
      description: jobDescription,
      skills,
      experienceLevel,
      jobType,
      location,
      salaryRange: `${salaryMin} - ${salaryMax}`,
      status: isDraft ? 'draft' : 'active',
      createdAt: new Date().toISOString(),
    };

    // Save to localStorage
    const jobs = JSON.parse(localStorage.getItem('recruiter_jobs') || '[]');
    jobs.push(jobData);
    localStorage.setItem('recruiter_jobs', JSON.stringify(jobs));

    navigate('/recruiter/home');
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <Button variant="ghost" onClick={() => navigate('/recruiter/home')} className="mb-6">
          ← Back to Dashboard
        </Button>

        <div className="mb-8">
          <h1 className="text-4xl mb-2">Create Job Posting</h1>
          <p className="text-gray-600">Our AI will use these details to rank applicants accurately.</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Job Details</CardTitle>
            <p className="text-sm text-gray-600">Be as specific as possible to get better AI matches.</p>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Job Title */}
            <div className="space-y-2">
              <Label htmlFor="jobTitle">Job Title</Label>
              <Input
                id="jobTitle"
                placeholder="e.g. Senior Frontend Developer"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
              />
            </div>

            {/* Job Description */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label htmlFor="jobDescription">Job Description</Label>
                <button className="text-sm text-purple-600 flex items-center gap-1 hover:underline">
                  <Sparkles className="w-4 h-4" />
                  Improve with AI
                </button>
              </div>
              <Textarea
                id="jobDescription"
                placeholder="Describe the role, responsibilities, and what success looks like..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={6}
              />
            </div>

            {/* Required Skills */}
            <div className="space-y-2">
              <Label>Required Skills</Label>
              <div className="flex flex-wrap gap-2 mb-2">
                {skills.map((skill) => (
                  <Badge key={skill} variant="secondary" className="pl-3 pr-1 py-1">
                    {skill}
                    <button
                      onClick={() => handleRemoveSkill(skill)}
                      className="ml-2 hover:bg-gray-300 rounded-full p-0.5"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))}
              </div>
              <Input
                placeholder="Type a skill and press Enter..."
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={handleAddSkill}
              />
              <p className="text-xs text-gray-500">
                Our AI uses these exact skills to generate the candidate Match Score.
              </p>
            </div>

            {/* Experience Level & Job Type */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label>Experience Level</Label>
                <Select value={experienceLevel} onValueChange={setExperienceLevel}>
                  <SelectTrigger>
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
                <Select value={jobType} onValueChange={setJobType}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="full-time">Full-time</SelectItem>
                    <SelectItem value="part-time">Part-time</SelectItem>
                    <SelectItem value="contract">Contract</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Location */}
            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                placeholder="e.g. Bangalore, India"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </div>

            {/* Salary Range */}
            <div className="space-y-2">
              <Label>Salary Range (LPA)</Label>
              <div className="flex items-center gap-4">
                <Input
                  placeholder="₹ Min"
                  value={salaryMin}
                  onChange={(e) => setSalaryMin(e.target.value)}
                />
                <span className="text-gray-500">-</span>
                <Input
                  placeholder="₹ Max"
                  value={salaryMax}
                  onChange={(e) => setSalaryMax(e.target.value)}
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 pt-6">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => handleSubmit(true)}
              >
                Save as Draft
              </Button>
              <Button
                className="flex-1 bg-orange-500 hover:bg-orange-600"
                onClick={() => handleSubmit(false)}
              >
                Post Job Opening
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
