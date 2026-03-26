import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

type ProtectedRouteProps = {
  children: React.ReactElement;
  redirectTo?: string;
  requireAdmin?: boolean;
  fallback?: React.ReactElement;
  allowUnonboarded?: boolean;
};

export function ProtectedRoute({
  children,
  redirectTo = "/login",
  requireAdmin = false,
  fallback,
  allowUnonboarded = false,
}: ProtectedRouteProps) {
  const { user, initializing } = useAuth();
  const location = useLocation();

  if (initializing) {
    return (
      <div className="page">
        <section className="card">
          <p className="muted">Checking your session...</p>
        </section>
      </div>
    );
  }

  if (!user) {
    return <Navigate to={redirectTo} replace state={{ from: location.pathname }} />;
  }

  if (!allowUnonboarded && user && !user.onboarding_completed && location.pathname !== "/onboarding") {
    return <Navigate to="/onboarding" replace state={{ from: location.pathname }} />;
  }

  if (requireAdmin && !user.is_admin) {
    return fallback ?? <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return children;
}
