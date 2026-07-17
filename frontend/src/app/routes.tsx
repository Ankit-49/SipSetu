import { createBrowserRouter, Navigate } from "react-router";
import LandingPage from "../pages/LandingPage";
import PreviewPage from "../pages/PreviewPage";
import LoginPage from "../pages/LoginPage";
import RegisterPage from "../pages/RegisterPage";
import NotFound from "../pages/not-found";

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

  // Applicant Routes
  { path: "/applicant", Component: () => <Navigate to="/applicant/dashboard" replace /> },
  { path: "/applicant/dashboard", Component: () => <ApplicantLayout><ApplicantDashboardHome /></ApplicantLayout> },
  { path: "/applicant/resume", Component: () => <ApplicantLayout><ApplicantResume /></ApplicantLayout> },
  { path: "/applicant/matches", Component: () => <ApplicantLayout><ApplicantJobMatches /></ApplicantLayout> },
  { path: "/applicant/skill-gap", Component: () => <ApplicantLayout><ApplicantSkillGap /></ApplicantLayout> },
  { path: "/applicant/profile", Component: () => <ApplicantLayout><ApplicantProfile /></ApplicantLayout> },

  // Recruiter Routes
  { path: "/recruiter", Component: () => <Navigate to="/recruiter/dashboard" replace /> },
  { path: "/recruiter/dashboard", Component: () => <RecruiterLayout><RecruiterDashboardHome /></RecruiterLayout> },
  { path: "/recruiter/post-job", Component: () => <RecruiterLayout><RecruiterPostJob /></RecruiterLayout> },
  { path: "/recruiter/candidates", Component: () => <RecruiterLayout><RecruiterCandidates /></RecruiterLayout> },
  { path: "/recruiter/bulk-screen", Component: () => <RecruiterLayout><RecruiterBulkScreening /></RecruiterLayout> },
  { path: "/recruiter/profile", Component: () => <RecruiterLayout><RecruiterProfile /></RecruiterLayout> },

  { path: "*", Component: NotFound },
]);
