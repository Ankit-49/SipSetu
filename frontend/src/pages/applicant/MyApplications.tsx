import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Briefcase,
  Building,
  MapPin,
  Clock,
  CheckCircle2,
  XCircle,
  Hourglass,
  Loader2,
  Search,
} from "lucide-react";
import { Link } from "react-router";
import { useState, useEffect } from "react";
import { NotificationBell } from "@/components/NotificationBell";
import api from "@/lib/api";
import { useAuth } from "@/app/context/AuthContext";

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: any; bg: string }> = {
  shortlisted: {
    label: "Shortlisted",
    color: "text-green-700 bg-green-100 border-green-200 hover:bg-green-100",
    icon: CheckCircle2,
    bg: "bg-green-50",
  },
  rejected: {
    label: "Rejected",
    color: "text-red-700 bg-red-100 border-red-200 hover:bg-red-100",
    icon: XCircle,
    bg: "bg-red-50",
  },
  pending: {
    label: "Pending",
    color: "text-amber-700 bg-amber-100 border-amber-200 hover:bg-amber-100",
    icon: Hourglass,
    bg: "bg-amber-50",
  },
};

export default function ApplicantMyApplications() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    const fetchApplications = async () => {
      try {
        const response = await api.get(`/applicants/${user.id}/applications`);
        setData(response.data.applications || []);
      } catch (err) {
        console.error("Failed to fetch applications", err);
      } finally {
        setLoading(false);
      }
    };
    fetchApplications();
  }, [user]);

  const filtered = data.filter((app) => {
    if (statusFilter !== "all" && app.status !== statusFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const title = (app.title || "").toLowerCase();
      const company = (app.recruiter_company || app.recruiter_name || "").toLowerCase();
      const location = (app.location || "").toLowerCase();
      if (!title.includes(q) && !company.includes(q) && !location.includes(q)) return false;
    }
    return true;
  });

  const stats = {
    total: data.length,
    shortlisted: data.filter((a) => a.status === "shortlisted").length,
    pending: data.filter((a) => a.status === "pending").length,
    rejected: data.filter((a) => a.status === "rejected").length,
  };

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
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">My Applications</h1>
          <p className="text-slate-500 mt-1">Track the status of every job you've applied to.</p>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/applicant/matches">
            <Button variant="outline" className="gap-2">
              <Search className="h-4 w-4" /> Browse Jobs
            </Button>
          </Link>
          <NotificationBell />
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Total</p>
              <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
            </div>
            <div className="h-10 w-10 rounded-full bg-blue-50 flex items-center justify-center">
              <Briefcase className="h-5 w-5 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Shortlisted</p>
              <p className="text-2xl font-bold text-green-700">{stats.shortlisted}</p>
            </div>
            <div className="h-10 w-10 rounded-full bg-green-50 flex items-center justify-center">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Pending</p>
              <p className="text-2xl font-bold text-amber-700">{stats.pending}</p>
            </div>
            <div className="h-10 w-10 rounded-full bg-amber-50 flex items-center justify-center">
              <Hourglass className="h-5 w-5 text-amber-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">Rejected</p>
              <p className="text-2xl font-bold text-red-700">{stats.rejected}</p>
            </div>
            <div className="h-10 w-10 rounded-full bg-red-50 flex items-center justify-center">
              <XCircle className="h-5 w-5 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex items-center gap-2 flex-wrap">
          {[
            { value: "all", label: "All Applications" },
            { value: "pending", label: "Pending" },
            { value: "shortlisted", label: "Shortlisted" },
            { value: "rejected", label: "Rejected" },
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => setStatusFilter(tab.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                statusFilter === tab.value
                  ? "bg-[#1E3A5F] text-white"
                  : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
              }`}
            >
              {tab.label}
              {tab.value !== "all" && (
                <span className="ml-1.5 text-xs opacity-70">
                  ({data.filter((a) => a.status === tab.value).length})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by title, company..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 bg-white text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#F97316]/20 focus:border-[#F97316] transition-colors"
          />
        </div>
      </div>

      {/* Applications List */}
      {filtered.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <div className="mx-auto h-16 w-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
              <Briefcase className="h-8 w-8 text-slate-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">
              {data.length === 0 ? "No applications yet" : "No matching applications"}
            </h3>
            <p className="text-slate-500 mb-6 max-w-md mx-auto">
              {data.length === 0
                ? "Start applying to jobs that match your skills. Browse available positions and submit your application."
                : "Try adjusting your filters or search query to find what you're looking for."}
            </p>
            {data.length === 0 && (
              <Link to="/applicant/matches">
                <Button className="bg-[#F97316] hover:bg-[#e8630e] text-white gap-2">
                  <Search className="h-4 w-4" /> Browse Job Matches
                </Button>
              </Link>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filtered.map((app) => {
            const statusCfg = STATUS_CONFIG[app.status] || STATUS_CONFIG.pending;
            const StatusIcon = statusCfg.icon;
            const appliedDate = app.applied_at
              ? new Date(app.applied_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })
              : "Recently";

            return (
              <Card key={app.application_id} className="hover:shadow-md transition-shadow group">
                <CardContent className="p-5">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start gap-4">
                        <div className="h-12 w-12 rounded-lg bg-[#1E3A5F]/5 flex items-center justify-center shrink-0 mt-0.5">
                          <Building className="h-6 w-6 text-[#1E3A5F]" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-3 flex-wrap">
                            <h3 className="font-semibold text-slate-900 text-lg">{app.title}</h3>
                            <Badge className={STATUS_CONFIG[app.status]?.color || STATUS_CONFIG.pending.color}>
                              <StatusIcon className="h-3 w-3 mr-1 inline" />
                              {STATUS_CONFIG[app.status]?.label || "Pending"}
                            </Badge>
                          </div>
                          <p className="text-sm text-slate-500 mt-0.5">
                            {app.recruiter_company || app.recruiter_name}
                          </p>
                          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs text-slate-400">
                            {app.location && (
                              <span className="flex items-center gap-1">
                                <MapPin className="h-3 w-3" /> {app.location}
                              </span>
                            )}
                            {app.job_type && (
                              <span className="flex items-center gap-1">
                                <Briefcase className="h-3 w-3" /> {app.job_type}
                              </span>
                            )}
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" /> Applied {appliedDate}
                            </span>
                          </div>
                          {app.skills && app.skills.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-3">
                              {app.skills.slice(0, 5).map((skill: string) => (
                                <Badge
                                  key={skill}
                                  variant="outline"
                                  className="text-[11px] px-2 py-0.5 text-slate-500 bg-white"
                                >
                                  {skill}
                                </Badge>
                              ))}
                              {app.skills.length > 5 && (
                                <span className="text-[11px] text-slate-400 self-center">
                                  +{app.skills.length - 5} more
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 shrink-0 md:flex-col md:items-end">
                      {app.matching_score > 0 && (
                        <Badge
                          className={`${
                            app.matching_score >= 80
                              ? "bg-green-100 text-green-700 hover:bg-green-100"
                              : app.matching_score >= 50
                              ? "bg-blue-100 text-blue-700 hover:bg-blue-100"
                              : "bg-slate-100 text-slate-600 hover:bg-slate-100"
                          } border-none text-xs`}
                        >
                          {app.matching_score}% Match
                        </Badge>
                      )}
                      <Button variant="ghost" size="sm" className="text-slate-400 hover:text-[#1E3A5F] gap-1" disabled>
                        View Job
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
