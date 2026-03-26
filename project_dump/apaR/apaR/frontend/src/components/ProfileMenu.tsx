import { useRef, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { authLogout } from "../api/client";

export function ProfileMenu() {
  const [open, setOpen] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { user } = useAuth();

  // Close menu on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [open]);

  const handleLogout = async () => {
    try {
      setIsLoggingOut(true);
      await authLogout();
      setToastMessage("Logged out successfully");
      setShowToast(true);
      setOpen(false);

      // Redirect to login after short delay
      setTimeout(() => {
        navigate("/login");
      }, 500);
    } catch (err) {
      setToastMessage("Logout failed");
      setShowToast(true);
    } finally {
      setIsLoggingOut(false);
    }
  };

  if (!user) return null;

  return (
    <>
      <div className="profile-menu-container" ref={containerRef}>
        <button
          className="profile-button"
          onClick={() => setOpen(!open)}
          aria-label="User menu"
        >
          <span className="profile-icon">👤</span>
          <span className="profile-name">{user.username || user.email}</span>
        </button>

        {open && (
          <div className="profile-dropdown">
            <div className="dropdown-header">
              <p className="dropdown-title">{user.email}</p>
              <p className="dropdown-subtitle">{user.username || "User"}</p>
            </div>

            <div className="dropdown-divider" />

            <nav className="dropdown-menu">
              <a
                href="/settings"
                className="dropdown-item"
                onClick={() => {
                  setOpen(false);
                  navigate("/settings");
                }}
              >
                <span>⚙️</span>
                <span>My Account</span>
              </a>

              <a
                href="/settings"
                className="dropdown-item"
                onClick={() => {
                  setOpen(false);
                  navigate("/settings");
                }}
              >
                <span>🔧</span>
                <span>Settings</span>
              </a>

              {user.is_admin && (
                <a
                  href="/admin"
                  className="dropdown-item"
                  onClick={() => {
                    setOpen(false);
                    navigate("/admin");
                  }}
                >
                  <span>🔐</span>
                  <span>Admin Panel</span>
                </a>
              )}
            </nav>

            <div className="dropdown-divider" />

            <button
              className="dropdown-item logout-item"
              onClick={handleLogout}
              disabled={isLoggingOut}
            >
              <span>🚪</span>
              <span>{isLoggingOut ? "Logging out..." : "Logout"}</span>
            </button>
          </div>
        )}
      </div>

      {showToast && (
        <div className="toast">
          <div className="toast-content">
            <span>✓</span>
            <p>{toastMessage}</p>
          </div>
        </div>
      )}
    </>
  );
}
