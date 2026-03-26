import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * HomeRedirect: Routes users to their personalized dashboard after onboarding
 * - If onboarded: redirect to /captain/dashboard
 * - If not onboarded: AppGate will redirect to /onboarding
 */
export function HomeRedirect() {
  const { user } = useAuth();

  // If user is onboarded, go to captain dashboard
  if (user?.onboarding_completed) {
    return <Navigate to="/captain/dashboard" replace />;
  }

  // Otherwise, let AppGate handle the redirect to onboarding
  // This shouldn't happen in normal flow, but as fallback show dashboard
  return <Navigate to="/dashboard" replace />;
}
