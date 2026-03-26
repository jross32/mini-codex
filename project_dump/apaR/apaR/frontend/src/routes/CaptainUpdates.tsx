import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getUpdates } from "../api/client";
import { Skeleton } from "../components/Skeleton";

export function CaptainUpdates() {
  const updatesQuery = useQuery({ queryKey: ["updates"], queryFn: getUpdates });
  const [divisionFilter, setDivisionFilter] = useState("");
  const [teamFilter, setTeamFilter] = useState("");
  const [playerFilter, setPlayerFilter] = useState("");

  const filteredSnapshots = useMemo(() => {
    const snapshots = updatesQuery.data?.snapshots ?? [];
    return snapshots.map((snap) => {
      const diffs = snap.diffs;
      const matchesDivision = (entry: any) => !divisionFilter || entry.division_id === divisionFilter;
      const matchesTeam = (entry: any) => !teamFilter || entry.team_id === teamFilter;
      const matchesPlayer = (entry: any) => !playerFilter || entry.player_id === playerFilter;
      return {
        ...snap,
        diffs: {
          ...diffs,
          standings_changed: diffs.standings_changed.filter((d) => matchesDivision(d) && matchesTeam(d)),
          team_points_changed: diffs.team_points_changed.filter((d) => matchesDivision(d) && matchesTeam(d)),
          players_sl_changed: diffs.players_sl_changed.filter((d) => matchesPlayer(d)),
          teams_moved: diffs.teams_moved.filter((d) => matchesTeam(d)),
          win_pct_swings: diffs.win_pct_swings.filter((d) => matchesPlayer(d)),
        },
      };
    });
  }, [updatesQuery.data, divisionFilter, teamFilter, playerFilter]);

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
        <div>
          <p className="eyebrow">Updates</p>
          <h1>Snapshots & diffs</h1>
          <p className="lede">Track what changed each import.</p>
        </div>
        <div className="filters stacked">
          <input
            type="text"
            placeholder="Filter division id"
            value={divisionFilter}
            onChange={(e) => setDivisionFilter(e.target.value)}
          />
          <input
            type="text"
            placeholder="Filter team id"
            value={teamFilter}
            onChange={(e) => setTeamFilter(e.target.value)}
          />
          <input
            type="text"
            placeholder="Filter player id"
            value={playerFilter}
            onChange={(e) => setPlayerFilter(e.target.value)}
          />
        </div>
      </section>

      {updatesQuery.isLoading && <Skeleton lines={4} />}
      {updatesQuery.isError && <p className="error">Unable to load updates.</p>}

      {(filteredSnapshots ?? []).map((snap) => (
        <article key={snap.id} className="card">
          <div className="card-header">
            <div>
              <p className="pill">{snap.source_file ?? "import"}</p>
              <h3>{new Date(snap.created_at).toLocaleString()}</h3>
              <p className="muted">
                Div {snap.counts.divisions} · Teams {snap.counts.teams} · Players {snap.counts.players} · Matches{" "}
                {snap.counts.matches}
              </p>
            </div>
          </div>

          <div className="stack">
            <DiffGroup title="Standings" items={snap.diffs.standings_changed} empty="No rank changes" />
            <DiffGroup title="Team points" items={snap.diffs.team_points_changed} empty="No point changes" />
            <DiffGroup title="Teams moved" items={snap.diffs.teams_moved} empty="No division moves" />
            <DiffGroup title="Player SL changes" items={snap.diffs.players_sl_changed} empty="No SL changes" />
            <DiffGroup title="Win% swings" items={snap.diffs.win_pct_swings} empty="No win% swings" />
          </div>
        </article>
      ))}

      {!updatesQuery.isLoading && !updatesQuery.isError && (filteredSnapshots?.length ?? 0) === 0 && (
        <p className="muted">No snapshots yet.</p>
      )}
      </div>
    </div>
  );
}

function DiffGroup({ title, items, empty }: { title: string; items: any[]; empty: string }) {
  return (
    <div className="diff-group">
      <p className="pill soft">{title}</p>
      {(!items || items.length === 0) && <p className="muted">{empty}</p>}
      {items?.length ? (
        <ul className="list">
          {items.map((item, idx) => (
            <li key={idx}>{renderDiff(item)}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function renderDiff(item: any): string {
  if ("team_id" in item && "from" in item && "to" in item && "division_id" in item) {
    return `Team ${item.team_id} in division ${item.division_id}: ${item.from} -> ${item.to}`;
  }
  if ("team_id" in item && "from" in item && "to" in item) {
    return `Team ${item.team_id}: ${item.from} -> ${item.to}`;
  }
  if ("player_id" in item) {
    return `Player ${item.player_id}: ${item.from ?? "?"} -> ${item.to ?? "?"}`;
  }
  return JSON.stringify(item);
}
