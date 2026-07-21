import { createBrowserRouter, Navigate } from "react-router";
import LandingPage from "../pages/LandingPage";
import PreviewPage from "../pages/PreviewPage";
import LoginPage from "../pages/LoginPage";
import RegisterPage from "../pages/RegisterPage";
import ForgotPasswordPage from "../pages/ForgotPasswordPage";
import ResetPasswordPage from "../pages/ResetPasswordPage";
import NotFound from "../pages/not-found";
import { ProtectedRoute } from "../components/ProtectedRoute";

// Applicant
import { ApplicantLayout } from "../components/ApplicantLayout";
import ApplicantDashboardHome from "../pages/applicant/Dashboard";
import ApplicantResume from "../pages/applicant/Resume";
import ApplicantJobMatches from "../pages/applicant/JobMatches";
import ApplicantSkillGap from "../pages/applicant/SkillGap";
import ApplicantProfile from "../pages/applicant/Profile";

// Recruiter
import { RecruiterLayout } from "../components/RecruiterLayout";
import RecruiterDashboardHome from "../pages/recruiter/Dashboard";
import RecruiterPostJob from "../pages/recruiter/PostJob";
import RecruiterCandidates from "../pages/recruiter/Candidates";
import RecruiterProfile from "../pages/recruiter/Profile";
import RecruiterBulkScreening from "../pages/recruiter/BulkScreening";

export const router = createBrowserRouter([
  { path: "/", Component: LandingPage },
  { path: "/preview", Component: PreviewPage },
  { path: "/login", Component: LoginPage },
  { path: "/register", Component: RegisterPage },
  { path: "/forgot-password", Component: ForgotPasswordPage },
  { path: "/reset-password", Component: ResetPasswordPage },

  // Applicant Routes (protected — require applicant role)
  {
    path: "/applicant",
    Component: () => (
      <ProtectedRoute requiredRole="applicant">
        <Navigate to="/applicant/dashboard" replace />
      </ProtectedRoute>
    ),
  },
  {
    path: "/applicant/dashboard",
    Component: () => (
      <ProtectedRoute requiredRole="applicant">
        <ApplicantLayout><ApplicantDashboardHome /></ApplicantLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: "/applicant/resume",
    Component: () => (
      <ProtectedRoute requiredRole="applicant">
        <ApplicantLayout><ApplicantResume /></ApplicantLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: "/applicant/matches",
    Component: () => (
      <ProtectedRoute requiredRole="applicant">
        <ApplicantLayout><ApplicantJobMatches /></ApplicantLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: "/applicant/skill-gap",
    Component: () => (
      <ProtectedRoute requiredRole="applicant">
        <ApplicantLayout><ApplicantSkillGap /></ApplicantLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: "/applicant/profile",
    Component: () => (
      <ProtectedRoute requiredRole="applicant">
        <ApplicantLayout><ApplicantProfile /></ApplicantLayout>
      </ProtectedRoute>
    ),
  },

  // Recruiter Routes (protected — require recruiter role)
  {
    path: "/recruiter",
    Component: () => (
      <ProtectedRoute requiredRole="recruiter">
        <Navigate to="/recruiter/dashboard" replace />
      </ProtectedRoute>
    ),
  },
  {
    path: "/recruiter/dashboard",
    Component: () => (
      <ProtectedRoute requiredRole="recruiter">
        <RecruiterLayout><RecruiterDashboardHome /></RecruiterLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: "/recruiter/post-job",
    Component: () => (
      <ProtectedRoute requiredRole="recruiter">
        <RecruiterLayout><RecruiterPostJob /></RecruiterLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: "/recruiter/candidates",
    Component: () => (
      <ProtectedRoute requiredRole="recruiter">
        <RecruiterLayout><RecruiterCandidates /></RecruiterLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: "/recruiter/bulk-screen",
    Component: () => (
      <ProtectedRoute requiredRole="recruiter">
        <RecruiterLayout><RecruiterBulkScreening /></RecruiterLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: "/recruiter/profile",
    Component: () => (
      <ProtectedRoute requiredRole="recruiter">
        <RecruiterLayout><RecruiterProfile /></RecruiterLayout>
      </ProtectedRoute>
    ),
  },

  { path: "*", Component: NotFound },
]);
