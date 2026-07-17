import { useState, useEffect, useRef } from "react";
import { Bell, X, CheckCheck, Briefcase, Star, XCircle, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import axios from "axios";

const API = "http://localhost:5000/api";

interface Notification {
  notification_id: string;
  title: string;
  message: string;
  type: string; // 'info' | 'success' | 'shortlisted' | 'rejected' | 'warning'
  is_read: boolean;
  related_job_title?: string;
  created_at: string;
}

function timeAgo(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function NotifIcon({ type }: { type: string }) {
  if (type === "shortlisted") return <Star className="h-4 w-4 text-yellow-500" />;
  if (type === "rejected") return <XCircle className="h-4 w-4 text-red-400" />;
  if (type === "success") return <CheckCheck className="h-4 w-4 text-emerald-500" />;
  if (type === "warning") return <Briefcase className="h-4 w-4 text-amber-500" />;
  return <Info className="h-4 w-4 text-blue-400" />;
}

function notifBg(type: string) {
  if (type === "shortlisted") return "bg-yellow-50 border-yellow-200";
  if (type === "rejected") return "bg-red-50 border-red-200";
  return "bg-blue-50 border-blue-200";
}

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const panelRef = useRef<HTMLDivElement>(null);
  const userId = localStorage.getItem("user_id");

  const unread = notifications.filter((n) => !n.is_read).length;

  const fetchNotifications = async () => {
    if (!userId) return;
    try {
      const res = await axios.get(`${API}/notifications/${userId}`);
      setNotifications(res.data);
    } catch {
      // silently fail
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  // Close panel when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const markAllRead = async () => {
    if (!userId) return;
    try {
      await axios.patch(`${API}/notifications/read-all/${userId}`);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {}
  };

  const markRead = async (id: string) => {
    try {
      await axios.patch(`${API}/notifications/${id}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === id ? { ...n, is_read: true } : n))
      );
    } catch {}
  };

  return (
    <div className="relative" ref={panelRef}>
      <button
        onClick={() => { setOpen((o) => !o); fetchNotifications(); }}
        className="relative flex items-center justify-center h-9 w-9 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-all duration-200"
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5" />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-[#F97316] text-[9px] font-bold text-white flex items-center justify-center leading-none">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-11 w-80 bg-white rounded-2xl shadow-2xl border border-slate-200/80 z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50/80">
            <div className="flex items-center gap-2">
              <Bell className="h-4 w-4 text-[#1E3A5F]" />
              <span className="font-semibold text-slate-900 text-sm">Notifications</span>
              {unread > 0 && (
                <span className="text-[10px] font-bold bg-[#F97316] text-white rounded-full px-1.5 py-0.5 leading-none">
                  {unread} new
                </span>
              )}
            </div>
            <div className="flex items-center gap-1">
              {unread > 0 && (
                <button
                  onClick={markAllRead}
                  className="text-[11px] font-medium text-[#1E3A5F] hover:underline mr-1"
                >
                  Mark all read
                </button>
              )}
              <button
                onClick={() => setOpen(false)}
                className="h-6 w-6 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          {/* Notification list */}
          <div className="max-h-[400px] overflow-y-auto divide-y divide-slate-100">
            {notifications.length === 0 ? (
              <div className="py-10 px-4 text-center">
                <Bell className="h-8 w-8 text-slate-200 mx-auto mb-2" />
                <p className="text-sm text-slate-400 font-medium">No notifications yet</p>
                <p className="text-xs text-slate-300 mt-1">We'll notify you when something happens</p>
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.notification_id}
                  onClick={() => markRead(n.notification_id)}
                  className={`relative flex gap-3 px-4 py-3 cursor-pointer hover:bg-slate-50 transition-colors ${
                    !n.is_read ? "bg-blue-50/40" : ""
                  }`}
                >
                  {/* Unread dot */}
                  {!n.is_read && (
                    <div className="absolute top-3.5 right-3.5 h-1.5 w-1.5 rounded-full bg-[#F97316]" />
                  )}
                  <div className={`h-8 w-8 rounded-xl flex items-center justify-center shrink-0 border ${notifBg(n.type)}`}>
                    <NotifIcon type={n.type} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs font-semibold text-slate-900 leading-snug ${!n.is_read ? "font-bold" : ""}`}>
                      {n.title}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5 leading-snug line-clamp-2">{n.message}</p>
                    <p className="text-[10px] text-slate-400 mt-1">{timeAgo(n.created_at)}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
