import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

type AppGateProps = { children: React.ReactElement };

export function AppGate({ children }: AppGateProps) {
  const { user, initializing } = useAuth();
  const location = useLocation();
  const path = location.pathname;

  const isAuthPage = path === "/login" || path === "/signup";
  const isOnboarding = path === "/onboarding";

  if (initializing) {
    return (
      <div className="page">
        <section className="card">
          <p className="muted">Loading your session...</p>
        </section>
      </div>
    );
  }

  if (!user) {
    return isAuthPage ? children : <Navigate to="/login" replace state={{ from: path }} />;
  }

  if (!user.onboarding_completed) {
    return isOnboarding ? children : <Navigate to="/onboarding" replace state={{ from: path }} />;
  }

  if (isAuthPage) {
    return <Navigate to="/" replace />;
  }

  return children;
}
