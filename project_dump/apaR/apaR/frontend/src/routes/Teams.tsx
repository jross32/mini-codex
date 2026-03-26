import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { search } from "../api/client";
import { Skeleton } from "../components/Skeleton";
import { EmptyState } from "../components/EmptyState";
import { VirtualList } from "../components/VirtualList";

export function Teams() {
  const [term, setTerm] = useState("");
  const [debounced, setDebounced] = useState("");

  useEffect(() => {
    const id = setTimeout(() => setDebounced(term), 250);
    return () => clearTimeout(id);
  }, [term]);

  const teamsQuery = useQuery({
    queryKey: ["search", debounced],
    queryFn: () => search(debounced),
    enabled: debounced.length > 1,
  });

  const teams = teamsQuery.data?.teams ?? [];
  const shouldVirtualize = teams.length > 30;

  const renderTeamCard = useCallback(
    (team: (typeof teams)[number], idx: number) => (
      <article key={team.id ?? `team-${idx}`} className="card link-card inline-card">
        <Link to={`/teams/${team.id ?? ""}`}>
          <div>
            <p className="pill">Team</p>
            <h3>{team.name ?? "Unnamed team"}</h3>
            <p className="muted small">Division {team.division_id ?? "TBD"}</p>
          </div>
          <span className="badge">Roster</span>
        </Link>
      </article>
    ),
    [teams],
  );

  const virtualHeight = useMemo(() => Math.min(520, Math.max(260, teams.length * 116)), [teams.length]);

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
        <div>
          <p className="eyebrow">Teams</p>
          <h1>Rosters and divisions</h1>
          <p className="lede">Search for a team to see its division and roster summary.</p>
        </div>
        <div className="search-inline">
          <input
            type="search"
            placeholder="Search teams"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
          />
        </div>
      </section>

      {teamsQuery.isLoading && <Skeleton lines={4} />}
      {teamsQuery.isError && <p className="error">Unable to load teams</p>}

      {teamsQuery.isSuccess && teams.length === 0 && (
        <EmptyState
          title="No teams found"
          message="Try another name or upload data."
          action={
            <Link to="/settings" className="button small primary">
              Upload data
            </Link>
          }
        />
      )}

      {teams.length === 0 && debounced.length <= 1 && !teamsQuery.isLoading && (
        <EmptyState
          title="Choose your team"
          message="Search by name or division to jump into rosters."
          action={
            <Link to="/team-roster" className="button small ghost">
              Open roster hub
            </Link>
          }
        />
      )}

      {teams.length > 0 &&
        (shouldVirtualize ? (
          <VirtualList
            items={teams}
            itemHeight={116}
            height={virtualHeight}
            renderRow={(team, idx) => <div style={{ padding: "0.25rem 0.15rem" }}>{renderTeamCard(team, idx)}</div>}
          />
        ) : (
          <div className="grid">{teams.map(renderTeamCard)}</div>
        ))}
      </div>
    </div>
  );
}
