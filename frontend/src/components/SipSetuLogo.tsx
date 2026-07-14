import { Link } from "react-router";
import { useAuth } from "@/app/context/AuthContext";

interface SipSetuLogoProps {
  /** Optional extra classes applied to the rendered text element. */
  className?: string;
  /** Where the logo should point when the user is logged out. Defaults to "/". */
  loggedOutHref?: string;
}

/**
 * SipSetu brand wordmark.
 *
 * Routes to the correct dashboard for the signed-in user's role, and falls
 * back to the landing page for guests. Use this anywhere the brand appears
 * in the chrome instead of a plain <Link to="/">.
 */
export function SipSetuLogo({ className, loggedOutHref = "/" }: SipSetuLogoProps) {
  const { user, isAuthenticated } = useAuth();

  const href = isAuthenticated && user
    ? user.role === "recruiter"
      ? "/recruiter/dashboard"
      : "/applicant/dashboard"
    : loggedOutHref;

  return (
    <Link to={href} className={className} data-testid="sipsetu-logo">
      SipSetu
    </Link>
  );
}
