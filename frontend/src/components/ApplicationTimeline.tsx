import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Clock,
  CheckCircle2,
  XCircle,
  Send,
  Star,
  Calendar,
  MessageSquare,
} from "lucide-react";

type TimelineEvent = {
  id: string;
  type: "applied" | "shortlisted" | "rejected" | "interview_scheduled" | "interview_confirmed" | "interview_completed" | "message";
  title: string;
  description: string;
  timestamp: string;
  metadata?: Record<string, any>;
};

type ApplicationTimelineProps = {
  events: TimelineEvent[];
};

const EVENT_CONFIG: Record<string, { icon: typeof Clock; color: string; bg: string }> = {
  applied: { icon: Send, color: "text-blue-600", bg: "bg-blue-50" },
  shortlisted: { icon: Star, color: "text-yellow-600", bg: "bg-yellow-50" },
  rejected: { icon: XCircle, color: "text-red-600", bg: "bg-red-50" },
  interview_scheduled: { icon: Calendar, color: "text-purple-600", bg: "bg-purple-50" },
  interview_confirmed: { icon: CheckCircle2, color: "text-green-600", bg: "bg-green-50" },
  interview_completed: { icon: CheckCircle2, color: "text-green-700", bg: "bg-green-100" },
  message: { icon: MessageSquare, color: "text-slate-600", bg: "bg-slate-50" },
};

export function ApplicationTimeline({ events }: ApplicationTimelineProps) {
  const formatTime = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Clock className="h-5 w-5 text-[#1E3A5F]" /> Application Timeline
        </CardTitle>
      </CardHeader>
      <CardContent className="relative">
        {events.length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-6">No timeline events yet.</p>
        ) : (
          <div className="relative pl-8">
            {/* Vertical line */}
            <div className="absolute left-3 top-2 bottom-2 w-0.5 bg-slate-200" />
            <div className="space-y-6">
              {events.map((event, i) => {
                const config = EVENT_CONFIG[event.type] || EVENT_CONFIG.message;
                const Icon = config.icon;
                return (
                  <div key={event.id} className="relative animate-in fade-in slide-in-from-left-2" style={{ animationDelay: `${i * 80}ms` }}>
                    {/* Icon dot */}
                    <div className={`absolute -left-8 top-1 w-6 h-6 rounded-full ${config.bg} flex items-center justify-center ring-2 ring-white`}>
                      <Icon className={`h-3 w-3 ${config.color}`} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-semibold text-sm text-slate-900">{event.title}</p>
                        <span className="text-[10px] text-slate-400">{formatTime(event.timestamp)}</span>
                      </div>
                      <p className="text-sm text-slate-600 mt-0.5">{event.description}</p>
                      {event.metadata?.meeting_link && (
                        <a
                          href={event.metadata.meeting_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-[#1E3A5F] hover:underline mt-1 inline-block"
                        >
                          Join Meeting →
                        </a>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
