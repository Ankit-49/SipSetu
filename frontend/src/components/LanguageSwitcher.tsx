import { useTranslation } from "react-i18next";
import { Globe } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SUPPORTED_LOCALES } from "@/i18n";

interface LanguageSwitcherProps {
  /** Render as a compact inline trigger (default) or a full-width button */
  variant?: "inline" | "full";
  className?: string;
}

export function LanguageSwitcher({ variant = "inline", className }: LanguageSwitcherProps) {
  const { i18n } = useTranslation();
  const currentLocale = i18n.language?.split("-")[0] || "en";

  const handleChange = (value: string) => {
    i18n.changeLanguage(value);
    localStorage.setItem("sipsetu_locale", value);
    // Update HTML lang attribute for accessibility
    document.documentElement.lang = value;
  };

  return (
    <Select value={currentLocale} onValueChange={handleChange}>
      <SelectTrigger
        className={`${variant === "full" ? "w-full" : "w-auto"} ${className ?? ""}`}
        aria-label="Select language"
      >
        <Globe className="h-4 w-4 mr-1.5 opacity-60" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {SUPPORTED_LOCALES.map((locale) => (
          <SelectItem key={locale.code} value={locale.code}>
            {locale.nativeName}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
