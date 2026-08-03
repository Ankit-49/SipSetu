import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Video } from "lucide-react";

type JoinInterviewButtonProps = {
  scheduledAt: string;
  durationMinutes?: number;
  meetingLink: string;
  label?: string;
  className?: string;
  variant?: "solid" | "outline";
};

/**
 * Time-gated "Join interview" button.
 *
 * Before the scheduled time it renders a disabled button with a live
 * countdown (it flips to active automatically at the scheduled minute).
 * During the interview window (start → start + duration) it renders a
 * working link to the meeting. After the window ends it disappears.
 */
export function JoinInterviewButton({
  scheduledAt,
  durationMinutes = 60,
  meetingLink,
  label = "Join",
  className = "",
  variant = "solid",
}: JoinInterviewButtonProps) {
  const [now, setNow] = useState(() => Date.now());

  const start = new Date(scheduledAt).getTime();
  const finished = !Number.isFinite(start) || now > start + (durationMinutes || 60) * 60 * 1000;

  // Tick once per second while we're still waiting for or inside the window;
  // stop ticking (and skip the interval entirely) once the interview is over.
  useEffect(() => {
    if (finished) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [finished]);

  // Invalid/missing date: never render an active link, just hide the button.
  if (!Number.isFinite(start)) return null;

  // Interview over — hide the button.
  if (finished) return null;

  // Not yet time — disabled button with a live countdown.
  if (now < start) {
    const diff = start - now;
    const mins = Math.floor(diff / 60000);
    const secs = Math.floor((diff % 60000) / 1000);
    const countdown = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
    return (
      <Button
        size="sm"
        variant="outline"
        disabled
        className={`h-8 gap-1.5 opacity-70 ${className}`}
        title={`Join available at ${new Date(start).toLocaleTimeString()}`}
      >
        <Video className="h-3.5 w-3.5" /> Starts in {countdown}
      </Button>
    );
  }

  // Live — active Join link.
  const isFullWidth = className.includes("w-full");
  const button = (
    <Button
      size="sm"
      className={`h-8 gap-1.5 ${className} ${
        variant === "solid"
          ? "bg-green-600 hover:bg-green-700 text-white"
          : "border-[#1E3A5F]/20 text-[#1E3A5F] hover:bg-blue-50"
      }`}
    >
      <Video className="h-3.5 w-3.5" /> {label}
    </Button>
  );

  return (
    <a
      href={meetingLink}
      target="_blank"
      rel="noopener noreferrer"
      className={isFullWidth ? "block" : "inline-flex"}
    >
      {button}
    </a>
  );
}
