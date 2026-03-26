import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { search } from "../api/client";
import { Skeleton } from "../components/Skeleton";
import { EmptyState } from "../components/EmptyState";
import { VirtualList } from "../components/VirtualList";

export function Players() {
  const [term, setTerm] = useState("");
  const [debounced, setDebounced] = useState("");

  useEffect(() => {
    const id = setTimeout(() => setDebounced(term), 250);
    return () => clearTimeout(id);
  }, [term]);

  const playersQuery = useQuery({
    queryKey: ["search-players", debounced],
    queryFn: () => search(debounced),
    enabled: debounced.length > 1,
  });

  const players = playersQuery.data?.players ?? [];
  const shouldVirtualize = players.length > 30;
  const renderPlayerCard = useCallback(
    (player: (typeof players)[number], idx: number) => (
      <article key={player.id ?? `player-${idx}`} className="card link-card inline-card">
        <Link to={`/players/${player.id ?? ""}`}>
          <div>
            <p className="pill">Player</p>
            <h3>{player.name ?? "Unnamed player"}</h3>
            <p className="muted small">Team {player.team_id ?? "TBD"}</p>
          </div>
          <span className="badge">Open</span>
        </Link>
      </article>
    ),
    [players],
  );

  const virtualHeight = useMemo(() => Math.min(520, Math.max(280, players.length * 116)), [players.length]);

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
        <div>
          <p className="eyebrow">Players</p>
          <h1>Find a player</h1>
          <p className="lede">Search across divisions to see roster and basic stats.</p>
        </div>
        <div className="search-inline">
          <input
            type="search"
            placeholder="Search players"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
          />
        </div>
      </section>

      {playersQuery.isLoading && <Skeleton lines={4} />}
      {playersQuery.isError && <p className="error">Unable to load players</p>}

      {playersQuery.isSuccess && players.length === 0 && (
        <EmptyState
          title="No players found"
          message="Try another name or refresh your data import."
          action={
            <Link to="/settings" className="button small primary">
              Upload data
            </Link>
          }
        />
      )}

      {players.length === 0 && debounced.length <= 1 && !playersQuery.isLoading && (
        <EmptyState
          title="Start typing"
          message="Search across all teams and divisions."
          action={
            <Link to="/teams" className="button small ghost">
              Choose my team
            </Link>
          }
        />
      )}

      {players.length > 0 &&
        (shouldVirtualize ? (
          <VirtualList
            items={players}
            itemHeight={116}
            height={virtualHeight}
            renderRow={(player, idx) => (
              <div style={{ padding: "0.25rem 0.15rem" }}>{renderPlayerCard(player, idx)}</div>
            )}
          />
        ) : (
          <div className="grid">{players.map(renderPlayerCard)}</div>
        ))}
      </div>
    </div>
  );
}
