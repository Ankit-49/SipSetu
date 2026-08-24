import { useState, useEffect } from "react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
  Link2,
  Plus,
  Trash2,
  RefreshCw,
  Send,
  Calendar,
  MessageSquare,
  Shield,
  ExternalLink,
  CheckCircle2,
  XCircle,

} from "lucide-react";
import { toast } from "sonner";

// ─── Interfaces ────────────────────────────────────────────────────────────

interface ATSConnection {
  connection_id: string;
  provider: string;
  ats_org_id: string | null;
  sync_status: string;
  last_synced_at: string | null;
  is_active: boolean;
  created_at: string;
}

interface OAuthToken {
  token_id: string;
  provider: string;
  scopes: string;
  calendar_id: string | null;
  is_active: boolean;
  token_expiry: string;
  created_at: string;
}

interface Channel {
  channel_id: string;
  provider: string;
  channel_name: string | null;
  channel_id_external: string | null;
  events_subscribed: string;
  is_active: boolean;
  last_notified_at: string | null;
  created_at: string;
}

interface SSOProvider {
  provider_id: string;
  organization_id: string | null;
  name: string;
  protocol: string;
  issuer: string;
  redirect_url: string;
  auto_provision: boolean;
  default_role: string;
  is_active: boolean;
  created_at: string;
}



// ─── Status Badge Helpers ──────────────────────────────────────────────────

function StatusBadge({ active }: { active: boolean }) {
  return active ? (
    <Badge className="bg-green-100 text-green-800 text-xs">
      <CheckCircle2 className="h-3 w-3 mr-1" />
      Active
    </Badge>
  ) : (
    <Badge className="bg-red-100 text-red-800 text-xs">
      <XCircle className="h-3 w-3 mr-1" />
      Inactive
    </Badge>
  );
}

function SyncStatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    idle: "bg-slate-100 text-slate-600",
    syncing: "bg-blue-100 text-blue-800",
    synced: "bg-green-100 text-green-800",
    pending: "bg-amber-100 text-amber-800",
    error: "bg-red-100 text-red-800",
  };
  return (
    <Badge className={`${colors[status] || colors.idle} text-xs`}>
      {status === "syncing" && <RefreshCw className="h-3 w-3 mr-1 animate-spin" />}
      {status}
    </Badge>
  );
}

// ─── Provider Icons ────────────────────────────────────────────────────────

function ProviderIcon({ provider, size = "h-8 w-8" }: { provider: string; size?: string }) {
  const colors: Record<string, string> = {
    greenhouse: "from-green-500 to-green-600",
    lever: "from-blue-500 to-blue-600",
    workday: "from-indigo-500 to-indigo-600",
    google: "from-red-500 to-amber-500",
    microsoft: "from-blue-600 to-blue-700",
    slack: "from-purple-500 to-pink-500",
    teams: "from-blue-500 to-indigo-600",
    saml: "from-cyan-500 to-blue-500",
    oidc: "from-violet-500 to-purple-600",
  };
  return (
    <div className={`${size} rounded-lg bg-gradient-to-br ${colors[provider] || "from-slate-400 to-slate-500"} flex items-center justify-center text-white font-bold text-xs`}>
      {provider.charAt(0).toUpperCase()}
    </div>
  );
}

// ─── ATS Tab ───────────────────────────────────────────────────────────────

function ATSTab() {
  const [connections, setConnections] = useState<ATSConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ provider: "greenhouse", api_key: "", ats_org_id: "" });

  useEffect(() => { fetchConnections(); }, []);

  const fetchConnections = async () => {
    try {
      const res = await api.get("/ats/connections");
      setConnections(res.data);
    } catch {
      toast.error("Failed to load ATS connections");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!form.api_key.trim()) {
      toast.error("API key is required");
      return;
    }
    setCreating(true);
    try {
      await api.post("/ats/connections", {
        provider: form.provider,
        api_key: form.api_key,
        ats_org_id: form.ats_org_id || undefined,
      });
      toast.success("ATS connection created!");
      setCreateOpen(false);
      setForm({ provider: "greenhouse", api_key: "", ats_org_id: "" });
      fetchConnections();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } }).response?.data?.error || "Failed to create connection";
      toast.error(msg);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/ats/connections/${id}`);
      toast.success("Connection removed");
      fetchConnections();
    } catch {
      toast.error("Failed to remove connection");
    }
  };

  const handleSync = async (id: string) => {
    try {
      await api.post(`/ats/connections/${id}/sync`);
      toast.success("Sync started");
      fetchConnections();
    } catch {
      toast.error("Failed to start sync");
    }
  };

  if (loading) {
    return <div className="h-32 bg-slate-100 rounded-xl animate-pulse" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">ATS Connections</h3>
          <p className="text-sm text-slate-500">Connect your Applicant Tracking System</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
              <Plus className="h-4 w-4 mr-2" />
              Connect ATS
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Connect ATS</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Provider</Label>
                <Select value={form.provider} onValueChange={(v) => setForm((f) => ({ ...f, provider: v }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="greenhouse">Greenhouse</SelectItem>
                    <SelectItem value="lever">Lever</SelectItem>
                    <SelectItem value="workday">Workday</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>API Key *</Label>
                <Input
                  type="password"
                  placeholder="Enter your ATS API key"
                  value={form.api_key}
                  onChange={(e) => setForm((f) => ({ ...f, api_key: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>ATS Organization ID (optional)</Label>
                <Input
                  placeholder="Your ATS org identifier"
                  value={form.ats_org_id}
                  onChange={(e) => setForm((f) => ({ ...f, ats_org_id: e.target.value }))}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={creating} className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
                {creating ? "Connecting..." : "Connect"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {connections.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Link2 className="h-10 w-10 text-slate-300 mb-3" />
            <p className="text-slate-500 mb-4">No ATS connections yet</p>
            <Button onClick={() => setCreateOpen(true)} className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
              <Plus className="h-4 w-4 mr-2" />
              Connect Your ATS
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {connections.map((conn) => (
            <Card key={conn.connection_id} className="hover:shadow-sm transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <ProviderIcon provider={conn.provider} />
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium capitalize">{conn.provider}</p>
                        <StatusBadge active={conn.is_active} />
                        <SyncStatusBadge status={conn.sync_status} />
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {conn.last_synced_at
                          ? `Last synced ${new Date(conn.last_synced_at).toLocaleString()}`
                          : "Never synced"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSync(conn.connection_id)}
                      className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                    >
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(conn.connection_id)}
                      className="text-red-500 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Calendar Tab ──────────────────────────────────────────────────────────

function CalendarTab() {
  const [tokens, setTokens] = useState<OAuthToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ provider: "google", access_token: "" });

  useEffect(() => { fetchTokens(); }, []);

  const fetchTokens = async () => {
    try {
      const res = await api.get("/calendar/tokens");
      setTokens(res.data);
    } catch {
      toast.error("Failed to load calendar tokens");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!form.access_token.trim()) {
      toast.error("Access token is required");
      return;
    }
    setCreating(true);
    try {
      await api.post("/calendar/tokens", {
        provider: form.provider,
        access_token: form.access_token,
      });
      toast.success("Calendar connected!");
      setCreateOpen(false);
      setForm({ provider: "google", access_token: "" });
      fetchTokens();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } }).response?.data?.error || "Failed to connect calendar";
      toast.error(msg);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/calendar/tokens/${id}`);
      toast.success("Calendar disconnected");
      fetchTokens();
    } catch {
      toast.error("Failed to disconnect calendar");
    }
  };

  if (loading) {
    return <div className="h-32 bg-slate-100 rounded-xl animate-pulse" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Calendar Integrations</h3>
          <p className="text-sm text-slate-500">Sync interviews with Google Calendar or Outlook</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
              <Plus className="h-4 w-4 mr-2" />
              Connect Calendar
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Connect Calendar</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Provider</Label>
                <Select value={form.provider} onValueChange={(v) => setForm((f) => ({ ...f, provider: v }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="google">Google Calendar</SelectItem>
                    <SelectItem value="microsoft">Microsoft Outlook</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Access Token *</Label>
                <Input
                  type="password"
                  placeholder="OAuth access token from provider"
                  value={form.access_token}
                  onChange={(e) => setForm((f) => ({ ...f, access_token: e.target.value }))}
                />
                <p className="text-xs text-slate-400">
                  Complete the OAuth flow in your provider's dashboard and paste the token here
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={creating} className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
                {creating ? "Connecting..." : "Connect"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {tokens.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Calendar className="h-10 w-10 text-slate-300 mb-3" />
            <p className="text-slate-500 mb-4">No calendar integrations yet</p>
            <Button onClick={() => setCreateOpen(true)} className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
              <Plus className="h-4 w-4 mr-2" />
              Connect Calendar
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {tokens.map((token) => (
            <Card key={token.token_id} className="hover:shadow-sm transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <ProviderIcon provider={token.provider} />
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium capitalize">{token.provider === "google" ? "Google Calendar" : "Microsoft Outlook"}</p>
                        <StatusBadge active={token.is_active} />
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {token.calendar_id || "Default calendar"} · Expires {new Date(token.token_expiry).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(token.token_id)}
                      className="text-red-500 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Channels Tab ──────────────────────────────────────────────────────────

function ChannelsTab() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [availableEvents, setAvailableEvents] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    provider: "slack",
    webhook_url: "",
    channel_name: "",
    events_subscribed: "application.received,application.shortlisted",
  });

  useEffect(() => {
    Promise.all([
      api.get("/channels").catch(() => ({ data: [] })),
      api.get("/channels/events").catch(() => ({ data: { events: [] } })),
    ]).then(([chRes, evRes]) => {
      setChannels(chRes.data);
      setAvailableEvents(evRes.data.events);
      setLoading(false);
    });
  }, []);

  const handleCreate = async () => {
    if (!form.webhook_url.trim()) {
      toast.error("Webhook URL is required");
      return;
    }
    setCreating(true);
    try {
      await api.post("/channels", {
        provider: form.provider,
        webhook_url: form.webhook_url,
        channel_name: form.channel_name || undefined,
        events_subscribed: form.events_subscribed,
      });
      toast.success("Channel added!");
      setCreateOpen(false);
      setForm({ provider: "slack", webhook_url: "", channel_name: "", events_subscribed: "application.received,application.shortlisted" });
      const res = await api.get("/channels");
      setChannels(res.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } }).response?.data?.error || "Failed to add channel";
      toast.error(msg);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/channels/${id}`);
      toast.success("Channel removed");
      const res = await api.get("/channels");
      setChannels(res.data);
    } catch {
      toast.error("Failed to remove channel");
    }
  };

  const handleTest = async (id: string) => {
    try {
      await api.post(`/channels/${id}/test`);
      toast.success("Test notification sent!");
    } catch {
      toast.error("Failed to send test notification");
    }
  };

  const toggleEvent = (event: string) => {
    const current = form.events_subscribed.split(",").filter(Boolean);
    const updated = current.includes(event)
      ? current.filter((e) => e !== event)
      : [...current, event];
    setForm((f) => ({ ...f, events_subscribed: updated.join(",") }));
  };

  if (loading) {
    return <div className="h-32 bg-slate-100 rounded-xl animate-pulse" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Notification Channels</h3>
          <p className="text-sm text-slate-500">Get real-time alerts via Slack or Microsoft Teams</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
              <Plus className="h-4 w-4 mr-2" />
              Add Channel
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Add Notification Channel</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Platform</Label>
                <Select value={form.provider} onValueChange={(v) => setForm((f) => ({ ...f, provider: v }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="slack">Slack</SelectItem>
                    <SelectItem value="teams">Microsoft Teams</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Webhook URL *</Label>
                <Input
                  placeholder={form.provider === "slack" ? "https://hooks.slack.com/services/..." : "https://outlook.office.com/webhook/..."}
                  value={form.webhook_url}
                  onChange={(e) => setForm((f) => ({ ...f, webhook_url: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Channel Name (optional)</Label>
                <Input
                  placeholder="#hiring or Hiring Team"
                  value={form.channel_name}
                  onChange={(e) => setForm((f) => ({ ...f, channel_name: e.target.value }))}
                />
              </div>
              {availableEvents.length > 0 && (
                <div className="space-y-2">
                  <Label>Events to Subscribe</Label>
                  <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto border rounded-lg p-3">
                    {availableEvents.map((event) => (
                      <label key={event} className="flex items-center gap-2 text-sm cursor-pointer">
                        <input
                          type="checkbox"
                          checked={form.events_subscribed.split(",").includes(event)}
                          onChange={() => toggleEvent(event)}
                          className="rounded"
                        />
                        <span className="text-slate-600">{event}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={creating} className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
                {creating ? "Adding..." : "Add Channel"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {channels.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <MessageSquare className="h-10 w-10 text-slate-300 mb-3" />
            <p className="text-slate-500 mb-4">No notification channels yet</p>
            <Button onClick={() => setCreateOpen(true)} className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
              <Plus className="h-4 w-4 mr-2" />
              Add Your First Channel
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {channels.map((ch) => (
            <Card key={ch.channel_id} className="hover:shadow-sm transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <ProviderIcon provider={ch.provider} />
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{ch.channel_name || `#${ch.provider} channel`}</p>
                        <Badge variant="secondary" className="text-xs capitalize">{ch.provider}</Badge>
                        <StatusBadge active={ch.is_active} />
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {ch.events_subscribed.split(",").length} events · {ch.last_notified_at ? `Last notified ${new Date(ch.last_notified_at).toLocaleString()}` : "No notifications yet"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleTest(ch.channel_id)}
                      className="text-green-600 hover:text-green-700 hover:bg-green-50"
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(ch.channel_id)}
                      className="text-red-500 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── SSO Tab ───────────────────────────────────────────────────────────────

function SSOTab() {
  const [providers, setProviders] = useState<SSOProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    name: "",
    protocol: "oidc",
    issuer: "",
    client_id: "",
    client_secret: "",
    redirect_url: "",
    auto_provision: true,
    default_role: "viewer",
  });

  useEffect(() => { fetchProviders(); }, []);

  const fetchProviders = async () => {
    try {
      const res = await api.get("/sso/providers");
      setProviders(res.data);
    } catch {
      toast.error("Failed to load SSO providers");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!form.name.trim() || !form.issuer.trim() || !form.redirect_url.trim()) {
      toast.error("Name, issuer, and redirect URL are required");
      return;
    }
    setCreating(true);
    try {
      await api.post("/sso/providers", {
        name: form.name,
        protocol: form.protocol,
        issuer: form.issuer,
        client_id: form.client_id || undefined,
        client_secret: form.client_secret || undefined,
        redirect_url: form.redirect_url,
        auto_provision: form.auto_provision,
        default_role: form.default_role,
      });
      toast.success("SSO provider created!");
      setCreateOpen(false);
      setForm({ name: "", protocol: "oidc", issuer: "", client_id: "", client_secret: "", redirect_url: "", auto_provision: true, default_role: "viewer" });
      fetchProviders();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } }).response?.data?.error || "Failed to create SSO provider";
      toast.error(msg);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/sso/providers/${id}`);
      toast.success("SSO provider removed");
      fetchProviders();
    } catch {
      toast.error("Failed to remove SSO provider");
    }
  };

  if (loading) {
    return <div className="h-32 bg-slate-100 rounded-xl animate-pulse" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">SSO Providers</h3>
          <p className="text-sm text-slate-500">Enterprise single sign-on with SAML or OIDC</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
              <Plus className="h-4 w-4 mr-2" />
              Add SSO Provider
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Add SSO Provider</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Display Name *</Label>
                <Input placeholder="e.g. Corporate SSO" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label>Protocol *</Label>
                <Select value={form.protocol} onValueChange={(v) => setForm((f) => ({ ...f, protocol: v }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="oidc">OpenID Connect (OIDC)</SelectItem>
                    <SelectItem value="saml">SAML 2.0</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Issuer URL *</Label>
                <Input placeholder="https://login.microsoftonline.com/..." value={form.issuer} onChange={(e) => setForm((f) => ({ ...f, issuer: e.target.value }))} />
              </div>
              {form.protocol === "oidc" && (
                <>
                  <div className="space-y-2">
                    <Label>Client ID</Label>
                    <Input placeholder="OIDC client ID" value={form.client_id} onChange={(e) => setForm((f) => ({ ...f, client_id: e.target.value }))} />
                  </div>
                  <div className="space-y-2">
                    <Label>Client Secret</Label>
                    <Input type="password" placeholder="OIDC client secret" value={form.client_secret} onChange={(e) => setForm((f) => ({ ...f, client_secret: e.target.value }))} />
                  </div>
                </>
              )}
              <div className="space-y-2">
                <Label>Redirect URL *</Label>
                <Input placeholder="https://sipsetu.com/sso/callback" value={form.redirect_url} onChange={(e) => setForm((f) => ({ ...f, redirect_url: e.target.value }))} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Default Role</Label>
                  <Select value={form.default_role} onValueChange={(v) => setForm((f) => ({ ...f, default_role: v }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="viewer">Viewer</SelectItem>
                      <SelectItem value="interviewer">Interviewer</SelectItem>
                      <SelectItem value="hiring_manager">Hiring Manager</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2 flex items-end">
                  <label className="flex items-center gap-2 text-sm cursor-pointer pb-2">
                    <input
                      type="checkbox"
                      checked={form.auto_provision}
                      onChange={(e) => setForm((f) => ({ ...f, auto_provision: e.target.checked }))}
                      className="rounded"
                    />
                    Auto-provision users
                  </label>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={creating} className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
                {creating ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {providers.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Shield className="h-10 w-10 text-slate-300 mb-3" />
            <p className="text-slate-500 mb-4">No SSO providers configured</p>
            <Button onClick={() => setCreateOpen(true)} className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">
              <Plus className="h-4 w-4 mr-2" />
              Add SSO Provider
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {providers.map((prov) => (
            <Card key={prov.provider_id} className="hover:shadow-sm transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <ProviderIcon provider={prov.protocol} />
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{prov.name}</p>
                        <Badge variant="secondary" className="text-xs uppercase">{prov.protocol}</Badge>
                        <StatusBadge active={prov.is_active} />
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5 max-w-md truncate">
                        {prov.issuer} · Auto-provision: {prov.auto_provision ? "On" : "Off"} · Default role: {prov.default_role}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <a
                      href={`/sso/login/${prov.provider_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex"
                    >
                      <Button variant="ghost" size="sm" className="text-blue-600 hover:text-blue-700 hover:bg-blue-50">
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </a>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(prov.provider_id)}
                      className="text-red-500 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────

export default function IntegrationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Integrations</h1>
        <p className="text-slate-500 mt-1">
          Connect external tools — ATS, calendars, notifications, and SSO
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "ATS Connections", icon: Link2, color: "text-blue-600" },
          { label: "Calendar Sync", icon: Calendar, color: "text-green-600" },
          { label: "Notification Channels", icon: MessageSquare, color: "text-purple-600" },
          { label: "SSO Providers", icon: Shield, color: "text-amber-600" },
        ].map((item) => (
          <Card key={item.label}>
            <CardContent className="p-3 flex items-center gap-2">
              <item.icon className={`h-4 w-4 ${item.color}`} />
              <span className="text-sm text-slate-600">{item.label}</span>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="ats">
        <TabsList>
          <TabsTrigger value="ats">
            <Link2 className="h-4 w-4 mr-2" />
            ATS
          </TabsTrigger>
          <TabsTrigger value="calendar">
            <Calendar className="h-4 w-4 mr-2" />
            Calendar
          </TabsTrigger>
          <TabsTrigger value="channels">
            <MessageSquare className="h-4 w-4 mr-2" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="sso">
            <Shield className="h-4 w-4 mr-2" />
            SSO
          </TabsTrigger>
        </TabsList>

        <TabsContent value="ats">
          <ATSTab />
        </TabsContent>
        <TabsContent value="calendar">
          <CalendarTab />
        </TabsContent>
        <TabsContent value="channels">
          <ChannelsTab />
        </TabsContent>
        <TabsContent value="sso">
          <SSOTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
