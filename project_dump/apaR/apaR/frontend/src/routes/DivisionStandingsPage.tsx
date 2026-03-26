import { useQuery } from "@tanstack/react-query";
import { getDivisions } from "../api/client";
import { Skeleton } from "../components/Skeleton";

export function DivisionStandingsPage() {
  const divisionsQuery = useQuery({ queryKey: ["divisions"], queryFn: getDivisions });

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
        <div>
          <p className="eyebrow">Division Standings</p>
          <h1>Ranks and points</h1>
          <p className="lede">Check who is on top before setting your lineup.</p>
        </div>
      </section>

      {divisionsQuery.isLoading && (
        <article className="card">
          <Skeleton lines={4} />
        </article>
      )}
      {divisionsQuery.isError && <p className="error">Unable to load divisions.</p>}

      {divisionsQuery.data?.divisions.map((division, idx) => (
        <section key={division.id ?? `div-${idx}`} className="card">
          <div className="card-header">
            <div>
              <p className="pill">{division.night ?? "Night"}</p>
              <h3>{division.name ?? "Division"}</h3>
              <p className="muted">{division.format ?? "Format"} · {division.session ?? "Session"}</p>
            </div>
            <div className="badge">Teams {division.team_ids?.length ?? 0}</div>
          </div>
          {division.standings?.length ? (
            <div className="table">
              <div className="table-head standings-head">
                <div>Rank</div>
                <div>Team</div>
                <div>Points</div>
                <div className="hide-on-tablet">Last week</div>
              </div>
              <div className="table-body">
                {division.standings.map((row, sIdx) => (
                  <div key={row.team_id ?? `row-${sIdx}`} className="table-row standings-row">
                    <div data-label="Rank">{row.rank ?? sIdx + 1}</div>
                    <div data-label="Team">{row.team_id ?? "Team"}</div>
                    <div data-label="Points">{row.points ?? 0}</div>
                    <div data-label="Last week" className="hide-on-tablet">{row.last_week ?? "—"}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="muted">No standings posted.</p>
          )}
        </section>
      ))}
      </div>
    </div>
  );
}
