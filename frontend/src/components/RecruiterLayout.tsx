import { Link, useLocation } from "react-router";
import { LayoutDashboard, PlusSquare, Users, User, Sparkles } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router";
import { useAuth } from "@/app/context/AuthContext";
import { SipSetuLogo } from "@/components/SipSetuLogo";

const navItems = [
  { name: "Dashboard", href: "/recruiter/dashboard", icon: LayoutDashboard },
  { name: "Post Job", href: "/recruiter/post-job", icon: PlusSquare },
  { name: "Candidates", href: "/recruiter/candidates", icon: Users },
  { name: "Bulk Screen", href: "/recruiter/bulk-screen", icon: Sparkles },
  { name: "Profile", href: "/recruiter/profile", icon: User },
];

export function RecruiterLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-[#1E3A5F] flex flex-col flex-shrink-0" data-testid="recruiter-sidebar">
        <div className="h-16 flex items-center px-6">
          <SipSetuLogo className="text-white text-2xl font-bold tracking-tight" />
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

        <Link
          to="/recruiter/profile"
          className="block p-4 border-t border-white/10 transition-colors hover:bg-white/5 rounded-t-xl"
          data-testid="sidebar-profile-link"
        >
          <div className="flex items-center gap-3">
            <Avatar>
              <AvatarImage src="" />
              <AvatarFallback className="bg-[#F97316] text-white">
                {localStorage.getItem("user_name")?.split(' ').map(n => n[0]).join('') || "RC"}
              </AvatarFallback>
            </Avatar>
            <div className="flex flex-col">
              <span className="text-sm font-medium text-white truncate max-w-[150px]">
                {localStorage.getItem("user_name") || "Recruiter"}
              </span>
              <span className="text-xs text-slate-400">HR Manager</span>
            </div>
          </div>
        </Link>

        <div className="p-4 border-t border-white/10">
          <Button
            onClick={handleLogout}
            variant="outline"
            className="w-full border-white/20 bg-white/5 text-white hover:bg-white/10 hover:text-white"
          >
            Logout
          </Button>
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
