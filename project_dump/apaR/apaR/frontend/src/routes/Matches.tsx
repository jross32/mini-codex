import { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getDivisions, getMatches } from "../api/client";
import { Skeleton } from "../components/Skeleton";
import { EmptyState } from "../components/EmptyState";
import { VirtualList } from "../components/VirtualList";

export function Matches() {
  const divisionsQuery = useQuery({ queryKey: ["divisions"], queryFn: getDivisions });
  const [division, setDivision] = useState("");
  const [team, setTeam] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const matchesQuery = useQuery({
    queryKey: ["matches", { division, team, dateFrom, dateTo }],
    queryFn: () =>
      getMatches({
        division: division || undefined,
        team: team || undefined,
        from: dateFrom || undefined,
        to: dateTo || undefined,
      }),
  });

  const matches = matchesQuery.data?.matches ?? [];
  const shouldVirtualize = matches.length > 24;
  const tableHeight = useMemo(() => Math.min(540, Math.max(300, matches.length * 62)), [matches.length]);
  const renderMatchRow = useCallback(
    (match: (typeof matches)[number], idx: number) => (
      <div key={match.id ?? `match-${idx}`} className="table-row">
        <div data-label="Date">{match.played_at ? new Date(match.played_at).toLocaleDateString() : "TBD"}</div>
        <div data-label="Division" className="hide-on-tablet">{match.division_id ?? "TBD"}</div>
        <div data-label="Home">{match.home_team_id ?? "Home"}</div>
        <div data-label="Away">{match.away_team_id ?? "Away"}</div>
        <div data-label="Score">
          {match.score.home} - {match.score.away}
        </div>
      </div>
    ),
    [matches],
  );

  const divisionOptions = useMemo(() => divisionsQuery.data?.divisions ?? [], [divisionsQuery.data]);

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
        <div>
          <p className="eyebrow">Matches</p>
          <h1>Scorecards and filters</h1>
          <p className="lede">Filter by division, team, or date range.</p>
        </div>
        <div className="filters">
          <select value={division} onChange={(e) => setDivision(e.target.value)}>
            <option value="">All divisions</option>
            {divisionOptions.map((div) => (
              <option key={div.id ?? `div-${Math.random()}`} value={div.id ?? ""}>
                {div.name ?? `Division ${div.id ?? ""}`}
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Team id"
            value={team}
            onChange={(e) => setTeam(e.target.value)}
            className="input"
          />
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Matches</p>
            <h3>Results</h3>
          </div>
        </div>

        {matchesQuery.isLoading && <Skeleton lines={4} />}
        {matchesQuery.isError && <p className="error">Unable to load matches</p>}

        {matches.length === 0 &&
          matchesQuery.isSuccess && (
            <EmptyState
              title="Upload data or adjust filters"
              message="No matches matched these filters yet."
              action={
                <>
                  <button
                    className="button small ghost"
                    onClick={() => {
                      setDivision("");
                      setTeam("");
                      setDateFrom("");
                      setDateTo("");
                    }}
                  >
                    Clear filters
                  </button>
                  <Link to="/settings" className="button small primary">
                    Upload data
                  </Link>
                </>
              }
            />
          )}

        {matches.length > 0 && (
          <div className="table">
            <div className="table-head">
              <div>Date</div>
              <div>Division</div>
              <div>Home</div>
              <div>Away</div>
              <div>Score</div>
            </div>
            {shouldVirtualize ? (
              <VirtualList
                items={matches}
                itemHeight={62}
                height={tableHeight}
                className="virtual-table"
                renderRow={renderMatchRow}
              />
            ) : (
              <div className="table-body">
                {matches.map(renderMatchRow)}
              </div>
            )}
          </div>
        )}
      </section>
      </div>
    </div>
  );
}
