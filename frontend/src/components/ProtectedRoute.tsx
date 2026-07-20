import { Navigate, useLocation } from "react-router";
import { useAuth } from "@/app/context/AuthContext";
import { Loader2 } from "lucide-react";

interface ProtectedRouteProps {
  children: React.ReactNode;
  /** If set, the user must have this role to access the route. */
  requiredRole?: "applicant" | "recruiter";
}

export function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();

  // Still checking the stored token against the backend
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <Loader2 className="h-8 w-8 animate-spin text-[#F97316]" />
      </div>
    );
  }

  // Not logged in — redirect to login, remembering where they came from
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  // Role mismatch — redirect to their appropriate dashboard
  if (requiredRole && user?.role !== requiredRole) {
    const redirect =
      user?.role === "applicant" ? "/applicant/dashboard" : "/recruiter/dashboard";
    return <Navigate to={redirect} replace />;
  }

  return <>{children}</>;
}
