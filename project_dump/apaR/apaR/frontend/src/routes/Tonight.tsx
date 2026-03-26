import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMatches, getMeta, getTeam } from "../api/client";
import { Skeleton } from "../components/Skeleton";

type ChecklistItem = { id: string; name: string; state: "yes" | "maybe" | "no" };

function useNextMatch() {
  const matchesQuery = useQuery({ queryKey: ["matches", "tonight"], queryFn: () => getMatches({}) });
  const match = useMemo(() => {
    const matches = matchesQuery.data?.matches ?? [];
    if (!matches.length) return undefined;
    const now = Date.now();
    const upcoming = matches
      .filter((m) => (m.played_at ? new Date(m.played_at).getTime() : 0) >= now)
      .sort((a, b) => {
        const ad = a.played_at ? new Date(a.played_at).getTime() : 0;
        const bd = b.played_at ? new Date(b.played_at).getTime() : 0;
        return ad - bd;
      });
    return upcoming[0] ?? matches[0];
  }, [matchesQuery.data]);

  return { match, matchesQuery };
}

export function Tonight() {
  const { match, matchesQuery } = useNextMatch();
  const metaQuery = useQuery({ queryKey: ["meta"], queryFn: getMeta });

  const [availability, setAvailability] = useState<Record<string, ChecklistItem>>({});
  const [dues, setDues] = useState<Record<string, ChecklistItem>>({});

  const teamId = match?.home_team_id ?? match?.away_team_id ?? undefined;
  const teamQuery = useQuery({
    queryKey: ["team", teamId],
    queryFn: () => getTeam(teamId ?? ""),
    enabled: Boolean(teamId),
  });

  // Initialize checklists when roster loads
  useEffect(() => {
    if (!teamQuery.data?.roster) return;
    const base: Record<string, ChecklistItem> = {};
    teamQuery.data.roster.forEach((player) => {
      const pid = player.id ?? "";
      base[pid] = availability[pid] ?? { id: pid, name: player.name ?? "Player", state: "maybe" };
    });
    setAvailability((prev) => ({ ...base, ...prev }));
    const duesBase: Record<string, ChecklistItem> = {};
    teamQuery.data.roster.forEach((player) => {
      const pid = player.id ?? "";
      duesBase[pid] = dues[pid] ?? { id: pid, name: player.name ?? "Player", state: "maybe" };
    });
    setDues((prev) => ({ ...duesBase, ...prev }));
  }, [teamQuery.data, availability, dues]);

  const switchState = (current: "yes" | "maybe" | "no"): "yes" | "maybe" | "no" => {
    if (current === "yes") return "no";
    if (current === "no") return "maybe";
    return "yes";
  };

  const suggestedStarters = useMemo(() => {
    const roster = teamQuery.data?.roster ?? [];
    // Heuristic: top 3 by id sort as stand-in for reliability; explain with placeholder reasons.
    return roster.slice(0, 3).map((player, idx) => ({
      id: player.id ?? `p-${idx}`,
      name: player.name ?? "Player",
      reliability: 80 - idx * 10,
      winRate: 50 + idx * 5,
      form: idx === 0 ? "Hot" : "Steady",
      why: idx === 0 ? "Recent wins & consistent attendance" : "Balanced performance and availability",
    }));
  }, [teamQuery.data]);

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
        <div>
          <p className="eyebrow">Tonight</p>
          <h1>Match planning hub</h1>
          <p className="lede">Everything you need for the next matchup, one-handed friendly.</p>
          {metaQuery.data?.last_loaded_at && (
            <p className="muted">Updated {new Date(metaQuery.data.last_loaded_at).toLocaleString()}</p>
          )}
        </div>
        <Link to="/lineup" className="button primary small">
          Build lineup
        </Link>
      </section>

      {/* Match header */}
      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Match</p>
            <h3>{match ? `${match.home_team_id ?? "Home"} vs ${match.away_team_id ?? "Away"}` : "No match"}</h3>
          </div>
          <div className="badge">{match?.played_at ? new Date(match.played_at).toLocaleDateString() : "TBD"}</div>
        </div>
        {matchesQuery.isLoading && <Skeleton lines={3} />}
        {matchesQuery.isError && <p className="error">Unable to load matches.</p>}
        {match && (
          <div className="stack">
            <div className="row">
              <span>Opponent</span>
              <strong>{match.away_team_id ?? match.home_team_id ?? "TBD"}</strong>
            </div>
            <div className="row">
              <span>Location</span>
              <strong>{match.location_id ?? "TBD"}</strong>
            </div>
            <div className="row">
              <span>Date/Time</span>
              <strong>{match.played_at ? new Date(match.played_at).toLocaleString() : "TBD"}</strong>
            </div>
            <div className="row">
              <span>Home/Away</span>
              <strong>{match.home_team_id ? "Home" : "Away"}</strong>
            </div>
          </div>
        )}
      </section>

      {/* Availability checklist */}
      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Availability</p>
            <h3>Who can play</h3>
          </div>
        </div>
        {teamQuery.isLoading && <Skeleton lines={4} />}
        {teamQuery.isError && <p className="error">Unable to load roster.</p>}
        {!teamQuery.isLoading && !teamQuery.isError && (teamQuery.data?.roster?.length ?? 0) === 0 && (
          <p className="muted">No roster found.</p>
        )}
        {teamQuery.data?.roster && (
          <div className="checklist">
            {teamQuery.data.roster.map((player) => {
              const item = availability[player.id ?? ""] ?? { id: player.id ?? "", name: player.name ?? "Player", state: "maybe" };
              return (
                <button
                  key={player.id ?? player.name}
                  className={`chip ${item.state}`}
                  onClick={() =>
                    setAvailability((prev) => ({
                      ...prev,
                      [item.id]: { ...item, state: switchState(item.state) },
                    }))
                  }
                >
                  <span>{item.name}</span>
                  <strong>{item.state}</strong>
                </button>
              );
            })}
          </div>
        )}
      </section>

      {/* Dues checklist */}
      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Dues</p>
            <h3>Money status</h3>
          </div>
        </div>
        {teamQuery.isLoading && <Skeleton lines={4} />}
        {teamQuery.isError && <p className="error">Unable to load roster.</p>}
        {teamQuery.data?.roster && (
          <div className="checklist">
            {teamQuery.data.roster.map((player) => {
              const item = dues[player.id ?? ""] ?? { id: player.id ?? "", name: player.name ?? "Player", state: "maybe" };
              return (
                <button
                  key={player.id ?? player.name}
                  className={`chip ${item.state}`}
                  onClick={() =>
                    setDues((prev) => ({
                      ...prev,
                      [item.id]: { ...item, state: switchState(item.state) },
                    }))
                  }
                >
                  <span>{item.name}</span>
                  <strong>{item.state}</strong>
                </button>
              );
            })}
          </div>
        )}
      </section>

      {/* Suggested Starters */}
      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Suggested Starters</p>
            <h3>Who to lead with</h3>
          </div>
        </div>
        {teamQuery.isLoading && <Skeleton lines={3} />}
        {teamQuery.isError && <p className="error">Unable to load roster.</p>}
        {!teamQuery.isLoading && !teamQuery.isError && suggestedStarters.length === 0 && (
          <p className="muted">No suggestions yet.</p>
        )}
        {suggestedStarters.length > 0 && (
          <div className="stack">
            {suggestedStarters.map((starter) => (
              <div key={starter.id} className="starter-card">
                <div className="row">
                  <span>{starter.name}</span>
                  <strong>{starter.form}</strong>
                </div>
                <p className="muted">Reliability {starter.reliability} · Win% {starter.winRate}</p>
                <p className="muted">Why: {starter.why}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Notes */}
      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Notes</p>
            <h3>Match & opponent</h3>
          </div>
        </div>
        <textarea className="textarea" rows={3} placeholder="Match notes..." />
        <textarea className="textarea" rows={3} placeholder="Opponent notes..." />
      </section>
      </div>
    </div>
  );
}
