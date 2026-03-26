import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMatches, getMeta, getTeam } from "../api/client";
import { Skeleton } from "../components/Skeleton";

export function TeamDetail() {
  const { teamId } = useParams<{ teamId: string }>();

  const teamQuery = useQuery({
    queryKey: ["team", teamId],
    queryFn: () => getTeam(teamId ?? ""),
    enabled: Boolean(teamId),
  });

  const matchesQuery = useQuery({
    queryKey: ["matches", "team", teamId],
    queryFn: () => getMatches({ team: teamId }),
    enabled: Boolean(teamId),
  });

  const metaQuery = useQuery({ queryKey: ["meta"], queryFn: getMeta });

  const roster = teamQuery.data?.roster ?? [];
  const recentMatches = useMemo(() => matchesQuery.data?.matches.slice(0, 5) ?? [], [matchesQuery.data]);

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
        <div>
          <p className="eyebrow">Team</p>
          <h1>{teamQuery.data?.name ?? "Team details"}</h1>
          <p className="lede">Division {teamQuery.data?.division_id ?? "TBD"} · Location {teamQuery.data?.location_id ?? "TBD"}</p>
          {metaQuery.data?.last_loaded_at && (
            <p className="muted">Last updated: {new Date(metaQuery.data.last_loaded_at).toLocaleString()}</p>
          )}
        </div>
        <div className="stack align-end">
          <Link to="/teams" className="ghost-button">
            Back to teams
          </Link>
        </div>
      </section>

      {teamQuery.isLoading && <Skeleton lines={4} />}
      {teamQuery.isError && <p className="error">Unable to load this team.</p>}

      {teamQuery.data && (
        <>
          <section className="card">
            <div className="card-header">
              <div>
                <p className="pill">Overview</p>
                <h3>{teamQuery.data.name ?? "Team"}</h3>
                <p className="muted">Home location: {teamQuery.data.location_id ?? "TBD"}</p>
              </div>
              <div className="badge">Division {teamQuery.data.division_id ?? "TBD"}</div>
            </div>
            <div className="stack">
              <div className="row">
                <span>Record</span>
                <strong>—</strong>
              </div>
              <div className="row">
                <span>Points</span>
                <strong>—</strong>
              </div>
            </div>
          </section>

          <section className="card">
            <div className="card-header">
              <div>
                <p className="pill">Roster</p>
                <h3>Players</h3>
              </div>
            </div>
            {roster.length === 0 ? (
              <p className="muted">No roster listed.</p>
            ) : (
              <div className="table">
                <div className="table-head roster-head">
                  <div>Name</div>
                  <div className="hide-on-tablet">SL</div>
                  <div className="hide-on-mobile">Matches</div>
                  <div className="hide-on-mobile">Win %</div>
                  <div className="hide-on-mobile">PPM / PA</div>
                </div>
                <div className="table-body">
                  {roster.map((player, idx) => (
                    <div key={player.id ?? `player-${idx}`} className="table-row roster-row">
                      <div data-label="Name">{player.name ?? "Player"}</div>
                      <div data-label="SL" className="hide-on-tablet">—</div>
                      <div data-label="Matches" className="hide-on-mobile">—</div>
                      <div data-label="Win %" className="hide-on-mobile">—</div>
                      <div data-label="PPM / PA" className="hide-on-mobile">—</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          <section className="card">
            <div className="card-header">
              <div>
                <p className="pill">Matches</p>
                <h3>Recent</h3>
              </div>
            </div>
            {matchesQuery.isLoading && <Skeleton lines={3} />}
            {matchesQuery.isError && <p className="error">Unable to load matches.</p>}
            {recentMatches.length === 0 && matchesQuery.isSuccess && <p className="muted">No recent matches.</p>}
            {recentMatches.length > 0 && (
              <div className="table">
                <div className="table-head">
                  <div>Date</div>
                  <div>Division</div>
                  <div>Opponent</div>
                  <div>Score</div>
                </div>
                <div className="table-body">
                  {recentMatches.map((match) => {
                    const isHome = match.home_team_id === teamId;
                    const opponent = isHome ? match.away_team_id : match.home_team_id;
                    const score = `${match.score.home} - ${match.score.away}`;
                    return (
                      <div key={match.id ?? `match-${Math.random()}`} className="table-row">
                        <div>{match.played_at ? new Date(match.played_at).toLocaleDateString() : "TBD"}</div>
                        <div>{match.division_id ?? "TBD"}</div>
                        <div>{opponent ?? "TBD"}</div>
                        <div>{score}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </section>

          <section className="card">
            <div className="card-header">
              <div>
                <p className="pill">Captain tools</p>
                <h3>Notes & lineup</h3>
              </div>
            </div>
            <div className="stack">
              <div className="captain-block">
                <p className="muted">Notes</p>
                <div className="placeholder-box">Add match prep or scouting notes.</div>
              </div>
              <div className="captain-block">
                <p className="muted">Availability</p>
                <div className="placeholder-box">Track who is in/out for the week.</div>
              </div>
              <div className="captain-block">
                <p className="muted">Lineup ideas</p>
                <div className="placeholder-box">Sketch pairings or sets here.</div>
              </div>
            </div>
          </section>
        </>
      )}
      </div>
    </div>
  );
}
