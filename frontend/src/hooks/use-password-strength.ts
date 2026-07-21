import { useMemo } from "react";

export interface PasswordCheck {
  label: string;
  met: boolean;
}

export interface PasswordStrength {
  score: number;        // 0–100
  label: string;        // "Weak" | "Fair" | "Good" | "Strong" | "Very Strong"
  barColor: string;     // css color value for the bar
  checks: PasswordCheck[];
}

const CHECKS: { label: string; test: (pw: string) => boolean }[] = [
  { label: "At least 8 characters", test: (pw) => pw.length >= 8 },
  { label: "Contains uppercase letter", test: (pw) => /[A-Z]/.test(pw) },
  { label: "Contains lowercase letter", test: (pw) => /[a-z]/.test(pw) },
  { label: "Contains a number", test: (pw) => /\d/.test(pw) },
  { label: "Contains a special character", test: (pw) => /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;'`~]/.test(pw) },
];

const LABELS = ["Weak", "Fair", "Good", "Strong", "Very Strong"];
const COLORS = ["#EF4444", "#F97316", "#EAB308", "#22C55E", "#16A34A"];

export function usePasswordStrength(password: string): PasswordStrength {
  return useMemo(() => {
    if (!password) {
      return {
        score: 0,
        label: "",
        barColor: "#E2E8F0",
        checks: CHECKS.map((c) => ({ label: c.label, met: false })),
      };
    }

    const checks = CHECKS.map((c) => ({
      label: c.label,
      met: c.test(password),
    }));

    const metCount = checks.filter((c) => c.met).length;
    const bonus = password.length > 12 ? 10 : password.length > 16 ? 20 : 0;
    const score = Math.min(100, Math.round((metCount / CHECKS.length) * 80 + bonus));

    let level = 0;
    if (score >= 80) level = 4;
    else if (score >= 60) level = 3;
    else if (score >= 40) level = 2;
    else if (score >= 20) level = 1;

    return {
      score,
      label: LABELS[level],
      barColor: COLORS[level],
      checks,
    };
  }, [password]);
}
