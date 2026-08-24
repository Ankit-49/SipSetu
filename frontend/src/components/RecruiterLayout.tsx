import { Link, useLocation } from "react-router";
import { LayoutDashboard, PlusSquare, Users, User, Sparkles, Menu, X, Briefcase, Building2, Link2 } from "lucide-react";
import { NotificationCenter } from "@/components/NotificationCenter";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router";
import { useAuth } from "@/app/context/AuthContext";
import { SipSetuLogo } from "@/components/SipSetuLogo";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useState, useEffect } from "react";

const navItems = [
  { name: "Dashboard", href: "/recruiter/dashboard", icon: LayoutDashboard },
  { name: "Manage Jobs", href: "/recruiter/jobs", icon: Briefcase },
  { name: "Post Job", href: "/recruiter/post-job", icon: PlusSquare },
  { name: "Candidates", href: "/recruiter/candidates", icon: Users },
  { name: "Bulk Screen", href: "/recruiter/bulk-screen", icon: Sparkles },
  { name: "Organizations", href: "/recruiter/organizations", icon: Building2 },
  { name: "Integrations", href: "/recruiter/integrations", icon: Link2 },
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
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/50 z-20 lg:hidden backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 w-64 bg-gradient-to-b from-[#1E3A5F] to-[#162d4a] flex flex-col flex-shrink-0 transition-transform duration-300 ease-out lg:relative lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        data-testid="recruiter-sidebar"
      >
        <div className="h-16 flex items-center justify-between px-6 flex-shrink-0 border-b border-white/5">
          <SipSetuLogo className="text-white text-2xl font-bold tracking-tight" />
          <button className="lg:hidden text-white/70 hover:text-white transition-colors" onClick={() => setSidebarOpen(false)}>
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
          {navItems.map((item, idx) => {
            const isActive = location.pathname === item.href;
            return (
              <motion.div
                key={item.href}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05, duration: 0.3 }}
              >
                <Link
                  to={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group ${
                    isActive
                      ? "bg-white/10 text-white shadow-sm border-l-[3px] border-[#F97316]"
                      : "text-slate-300 hover:text-white hover:bg-white/5 border-l-[3px] border-transparent"
                  }`}
                  data-testid={`nav-link-${item.name.toLowerCase().replace(' ', '-')}`}
                >
                  <item.icon className={`h-5 w-5 transition-transform duration-200 ${isActive ? 'scale-110' : 'group-hover:scale-110'}`} />
                  <span className="font-medium">{item.name}</span>
                  {isActive && (
                    <motion.div
                      layoutId="active-indicator"
                      className="ml-auto h-2 w-2 rounded-full bg-[#F97316]"
                    />
                  )}
                </Link>
              </motion.div>
            );
          })}
        </nav>

        <Link
          to="/recruiter/profile"
          className="block p-4 border-t border-white/10 transition-all duration-200 hover:bg-white/5 group"
          data-testid="sidebar-profile-link"
        >
          <div className="flex items-center gap-3">
            <Avatar className="h-9 w-9 ring-2 ring-white/20 group-hover:ring-[#F97316]/50 transition-all">
              <AvatarImage src={profileImage} className="object-cover" />
              <AvatarFallback className="bg-gradient-to-br from-[#F97316] to-orange-500 text-white text-sm font-semibold">
                {userInitials}
              </AvatarFallback>
            </Avatar>
            <div className="flex flex-col min-w-0">
              <span className="text-sm font-medium text-white truncate max-w-[140px] group-hover:text-orange-200 transition-colors">
                {userName}
              </span>
              <span className="text-xs text-slate-400 group-hover:text-slate-300 transition-colors">
                {userRole.toUpperCase()}
              </span>
            </div>
          </div>
        </Link>

        <div className="p-4 border-t border-white/10">
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="outline"
                className="w-full border-white/20 bg-white/5 text-white hover:bg-white/10 hover:text-white hover:border-white/30 transition-all duration-200"
              >
                Logout
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Are you sure you want to sign out?</AlertDialogTitle>
                <AlertDialogDescription>
                  You can sign back in anytime. Your dashboard and saved data will be waiting for you.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel className="border-slate-200">Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleLogout} className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90 shadow-lg">
                  Sign Out
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile top bar */}
        <div className="lg:hidden h-14 bg-gradient-to-r from-[#1E3A5F] to-[#162d4a] flex items-center px-4 gap-3 flex-shrink-0 shadow-md">
          <button className="text-white p-1 hover:bg-white/10 rounded-lg transition-colors" onClick={() => setSidebarOpen(true)}>
            <Menu className="h-6 w-6" />
          </button>
          <SipSetuLogo className="text-white text-xl font-bold tracking-tight" />
          <div className="ml-auto"><NotificationCenter /></div>
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
