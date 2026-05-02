import { Outlet } from "react-router";
import { AuthProvider } from "../context/AuthContext";

export default function Root() {
  return (
    <AuthProvider>
      <Outlet />
    </AuthProvider>
  );
}
