import { Link, useLocation } from "react-router";
import { LayoutDashboard, PlusSquare, Users, User, Sparkles, Menu, X } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router";
import { useAuth } from "@/app/context/AuthContext";
import { SipSetuLogo } from "@/components/SipSetuLogo";
import { useState, useEffect } from "react";

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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user } = useAuth();
  const [profileImage, setProfileImage] = useState<string>(() => localStorage.getItem("profile_image") || "");
  const [userName, setUserName] = useState<string>(() => localStorage.getItem("user_name") || "Recruiter");

  // Sync from AuthContext whenever user changes and listen for storage events
  useEffect(() => {
    if (user) {
      setProfileImage(user.profile_image || localStorage.getItem("profile_image") || "");
      setUserName(user.name || localStorage.getItem("user_name") || "Recruiter");
    }
  }, [user]);

  useEffect(() => {
    const handleStorage = () => {
      setProfileImage(localStorage.getItem("profile_image") || "");
      setUserName(localStorage.getItem("user_name") || "Recruiter");
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const userRole = user?.role || localStorage.getItem("user_role") || "recruiter";

  // Close sidebar on route change (mobile)
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);


  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const userInitials = userName.split(' ').map(n => n[0]).join('') || "RC";

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 w-64 bg-[#1E3A5F] flex flex-col flex-shrink-0 transition-transform duration-300 lg:relative lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        data-testid="recruiter-sidebar"
      >
        <div className="h-16 flex items-center justify-between px-6 flex-shrink-0">
          <SipSetuLogo className="text-white text-2xl font-bold tracking-tight" />
          <button className="lg:hidden text-white/70 hover:text-white" onClick={() => setSidebarOpen(false)}>
            <X className="h-5 w-5" />
          </button>
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
            <Avatar className="h-9 w-9 ring-2 ring-white/20">
              <AvatarImage src={profileImage} className="object-cover" />
              <AvatarFallback className="bg-[#F97316] text-white text-sm font-semibold">
                {userInitials}
              </AvatarFallback>
            </Avatar>
            <div className="flex flex-col min-w-0">
              <span className="text-sm font-medium text-white truncate max-w-[140px]">
                {userName}
              </span>
              <span className="text-xs text-slate-400">
                {userRole.toUpperCase()}
              </span>
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
        {/* Mobile top bar */}
        <div className="lg:hidden h-14 bg-[#1E3A5F] flex items-center px-4 gap-3 flex-shrink-0">
          <button className="text-white p-1" onClick={() => setSidebarOpen(true)}>
            <Menu className="h-6 w-6" />
          </button>
          <SipSetuLogo className="text-white text-xl font-bold tracking-tight" />
        </div>

        <ScrollArea className="flex-1 h-full">
          <div className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto w-full">
            {children}
          </div>
        </ScrollArea>
      </main>
    </div>
  );
}
