import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import api from "@/lib/api";

export interface User {
  id: string;
  email: string;
  name: string | null;
  role: "applicant" | "recruiter";
  phone: string | null;
  location: string | null;
  profile_image: string | null;
  company?: string | null;
  job_title?: string | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, role: "applicant" | "recruiter") => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount, try to restore the session from the stored token
  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (!token) {
      setLoading(false);
      return;
    }

    const restoreSession = async () => {
      try {
        const res = await api.get("/auth/me");
        const u: User = {
          id: res.data.user_id,
          email: res.data.email,
          name: res.data.name,
          role: res.data.role,
          phone: res.data.phone,
          location: res.data.location,
          profile_image: res.data.profile_image,
          company: res.data.company,
          job_title: res.data.job_title,
        };
        setUser(u);
        // Sync localStorage for components that read these directly
        localStorage.setItem("user_id", u.id);
        localStorage.setItem("user_role", u.role);
        if (u.name) localStorage.setItem("user_name", u.name);
        if (u.profile_image) localStorage.setItem("profile_image", u.profile_image);
        if (u.company) localStorage.setItem("company", u.company);
      } catch {
        // Token invalid or expired — clear state
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user_id");
        localStorage.removeItem("user_role");
        localStorage.removeItem("user_name");
        localStorage.removeItem("profile_image");
        localStorage.removeItem("company");
      } finally {
        setLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.post("/auth/login", { email, password });
    const data = res.data;

    localStorage.setItem("auth_token", data.token);
    localStorage.setItem("user_id", data.user_id);
    localStorage.setItem("user_role", data.role);
    if (data.name) localStorage.setItem("user_name", data.name);
    if (data.profile_image) localStorage.setItem("profile_image", data.profile_image);

    setUser({
      id: data.user_id,
      email: data.email,
      name: data.name,
      role: data.role,
      phone: null,
      location: null,
      profile_image: data.profile_image,
    });
  }, []);

  const register = useCallback(async (
    name: string, email: string, password: string, role: "applicant" | "recruiter",
  ) => {
    const res = await api.post("/auth/register", { name, email, password, role });
    const data = res.data;

    localStorage.setItem("auth_token", data.token);
    localStorage.setItem("user_id", data.user_id);
    localStorage.setItem("user_role", data.role);
    localStorage.setItem("user_name", name);

    setUser({
      id: data.user_id,
      email: data.email,
      name: data.name,
      role: data.role as "applicant" | "recruiter",
      phone: null,
      location: null,
      profile_image: null,
    });
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // Do nothing — local cleanup is what matters
    }
    setUser(null);
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_id");
    localStorage.removeItem("user_role");
    localStorage.removeItem("user_name");
    localStorage.removeItem("profile_image");
    localStorage.removeItem("company");
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, isAuthenticated: !!user }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
