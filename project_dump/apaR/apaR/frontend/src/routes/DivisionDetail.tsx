import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getDivision, getMeta } from "../api/client";
import { Skeleton } from "../components/Skeleton";

export function DivisionDetail() {
  const { divisionId } = useParams<{ divisionId: string }>();

  const divisionQuery = useQuery({
    queryKey: ["division", divisionId],
    queryFn: () => getDivision(divisionId ?? ""),
    enabled: Boolean(divisionId),
  });

  const metaQuery = useQuery({ queryKey: ["meta"], queryFn: getMeta });

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
        <div>
          <p className="eyebrow">Division</p>
          <h1>{divisionQuery.data?.name ?? "Division details"}</h1>
          <p className="lede">
            {divisionQuery.data?.night ?? "Night TBD"} · {divisionQuery.data?.format ?? "Format TBD"} ·{" "}
            {divisionQuery.data?.session ?? "Session TBD"}
          </p>
          {metaQuery.data?.last_loaded_at && (
            <p className="muted">Last updated: {new Date(metaQuery.data.last_loaded_at).toLocaleString()}</p>
          )}
        </div>
        <Link to="/divisions" className="ghost-button">
          Back to divisions
        </Link>
      </section>

      {divisionQuery.isLoading && <Skeleton lines={4} />}
      {divisionQuery.isError && <p className="error">Unable to load this division.</p>}

      {divisionQuery.data && (
        <section className="card">
          <div className="card-header">
            <div>
              <p className="pill">Standings</p>
              <h3>Rankings</h3>
            </div>
          </div>
          {divisionQuery.data.standings.length === 0 ? (
            <p className="muted">No standings available.</p>
          ) : (
            <div className="table">
              <div className="table-head standings-head">
                <div>Rank</div>
                <div>Team</div>
                <div>Points</div>
                <div className="hide-on-tablet">Last week</div>
              </div>
              <div className="table-body">
                {divisionQuery.data.standings.map((entry, idx) => (
                  <Link
                    key={entry.team_id ?? `stand-${idx}`}
                    to={entry.team_id ? `/teams/${entry.team_id}` : "#"}
                    className={`table-row standings-row ${entry.team_id ? "link-row" : "disabled"}`}
                  >
                    <div data-label="Rank">{entry.rank ?? idx + 1}</div>
                    <div data-label="Team">{entry.team_id ?? "Team"}</div>
                    <div data-label="Points">{entry.points ?? 0}</div>
                    <div data-label="Last week" className="hide-on-tablet">{entry.last_week ?? "—"}</div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
      </div>
    </div>
  );
}
