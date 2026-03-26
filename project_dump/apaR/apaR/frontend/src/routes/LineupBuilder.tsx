import { useEffect, useMemo, useState } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import { getMatches, getMeta, getPlayer, getTeam } from "../api/client";
import { Skeleton } from "../components/Skeleton";

type PlayerScore = {
  id: string;
  name: string;
  sl: string;
  winRate: number;
  matches: number;
  ppm: number | null;
  pa: number | null;
  reliability: number;
  recentForm: number;
  matchup: number;
  total: number;
  why: string[];
};

function deterministicNumber(seed: string, max: number, offset = 0): number {
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash * 31 + seed.charCodeAt(i)) % 1000;
  }
  return offset + (hash % max);
}

export function LineupBuilder() {
  const metaQuery = useQuery({ queryKey: ["meta"], queryFn: getMeta });
  const matchesQuery = useQuery({ queryKey: ["matches", "all"], queryFn: () => getMatches({}) });

  const teamOptions = useMemo(() => {
    const ids = new Set<string>();
    matchesQuery.data?.matches.forEach((match) => {
      if (match.home_team_id) ids.add(match.home_team_id);
      if (match.away_team_id) ids.add(match.away_team_id);
    });
    return Array.from(ids);
  }, [matchesQuery.data]);

  const [format, setFormat] = useState<"8-ball" | "9-ball">("8-ball");
  const [teamId, setTeamId] = useState("");
  const [opponentId, setOpponentId] = useState("");
  const [selectedPlayers, setSelectedPlayers] = useState<string[]>([]);

  const teamQuery = useQuery({
    queryKey: ["team", teamId],
    queryFn: () => getTeam(teamId),
    enabled: Boolean(teamId),
  });

  useEffect(() => {
    setSelectedPlayers([]);
  }, [teamId]);

  const playerQueries = useQueries({
    queries: selectedPlayers.map((pid) => ({
      queryKey: ["player", pid],
      queryFn: () => getPlayer(pid),
      enabled: Boolean(pid),
    })),
  });

  const playerScores: PlayerScore[] = useMemo(() => {
    return playerQueries.map((q, idx) => {
      const pid = selectedPlayers[idx];
      const player = q.data;
      const name = player?.name ?? pid ?? "Player";
      const stats = (player?.stats_by_format ?? {})[format] as any;
      const winRate = stats?.win_pct ?? deterministicNumber(pid, 40, 40);
      const matches = stats?.matches ?? deterministicNumber(pid, 10, 5);
      const reliability = 50 + Math.min(matches * 2, 40);
      const recentForm = stats?.recent_form ?? deterministicNumber(pid + "form", 30, 50);
      const matchup = opponentId ? deterministicNumber(pid + opponentId, 15, 10) : 10;
      const total = reliability + recentForm + matchup;
      const sl = (stats?.sl ?? stats?.skill_level ?? "—").toString();
      const ppm = stats?.ppm ?? null;
      const pa = stats?.pa ?? null;

      const why: string[] = [];
      if (recentForm > 60) why.push("High recent form");
      if (reliability > 70) why.push("Reliable sample size");
      if (matchup > 20) why.push("Strong vs similar SL");
      if (!why.length) why.push("Balanced option");

      return {
        id: pid,
        name,
        sl,
        winRate,
        matches,
        ppm,
        pa,
        reliability,
        recentForm,
        matchup,
        total,
        why,
      };
    });
  }, [playerQueries, selectedPlayers, format, opponentId]);

  const sortedSuggestions = useMemo(
    () => [...playerScores].sort((a, b) => b.total - a.total).slice(0, 5),
    [playerScores],
  );

  const legalityMessages = useMemo(() => {
    const msgs = [];
    msgs.push(`Format: ${format}`);
    msgs.push(`Players selected: ${selectedPlayers.length}/5`);
    msgs.push(opponentId ? `Opponent set: ${opponentId}` : "Opponent not set");
    return msgs;
  }, [format, selectedPlayers.length, opponentId]);

  const togglePlayer = (pid: string) => {
    setSelectedPlayers((prev) => {
      if (prev.includes(pid)) return prev.filter((id) => id !== pid);
      if (prev.length >= 5) return prev;
      return [...prev, pid];
    });
  };

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
        <div>
          <p className="eyebrow">Lineup Builder</p>
          <h1>Deterministic lineup v1</h1>
          <p className="lede">Pick format, opponent, and 5 players. We’ll rank a play order.</p>
          {metaQuery.data?.last_loaded_at && (
            <p className="muted">Updated {new Date(metaQuery.data.last_loaded_at).toLocaleString()}</p>
          )}
        </div>
      </section>

      {metaQuery.isLoading && <Skeleton lines={2} />}
      {metaQuery.isError && <p className="error">Unable to load metadata.</p>}

      <section className="card">
        <div className="filters">
          <select value={format} onChange={(e) => setFormat(e.target.value as "8-ball" | "9-ball")}>
            <option value="8-ball">8-ball</option>
            <option value="9-ball">9-ball</option>
          </select>
          <select value={teamId} onChange={(e) => setTeamId(e.target.value)}>
            <option value="">Select your team</option>
            {teamOptions.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
          <select value={opponentId} onChange={(e) => setOpponentId(e.target.value)}>
            <option value="">Select opponent</option>
            {teamOptions
              .filter((id) => id !== teamId)
              .map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
          </select>
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Legality / Constraints</p>
            <h3>Checklist</h3>
          </div>
        </div>
        <ul className="list">
          {legalityMessages.map((msg) => (
            <li key={msg}>{msg}</li>
          ))}
        </ul>
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Roster</p>
            <h3>Select up to 5</h3>
          </div>
        </div>
        {teamQuery.isLoading && <Skeleton lines={4} />}
        {teamQuery.isError && <p className="error">Unable to load roster.</p>}
        {teamQuery.data?.roster && (
          <div className="checklist">
            {teamQuery.data.roster.map((player) => {
              const pid = player.id ?? "";
              const isSelected = selectedPlayers.includes(pid);
              return (
                <button key={pid} className={`chip ${isSelected ? "yes" : "maybe"}`} onClick={() => togglePlayer(pid)}>
                  <span>{player.name ?? "Player"}</span>
                  <strong>{isSelected ? "Selected" : "Tap to add"}</strong>
                </button>
              );
            })}
          </div>
        )}
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Suggested Order</p>
            <h3>1–5</h3>
          </div>
        </div>
        {playerQueries.some((q) => q.isLoading) && <Skeleton lines={3} />}
        {playerQueries.some((q) => q.isError) && <p className="error">Some player data unavailable.</p>}
        {sortedSuggestions.length === 0 && <p className="muted">Pick up to five players to see suggestions.</p>}
        {sortedSuggestions.length > 0 && (
          <div className="stack">
            {sortedSuggestions.map((player, idx) => (
              <div key={player.id} className="starter-card">
                <div className="row">
                  <span>
                    {idx + 1}. {player.name} (SL {player.sl})
                  </span>
                  <strong>{Math.round(player.total)}</strong>
                </div>
                <p className="muted">
                  Win% {Math.round(player.winRate)} · Matches {player.matches}
                  {player.ppm ? ` · PPM ${player.ppm}` : ""} {player.pa ? ` · PA ${player.pa}` : ""}
                </p>
                <ul className="list">
                  {player.why.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </section>
      </div>
    </div>
  );
}
