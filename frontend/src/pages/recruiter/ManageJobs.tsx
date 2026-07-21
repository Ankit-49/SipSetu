import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Briefcase,
  MapPin,
  Clock,
  DollarSign,
  Pencil,
  Trash2,
  Loader2,
  Plus,
  Save,
  Eye,
  Search,
  TrendingUp,
} from "lucide-react";
import { Link } from "react-router";
import { useState, useEffect, useMemo } from "react";
import { NotificationBell } from "@/components/NotificationBell";
import { useToast } from "@/hooks/use-toast";
import api from "@/lib/api";
import { useAuth } from "@/app/context/AuthContext";

const EXPERIENCE_MAP: Record<string, string> = {
  fresher: "Fresher",
  "1-3": "1-3 years",
  "3-5": "3-5 years",
  "5+": "5+ years",
  Entry: "Entry",
  Mid: "Mid",
  Senior: "Senior",
  Lead: "Lead",
};

export default function RecruiterManageJobs() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [jobs, setJobs] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  // Edit state
  const [editJob, setEditJob] = useState<any>(null);
  const [saving, setSaving] = useState(false);

  // Delete state
  const [deleteJobId, setDeleteJobId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchJobs = async () => {
    if (!user) return;
    try {
      const response = await api.get(`/jobs?recruiter_id=${user.id}&per_page=100`);
      setJobs(response.data.jobs || []);
    } catch (err) {
      console.error("Failed to fetch jobs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    fetchJobs();
  }, [user]);

  const filtered = useMemo(() => {
    if (!searchQuery) return jobs;
    const q = searchQuery.toLowerCase();
    return jobs.filter(
      (j) =>
        (j.title || "").toLowerCase().includes(q) ||
        (j.location || "").toLowerCase().includes(q) ||
        (j.job_type || "").toLowerCase().includes(q) ||
        (j.skills || []).some((s: string) => s.toLowerCase().includes(q))
    );
  }, [jobs, searchQuery]);

  // Stats
  const stats = useMemo(() => {
    const total = jobs.length;
    const withSalary = jobs.filter((j) => j.salary_min || j.salary_max).length;
    return { total, withSalary };
  }, [jobs]);

  // --- Edit handlers ---
  const openEdit = (job: any) => {
    setEditJob({
      job_id: job.job_id,
      title: job.title || "",
      description: job.description || "",
      location: job.location || "",
      job_type: job.job_type || "",
      experience_level: job.experience_level || "",
      salary_min: job.salary_min || "",
      salary_max: job.salary_max || "",
      skills: (job.skills || []).join(", "),
    });
  };

  const handleSaveEdit = async () => {
    if (!editJob) return;
    setSaving(true);
    try {
      const skillsArray = editJob.skills
        ? editJob.skills.split(",").map((s: string) => s.trim()).filter(Boolean)
        : [];

      await api.put(`/jobs/${editJob.job_id}`, {
        title: editJob.title,
        description: editJob.description,
        location: editJob.location,
        job_type: editJob.job_type,
        experience_level: editJob.experience_level,
        salary_min: editJob.salary_min || null,
        salary_max: editJob.salary_max || null,
        skills: skillsArray,
      });

      toast({ title: "Job updated successfully" });
      setEditJob(null);
      await fetchJobs();
    } catch (err: any) {
      const msg = err?.response?.data?.error || "Failed to update job";
      toast({ title: "Error", description: msg, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  // --- Delete handlers ---
  const handleDeleteJob = async () => {
    if (!deleteJobId) return;
    setDeleting(true);
    try {
      await api.delete(`/jobs/${deleteJobId}`);
      toast({ title: "Job deleted successfully" });
      setDeleteJobId(null);
      await fetchJobs();
    } catch (err: any) {
      const msg = err?.response?.data?.error || "Failed to delete job";
      toast({ title: "Error", description: msg, variant: "destructive" });
    } finally {
      setDeleting(false);
    }
  };

  // --- Renderers ---
  const renderEditModal = () => {
    if (!editJob) return null;
    return (
      <Dialog open={!!editJob} onOpenChange={() => setEditJob(null)}>
        <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-slate-900">Edit Job Posting</DialogTitle>
            <DialogDescription>Update the details of your job posting below.</DialogDescription>
          </DialogHeader>
          <div className="space-y-5 py-4">
            <div className="space-y-2">
              <Label htmlFor="m-edit-title">
                Job Title <span className="text-red-500">*</span>
              </Label>
              <Input
                id="m-edit-title"
                value={editJob.title}
                onChange={(e) => setEditJob({ ...editJob, title: e.target.value })}
                placeholder="e.g. Senior Software Engineer"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="m-edit-desc">Job Description</Label>
              <Textarea
                id="m-edit-desc"
                value={editJob.description}
                onChange={(e) => setEditJob({ ...editJob, description: e.target.value })}
                placeholder="Describe the role, responsibilities, and requirements..."
                rows={5}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="m-edit-skills">Skills (comma-separated)</Label>
              <Input
                id="m-edit-skills"
                value={editJob.skills}
                onChange={(e) => setEditJob({ ...editJob, skills: e.target.value })}
                placeholder="e.g. Python, React, SQL, Machine Learning"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="m-edit-location">Location</Label>
                <Input
                  id="m-edit-location"
                  value={editJob.location}
                  onChange={(e) => setEditJob({ ...editJob, location: e.target.value })}
                  placeholder="e.g. New York, NY"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="m-edit-type">Job Type</Label>
                <Select
                  value={editJob.job_type}
                  onValueChange={(v) => setEditJob({ ...editJob, job_type: v })}
                >
                  <SelectTrigger id="m-edit-type">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Full-time">Full-time</SelectItem>
                    <SelectItem value="Part-time">Part-time</SelectItem>
                    <SelectItem value="Contract">Contract</SelectItem>
                    <SelectItem value="Internship">Internship</SelectItem>
                    <SelectItem value="Remote">Remote</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="m-edit-exp">Experience Level</Label>
                <Select
                  value={editJob.experience_level}
                  onValueChange={(v) => setEditJob({ ...editJob, experience_level: v })}
                >
                  <SelectTrigger id="m-edit-exp">
                    <SelectValue placeholder="Select level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Entry">Entry</SelectItem>
                    <SelectItem value="Mid">Mid</SelectItem>
                    <SelectItem value="Senior">Senior</SelectItem>
                    <SelectItem value="Lead">Lead</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Salary Range</Label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="number"
                    placeholder="Min"
                    value={editJob.salary_min}
                    onChange={(e) => setEditJob({ ...editJob, salary_min: e.target.value })}
                  />
                  <Input
                    type="number"
                    placeholder="Max"
                    value={editJob.salary_max}
                    onChange={(e) => setEditJob({ ...editJob, salary_max: e.target.value })}
                  />
                </div>
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2 border-t border-slate-100">
            <Button variant="outline" onClick={() => setEditJob(null)} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={handleSaveEdit} disabled={saving || !editJob.title.trim()}>
              {saving ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Saving...</>
              ) : (
                <><Save className="h-4 w-4 mr-2" /> Save Changes</>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  };

  const renderDeleteDialog = () => (
    <AlertDialog open={!!deleteJobId} onOpenChange={() => setDeleteJobId(null)}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="text-lg font-bold text-slate-900">
            Delete Job Posting
          </AlertDialogTitle>
          <AlertDialogDescription className="text-slate-600">
            Are you sure you want to delete this job posting? This action cannot be undone.
            All associated applications, rankings, and notifications will be permanently removed.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDeleteJob}
            disabled={deleting}
            className="bg-red-600 hover:bg-red-700 text-white focus:ring-red-600"
          >
            {deleting ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Deleting...</>
            ) : (
              <><Trash2 className="h-4 w-4 mr-2" /> Delete</>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#F97316] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Manage Jobs</h1>
          <p className="text-slate-500 mt-1">View, edit, and manage all your job postings.</p>
        </div>
        <div className="flex items-center gap-3">
          <NotificationBell />
          <Link to="/recruiter/post-job">
            <Button className="bg-[#F97316] hover:bg-[#e8630e] text-white gap-2">
              <Plus className="h-4 w-4" /> New Job
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Total Jobs</p>
              <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
            </div>
            <div className="h-10 w-10 rounded-full bg-blue-50 flex items-center justify-center">
              <Briefcase className="h-5 w-5 text-[#1E3A5F]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">With Salary</p>
              <p className="text-2xl font-bold text-slate-900">{stats.withSalary}</p>
            </div>
            <div className="h-10 w-10 rounded-full bg-green-50 flex items-center justify-center">
              <DollarSign className="h-5 w-5 text-green-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Active</p>
              <p className="text-2xl font-bold text-green-700">{stats.total}</p>
            </div>
            <div className="h-10 w-10 rounded-full bg-amber-50 flex items-center justify-center">
              <TrendingUp className="h-5 w-5 text-amber-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="relative w-full sm:w-80">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <input
          type="text"
          placeholder="Search by title, location, skills..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-slate-200 bg-white text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#F97316]/20 focus:border-[#F97316] transition-colors"
        />
      </div>

      {/* Jobs List */}
      {filtered.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <div className="mx-auto h-16 w-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
              <Briefcase className="h-8 w-8 text-slate-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">
              {jobs.length === 0 ? "No jobs posted yet" : "No matching jobs"}
            </h3>
            <p className="text-slate-500 mb-6 max-w-md mx-auto">
              {jobs.length === 0
                ? "Create your first job posting to start receiving AI-ranked candidate matches."
                : "Try adjusting your search query to find what you're looking for."}
            </p>
            {jobs.length === 0 && (
              <Link to="/recruiter/post-job">
                <Button className="bg-[#F97316] hover:bg-[#e8630e] text-white gap-2">
                  <Plus className="h-4 w-4" /> Post Your First Job
                </Button>
              </Link>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filtered.map((job) => {
            const expKey = job.experience_level || "";
            const expLabel = EXPERIENCE_MAP[expKey] || expKey;
            const createdDate = job.created_at
              ? new Date(job.created_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })
              : "Unknown";

            return (
              <Card key={job.job_id} className="hover:shadow-md transition-shadow group">
                <CardContent className="p-5">
                  <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                    {/* Left: Job info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start gap-3">
                        <div className="h-10 w-10 rounded-lg bg-[#1E3A5F]/5 flex items-center justify-center shrink-0 mt-0.5">
                          <Briefcase className="h-5 w-5 text-[#1E3A5F]" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-3 flex-wrap">
                            <h3 className="font-semibold text-slate-900 text-base">{job.title}</h3>
                            <Badge className="bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-50">
                              Active
                            </Badge>
                          </div>

                          {/* Meta row */}
                          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs text-slate-500">
                            {job.location && (
                              <span className="flex items-center gap-1">
                                <MapPin className="h-3 w-3" /> {job.location}
                              </span>
                            )}
                            {job.job_type && (
                              <span className="flex items-center gap-1">
                                <Briefcase className="h-3 w-3" /> {job.job_type}
                              </span>
                            )}
                            {expLabel && (
                              <span className="flex items-center gap-1">
                                <TrendingUp className="h-3 w-3" /> {expLabel}
                              </span>
                            )}
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" /> {createdDate}
                            </span>
                          </div>

                          {/* Skills */}
                          {job.skills && job.skills.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-3">
                              {job.skills.slice(0, 6).map((skill: string) => (
                                <Badge
                                  key={skill}
                                  variant="outline"
                                  className="text-[11px] px-2 py-0.5 text-slate-500 bg-white"
                                >
                                  {skill}
                                </Badge>
                              ))}
                              {job.skills.length > 6 && (
                                <span className="text-[11px] text-slate-400 self-center">
                                  +{job.skills.length - 6} more
                                </span>
                              )}
                            </div>
                          )}

                          {/* Description snippet */}
                          {job.description && (
                            <p className="text-xs text-slate-400 mt-3 line-clamp-2">
                              {job.description}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Right: Salary + Actions */}
                    <div className="flex flex-row lg:flex-col items-center lg:items-end gap-3 shrink-0">
                      {(job.salary_min || job.salary_max) && (
                        <Badge
                          variant="secondary"
                          className="bg-green-50 text-green-700 border-green-200 text-xs whitespace-nowrap"
                        >
                          NPR
                          {job.salary_min
                            ? ` ${Number(job.salary_min).toLocaleString()}`
                            : " 0"}
                          {job.salary_max
                            ? ` - ${Number(job.salary_max).toLocaleString()}`
                            : ""}
                          {" LPA"}
                        </Badge>
                      )}
                      <div className="flex items-center gap-2">
                        <Link to={`/recruiter/candidates?job_id=${job.job_id}`}>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-slate-500 hover:text-[#1E3A5F] hover:bg-blue-50 gap-1.5"
                          >
                            <Eye className="h-3.5 w-3.5" /> Candidates
                          </Button>
                        </Link>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-slate-500 hover:text-[#1E3A5F] hover:bg-blue-50 gap-1.5"
                          onClick={() => openEdit(job)}
                        >
                          <Pencil className="h-3.5 w-3.5" /> Edit
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-slate-500 hover:text-red-600 hover:bg-red-50 gap-1.5"
                          onClick={() => setDeleteJobId(job.job_id)}
                        >
                          <Trash2 className="h-3.5 w-3.5" /> Delete
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Modals */}
      {renderEditModal()}
      {renderDeleteDialog()}
    </div>
  );
}
