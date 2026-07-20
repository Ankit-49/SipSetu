import { useState, useEffect, useRef, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import {
  FileText,
  UploadCloud,
  Loader2,
  CheckCircle2,
  Plus,
  X,
  Save,
  Trash2,
  Pencil,
  Sparkles,
  GraduationCap,
  Briefcase,
  User,
  Download,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import api from "@/lib/api";
import { useAuth } from "@/app/context/AuthContext";

// ----- Structured resume types -----

interface EducationEntry {
  id: string;
  school: string;
  degree: string;
  field: string;
  startYear: string;
  endYear: string;
}

interface ExperienceEntry {
  id: string;
  company: string;
  role: string;
  location: string;
  startDate: string;
  endDate: string;
  description: string;
}

interface ResumeForm {
  fullName: string;
  headline: string;
  summary: string;
  skills: string[];
  education: EducationEntry[];
  experience: ExperienceEntry[];
}

const EMPTY_EDUCATION: Omit<EducationEntry, "id"> = {
  school: "",
  degree: "",
  field: "",
  startYear: "",
  endYear: "",
};

const EMPTY_EXPERIENCE: Omit<ExperienceEntry, "id"> = {
  company: "",
  role: "",
  location: "",
  startDate: "",
  endDate: "",
  description: "",
};

const EMPTY_FORM: ResumeForm = {
  fullName: "",
  headline: "",
  summary: "",
  skills: [],
  education: [],
  experience: [],
};

const uid = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2) + Date.now().toString(36);

/**
 * Heuristic parser: if the existing raw_text doesn't look like a structured
 * builder document (i.e. it's a free-form PDF extract), we surface the
 * already-stored skills as the form's skill chips (so the user can refine
 * them in the builder) and leave the summary empty with a placeholder. The
 * raw_text is kept on the form as `rawTextOriginal` only for reference; we
 * do NOT dump the full PDF text into the summary because the user can't
 * sensibly edit a 800-character wall of text.
 *
 * If the raw_text does look builder-generated, we parse sections back into
 * the form. Stored skills still win as the chip list so we never lose a
 * skill the user previously had.
 */
function parseRawTextIntoForm(
  rawText: string,
  profileName?: string | null,
  storedSkills: string[] = []
): ResumeForm {
  const form: ResumeForm = {
    ...EMPTY_FORM,
    fullName: profileName || "",
    skills: storedSkills.slice(),
  };
  if (!rawText) return form;

  // Builder-generated docs start with "Name: ..." and "Headline: ...".
  const isStructured = /^Name:\s*/m.test(rawText) && /^Headline:\s*/m.test(rawText);
  if (!isStructured) {
    // Free-form PDF text — skills come from the stored associations on the
    // resume row (already extracted server-side). We leave the summary blank
    // so the user can write their own pitch instead of editing a giant blob.
    return form;
  }

  const grab = (label: string): string => {
    const re = new RegExp(`^${label}:\\s*([\\s\\S]*?)(?=\\n[A-Z][a-zA-Z]+:|$)`, "m");
    const match = rawText.match(re);
    return match ? match[1].trim() : "";
  };

  const name = grab("Name");
  const headline = grab("Headline");
  const summary = grab("Summary");
  const skillsBlock = grab("Skills");
  const educationBlock = grab("Education");
  const experienceBlock = grab("Experience");

  if (name) form.fullName = name;
  if (headline) form.headline = headline;
  if (summary) form.summary = summary;

  if (skillsBlock) {
    const parsed = skillsBlock
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    // Merge with stored skills so we don't drop anything that the server
    // extracted but the builder save lost (e.g. a custom skill the user
    // added through the form and was re-extracted on save).
    const merged = Array.from(new Set([...form.skills, ...parsed]));
    form.skills = merged;
  }

  if (educationBlock) {
    form.education = educationBlock
      .split(/\n\s*-\s*/)
      .map((s) => s.trim())
      .filter(Boolean)
      .map((line) => {
        // Expected shape: "Degree in Field at School (startYear - endYear)"
        const atMatch = line.match(/^(.*?)\s+at\s+(.*?)\s*\((\d{4})\s*-\s*(\d{4}|Present)\)\s*$/i);
        if (atMatch) {
          const degreeField = atMatch[1].trim();
          const school = atMatch[2].trim();
          const startYear = atMatch[3];
          const endYear = atMatch[4] === "Present" ? "" : atMatch[4];
          const [degree, ...fieldParts] = degreeField.split(/\s+in\s+/i);
          return {
            id: uid(),
            school,
            degree: degree?.trim() || "",
            field: fieldParts.join(" in ").trim(),
            startYear,
            endYear,
          };
        }
        return { id: uid(), school: line, degree: "", field: "", startYear: "", endYear: "" };
      });
  }

  if (experienceBlock) {
    form.experience = experienceBlock
      .split(/\n\s*-\s*/)
      .map((s) => s.trim())
      .filter(Boolean)
      .map((line) => {
        // Expected shape: "Role at Company, Location (startDate - endDate): description"
        const match = line.match(
          /^(.*?)\s+at\s+(.*?),\s*(.*?)\s*\((.*?)\s*-\s*(.*?)\):\s*([\s\S]*)$/
        );
        if (match) {
          return {
            id: uid(),
            role: match[1].trim(),
            company: match[2].trim(),
            location: match[3].trim(),
            startDate: match[4].trim(),
            endDate: match[5].trim(),
            description: match[6].trim(),
          };
        }
        return { ...EMPTY_EXPERIENCE, id: uid(), company: line };
      });
  }

  return form;
}

function buildRawText(form: ResumeForm): string {
  const lines: string[] = [];
  lines.push(`Name: ${form.fullName.trim() || "Unknown"}`);
  lines.push(`Headline: ${form.headline.trim() || "N/A"}`);
  lines.push("");
  lines.push("Summary:");
  lines.push(form.summary.trim() || "(no summary)");
  lines.push("");
  lines.push("Skills:");
  if (form.skills.length === 0) {
    lines.push("(none listed)");
  } else {
    lines.push(form.skills.map((s) => s.trim()).filter(Boolean).join(", "));
  }
  lines.push("");
  lines.push("Education:");
  if (form.education.length === 0) {
    lines.push("(no education listed)");
  } else {
    form.education.forEach((e) => {
      const degreeField = [e.degree, e.field].filter(Boolean).join(" in ");
      const dates = [e.startYear, e.endYear || "Present"].filter(Boolean).join(" - ");
      lines.push(`- ${degreeField || "Degree"} at ${e.school || "School"} (${dates || "dates unknown"})`);
    });
  }
  lines.push("");
  lines.push("Experience:");
  if (form.experience.length === 0) {
    lines.push("(no experience listed)");
  } else {
    form.experience.forEach((exp) => {
      const dates = [exp.startDate, exp.endDate || "Present"].filter(Boolean).join(" - ");
      lines.push(
        `- ${exp.role || "Role"} at ${exp.company || "Company"}, ${exp.location || "Location"} (${dates || "dates unknown"}): ${exp.description || ""}`.trim()
      );
    });
  }
  return lines.join("\n");
}

export default function ApplicantResume() {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);

  // The latest resume row for this applicant, or null if none exists.
  const [resume, setResume] = useState<any>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (pendingFile) {
      const url = URL.createObjectURL(pendingFile);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setPreviewUrl(null);
    }
  }, [pendingFile]);

  // The active tab — when no resume exists, force the builder tab so users
  // can start creating one immediately.
  const [activeTab, setActiveTab] = useState<string>("builder");

  // Builder form state
  const [form, setForm] = useState<ResumeForm>(EMPTY_FORM);
  const [skillDraft, setSkillDraft] = useState("");
  // Track whether the user has made unsaved changes
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // ---------- data loading ----------

  const fetchResume = async () => {
    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setLoading(false);
      return;
    }      try {
          const res = await api.get(`/resumes?applicant_id=${userId}`);
      if (res.data && res.data.length > 0) {
        const latest = res.data[0];
        setResume(latest);
        // Fetch the full raw_text (list endpoint does not return it) so we
        // can pre-populate the builder for edits. We also pass the stored
        // skills so PDF-extracted skills show up as chips in the builder
        // (the raw_text alone is unstructured for a PDF, so the parser
        // would otherwise leave the skill list empty).
        try {
          const detail = await api.get(`/resumes/${latest.resume_id}`);
          const profileName = localStorage.getItem("user_name");
          const storedSkills: string[] = (detail.data.skills as string[]) || latest.skills || [];
          setForm(
            parseRawTextIntoForm(
              detail.data.raw_text || "",
              profileName,
              storedSkills
            )
          );
        } catch {
          // Fall back to whatever skills we have so the user can still edit.
          setForm((prev) => ({ ...prev, skills: latest.skills || [] }));
        }
      } else {
        setResume(null);
        // No resume yet — prefill the form with the profile name so the
        // first save isn't blank.
        setForm({ ...EMPTY_FORM, fullName: localStorage.getItem("user_name") || "" });
        setActiveTab("builder");
      }
    } catch (err) {
      console.error("Failed to load resume", err);
      toast({
        title: "Failed to load resume",
        description: "Could not reach the server. Check your connection.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResume();
  }, []);

  // ---------- derived: skills currently in the saved resume ----------

  // Use form.skills as the source of truth so the right column updates
  // live as the user edits the builder. The resume.skills is the snapshot
  // from the server (used until the first edit).
  const currentSkills = useMemo(() => {
    return form.skills.map((s) => s.trim()).filter(Boolean);
  }, [form.skills]);

  // ---------- form helpers ----------

  const addSkill = () => {
    const v = skillDraft.trim();
    if (!v) return;
    if (form.skills.some((s) => s.toLowerCase() === v.toLowerCase())) {
      setSkillDraft("");
      return;
    }
    setForm({ ...form, skills: [...form.skills, v] });
    setSkillDraft("");
  };

  const removeSkill = (skill: string) => {
    setForm({ ...form, skills: form.skills.filter((s) => s !== skill) });
    setHasUnsavedChanges(true);
  };

  const addEducation = () => {
    setForm({
      ...form,
      education: [...form.education, { ...EMPTY_EDUCATION, id: uid() }],
    });
    setHasUnsavedChanges(true);
  };

  const updateEducation = (id: string, patch: Partial<EducationEntry>) => {
    setForm({
      ...form,
      education: form.education.map((e) => (e.id === id ? { ...e, ...patch } : e)),
    });
    setHasUnsavedChanges(true);
  };

  const removeEducation = (id: string) => {
    // Immediately remove from local state — do NOT re-fetch from server until user saves
    setForm((prev) => ({ ...prev, education: prev.education.filter((e) => e.id !== id) }));
    setHasUnsavedChanges(true);
  };

  const addExperience = () => {
    setForm({
      ...form,
      experience: [...form.experience, { ...EMPTY_EXPERIENCE, id: uid() }],
    });
    setHasUnsavedChanges(true);
  };

  const updateExperience = (id: string, patch: Partial<ExperienceEntry>) => {
    setForm({
      ...form,
      experience: form.experience.map((e) => (e.id === id ? { ...e, ...patch } : e)),
    });
    setHasUnsavedChanges(true);
  };

  const removeExperience = (id: string) => {
    // Immediately remove from local state — do NOT re-fetch from server until user saves
    setForm((prev) => ({ ...prev, experience: prev.experience.filter((e) => e.id !== id) }));
    setHasUnsavedChanges(true);
  };

  // ---------- actions ----------

  const handleSave = async () => {
    const userId = localStorage.getItem("user_id");
    if (!userId) {
      toast({ title: "Not logged in", variant: "destructive" });
      return;
    }

    if (!form.fullName.trim()) {
      toast({
        title: "Add your name",
        description: "Your resume needs a name at the top before saving.",
        variant: "destructive",
      });
      return;
    }

    setSaving(true);
    const rawText = buildRawText(form);
    // The form's skills list is the source of truth for what the user
    // has approved. Send it to the backend so edits (additions and
    // removals) survive a re-save even when the underlying raw_text
    // doesn't contain those exact words.
    const skillsPayload = form.skills
      .map((s) => s.trim())
      .filter(Boolean);
    // Capture current form state before save so we can restore it
    // after fetchResume (prevents server-merged skills from overriding deletions).
    const formSnapshot = { ...form };

    try {
      if (resume?.resume_id) {
        // Update existing resume
        const res = await api.put(`/resumes/${resume.resume_id}`, {
          raw_text: rawText,
          file_path: resume.file_path || null,
          skills: skillsPayload,
        });
        toast({
          title: "Resume updated ✓",
          description: `${res.data.skill_count} skill${res.data.skill_count === 1 ? "" : "s"} saved. Your matches will refresh.`,
        });
      } else {
        // First-time create
        const res = await api.post("/resumes", {
          applicant_id: userId,
          raw_text: rawText,
          skills: skillsPayload,
        });
        toast({
          title: "Resume created ✓",
          description: `${res.data.skills_extracted.length} skill${res.data.skills_extracted.length === 1 ? "" : "s"} detected. Start applying to jobs!`,
        });
      }
      // Only refresh the resume metadata (id, uploaded_at etc.) — do NOT
      // re-parse raw_text from the server, which would merge back deleted
      // entries from storedSkills. Keep the user's current form state.
      const userId2 = localStorage.getItem("user_id");
      if (userId2) {
        const metaRes = await api.get(`/resumes?applicant_id=${userId2}`);
        if (metaRes.data?.length > 0) setResume(metaRes.data[0]);
      }
      // Restore form snapshot so deletions remain visible without a full refetch
      setForm(formSnapshot);
      setHasUnsavedChanges(false);
    } catch (err: any) {
      toast({
        title: "Save failed",
        description: err.response?.data?.error || "Could not save your resume.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      toast({ title: "Invalid file", description: "Please upload a PDF file.", variant: "destructive" });
      return;
    }
    setPendingFile(file);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      toast({ title: "Invalid file", description: "Please drop a PDF file.", variant: "destructive" });
      return;
    }
    setPendingFile(file);
  };

  const handleUploadConfirm = async () => {
    if (!pendingFile) return;
    const userId = localStorage.getItem("user_id");
    if (!userId) {
      toast({ title: "Not logged in", variant: "destructive" });
      return;
    }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", pendingFile);
      formData.append("applicant_id", userId);
      const res = await api.post("/resumes/upload-pdf", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast({
        title: "Resume uploaded ✓",
        description: `${res.data.skill_count} skills extracted. Switching to Build tab to fine-tune.`,
      });
      await fetchResume();
      setActiveTab("builder");
      setPendingFile(null);
    } catch (err: any) {
      toast({
        title: "Upload failed",
        description: err.response?.data?.error || "Failed to upload resume.",
        variant: "destructive",
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadRaw = () => {
    const text = buildRawText(form);
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(form.fullName || "resume").replace(/\s+/g, "_")}_resume.txt`;
    a.click();
    URL.revokeObjectURL(url);
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
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">My Resume</h1>
          <p className="text-slate-500 mt-1">
            {resume
              ? "Update your profile so the matcher sees your latest skills."
              : "Create your resume so we can match you to the right roles."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {resume && (
            <Badge variant="secondary" className="bg-green-50 text-green-700 border-green-200">
              <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Active
            </Badge>
          )}
          {hasUnsavedChanges && (
            <Badge variant="secondary" className="bg-amber-50 text-amber-700 border-amber-200 animate-pulse">
              Unsaved changes
            </Badge>
          )}
          <Button
            onClick={handleSave}
            disabled={saving}
            className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90"
            data-testid="resume-save-btn"
          >
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" /> {resume ? "Update Resume" : "Create Resume"}
              </>
            )}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left + Center: editor (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-2 bg-slate-100">
              <TabsTrigger value="builder" data-testid="resume-tab-builder">
                <Pencil className="h-4 w-4 mr-2" /> Build / Edit
              </TabsTrigger>
              <TabsTrigger value="upload" data-testid="resume-tab-upload">
                <UploadCloud className="h-4 w-4 mr-2" /> Upload PDF
              </TabsTrigger>
            </TabsList>

            {/* ========== BUILDER TAB ========== */}
            <TabsContent value="builder" className="space-y-6 mt-6">
              {/* Identity */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5 text-[#1E3A5F]" /> Identity
                  </CardTitle>
                  <CardDescription>How you appear to recruiters.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="fullName">Full Name *</Label>
                      <Input
                        id="fullName"
                        value={form.fullName}
                        onChange={(e) => setForm({ ...form, fullName: e.target.value })}
                        placeholder="Ada Lovelace"
                        data-testid="resume-fullname"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="headline">Headline</Label>
                      <Input
                        id="headline"
                        value={form.headline}
                        onChange={(e) => setForm({ ...form, headline: e.target.value })}
                        placeholder="Senior Backend Engineer"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="summary">Summary</Label>
                    <Textarea
                      id="summary"
                      value={form.summary}
                      onChange={(e) => setForm({ ...form, summary: e.target.value })}
                      placeholder="A short pitch about what you do and what you want next."
                      rows={4}
                      data-testid="resume-summary"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Skills */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-[#F97316]" /> Skills
                  </CardTitle>
                  <CardDescription>
                    Add the technologies and strengths you want to be matched on. Press Enter to add.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <Input
                      value={skillDraft}
                      onChange={(e) => setSkillDraft(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addSkill();
                        }
                      }}
                      placeholder="e.g. Python, React, AWS"
                      data-testid="resume-skill-input"
                    />
                    <Button type="button" onClick={addSkill} variant="outline" data-testid="resume-add-skill">
                      <Plus className="h-4 w-4 mr-1" /> Add
                    </Button>
                  </div>
                  {form.skills.length === 0 ? (
                    <p className="text-sm text-slate-400 italic">No skills added yet.</p>
                  ) : (
                    <div className="flex flex-wrap gap-2" data-testid="resume-skill-chips">
                      {form.skills.map((skill) => (
                        <Badge
                          key={skill}
                          className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 text-white px-3 py-1 gap-1.5"
                        >
                          {skill}
                          <button
                            type="button"
                            onClick={() => removeSkill(skill)}
                            className="hover:text-orange-200"
                            aria-label={`Remove ${skill}`}
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Experience */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Briefcase className="h-5 w-5 text-[#1E3A5F]" /> Experience
                    </CardTitle>
                    <CardDescription>Most recent role first.</CardDescription>
                  </div>
                  <Button type="button" onClick={addExperience} variant="outline" size="sm" data-testid="resume-add-experience">
                    <Plus className="h-4 w-4 mr-1" /> Add role
                  </Button>
                </CardHeader>
                <CardContent className="space-y-6">
                  {form.experience.length === 0 ? (
                    <p className="text-sm text-slate-400 italic">No work experience added yet.</p>
                  ) : (
                    form.experience.map((exp, idx) => (
                      <div
                        key={exp.id}
                        className="rounded-xl border border-slate-200 p-4 space-y-3 bg-slate-50/40"
                        data-testid={`resume-experience-${idx}`}
                      >
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-semibold text-slate-700">Role #{idx + 1}</p>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeExperience(exp.id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          <div className="space-y-1.5">
                            <Label>Role</Label>
                            <Input
                              value={exp.role}
                              onChange={(e) => updateExperience(exp.id, { role: e.target.value })}
                              placeholder="Software Engineer"
                            />
                          </div>
                          <div className="space-y-1.5">
                            <Label>Company</Label>
                            <Input
                              value={exp.company}
                              onChange={(e) => updateExperience(exp.id, { company: e.target.value })}
                              placeholder="Acme Corp"
                            />
                          </div>
                          <div className="space-y-1.5">
                            <Label>Location</Label>
                            <Input
                              value={exp.location}
                              onChange={(e) => updateExperience(exp.id, { location: e.target.value })}
                              placeholder="Remote / Bangalore / ..."
                            />
                          </div>
                          <div className="grid grid-cols-2 gap-2">
                            <div className="space-y-1.5">
                              <Label>Start</Label>
                              <Input
                                value={exp.startDate}
                                onChange={(e) => updateExperience(exp.id, { startDate: e.target.value })}
                                placeholder="Jan 2022"
                              />
                            </div>
                            <div className="space-y-1.5">
                              <Label>End</Label>
                              <Input
                                value={exp.endDate}
                                onChange={(e) => updateExperience(exp.id, { endDate: e.target.value })}
                                placeholder="Present"
                              />
                            </div>
                          </div>
                        </div>
                        <div className="space-y-1.5">
                          <Label>Description</Label>
                          <Textarea
                            value={exp.description}
                            onChange={(e) => updateExperience(exp.id, { description: e.target.value })}
                            placeholder="What you owned, built, and the impact it had."
                            rows={3}
                          />
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>

              {/* Education */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <GraduationCap className="h-5 w-5 text-[#1E3A5F]" /> Education
                    </CardTitle>
                    <CardDescription>Degrees, bootcamps, certifications.</CardDescription>
                  </div>
                  <Button type="button" onClick={addEducation} variant="outline" size="sm" data-testid="resume-add-education">
                    <Plus className="h-4 w-4 mr-1" /> Add
                  </Button>
                </CardHeader>
                <CardContent className="space-y-6">
                  {form.education.length === 0 ? (
                    <p className="text-sm text-slate-400 italic">No education added yet.</p>
                  ) : (
                    form.education.map((ed, idx) => (
                      <div
                        key={ed.id}
                        className="rounded-xl border border-slate-200 p-4 space-y-3 bg-slate-50/40"
                        data-testid={`resume-education-${idx}`}
                      >
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-semibold text-slate-700">Entry #{idx + 1}</p>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeEducation(ed.id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          <div className="space-y-1.5">
                            <Label>School</Label>
                            <Input
                              value={ed.school}
                              onChange={(e) => updateEducation(ed.id, { school: e.target.value })}
                              placeholder="IIT Bombay"
                            />
                          </div>
                          <div className="space-y-1.5">
                            <Label>Degree</Label>
                            <Input
                              value={ed.degree}
                              onChange={(e) => updateEducation(ed.id, { degree: e.target.value })}
                              placeholder="B.Tech"
                            />
                          </div>
                          <div className="space-y-1.5">
                            <Label>Field of study</Label>
                            <Input
                              value={ed.field}
                              onChange={(e) => updateEducation(ed.id, { field: e.target.value })}
                              placeholder="Computer Science"
                            />
                          </div>
                          <div className="grid grid-cols-2 gap-2">
                            <div className="space-y-1.5">
                              <Label>Start year</Label>
                              <Input
                                value={ed.startYear}
                                onChange={(e) => updateEducation(ed.id, { startYear: e.target.value })}
                                placeholder="2018"
                              />
                            </div>
                            <div className="space-y-1.5">
                              <Label>End year</Label>
                              <Input
                                value={ed.endYear}
                                onChange={(e) => updateEducation(ed.id, { endYear: e.target.value })}
                                placeholder="2022"
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>

              <Separator />

              <div className="flex justify-between items-center">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={handleDownloadRaw}
                  className="text-slate-600"
                >
                  <Download className="h-4 w-4 mr-2" /> Download as .txt
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={saving}
                  className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90"
                  data-testid="resume-save-btn-bottom"
                >
                  {saving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" /> {resume ? "Update Resume" : "Create Resume"}
                    </>
                  )}
                </Button>
              </div>
            </TabsContent>

            {/* ========== UPLOAD TAB ========== */}
            <TabsContent value="upload" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>{resume ? "Replace Resume PDF" : "Upload Your Resume"}</CardTitle>
                  <CardDescription>
                    {resume
                      ? "Drop a new PDF to replace your current resume. Skills are auto-extracted and matched."
                      : "Upload your PDF resume and we'll extract your skills and experience automatically."}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Current resume info */}
                  {resume && (
                    <div className="p-4 border border-slate-200 rounded-xl bg-slate-50 flex items-start gap-4">
                      <div className="h-12 w-12 rounded-lg bg-red-100 flex items-center justify-center flex-shrink-0">
                        <FileText className="h-6 w-6 text-red-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-slate-900 truncate">
                          {resume.file_path || "Manual resume"}
                        </h4>
                        <p className="text-sm text-slate-500 mt-1">
                          {resume.uploaded_at &&
                            `Updated ${new Date(resume.uploaded_at).toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                              year: "numeric",
                            })}`}{" "}
                          • {resume.skills?.length || 0} skills detected
                        </p>
                        <div className="flex items-center gap-1.5 mt-1">
                          <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                          <span className="text-xs text-green-600 font-medium">Active for matching</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* File preview before upload */}
                  {pendingFile && !uploading && (
                    <div className="space-y-4">
                      <div className="p-4 border-2 border-[#1E3A5F]/40 rounded-xl bg-blue-50/60 flex items-center gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <div className="h-12 w-12 rounded-lg bg-[#1E3A5F]/10 flex items-center justify-center flex-shrink-0">
                          <FileText className="h-6 w-6 text-[#1E3A5F]" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-slate-900 truncate">{pendingFile.name}</p>
                          <p className="text-sm text-slate-500">{(pendingFile.size / 1024).toFixed(1)} KB • PDF</p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-slate-500 hover:text-red-600"
                            onClick={() => setPendingFile(null)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 text-white"
                            onClick={handleUploadConfirm}
                          >
                            <UploadCloud className="h-3.5 w-3.5 mr-1.5" /> Upload
                          </Button>
                        </div>
                      </div>
                      
                      {/* PDF Live Preview Iframe */}
                      {previewUrl && (
                        <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm bg-slate-100 p-1 animate-in fade-in zoom-in-95 duration-300">
                          <div className="bg-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 flex justify-between items-center">
                            <span>Document Preview</span>
                            <span className="text-[10px] bg-slate-300 text-slate-700 px-2 py-0.5 rounded-full">PDF Viewer</span>
                          </div>
                          <iframe
                            src={previewUrl}
                            className="w-full h-[380px] bg-white rounded-b-lg border-0"
                            title="PDF Resume Preview"
                          />
                        </div>
                      )}
                    </div>
                  )}

                  {/* Drop zone */}
                  <div
                    ref={dropZoneRef}
                    className={`relative border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 ${
                      isDragging
                        ? "border-[#F97316] bg-orange-50/60 shadow-[0_0_0_4px_rgba(249,115,22,0.15)] scale-[1.01]"
                        : "border-slate-300 bg-slate-50/50 hover:border-[#1E3A5F]/50 hover:bg-slate-50 hover:shadow-[0_0_0_3px_rgba(30,58,95,0.08)]"
                    }`}
                    onClick={() => !uploading && fileInputRef.current?.click()}
                    onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true); }}
                    onDragEnter={(e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true); }}
                    onDragLeave={(e) => { e.preventDefault(); e.stopPropagation(); if (!dropZoneRef.current?.contains(e.relatedTarget as Node)) setIsDragging(false); }}
                    onDrop={handleDrop}
                  >
                    <div className={`h-14 w-14 rounded-full flex items-center justify-center mb-4 transition-all duration-300 ${
                      isDragging ? "bg-orange-100 scale-110" : "bg-blue-50 group-hover:scale-110"
                    }`}>
                      {uploading ? (
                        <Loader2 className="h-7 w-7 text-[#1E3A5F] animate-spin" />
                      ) : isDragging ? (
                        <UploadCloud className="h-7 w-7 text-[#F97316]" />
                      ) : (
                        <UploadCloud className="h-7 w-7 text-[#1E3A5F]" />
                      )}
                    </div>
                    <h4 className={`font-semibold text-base ${ isDragging ? "text-[#F97316]" : "text-slate-900" }`}>
                      {uploading
                        ? "Analyzing your resume..."
                        : isDragging
                        ? "Release to upload"
                        : pendingFile
                        ? "Drop another file to replace"
                        : resume
                        ? "Drop PDF here or click to browse"
                        : "Drop your PDF here or click to browse"}
                    </h4>
                    <p className="text-sm text-slate-400 mt-1.5 max-w-xs">
                      {uploading
                        ? "Extracting skills and building your profile..."
                        : "Only PDF files are accepted · Max 10 MB"}
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
            </TabsContent>
          </Tabs>
        </div>

        {/* Right: live profile summary */}
        <div className="space-y-6">
          <Card className="lg:sticky lg:top-6">
            <CardHeader>
              <CardTitle>Profile Summary</CardTitle>
              <CardDescription>What the matcher sees right now.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Detected Skills ({currentSkills.length})
                </p>
                {currentSkills.length === 0 ? (
                  <p className="text-sm text-slate-400 italic">Add skills to start matching.</p>
                ) : (
                  <div className="flex flex-wrap gap-1.5" data-testid="resume-summary-skills">
                    {currentSkills.map((skill, i) => (
                      <Badge
                        key={skill}
                        className={
                          i < 4
                            ? "bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 text-white px-2.5 py-0.5"
                            : "bg-slate-100 text-slate-700 hover:bg-slate-200 px-2.5 py-0.5"
                        }
                      >
                        {skill}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              <Separator />

              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Identity</span>
                  <span className="font-medium text-slate-900 truncate max-w-[160px]">
                    {form.fullName || "—"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Headline</span>
                  <span className="font-medium text-slate-900 truncate max-w-[160px]">
                    {form.headline || "—"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Experience</span>
                  <span className="font-medium text-slate-900">
                    {form.experience.length} {form.experience.length === 1 ? "role" : "roles"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Education</span>
                  <span className="font-medium text-slate-900">
                    {form.education.length} {form.education.length === 1 ? "entry" : "entries"}
                  </span>
                </div>
              </div>

              {resume && (
                <>
                  <Separator />
                  <p className="text-xs text-slate-500">
                    Last saved{" "}
                    {new Date(resume.uploaded_at).toLocaleString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </p>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
