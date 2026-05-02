import { createBrowserRouter } from "react-router";
import RoleSelection from "./pages/RoleSelection";
import Login from "./pages/Login";
import RecruiterDashboard from "./pages/RecruiterDashboard";
import RecruiterHome from "./pages/RecruiterHome";
import RecruiterProfile from "./pages/RecruiterProfile";
import PostJob from "./pages/PostJob";
import RankedCandidates from "./pages/RankedCandidates";
import ApplicantDashboard from "./pages/ApplicantDashboard";
import JobPostings from "./pages/JobPostings";
import NotFound from "./pages/NotFound";
import Root from "./pages/Root";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Root,
    children: [
      { index: true, Component: RoleSelection },
      { path: "login/:role", Component: Login },
      { path: "recruiter/dashboard", Component: RecruiterDashboard },
      { path: "recruiter/home", Component: RecruiterHome },
      { path: "recruiter/profile", Component: RecruiterProfile },
      { path: "recruiter/post-job", Component: PostJob },
      { path: "recruiter/candidates", Component: RankedCandidates },
      { path: "recruiter/jobs", Component: JobPostings },
      { path: "applicant/dashboard", Component: ApplicantDashboard },
      { path: "*", Component: NotFound },
    ],
  },
]);
