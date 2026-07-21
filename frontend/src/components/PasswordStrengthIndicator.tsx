import { motion } from "framer-motion";
import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { PasswordStrength } from "@/hooks/use-password-strength";

interface Props {
  strength: PasswordStrength;
  /** If true, renders the full checklist below the bar. Default true */
  showChecks?: boolean;
  className?: string;
}

export function PasswordStrengthIndicator({
  strength,
  showChecks = true,
  className,
}: Props) {
  const { score, label, barColor, checks } = strength;
  const hasPassword = score > 0;

  if (!hasPassword) return null;

  return (
    <div className={cn("space-y-3", className)}>
      {/* Strength bar */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-500">Password strength</span>
          {label && (
            <motion.span
              key={label}
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-xs font-bold"
              style={{ color: barColor }}
            >
              {label}
            </motion.span>
          )}
        </div>
        <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ backgroundColor: barColor }}
            initial={{ width: 0 }}
            animate={{ width: `${score}%` }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Checklist */}
      {showChecks && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="space-y-1"
        >
          {checks.map((check) => (
            <div key={check.label} className="flex items-center gap-2 text-xs">
              {check.met ? (
                <Check className="h-3 w-3 text-green-500 shrink-0" />
              ) : (
                <X className="h-3 w-3 text-slate-300 shrink-0" />
              )}
              <span
                className={cn(
                  "transition-colors duration-200",
                  check.met ? "text-green-600 font-medium" : "text-slate-400"
                )}
              >
                {check.label}
              </span>
            </div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
