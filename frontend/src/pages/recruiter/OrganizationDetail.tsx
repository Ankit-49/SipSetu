import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  ArrowLeft,
  Plus,
  Trash2,
  UserPlus,
  Settings,
  Users,
  Briefcase,
  BarChart3,
} from "lucide-react";
import { toast } from "sonner";

const ROLE_LABELS: Record<string, string> = {
  owner: "Owner",
  admin: "Admin",
  hiring_manager: "Hiring Manager",
  interviewer: "Interviewer",
  viewer: "Viewer",
};

const ROLE_COLORS: Record<string, string> = {
  owner: "bg-amber-100 text-amber-800",
  admin: "bg-blue-100 text-blue-800",
  hiring_manager: "bg-purple-100 text-purple-800",
  interviewer: "bg-green-100 text-green-800",
  viewer: "bg-slate-100 text-slate-600",
};

interface OrgDetail {
  org_id: string;
  name: string;
  slug: string;
  description: string | null;
  website: string | null;
  industry: string | null;
  size: string | null;
  logo_url: string | null;
  your_role: string;
  member_count: number;
  created_at: string;
}

interface Member {
  membership_id: string;
  user_id: string;
  email: string;
  name: string;
  role: string;
  inviter_name: string | null;
  joined_at: string;
}

interface DashboardStats {
  total_members: number;
  total_jobs: number;
  total_applications: number;
  unique_applicants: number;
  application_status_breakdown: Record<string, number>;
  jobs_posted_this_week: number;
  avg_match_score: number;
}

interface OrgJob {
  job_id: string;
  title: string;
  location: string;
  job_type: string;
  created_at: string;
  skills: string[];
}

export default function OrganizationDetailPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const navigate = useNavigate();
  const [org, setOrg] = useState<OrgDetail | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [dashboard, setDashboard] = useState<DashboardStats | null>(null);
  const [jobs, setJobs] = useState<OrgJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("viewer");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsForm, setSettingsForm] = useState({
    name: "",
    description: "",
    website: "",
    industry: "",
    size: "",
  });

  const isAdmin = ["owner", "admin"].includes(org?.your_role || "");

  useEffect(() => {
    if (orgId) loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  const loadAll = async () => {
    try {
      const [orgRes, membersRes, dashRes, jobsRes] = await Promise.all([
        api.get(`/organizations/${orgId}`),
        api.get(`/organizations/${orgId}/members`),
        api.get(`/organizations/${orgId}/dashboard`),
        api.get(`/organizations/${orgId}/jobs`),
      ]);
      setOrg(orgRes.data);
      setMembers(membersRes.data.members);
      setDashboard(dashRes.data);
      setJobs(jobsRes.data.jobs);
      setSettingsForm({
        name: orgRes.data.name || "",
        description: orgRes.data.description || "",
        website: orgRes.data.website || "",
        industry: orgRes.data.industry || "",
        size: orgRes.data.size || "",
      });
    } catch {
      toast.error("Failed to load organization");
      navigate("/recruiter/organizations");
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async () => {
    if (!inviteEmail.trim()) {
      toast.error("Email is required");
      return;
    }
    try {
      // First find user by email (using admin user list)
      const userRes = await api.get("/admin/users", {
        params: { search: inviteEmail },
      });
      const users = userRes.data.users || [];
      const target = users.find(
        (u: { email: string }) => u.email === inviteEmail
      );
      if (!target) {
        toast.error("No recruiter found with that email");
        return;
      }
      await api.post(`/organizations/${orgId}/members`, {
        user_id: target.user_id,
        role: inviteRole,
      });
      toast.success("Member invited!");
      setInviteOpen(false);
      setInviteEmail("");
      setInviteRole("viewer");
      loadAll();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: string } } }).response?.data
          ?.error || "Failed to invite member";
      toast.error(msg);
    }
  };

  const handleRemoveMember = async (membershipId: string) => {
    try {
      await api.delete(`/organizations/${orgId}/members/${membershipId}`);
      toast.success("Member removed");
      loadAll();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: string } } }).response?.data
          ?.error || "Failed to remove member";
      toast.error(msg);
    }
  };

  const handleUpdateRole = async (membershipId: string, newRole: string) => {
    try {
      await api.put(`/organizations/${orgId}/members/${membershipId}`, {
        role: newRole,
      });
      toast.success("Role updated");
      loadAll();
    } catch {
      toast.error("Failed to update role");
    }
  };

  const handleSaveSettings = async () => {
    try {
      await api.put(`/organizations/${orgId}`, settingsForm);
      toast.success("Settings saved");
      setSettingsOpen(false);
      loadAll();
    } catch {
      toast.error("Failed to update settings");
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-slate-200 rounded w-64 animate-pulse" />
        <div className="h-64 bg-slate-100 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (!org) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link
            to="/recruiter/organizations"
            className="inline-flex items-center text-sm text-slate-500 hover:text-[#1E3A5F] mb-2 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Organizations
          </Link>
          <div className="flex items-center gap-3 mt-1">
            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-[#1E3A5F] to-[#2d5a8e] flex items-center justify-center text-white font-bold text-lg">
              {org.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">{org.name}</h1>
              <div className="flex items-center gap-2 mt-0.5">
                <Badge variant="secondary" className="text-xs">
                  {ROLE_LABELS[org.your_role]}
                </Badge>
                {org.industry && (
                  <Badge variant="outline" className="text-xs">
                    {org.industry}
                  </Badge>
                )}
                {org.size && (
                  <Badge variant="outline" className="text-xs">
                    {org.size}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>
        {isAdmin && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSettingsOpen(true)}
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
        )}
      </div>

      {/* Tabs */}
      <Tabs defaultValue="dashboard">
        <TabsList>
          <TabsTrigger value="dashboard">
            <BarChart3 className="h-4 w-4 mr-2" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="members">
            <Users className="h-4 w-4 mr-2" />
            Members ({members.length})
          </TabsTrigger>
          <TabsTrigger value="jobs">
            <Briefcase className="h-4 w-4 mr-2" />
            Team Jobs
          </TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="space-y-4">
          {dashboard && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-slate-500">Team Members</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {dashboard.total_members}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-slate-500">Total Jobs</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {dashboard.total_jobs}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-slate-500">Applications</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {dashboard.total_applications}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-slate-500">Avg Match Score</p>
                    <p className="text-2xl font-bold text-[#1E3A5F]">
                      {dashboard.avg_match_score}%
                    </p>
                  </CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-slate-500">
                      Application Status Breakdown
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {Object.keys(dashboard.application_status_breakdown).length ===
                    0 ? (
                      <p className="text-sm text-slate-400">No applications yet</p>
                    ) : (
                      <div className="space-y-2">
                        {Object.entries(dashboard.application_status_breakdown).map(
                          ([status, count]) => (
                            <div key={status} className="flex items-center justify-between">
                              <Badge
                                variant="secondary"
                                className={
                                  status === "shortlisted"
                                    ? "bg-green-100 text-green-800"
                                    : status === "rejected"
                                    ? "bg-red-100 text-red-800"
                                    : ""
                                }
                              >
                                {status}
                              </Badge>
                              <span className="font-medium">{count as number}</span>
                            </div>
                          )
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-slate-500">
                      Weekly Activity
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-600">Jobs posted this week</span>
                        <span className="font-bold text-lg text-[#1E3A5F]">
                          {dashboard.jobs_posted_this_week}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-600">Unique applicants</span>
                        <span className="font-bold text-lg text-[#1E3A5F]">
                          {dashboard.unique_applicants}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </TabsContent>

        {/* Members Tab */}
        <TabsContent value="members" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Team Members</h2>
            {isAdmin && (
              <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
                <DialogTrigger asChild>
                  <Button size="sm" className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
                    <UserPlus className="h-4 w-4 mr-2" />
                    Invite Member
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Invite Team Member</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label>Email</Label>
                      <div className="flex gap-2">
                        <Input
                          placeholder="colleague@company.com"
                          type="email"
                          value={inviteEmail}
                          onChange={(e) => setInviteEmail(e.target.value)}
                        />
                      </div>
                      <p className="text-xs text-slate-400">
                        Must be a registered recruiter on SipSetu
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label>Role</Label>
                      <Select value={inviteRole} onValueChange={setInviteRole}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="admin">Admin</SelectItem>
                          <SelectItem value="hiring_manager">Hiring Manager</SelectItem>
                          <SelectItem value="interviewer">Interviewer</SelectItem>
                          <SelectItem value="viewer">Viewer</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setInviteOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleInvite} className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
                      Send Invite
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            )}
          </div>

          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Member</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((m) => (
                  <TableRow key={m.membership_id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{m.name || "Unknown"}</p>
                        <p className="text-xs text-slate-400">{m.email}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      {isAdmin &&
                      m.role !== "owner" &&
                      m.user_id !== org.org_id ? (
                        <Select
                          value={m.role}
                          onValueChange={(v) => handleUpdateRole(m.membership_id, v)}
                        >
                          <SelectTrigger className="w-36 h-8">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="admin">Admin</SelectItem>
                            <SelectItem value="hiring_manager">Hiring Manager</SelectItem>
                            <SelectItem value="interviewer">Interviewer</SelectItem>
                            <SelectItem value="viewer">Viewer</SelectItem>
                          </SelectContent>
                        </Select>
                      ) : (
                        <Badge className={ROLE_COLORS[m.role]}>
                          {ROLE_LABELS[m.role]}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-slate-500">
                      {m.joined_at
                        ? new Date(m.joined_at).toLocaleDateString()
                        : "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      {isAdmin && m.role !== "owner" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveMember(m.membership_id)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        {/* Jobs Tab */}
        <TabsContent value="jobs" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Team Job Postings</h2>
            <Link to="/recruiter/post-job">
              <Button size="sm" className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
                <Plus className="h-4 w-4 mr-2" />
                Post Job
              </Button>
            </Link>
          </div>

          {jobs.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Briefcase className="h-10 w-10 text-slate-300 mb-3" />
                <p className="text-slate-500">No team jobs yet</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {jobs.map((job) => (
                <Card key={job.job_id} className="hover:shadow-sm transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium">{job.title}</h3>
                        <p className="text-xs text-slate-400 mt-1">
                          {job.location || "Remote"} · {job.job_type || "Full-time"}
                        </p>
                      </div>
                      <span className="text-xs text-slate-400">
                        {job.created_at
                          ? new Date(job.created_at).toLocaleDateString()
                          : ""}
                      </span>
                    </div>
                    {job.skills && job.skills.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {job.skills.slice(0, 4).map((s) => (
                          <Badge key={s} variant="secondary" className="text-xs">
                            {s}
                          </Badge>
                        ))}
                        {job.skills.length > 4 && (
                          <Badge variant="secondary" className="text-xs">
                            +{job.skills.length - 4}
                          </Badge>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Settings Dialog */}
      <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Organization Settings</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Name</Label>
              <Input
                value={settingsForm.name}
                onChange={(e) =>
                  setSettingsForm((f) => ({ ...f, name: e.target.value }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                rows={3}
                value={settingsForm.description}
                onChange={(e) =>
                  setSettingsForm((f) => ({ ...f, description: e.target.value }))
                }
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Industry</Label>
                <Input
                  value={settingsForm.industry}
                  onChange={(e) =>
                    setSettingsForm((f) => ({ ...f, industry: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Company Size</Label>
                <Select
                  value={settingsForm.size}
                  onValueChange={(v) =>
                    setSettingsForm((f) => ({ ...f, size: v }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1-10">1–10</SelectItem>
                    <SelectItem value="11-50">11–50</SelectItem>
                    <SelectItem value="51-200">51–200</SelectItem>
                    <SelectItem value="201-500">201–500</SelectItem>
                    <SelectItem value="500+">500+</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Website</Label>
              <Input
                value={settingsForm.website}
                onChange={(e) =>
                  setSettingsForm((f) => ({ ...f, website: e.target.value }))
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSettingsOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSaveSettings}
              className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90"
            >
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
