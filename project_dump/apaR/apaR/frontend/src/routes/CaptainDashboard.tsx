import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMatches, getMeta, getDivision, getTeam } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { Skeleton } from "../components/Skeleton";

// Mock dataset for development/empty states
const MOCK_DATASET = {
  team: { id: "team-demo", name: "Demo Team", division_id: "div-demo" },
  division: { id: "div-demo", name: "Premier League", night: "Tuesday" },
  nextMatch: {
    id: "match-1",
    home_team_id: "team-demo",
    away_team_id: "team-rival",
    location_id: "venue-1",
    played_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 1 week from now
  },
  recentMatches: [
    {
      id: "match-1",
      home_team_id: "team-demo",
      away_team_id: "team-a",
      location_id: "venue-1",
      played_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      score_home: 11,
      score_away: 9,
    },
    {
      id: "match-2",
      home_team_id: "team-b",
      away_team_id: "team-demo",
      location_id: "venue-2",
      played_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
      score_home: 8,
      score_away: 10,
    },
  ],
};

export function CaptainDashboard() {
  const { context } = useAuth();

  // Check if user has selected team/division (onboarding complete)
  const needsOnboarding = !context?.team_id || !context?.division_id;

  // Queries
  const metaQuery = useQuery({ queryKey: ["meta"], queryFn: getMeta });
  const matchesQuery = useQuery({
    queryKey: ["matches", "captain", context?.team_id],
    queryFn: () => getMatches(context?.team_id ? { team: context.team_id } : {}),
    enabled: true, // Always enabled; we'll use mock on error
  });

  const divisionQuery = useQuery({
    queryKey: ["division", context?.division_id],
    queryFn: () => getDivision(context?.division_id!),
    enabled: !!context?.division_id,
  });

  const teamQuery = useQuery({
    queryKey: ["team", context?.team_id],
    queryFn: () => getTeam(context?.team_id!),
    enabled: !!context?.team_id,
  });

  // Compute next match (upcoming or most recent)
  const nextMatch = useMemo(() => {
    const matches = matchesQuery.data?.matches ?? [];
    if (!matches.length) return MOCK_DATASET.nextMatch;

    const now = Date.now();
    const upcoming = matches
      .filter((m) => (m.played_at ? new Date(m.played_at).getTime() : 0) > now)
      .sort((a, b) => {
        const ad = a.played_at ? new Date(a.played_at).getTime() : 0;
        const bd = b.played_at ? new Date(b.played_at).getTime() : 0;
        return ad - bd;
      });

    return upcoming[0] ?? matches[0] ?? MOCK_DATASET.nextMatch;
  }, [matchesQuery.data]);

  // Get recent matches
  const recentMatches = useMemo(() => {
    const matches = matchesQuery.data?.matches ?? [];
    return matches.slice(0, 5);
  }, [matchesQuery.data]);

  // Determine if we're using mock data
  const isUsingMockData = matchesQuery.isError || !matchesQuery.data;

  // Loading state
  const isLoading = matchesQuery.isLoading || teamQuery.isLoading || divisionQuery.isLoading;
  const hasError = matchesQuery.isError || teamQuery.isError || divisionQuery.isError;
  const hasMissingContext = needsOnboarding;

  // Render JSX
  return (
    <div className="page-container">
      <div className="page">
        {/* ONBOARDING EMPTY STATE */}
        {hasMissingContext && (
          <section className="card card-empty">
            <div className="empty-state">
              <h2>Finish Onboarding</h2>
              <p className="lede">
                Choose your team and division to unlock the Captain Dashboard.
              </p>
              <Link to="/onboarding" className="button primary">
                Go to Onboarding
              </Link>
            </div>
          </section>
        )}

        {/* ERROR STATE */}
        {hasError && !hasMissingContext && (
          <section className="card card-error">
            <div className="error-state">
              <h2>Failed to Load Dashboard</h2>
              <p className="muted">
                We couldn't fetch your data. Using mock data to show what's possible.
              </p>
              <button
                onClick={() => {
                  matchesQuery.refetch();
                  teamQuery.refetch();
                  divisionQuery.refetch();
                }}
                className="button primary small"
              >
                Retry
              </button>
            </div>
          </section>
        )}

        {/* LOADING STATE */}
        {isLoading && !hasMissingContext && (
          <>
            <section className="page-header">
              <div>
                <p className="eyebrow">Captain Dashboard</p>
                <h1>Loading...</h1>
              </div>
            </section>
            <section className="dashboard-grid">
              <article className="card widget-tall">
                <Skeleton lines={5} />
              </article>
              <article className="card widget-tall">
                <Skeleton lines={5} />
              </article>
              <article className="card widget-tall">
                <Skeleton lines={5} />
              </article>
            </section>
          </>
        )}

        {/* MAIN DASHBOARD CONTENT */}
        {!isLoading && !hasMissingContext && (
          <>
            {/* Page Header */}
            <section className="page-header">
              <div>
                <p className="eyebrow">Captain Dashboard</p>
                <h1>Decision-First View</h1>
                <p className="lede">
                  {teamQuery.data
                    ? `${teamQuery.data.name} • ${divisionQuery.data?.name || "Your Division"}`
                    : "See the next match, division trend, and who needs reps."}
                </p>
              </div>
              <div className="page-header-actions">
                {isUsingMockData && (
                  <span className="pill soft">Mock data</span>
                )}
                {metaQuery.data?.last_loaded_at && (
                  <p className="muted small">
                    Updated {new Date(metaQuery.data.last_loaded_at).toLocaleString()}
                  </p>
                )}
              </div>
            </section>

            {/* Widget Grid: 3 columns desktop */}
            <section className="dashboard-grid">
              {/* Next Match Widget */}
              <article className="card widget-tall">
                <div className="card-header">
                  <div>
                    <p className="pill">Next Match</p>
                    <h3>Opponent & Timing</h3>
                  </div>
                </div>
                {nextMatch ? (
                  <div className="stack">
                    <div className="row">
                      <span>Opponent</span>
                      <strong>
                        {nextMatch.away_team_id === context?.team_id
                          ? nextMatch.home_team_id ?? "TBD"
                          : nextMatch.away_team_id ?? "TBD"}
                      </strong>
                    </div>
                    <div className="row">
                      <span>Location</span>
                      <strong>{nextMatch.location_id ?? "TBD"}</strong>
                    </div>
                    <div className="row">
                      <span>Date/Time</span>
                      <strong>
                        {nextMatch.played_at
                          ? new Date(nextMatch.played_at).toLocaleString()
                          : "TBD"}
                      </strong>
                    </div>
                    <div className="row">
                      <span>Home/Away</span>
                      <strong>
                        {nextMatch.home_team_id === context?.team_id
                          ? "Home"
                          : "Away"}
                      </strong>
                    </div>
                  </div>
                ) : (
                  <p className="muted">No matches scheduled.</p>
                )}
                <div className="widget-actions">
                  <Link to="/lineup" className="button primary small">
                    Build Lineup
                  </Link>
                  <Link to="/captain/tonight" className="button ghost small">
                    Match Night
                  </Link>
                </div>
              </article>

              {/* Division Snapshot Widget */}
              <article className="card widget-tall">
                <div className="card-header">
                  <div>
                    <p className="pill">Division Snapshot</p>
                    <h3>Rank & Momentum</h3>
                  </div>
                </div>
                <div className="stack">
                  <div className="row">
                    <span>Division</span>
                    <strong>{divisionQuery.data?.name ?? "—"}</strong>
                  </div>
                  <div className="row">
                    <span>Your Rank</span>
                    <strong>—</strong>
                  </div>
                  <div className="row">
                    <span>To Next</span>
                    <strong>—</strong>
                  </div>
                  <div className="row">
                    <span>Trend</span>
                    <strong>Steady</strong>
                  </div>
                </div>
                <div className="widget-actions">
                  <Link to="/division-standings" className="button primary small">
                    Standings
                  </Link>
                </div>
              </article>

              {/* Team Readiness Widget */}
              <article className="card widget-tall">
                <div className="card-header">
                  <div>
                    <p className="pill">Team Readiness</p>
                    <h3>Availability & Dues</h3>
                  </div>
                </div>
                <div className="stack">
                  <div className="row">
                    <span>Availability</span>
                    <strong>Yes: 0 · No: 0</strong>
                  </div>
                  <div className="row">
                    <span>Dues Status</span>
                    <strong>Paid: 0 · Owes: 0</strong>
                  </div>
                  <div className="row">
                    <span>Needs Reps</span>
                    <strong>—</strong>
                  </div>
                </div>
                <div className="widget-actions">
                  <Link to="/notes" className="button primary small">
                    Notes & Dues
                  </Link>
                </div>
              </article>
            </section>

            {/* Second Row: Recent Matches */}
            <section className="card widget-recent-matches">
              <div className="card-header">
                <div>
                  <p className="pill">Recent Matches</p>
                  <h3>Last 5 Contests</h3>
                </div>
              </div>
              {recentMatches.length > 0 ? (
                <div className="stack gap-lg">
                  {recentMatches.map((match) => (
                    <div key={match.id} className="row">
                      <span>
                        {new Date(match.played_at ?? "").toLocaleDateString()}
                      </span>
                      <strong>
                        {match.home_team_id ?? "Home"} vs{" "}
                        {match.away_team_id ?? "Away"}
                      </strong>
                      <span>
                        {match.score?.home ?? "—"} - {match.score?.away ?? "—"}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">No recent matches.</p>
              )}
            </section>

            {/* Quick Actions */}
            <section className="card widget-actions-panel">
              <div className="card-header">
                <div>
                  <p className="pill">Quick Actions</p>
                  <h3>Fast Decisions</h3>
                </div>
              </div>
              <div className="actions-row dense">
                <Link to="/lineup" className="button primary small">
                  Build Lineup
                </Link>
                <Link to="/notes" className="button ghost small">
                  Add Note
                </Link>
                <Link to="/notes" className="button ghost small">
                  Availability
                </Link>
                <Link to="/settings" className="button ghost small">
                  Refresh Data
                </Link>
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
