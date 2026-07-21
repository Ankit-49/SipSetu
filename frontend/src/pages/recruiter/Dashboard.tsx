import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Briefcase, Users, UserCheck, TrendingUp, ChevronRight, FileText, Plus, ExternalLink } from "lucide-react";
import { Link } from "react-router";
import { useState, useEffect } from "react";
import { NotificationBell } from "@/components/NotificationBell";
import api from "@/lib/api";
import { useAuth } from "@/app/context/AuthContext";

export default function RecruiterDashboardHome() {
  const { user } = useAuth();
  const date = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchDashboard();
  }, [user]);

  const fetchDashboard = async () => {
    if (!user) return;
    try {
      const response = await api.get(`/recruiters/${user.id}/dashboard`);
      setData(response.data);
    } catch (err) {
      console.error("Failed to fetch recruiter dashboard", err);
    } finally {
      setLoading(false);
    }
  };

  const topCandidates = data?.top_candidates || [];
  const activeJobs = data?.jobs || [];
  // ------------- Edit Job Modal -------------
  const renderEditModal = () => {
    if (!editJob) return null;
    return (
      <Dialog open={!!editJob} onOpenChange={() => setEditJob(null)}>
        <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-slate-900">Edit Job Posting</DialogTitle>
            <DialogDescription>
              Update the details of your job posting below.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-5 py-4">
            {/* Title */}
            <div className="space-y-2">
              <Label htmlFor="edit-title">Job Title <span className="text-red-500">*</span></Label>
              <Input
                id="edit-title"
                value={editJob.title}
                onChange={(e) => setEditJob({ ...editJob, title: e.target.value })}
                placeholder="e.g. Senior Software Engineer"
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="edit-desc">Job Description</Label>
              <Textarea
                id="edit-desc"
                value={editJob.description}
                onChange={(e) => setEditJob({ ...editJob, description: e.target.value })}
                placeholder="Describe the role, responsibilities, and requirements..."
                rows={5}
              />
            </div>

            {/* Skills */}
            <div className="space-y-2">
              <Label htmlFor="edit-skills">Skills (comma-separated)</Label>
              <Input
                id="edit-skills"
                value={editJob.skills}
                onChange={(e) => setEditJob({ ...editJob, skills: e.target.value })}
                placeholder="e.g. Python, React, SQL, Machine Learning"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Location */}
              <div className="space-y-2">
                <Label htmlFor="edit-location">Location</Label>
                <Input
                  id="edit-location"
                  value={editJob.location}
                  onChange={(e) => setEditJob({ ...editJob, location: e.target.value })}
                  placeholder="e.g. New York, NY"
                />
              </div>

              {/* Job Type */}
              <div className="space-y-2">
                <Label htmlFor="edit-type">Job Type</Label>
                <Select
                  value={editJob.job_type}
                  onValueChange={(v) => setEditJob({ ...editJob, job_type: v })}
                >
                  <SelectTrigger id="edit-type">
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

              {/* Experience Level */}
              <div className="space-y-2">
                <Label htmlFor="edit-exp">Experience Level</Label>
                <Select
                  value={editJob.experience_level}
                  onValueChange={(v) => setEditJob({ ...editJob, experience_level: v })}
                >
                  <SelectTrigger id="edit-exp">
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

              {/* Salary Range */}
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

  // ------------- Delete Confirmation -------------
  const renderDeleteDialog = () => {
    return (
      <AlertDialog open={!!deleteJobId} onOpenChange={() => setDeleteJobId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="text-lg font-bold text-slate-900">Delete Job Posting</AlertDialogTitle>
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
  };

  const userName = data?.name || user?.name || localStorage.getItem("user_name") || "Recruiter";

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#F97316] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Good morning, {userName.split(' ')[0]} 👋</h1>
          <p className="text-slate-500 mt-1">{date}</p>
        </div>
        <div className="flex items-center gap-4">
          <NotificationBell />
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Active Postings</p>
              <p className="text-3xl font-bold text-slate-900">{data?.active_postings ?? 0}</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-blue-50 flex items-center justify-center">
              <Briefcase className="h-6 w-6 text-[#1E3A5F]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Total Candidates</p>
              <p className="text-3xl font-bold text-slate-900">{data?.total_candidates ?? 0}</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center">
              <Users className="h-6 w-6 text-slate-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Top Match</p>
              <p className="text-3xl font-bold text-[#F97316]">{Number(data?.top_match_score ?? 0).toFixed(2)}%</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-orange-50 flex items-center justify-center">
              <UserCheck className="h-6 w-6 text-[#F97316]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Recent Jobs</p>
              <div className="flex items-center gap-2">
                <p className="text-3xl font-bold text-slate-900">{activeJobs.length}</p>
                <TrendingUp className="h-4 w-4 text-green-500" />
              </div>
            </div>
            <div className="h-12 w-12 rounded-full bg-green-50 flex items-center justify-center">
              <Users className="h-6 w-6 text-green-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Top Candidates */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2 border-b border-slate-100">
            <CardTitle className="text-lg font-bold">Top Matches (AI Ranked)</CardTitle>
            <Link to="/recruiter/candidates">
              <Button variant="ghost" size="sm" className="text-slate-500 hover:text-[#1E3A5F]">
                View All <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100">
              {topCandidates.length === 0 ? (
                <div className="p-8 text-center text-slate-500">No ranked candidates yet. Upload resumes and create jobs to see matches.</div>
              ) : topCandidates.map((candidate: any) => (
                <div key={`${candidate.applicant_id}-${candidate.job_title}`} className="p-4 flex items-center justify-between gap-4 hover:bg-slate-50 transition-colors group min-w-0">
                  <div className="flex items-start gap-4 min-w-0 flex-1">
                    <div className="h-10 w-10 rounded-full bg-[#1E3A5F] text-white flex items-center justify-center font-semibold text-sm shrink-0 mt-0.5">
                      {candidate.applicant_name.split(' ').map((n: string) => n[0]).join('')}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-semibold text-slate-900">{candidate.applicant_name}</h3>
                        <Badge className="bg-green-100 text-green-700 hover:bg-green-100 border-none h-5 text-[10px] shrink-0">
                          {Number(candidate.matching_score).toFixed(2)}% Match
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-500 truncate">{candidate.job_title}</p>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {candidate.resume_skills.map((s: string) => (
                          <Badge key={s} variant="outline" className="text-[11px] px-2 py-0.5 text-slate-500 bg-white">
                            {s}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 shrink-0">
                    <Button variant="outline" size="sm" className="gap-2">
                      <FileText className="h-3.5 w-3.5" /> Resume
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Postings */}
        <Card>
          <CardHeader className="pb-2 border-b border-slate-100 flex flex-row items-center justify-between">
            <CardTitle className="text-lg font-bold">Active Job Postings</CardTitle>
            <Link to="/recruiter/post-job">
              <Button size="sm" className="bg-[#F97316] hover:bg-[#e8630e] text-white gap-1.5">
                <Plus className="h-4 w-4" /> New Job
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100">
              {activeJobs.length === 0 ? (
                <div className="p-8 text-center text-slate-500">No active job postings yet.</div>
              ) : activeJobs.map((post: any) => (
                <div key={post.job_id} className="p-4 hover:bg-slate-50 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-semibold text-slate-900">{post.title}</h4>
                    <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50 border-blue-200">Active</Badge>
                  </div>
                  <div className="flex justify-between items-center text-sm text-slate-500">
                    <span className="flex items-center gap-1.5"><Users className="h-3.5 w-3.5" /> {data?.total_candidates ?? 0} Candidates</span>
                    <span>{post.created_at ? new Date(post.created_at).toLocaleDateString() : "Recent"}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="p-3 bg-slate-50 border-t border-slate-100 text-center rounded-b-xl">
              <Link to="/recruiter/jobs" className="text-sm font-medium text-[#1E3A5F] hover:underline inline-flex items-center gap-1">
                Manage Jobs <ExternalLink className="h-3 w-3" />
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

    </div>
  );
}
