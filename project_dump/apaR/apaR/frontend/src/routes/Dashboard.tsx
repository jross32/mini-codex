import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getDivisions, getHealth, getMatches, getMeta } from "../api/client";
import { Skeleton } from "../components/Skeleton";
import { EmptyState } from "../components/EmptyState";

export function Dashboard() {
  const healthQuery = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const metaQuery = useQuery({ queryKey: ["meta"], queryFn: getMeta });
  const divisionsQuery = useQuery({ queryKey: ["divisions"], queryFn: getDivisions });
  const matchesQuery = useQuery({
    queryKey: ["matches", "recent"],
    queryFn: () => getMatches({}),
  });

  const recentMatches = useMemo(() => matchesQuery.data?.matches?.slice(0, 5) ?? [], [matchesQuery.data]);

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
          <div>
            <p className="eyebrow">Dashboard</p>
            <h1>League command center</h1>
            <p className="lede">Quick health, counts, and the latest matches.</p>
          </div>
        </section>

      <section className="grid">
        <article className="card">
          <div className="pill">Health</div>
          <h3>API status</h3>
          {healthQuery.isLoading && <Skeleton lines={3} />}
          {healthQuery.isError && <p className="error">Unable to load health</p>}
          {healthQuery.data && (
            <ul className="stats-list">
              <li>
                <span>Environment</span>
                <strong>{healthQuery.data.environment}</strong>
              </li>
              <li>
                <span>Database</span>
                <strong>{healthQuery.data.database ?? "not configured"}</strong>
              </li>
              <li>
                <span>Dataset</span>
                <strong>{healthQuery.data.data?.status ?? "unknown"}</strong>
              </li>
            </ul>
          )}
        </article>

        <article className="card">
          <div className="pill">Data</div>
          <h3>Counts</h3>
          {metaQuery.isLoading && <Skeleton lines={4} />}
          {metaQuery.isError && <p className="error">Unable to load metadata</p>}
          {metaQuery.data && (
            <ul className="stats-list">
              <li>
                <span>Divisions</span>
                <strong>{metaQuery.data.counts.divisions}</strong>
              </li>
              <li>
                <span>Teams</span>
                <strong>{metaQuery.data.counts.teams}</strong>
              </li>
              <li>
                <span>Players</span>
                <strong>{metaQuery.data.counts.players}</strong>
              </li>
              <li>
                <span>Matches</span>
                <strong>{metaQuery.data.counts.matches}</strong>
              </li>
            </ul>
          )}
        </article>

        <article className="card">
          <div className="pill">Divisions</div>
          <h3>Active sessions</h3>
          {divisionsQuery.isLoading && <Skeleton lines={4} />}
          {divisionsQuery.isError && <p className="error">Unable to load divisions</p>}
          {divisionsQuery.data && (
            <ul className="list">
              {divisionsQuery.data.divisions.map((division) => (
                <li key={division.id ?? Math.random()}>
                  <div>
                    <strong>{division.name ?? "Unnamed division"}</strong>
                    <p className="muted">
                      {division.night ?? "Night TBD"} · {division.format ?? "Format"} · {division.session ?? "Session"}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Matches</p>
            <h3>Recent</h3>
          </div>
        </div>
        {matchesQuery.isLoading && <Skeleton lines={5} />}
        {matchesQuery.isError && <p className="error">Unable to load matches</p>}
        {recentMatches.length > 0 ? (
          <div className="table">
            <div className="table-head">
              <div>Date</div>
              <div>Home</div>
              <div>Away</div>
              <div>Score</div>
            </div>
            <div className="table-body">
              {recentMatches.map((match) => (
                <div key={match.id ?? Math.random()} className="table-row">
                  <div>{match.played_at ? new Date(match.played_at).toLocaleDateString() : "TBD"}</div>
                  <div>{match.home_team_id ?? "Home"}</div>
                  <div>{match.away_team_id ?? "Away"}</div>
                  <div>
                    {match.score.home} - {match.score.away}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          matchesQuery.isSuccess && (
            <EmptyState
              title="No matches yet"
              message="Upload data or sync to see recent games."
              action={
                <Link to="/settings" className="button small primary">
                  Upload data
                </Link>
              }
            />
          )
        )}
      </section>
      </div>
    </div>
  );
}
