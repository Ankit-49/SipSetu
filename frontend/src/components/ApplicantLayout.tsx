import { Link, useLocation } from "react-router";
import { LayoutDashboard, FileText, Briefcase, TrendingUp, User } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";

const navItems = [
  { name: "Dashboard", href: "/applicant/dashboard", icon: LayoutDashboard },
  { name: "My Resume", href: "/applicant/resume", icon: FileText },
  { name: "Job Matches", href: "/applicant/matches", icon: Briefcase },
  { name: "Skill Gap", href: "/applicant/skill-gap", icon: TrendingUp },
  { name: "Profile", href: "/applicant/profile", icon: User },
];

export function ApplicantLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-[#1E3A5F] flex flex-col flex-shrink-0" data-testid="applicant-sidebar">
        <div className="h-16 flex items-center px-6">
          <Link to="/" className="text-white text-2xl font-bold tracking-tight">SipSetu</Link>
        </div>
        
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.href}
                to={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                  isActive 
                    ? "bg-white/10 text-white border-l-4 border-[#F97316]" 
                    : "text-slate-300 hover:text-white hover:bg-white/5 border-l-4 border-transparent"
                }`}
                data-testid={`nav-link-${item.name.toLowerCase().replace(' ', '-')}`}
              >
                <item.icon className="h-5 w-5" />
                <span className="font-medium">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-3">
            <Avatar>
              <AvatarImage src="" />
              <AvatarFallback className="bg-[#F97316] text-white">
                {localStorage.getItem("user_name")?.split(' ').map(n => n[0]).join('') || "AP"}
              </AvatarFallback>
            </Avatar>
            <div className="flex flex-col">
              <span className="text-sm font-medium text-white truncate max-w-[150px]">
                {localStorage.getItem("user_name") || "Applicant"}
              </span>
              <span className="text-xs text-slate-400">Job Seeker</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <ScrollArea className="flex-1 h-full">
          <div className="p-6 md:p-8 max-w-7xl mx-auto w-full">
            {children}
          </div>
        </ScrollArea>
      </main>
    </div>
  );
}
