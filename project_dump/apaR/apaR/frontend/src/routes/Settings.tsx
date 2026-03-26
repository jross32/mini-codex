import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { importDataset, getMeta } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { Skeleton } from "../components/Skeleton";

type SettingsTab = "account" | "data" | "advanced";

export function Settings() {
  const [activeTab, setActiveTab] = useState<SettingsTab>("account");
  const navigate = useNavigate();
  const { user, context } = useAuth();
  const metaQuery = useQuery({ queryKey: ["meta"], queryFn: getMeta });
  const importMutation = useMutation({
    mutationFn: importDataset,
  });

  const diffs = importMutation.data?.diffs;

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
          <div>
            <p className="eyebrow">Settings</p>
            <h1>Account & Preferences</h1>
            <p className="lede">Manage your account and customize your experience.</p>
          </div>
        </section>

        <div className="settings-layout">
          {/* Left sidebar nav */}
          <nav className="settings-nav">
            <button
              className={`settings-nav-item ${activeTab === "account" ? "active" : ""}`}
              onClick={() => setActiveTab("account")}
            >
              <span>👤</span>
              My Account
            </button>
            <button
              className={`settings-nav-item ${activeTab === "data" ? "active" : ""}`}
              onClick={() => setActiveTab("data")}
            >
              <span>💾</span>
              Data & Import
            </button>
            <button
              className={`settings-nav-item ${activeTab === "advanced" ? "active" : ""}`}
              onClick={() => setActiveTab("advanced")}
            >
              <span>🔧</span>
              Advanced
            </button>
          </nav>

          {/* Right content area */}
          <div className="settings-content">
            {/* Account Tab */}
            {activeTab === "account" && (
              <section className="card">
                <div className="card-header">
                  <div>
                    <p className="pill">Account</p>
                    <h2>Your Profile</h2>
                  </div>
                </div>

                {user && (
                  <div className="stack">
                    <div className="settings-field">
                      <label>Email</label>
                      <p className="settings-value">{user.email}</p>
                    </div>

                    <div className="settings-field">
                      <label>Username</label>
                      <p className="settings-value">{user.username || "Not set"}</p>
                    </div>

                    {user.is_admin && (
                      <div className="settings-field">
                        <label>Account Type</label>
                        <span className="pill">Administrator</span>
                      </div>
                    )}
                  </div>
                )}

                {context && (
                  <>
                    <div className="settings-divider" />

                    <div className="stack">
                      <p className="settings-section-title">Team & Role</p>

                      <div className="settings-field">
                        <label>Division</label>
                        <p className="settings-value">{context.division_id || "Not selected"}</p>
                      </div>

                      <div className="settings-field">
                        <label>Team</label>
                        <p className="settings-value">{context.team_id || "Not selected"}</p>
                      </div>

                      <div className="settings-field">
                        <label>Role</label>
                        <p className="settings-value">
                          <span className="pill soft">{context.role}</span>
                        </p>
                      </div>

                      <button
                        className="button secondary"
                        onClick={() => navigate("/onboarding")}
                      >
                        Change Team or Role
                      </button>
                    </div>
                  </>
                )}
              </section>
            )}

            {/* Data & Import Tab */}
            {activeTab === "data" && (
              <>
                <section className="card">
                  <div className="card-header">
                    <div>
                      <p className="pill">Data</p>
                      <h2>Dataset Management</h2>
                    </div>
                  </div>

                  <div className="stack">
                    <div>
                      <p className="settings-section-title">Current Dataset</p>
                      {metaQuery.data?.last_loaded_at && (
                        <p className="settings-value">
                          Last loaded: {new Date(metaQuery.data.last_loaded_at).toLocaleString()}
                        </p>
                      )}
                    </div>

                    <div>
                      <p className="settings-section-title">Import Dataset</p>
                      <button
                        className="button primary"
                        disabled={importMutation.isPending}
                        onClick={() => importMutation.mutate()}
                      >
                        {importMutation.isPending ? "Refreshing..." : "Import / Refresh Data"}
                      </button>

                      {importMutation.isError && (
                        <p className="error" style={{ marginTop: "0.5rem" }}>
                          Import failed. Please try again.
                        </p>
                      )}

                      {importMutation.isSuccess && (
                        <p className="muted" style={{ marginTop: "0.5rem" }}>
                          ✓ Reloaded {importMutation.data.source ?? "latest"} at{" "}
                          {importMutation.data.last_loaded_at
                            ? new Date(importMutation.data.last_loaded_at).toLocaleString()
                            : "just now"}
                        </p>
                      )}
                    </div>
                  </div>
                </section>

                {diffs && (
                  <section className="card">
                    <div className="card-header">
                      <div>
                        <p className="pill">Changes</p>
                        <h3>Last import diffs</h3>
                      </div>
                    </div>

                    <div className="stack">
                      <div>
                        <p className="settings-subsection-title">Teams Moved</p>
                        {diffs.teams_moved.length === 0 ? (
                          <p className="muted">None</p>
                        ) : (
                          <ul className="list">
                            {diffs.teams_moved.map((team, idx) => (
                              <li key={team.team_id ?? `team-move-${idx}`}>
                                <strong>{team.team_id}</strong>
                                <span className="muted">
                                  {team.from ?? "?"} → {team.to ?? "?"}
                                </span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>

                      <div>
                        <p className="settings-subsection-title">Player SL Changes</p>
                        {diffs.players_sl_changed.length === 0 ? (
                          <p className="muted">None</p>
                        ) : (
                          <ul className="list">
                            {diffs.players_sl_changed.map((player, idx) => (
                              <li key={player.player_id ?? `sl-${idx}`}>
                                <strong>{player.player_id}</strong>
                                <span className="muted">
                                  {String(player.from ?? "—")} → {String(player.to ?? "—")}
                                </span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </div>
                  </section>
                )}
              </>
            )}

            {/* Advanced Tab */}
            {activeTab === "advanced" && (
              <section className="card">
                <div className="card-header">
                  <div>
                    <p className="pill">System</p>
                    <h2>Advanced Settings</h2>
                  </div>
                </div>

                <div className="stack">
                  <div>
                    <p className="settings-section-title">API Configuration</p>
                    <p className="muted">
                      Frontend reads <code>VITE_API_BASE_URL</code> environment variable to connect to the backend.
                    </p>
                  </div>

                  <div>
                    <p className="settings-section-title">Data Storage</p>
                    <p className="muted">
                      Backend loads the latest dataset from <code>data/</code> directory and caches it in memory. Snapshots
                      persist to PostgreSQL as JSON for history and auditing.
                    </p>
                  </div>

                  <div>
                    <p className="settings-section-title">Environment</p>
                    {metaQuery.data && (
                      <div className="settings-code-block">
                        {metaQuery.isLoading && <Skeleton lines={2} />}
                        {!metaQuery.isLoading && (
                          <>
                            <p className="muted"><strong>Data Source:</strong> {metaQuery.data.source || "not loaded"}</p>
                            <p className="muted"><strong>Last Loaded:</strong> {metaQuery.data.last_loaded_at ? new Date(metaQuery.data.last_loaded_at).toLocaleString() : "never"}</p>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </section>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


