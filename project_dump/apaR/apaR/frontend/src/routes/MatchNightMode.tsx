import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMatch, getTeam } from "../api/client";
import { Skeleton } from "../components/Skeleton";
import { EmptyState } from "../components/EmptyState";

type Note = { id: string; text: string };
type Recap = { worked: string; didnt: string; adjustments: string };

export function MatchNightMode() {
  const { matchId } = useParams<{ matchId: string }>();
  const matchQuery = useQuery({
    queryKey: ["match", "mode", matchId],
    queryFn: () => getMatch(matchId ?? ""),
    enabled: Boolean(matchId),
  });
  const homeTeamId = matchQuery.data?.teams.home.id ?? null;
  const awayTeamId = matchQuery.data?.teams.away.id ?? null;
  const homeTeam = useQuery({ queryKey: ["team", homeTeamId], queryFn: () => getTeam(homeTeamId ?? ""), enabled: Boolean(homeTeamId) });
  const awayTeam = useQuery({ queryKey: ["team", awayTeamId], queryFn: () => getTeam(awayTeamId ?? ""), enabled: Boolean(awayTeamId) });

  const [watched, setWatched] = useState<Record<number, boolean>>({});
  const [notes, setNotes] = useState<Record<number, Note[]>>({});
  const [setNotesText, setSetNotesText] = useState<Record<number, string>>({});
  const [playerNotes, setPlayerNotes] = useState<Record<string, string>>({});
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});
  const [recapOpen, setRecapOpen] = useState(false);
  const [recap, setRecap] = useState<Recap>({
    worked: "",
    didnt: "",
    adjustments: "",
  });

  useEffect(() => {
    if (!matchId) return;
    const raw = window.localStorage.getItem(`match_notes_${matchId}`);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw);
      setNotes(parsed.notes ?? {});
      setWatched(parsed.watched ?? {});
      setSetNotesText(parsed.setNotesText ?? {});
      setPlayerNotes(parsed.playerNotes ?? {});
      const storedRecap = parsed.recap ?? {};
      setRecap({
        worked: storedRecap.worked ?? "",
        didnt: storedRecap.didnt ?? "",
        adjustments: storedRecap.adjustments ?? storedRecap.next ?? "",
      });
    } catch {
      // ignore corrupted payloads
    }
  }, [matchId]);

  useEffect(() => {
    if (!matchId) return;
    const data = {
      notes,
      watched,
      setNotesText,
      playerNotes,
      recap,
    };
    window.localStorage.setItem(`match_notes_${matchId}`, JSON.stringify(data));
  }, [matchId, notes, watched, setNotesText, playerNotes, recap]);

  const match = matchQuery.data;
  const sets = match?.sets ?? [];

  const playerLookup = useMemo(() => {
    const lookup = new Map<string, string>();
    (homeTeam.data?.roster ?? []).forEach((p) => {
      if (p.id) lookup.set(String(p.id), p.name ?? String(p.id));
    });
    (awayTeam.data?.roster ?? []).forEach((p) => {
      if (p.id) lookup.set(String(p.id), p.name ?? String(p.id));
    });
    return lookup;
  }, [homeTeam.data, awayTeam.data]);

  const rosterIds = useMemo(() => {
    const roster = new Set<string>();
    (homeTeam.data?.roster ?? []).forEach((p) => p.id && roster.add(String(p.id)));
    (awayTeam.data?.roster ?? []).forEach((p) => p.id && roster.add(String(p.id)));
    return roster;
  }, [homeTeam.data, awayTeam.data]);

  const seenIds = useMemo(() => {
    const seen = new Set<string>();
    sets.forEach((set) => {
      (set.home_player_ids ?? []).forEach((id: unknown) => seen.add(String(id)));
      (set.away_player_ids ?? []).forEach((id: unknown) => seen.add(String(id)));
    });
    return seen;
  }, [sets]);

  const notPlayed = useMemo(() => {
    return [...rosterIds]
      .filter((id) => !seenIds.has(id))
      .map((id) => playerLookup.get(id) ?? id)
      .sort((a, b) => a.localeCompare(b));
  }, [playerLookup, rosterIds, seenIds]);

  const rosterReady = rosterIds.size > 0;

  const runningScore = useMemo(() => {
    if (!match) return { home: 0, away: 0 };
    return {
      home: match.totals.home.points,
      away: match.totals.away.points,
    };
  }, [match]);

  const homeName = homeTeam.data?.name ?? match?.teams.home.id ?? "Home";
  const awayName = awayTeam.data?.name ?? match?.teams.away.id ?? "Away";

  const formatPlayers = (ids?: unknown[]) => {
    const names = (ids ?? []).map((id) => playerLookup.get(String(id)) ?? String(id));
    if (names.length === 0) return "Players TBD";
    return names.join(" / ");
  };

  const toggleWatched = (idx: number) => {
    setWatched((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const addNote = (idx: number, text: string) => {
    if (!text.trim()) return;
    setNotes((prev) => ({
      ...prev,
      [idx]: [...(prev[idx] ?? []), { id: `${idx}-${Date.now()}`, text }],
    }));
  };

  return (
    <div className="page-container">
      <div className="page match-mode">
        <div className="sticky-score">
        <div className="score-meta">
          <p className="eyebrow">Running score</p>
          <div className="scoreline">
            <div className="score-team">
              <span className="team-label">{homeName}</span>
              <span className="score-value">{runningScore.home}</span>
            </div>
            <span className="score-divider">-</span>
            <div className="score-team">
              <span className="team-label">{awayName}</span>
              <span className="score-value">{runningScore.away}</span>
            </div>
          </div>
          <p className="muted">Totals update as sets change. Notes stay on this device.</p>
        </div>
        <div className="score-actions">
          <button className="button primary small" onClick={() => setRecapOpen(true)}>
            Open recap
          </button>
          <Link className="ghost-button" to={matchId ? `/matches/${matchId}` : "/matches"}>
            Full scorecard
          </Link>
        </div>
      </div>

      <section className="card banner">
        <div className="row">
          <div>
            <p className="pill">Not played yet</p>
            <p className="muted">Based on roster vs sets</p>
          </div>
          <span className="pill soft">{rosterReady ? `${notPlayed.length} remaining` : "Roster pending"}</span>
        </div>
        <div className="not-played-list">
          {!rosterReady ? (
            <p className="muted">Roster data is loading.</p>
          ) : notPlayed.length === 0 ? (
            <p className="muted">Everyone has appeared so far.</p>
          ) : (
            notPlayed.map((name) => <span key={name} className="chip subtle">{name}</span>)
          )}
        </div>
      </section>

      {matchQuery.isLoading && <Skeleton lines={4} />}
      {matchQuery.isError && <p className="error">Unable to load match.</p>}

      {match && sets.length === 0 && <EmptyState title="No sets yet" message="Add sets to track score and notes." />}

      {sets.map((set, idx) => {
        const isExpanded = expanded[idx] ?? idx === 0;
        return (
          <details
            key={set.index}
            className="set-card"
            open={isExpanded}
            onToggle={(event) => {
              const el = event.currentTarget as HTMLDetailsElement;
              setExpanded((prev) => ({ ...prev, [idx]: el.open }));
            }}
          >
            <summary>
              <div className="set-header">
                <div className="set-labels">
                  <p className="pill soft">Set {idx + 1}</p>
                  <div className="set-players">
                    <span className="muted">Home</span>
                    <strong>{formatPlayers(set.home_player_ids)}</strong>
                    <span className="muted">Away</span>
                    <strong>{formatPlayers(set.away_player_ids)}</strong>
                  </div>
                </div>
                <div className="set-score">
                  <span>{set.home_score}</span>
                  <small>to</small>
                  <span>{set.away_score}</span>
                </div>
              </div>
            </summary>

            <div className="set-body">
              <div className="set-meta-grid">
                <div className="meta-chip">
                  <span className="muted">Skill level</span>
                  <strong>
                    {set.home_sl ?? "?"} / {set.away_sl ?? "?"}
                  </strong>
                </div>
                <div className="meta-chip">
                  <span className="muted">Innings</span>
                  <strong>{set.innings ?? "?"}</strong>
                </div>
                <div className="meta-chip">
                  <span className="muted">Def shots</span>
                  <strong>{set.defensive_shots ?? "?"}</strong>
                </div>
                <div className="meta-chip">
                  <span className="muted">Special</span>
                  <strong>{set.special && set.special.trim() ? set.special : "None"}</strong>
                </div>
              </div>

              <div className="set-actions">
                <button className={`chip block ${watched[idx] ? "yes" : "maybe"}`} onClick={() => toggleWatched(idx)}>
                  {watched[idx] ? "Watched" : "Watch next"}
                </button>
                <QuickNote onSubmit={(text) => addNote(idx, text)} />
              </div>

              {notes[idx]?.length ? (
                <ul className="list note-list">
                  {notes[idx].map((note) => (
                    <li key={note.id}>{note.text}</li>
                  ))}
                </ul>
              ) : null}

              <div className="stack">
                <label className="muted">Set note</label>
                <textarea
                  className="textarea"
                  rows={2}
                  value={setNotesText[idx] ?? ""}
                  placeholder="Key shots, pace, who to target"
                  onChange={(e) =>
                    setSetNotesText((prev) => ({
                      ...prev,
                      [idx]: e.target.value,
                    }))
                  }
                />
              </div>
            </div>
          </details>
        );
      })}

      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Player notes</p>
            <h3>Quick mentions</h3>
            <p className="muted">Local to this device.</p>
          </div>
        </div>
        <div className="stack player-notes">
          {(homeTeam.data?.roster ?? []).concat(awayTeam.data?.roster ?? []).map((p, idx) => {
            const playerKey = p.id ?? p.name ?? `player-${idx}`;
            return (
              <label key={playerKey} className="player-note-row">
                <span>{p.name ?? p.id ?? "Player"}</span>
                <input
                  type="text"
                  className="input"
                  value={playerNotes[playerKey] ?? ""}
                  onChange={(e) =>
                    setPlayerNotes((prev) => ({
                      ...prev,
                      [playerKey]: e.target.value,
                    }))
                  }
                  placeholder="Match note"
                />
              </label>
            );
          })}
          {(homeTeam.data?.roster ?? []).length + (awayTeam.data?.roster ?? []).length === 0 ? (
            <p className="muted">Roster details not available.</p>
          ) : null}
        </div>
      </section>

      {recapOpen && (
        <div className="modal">
          <div className="modal-content">
            <div className="card-header">
              <div>
                <p className="pill">Captain Recap</p>
                <h3>End of match</h3>
              </div>
              <button className="ghost-button" onClick={() => setRecapOpen(false)}>
                Close
              </button>
            </div>
            <textarea
              className="textarea"
              rows={3}
              placeholder="What worked"
              value={recap.worked}
              onChange={(e) => setRecap((r) => ({ ...r, worked: e.target.value }))}
            />
            <textarea
              className="textarea"
              rows={3}
              placeholder="What did not work"
              value={recap.didnt}
              onChange={(e) => setRecap((r) => ({ ...r, didnt: e.target.value }))}
            />
            <textarea
              className="textarea"
              rows={3}
              placeholder="Adjustments for next week"
              value={recap.adjustments}
              onChange={(e) => setRecap((r) => ({ ...r, adjustments: e.target.value }))}
            />
            <div className="actions-row">
              <button className="button primary small" onClick={() => setRecapOpen(false)}>
                Save recap
              </button>
            </div>
          </div>
        </div>
      )}

      <button className="button primary recap-fab" onClick={() => setRecapOpen(true)}>
        Recap
      </button>
      </div>
    </div>
  );
}

function QuickNote({ onSubmit }: { onSubmit: (text: string) => void }) {
  const [value, setValue] = useState("");
  return (
    <form
      className="quick-note"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(value);
        setValue("");
      }}
    >
      <input type="text" placeholder="Quick note" value={value} onChange={(e) => setValue(e.target.value)} />
      <button type="submit" className="button small primary">
        Add
      </button>
    </form>
  );
}
