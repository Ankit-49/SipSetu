import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Bell, CheckCheck, Star, XCircle, Info, Calendar } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import axios from "axios";

const API = "http://localhost:5000/api";

interface Notification {
  notification_id: string;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  related_job_title?: string;
  created_at: string;
}

export default function ApplicantNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const userId = localStorage.getItem("user_id");

  const fetchNotifications = async () => {
    if (!userId) return;
    try {
      const res = await axios.get(`${API}/notifications/${userId}`);
      setNotifications(res.data);
    } catch {
      toast({ title: "Failed to load notifications", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const markAllRead = async () => {
    if (!userId) return;
    try {
      await axios.patch(`${API}/notifications/read-all/${userId}`);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      toast({ title: "All notifications marked as read ✓" });
    } catch {
      toast({ title: "Operation failed", variant: "destructive" });
    }
  };

  const markRead = async (id: string) => {
    try {
      await axios.patch(`${API}/notifications/${id}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === id ? { ...n, is_read: true } : n))
      );
    } catch {}
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#1E3A5F] border-t-transparent" />
      </div>
    );
  }

  const getNotifStyles = (type: string) => {
    if (type === "shortlisted") return { bg: "bg-yellow-50 border-yellow-100", icon: <Star className="h-5 w-5 text-yellow-500" />, border: "border-l-yellow-400" };
    if (type === "rejected") return { bg: "bg-red-50 border-red-100", icon: <XCircle className="h-5 w-5 text-red-500" />, border: "border-l-red-400" };
    return { bg: "bg-blue-50 border-blue-100", icon: <Info className="h-5 w-5 text-[#1E3A5F]" />, border: "border-l-[#1E3A5F]" };
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            <Bell className="h-8 w-8 text-[#1E3A5F]" /> Notifications
          </h1>
          <p className="text-slate-500 mt-1">Stay updated with your job application status and recommendations.</p>
        </div>
        {notifications.some((n) => !n.is_read) && (
          <Button
            onClick={markAllRead}
            variant="outline"
            className="border-slate-200 text-[#1E3A5F] hover:bg-[#1E3A5F]/5"
          >
            <CheckCheck className="h-4 w-4 mr-2" /> Mark all read
          </Button>
        )}
      </div>

      <Card className="border-slate-200/80 shadow-md">
        <CardContent className="p-0">
          {notifications.length === 0 ? (
            <div className="py-16 px-4 text-center">
              <div className="h-16 w-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Bell className="h-8 w-8 text-slate-400" />
              </div>
              <h3 className="font-semibold text-slate-900 text-lg">No notifications yet</h3>
              <p className="text-slate-400 text-sm mt-1 max-w-sm mx-auto">
                You're all caught up! Updates about your resume or applications will appear here.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {notifications.map((n) => {
                const styles = getNotifStyles(n.type);
                return (
                  <div
                    key={n.notification_id}
                    onClick={() => !n.is_read && markRead(n.notification_id)}
                    className={`p-5 flex gap-4 transition-all duration-200 hover:bg-slate-50/80 ${
                      !n.is_read ? `bg-blue-50/10 border-l-4 ${styles.border}` : "border-l-4 border-l-transparent"
                    }`}
                  >
                    <div className={`h-10 w-10 rounded-xl flex items-center justify-center shrink-0 border ${styles.bg}`}>
                      {styles.icon}
                    </div>
                    <div className="flex-1 min-w-0 space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className={`text-base text-slate-900 ${!n.is_read ? "font-bold" : "font-semibold"}`}>
                          {n.title}
                        </h4>
                        {!n.is_read && (
                          <span className="h-2 w-2 rounded-full bg-[#F97316] shrink-0" />
                        )}
                      </div>
                      <p className="text-sm text-slate-600 leading-relaxed">{n.message}</p>
                      <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-2">
                        <Calendar className="h-3.5 w-3.5" />
                        <span>{new Date(n.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
