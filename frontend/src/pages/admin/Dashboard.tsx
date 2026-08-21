import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Users,
  Briefcase,
  FileText,
  BarChart3,
  Activity,
  Search,
  Shield,
  Trash2,
  UserX,
  UserCheck,
  RefreshCw,
  Loader2,
  Clock,
  TrendingUp,
} from "lucide-react";
import { toast } from "@/hooks/use-toast";
import api from "@/lib/api";

type AdminStats = {
  users: { total: number; applicants: number; recruiters: number };
  jobs: { total: number };
  applications: { total: number; by_status: Record<string, number> };
  resumes: { total: number };
  weekly_jobs: Record<string, number>;
  weekly_registrations: Record<string, number>;
  system: { database: string };
};

type UserRow = {
  user_id: string;
  email: string;
  name: string;
  role: string;
  email_verified: boolean;
  created_at: string;
};

type JobRow = {
  job_id: string;
  title: string;
  recruiter_name: string;
  recruiter_id: string;
  location: string;
  job_type: string;
  created_at: string;
  application_count: number;
};

export default function AdminDashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [userSearch, setUserSearch] = useState("");
  const [userPage, setUserPage] = useState(1);
  const [userTotal, setUserTotal] = useState(0);
  const [jobs, setJobs] = useState<JobRow[]>([]);
  const [jobSearch, setJobSearch] = useState("");
  const [jobPage, setJobPage] = useState(1);
  const [jobTotal, setJobTotal] = useState(0);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [userSearch, userPage]);

  useEffect(() => {
    fetchJobs();
  }, [jobSearch, jobPage]);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await api.get("/admin/stats");
      setStats(res.data);
    } catch (err) {
      toast({ title: "Error", description: "Failed to load admin stats", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const params = new URLSearchParams({ page: String(userPage), per_page: "15" });
      if (userSearch) params.set("search", userSearch);
      const res = await api.get(`/admin/users?${params}`);
      setUsers(res.data.users || []);
      setUserTotal(res.data.total || 0);
    } catch {
      setUsers([]);
    }
  };

  const fetchJobs = async () => {
    try {
      const params = new URLSearchParams({ page: String(jobPage), per_page: "15" });
      if (jobSearch) params.set("search", jobSearch);
      const res = await api.get(`/admin/jobs?${params}`);
      setJobs(res.data.jobs || []);
      setJobTotal(res.data.total || 0);
    } catch {
      setJobs([]);
    }
  };

  const suspendUser = async (userId: string, suspend: boolean) => {
    setActionLoading(userId);
    try {
      await api.patch(`/admin/users/${userId}/suspend`, { suspend });
      toast({ title: suspend ? "User suspended" : "User unsuspended" });
      fetchUsers();
    } catch {
      toast({ title: "Error", description: "Failed to update user", variant: "destructive" });
    } finally {
      setActionLoading(null);
    }
  };

  const deleteJob = async (jobId: string) => {
    if (!confirm("Are you sure you want to delete this job?")) return;
    setActionLoading(jobId);
    try {
      await api.delete(`/admin/jobs/${jobId}`);
      toast({ title: "Job deleted" });
      fetchJobs();
      fetchStats();
    } catch {
      toast({ title: "Error", description: "Failed to delete job", variant: "destructive" });
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#F97316]" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            <Shield className="h-8 w-8 text-[#1E3A5F]" /> Admin Dashboard
          </h1>
          <p className="text-slate-500 mt-1">Platform overview, user management, and system health.</p>
        </div>
        <Button variant="outline" onClick={fetchStats} className="gap-2">
          <RefreshCw className="h-4 w-4" /> Refresh
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-blue-50 text-blue-600"><Users className="h-5 w-5" /></div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats?.users.total ?? 0}</p>
                <p className="text-xs text-slate-500">Total Users</p>
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-2">
              {stats?.users.applicants ?? 0} applicants · {stats?.users.recruiters ?? 0} recruiters
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-[#F97316]/10 text-[#F97316]"><Briefcase className="h-5 w-5" /></div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats?.jobs.total ?? 0}</p>
                <p className="text-xs text-slate-500">Job Postings</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-green-50 text-green-600"><FileText className="h-5 w-5" /></div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats?.applications.total ?? 0}</p>
                <p className="text-xs text-slate-500">Applications</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-1 mt-2">
              {Object.entries(stats?.applications.by_status ?? {}).map(([status, count]) => (
                <Badge key={status} variant="secondary" className="text-[10px]">
                  {status}: {count}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-purple-50 text-purple-600"><Activity className="h-5 w-5" /></div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats?.resumes.total ?? 0}</p>
                <p className="text-xs text-slate-500">Resumes</p>
              </div>
            </div>
            <p className="text-xs mt-2">
              DB: <span className={stats?.system.database === "ok" ? "text-green-600" : "text-red-600"}>
                {stats?.system.database ?? "unknown"}
              </span>
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="users">
        <TabsList className="bg-white border border-slate-200">
          <TabsTrigger value="users" className="gap-1.5"><Users className="h-3.5 w-3.5" /> Users ({userTotal})</TabsTrigger>
          <TabsTrigger value="jobs" className="gap-1.5"><Briefcase className="h-3.5 w-3.5" /> Jobs ({jobTotal})</TabsTrigger>
          <TabsTrigger value="activity" className="gap-1.5"><Clock className="h-3.5 w-3.5" /> Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="mt-4">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-3">
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="Search by name or email..."
                    value={userSearch}
                    onChange={(e) => { setUserSearch(e.target.value); setUserPage(1); }}
                    className="pl-9"
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-slate-100">
                {users.map((u) => (
                  <div key={u.user_id} className="flex items-center justify-between px-5 py-3 hover:bg-slate-50">
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-slate-900 truncate">{u.name || u.email}</p>
                      <p className="text-sm text-slate-500 truncate">{u.email}</p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <Badge variant={u.role === "recruiter" ? "default" : "secondary"}>
                        {u.role}
                      </Badge>
                      <Badge variant={u.email_verified ? "default" : "destructive"}>
                        {u.email_verified ? "Verified" : "Unverified"}
                      </Badge>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => suspendUser(u.user_id, u.email_verified)}
                        disabled={actionLoading === u.user_id}
                        className="text-red-500 hover:text-red-700"
                      >
                        {u.email_verified ? <UserX className="h-4 w-4" /> : <UserCheck className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                ))}
                {users.length === 0 && (
                  <p className="p-8 text-center text-slate-400">No users found.</p>
                )}
              </div>
              {userTotal > 15 && (
                <div className="flex justify-center gap-2 p-4 border-t border-slate-100">
                  <Button size="sm" variant="outline" disabled={userPage <= 1} onClick={() => setUserPage(p => p - 1)}>Previous</Button>
                  <span className="text-sm text-slate-500 py-1">Page {userPage} of {Math.ceil(userTotal / 15)}</span>
                  <Button size="sm" variant="outline" disabled={userPage * 15 >= userTotal} onClick={() => setUserPage(p => p + 1)}>Next</Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="jobs" className="mt-4">
          <Card>
            <CardHeader className="pb-3">
              <div className="relative max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search jobs..."
                  value={jobSearch}
                  onChange={(e) => { setJobSearch(e.target.value); setJobPage(1); }}
                  className="pl-9"
                />
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-slate-100">
                {jobs.map((j) => (
                  <div key={j.job_id} className="flex items-center justify-between px-5 py-3 hover:bg-slate-50">
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-slate-900 truncate">{j.title}</p>
                      <p className="text-sm text-slate-500">
                        by {j.recruiter_name} · {j.location || "No location"} · {j.application_count} applicants
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => deleteJob(j.job_id)}
                      disabled={actionLoading === j.job_id}
                      className="text-red-500 hover:text-red-700 shrink-0"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
                {jobs.length === 0 && (
                  <p className="p-8 text-center text-slate-400">No jobs found.</p>
                )}
              </div>
              {jobTotal > 15 && (
                <div className="flex justify-center gap-2 p-4 border-t border-slate-100">
                  <Button size="sm" variant="outline" disabled={jobPage <= 1} onClick={() => setJobPage(p => p - 1)}>Previous</Button>
                  <span className="text-sm text-slate-500 py-1">Page {jobPage} of {Math.ceil(jobTotal / 15)}</span>
                  <Button size="sm" variant="outline" disabled={jobPage * 15 >= jobTotal} onClick={() => setJobPage(p => p + 1)}>Next</Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" /> Weekly Trends
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-semibold text-slate-700 mb-3">Jobs Posted per Week</h4>
                  <div className="space-y-2">
                    {Object.entries(stats?.weekly_jobs ?? {}).map(([week, count]) => (
                      <div key={week} className="flex items-center gap-3">
                        <span className="text-xs text-slate-500 w-16">{week}</span>
                        <div className="flex-1 bg-slate-100 rounded-full h-4">
                          <div
                            className="bg-[#1E3A5F] rounded-full h-4 flex items-center justify-end pr-2"
                            style={{ width: `${Math.min(100, (count / Math.max(...Object.values(stats?.weekly_jobs ?? { a: 1 }), 1)) * 100)}%` }}
                          >
                            <span className="text-[10px] text-white font-bold">{count}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                    {Object.keys(stats?.weekly_jobs ?? {}).length === 0 && (
                      <p className="text-sm text-slate-400">No data yet.</p>
                    )}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-700 mb-3">Registrations per Week</h4>
                  <div className="space-y-2">
                    {Object.entries(stats?.weekly_registrations ?? {}).map(([week, count]) => (
                      <div key={week} className="flex items-center gap-3">
                        <span className="text-xs text-slate-500 w-16">{week}</span>
                        <div className="flex-1 bg-slate-100 rounded-full h-4">
                          <div
                            className="bg-[#F97316] rounded-full h-4 flex items-center justify-end pr-2"
                            style={{ width: `${Math.min(100, (count / Math.max(...Object.values(stats?.weekly_registrations ?? { a: 1 }), 1)) * 100)}%` }}
                          >
                            <span className="text-[10px] text-white font-bold">{count}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                    {Object.keys(stats?.weekly_registrations ?? {}).length === 0 && (
                      <p className="text-sm text-slate-400">No data yet.</p>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
