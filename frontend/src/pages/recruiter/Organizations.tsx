import { useState, useEffect } from "react";
import { Link } from "react-router";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
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
import { Building2, Plus, Users, Briefcase, Globe, ArrowRight } from "lucide-react";
import { toast } from "sonner";

interface Organization {
  org_id: string;
  name: string;
  slug: string;
  logo_url: string | null;
  description: string | null;
  website: string | null;
  industry: string | null;
  size: string | null;
  member_count: number;
  created_at: string;
}

export default function RecruiterOrganizations() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    name: "",
    slug: "",
    description: "",
    website: "",
    industry: "",
    size: "",
  });

  useEffect(() => {
    fetchOrgs();
  }, []);

  const fetchOrgs = async () => {
    try {
      const res = await api.get("/organizations");
      setOrgs(res.data.organizations);
    } catch {
      toast.error("Failed to load organizations");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!form.name.trim()) {
      toast.error("Organization name is required");
      return;
    }
    setCreating(true);
    try {
      const slug =
        form.slug.trim() ||
        form.name
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-|-$/g, "");
      await api.post("/organizations", { ...form, slug });
      toast.success("Organization created!");
      setCreateOpen(false);
      setForm({ name: "", slug: "", description: "", website: "", industry: "", size: "" });
      fetchOrgs();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: string } } }).response?.data
          ?.error || "Failed to create organization";
      toast.error(msg);
    } finally {
      setCreating(false);
    }
  };

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-slate-200 rounded w-48 animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-48 bg-slate-100 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Organizations</h1>
          <p className="text-slate-500 mt-1">
            Manage your hiring teams and shared job pools
          </p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
              <Plus className="h-4 w-4 mr-2" />
              New Organization
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Create Organization</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="org-name">Name *</Label>
                <Input
                  id="org-name"
                  placeholder="e.g. Acme Corp"
                  value={form.name}
                  onChange={(e) => {
                    const name = e.target.value;
                    setForm((f) => ({
                      ...f,
                      name,
                      slug: f.slug || generateSlug(name),
                    }));
                  }}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="org-slug">Slug</Label>
                <Input
                  id="org-slug"
                  placeholder="auto-generated from name"
                  value={form.slug}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, slug: e.target.value }))
                  }
                />
                <p className="text-xs text-slate-400">
                  Used in URLs. Auto-generated if left blank.
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="org-desc">Description</Label>
                <Textarea
                  id="org-desc"
                  placeholder="What does your organization do?"
                  rows={3}
                  value={form.description}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, description: e.target.value }))
                  }
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="org-industry">Industry</Label>
                  <Input
                    id="org-industry"
                    placeholder="e.g. Technology"
                    value={form.industry}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, industry: e.target.value }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-size">Company Size</Label>
                  <Select
                    value={form.size}
                    onValueChange={(v) => setForm((f) => ({ ...f, size: v }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select size" />
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
                <Label htmlFor="org-website">Website</Label>
                <Input
                  id="org-website"
                  placeholder="https://example.com"
                  value={form.website}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, website: e.target.value }))
                  }
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleCreate}
                disabled={creating}
                className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90"
              >
                {creating ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {orgs.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Building2 className="h-12 w-12 text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-600 mb-2">
              No organizations yet
            </h3>
            <p className="text-slate-400 text-center max-w-sm mb-4">
              Create an organization to collaborate with your hiring team, share
              job pools, and track team performance.
            </p>
            <Button
              onClick={() => setCreateOpen(true)}
              className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Your First Organization
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {orgs.map((org) => (
            <Link key={org.org_id} to={`/recruiter/organizations/${org.org_id}`}>
              <Card className="hover:shadow-md transition-all duration-200 cursor-pointer group border-slate-200 hover:border-[#1E3A5F]/30 h-full">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-[#1E3A5F] to-[#2d5a8e] flex items-center justify-center text-white font-bold text-sm">
                        {org.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <CardTitle className="text-base group-hover:text-[#1E3A5F] transition-colors">
                          {org.name}
                        </CardTitle>
                        <p className="text-xs text-slate-400">{org.slug}</p>
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-slate-300 group-hover:text-[#1E3A5F] transition-colors mt-1" />
                  </div>
                </CardHeader>
                <CardContent>
                  {org.description && (
                    <p className="text-sm text-slate-500 line-clamp-2 mb-3">
                      {org.description}
                    </p>
                  )}
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary" className="text-xs">
                      <Users className="h-3 w-3 mr-1" />
                      {org.member_count} members
                    </Badge>
                    {org.industry && (
                      <Badge variant="secondary" className="text-xs">
                        <Briefcase className="h-3 w-3 mr-1" />
                        {org.industry}
                      </Badge>
                    )}
                    {org.website && (
                      <Badge variant="secondary" className="text-xs">
                        <Globe className="h-3 w-3 mr-1" />
                        {new URL(org.website).hostname}
                      </Badge>
                    )}
                    {org.size && (
                      <Badge variant="outline" className="text-xs">
                        {org.size} employees
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
