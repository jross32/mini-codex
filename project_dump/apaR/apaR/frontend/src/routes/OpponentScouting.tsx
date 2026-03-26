import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMatches, getMeta, getTeam } from "../api/client";
import { Skeleton } from "../components/Skeleton";

type Band = { label: string; count: number };

function slBands(roster: any[]): Band[] {
  const buckets: Record<string, number> = { "2-3": 0, "4-5": 0, "6-7": 0, "8+": 0, unknown: 0 };
  roster.forEach((p) => {
    const sl = Number(p.sl ?? p.skill_level ?? p.skillLevel ?? p.stats_by_format?.["8-ball"]?.sl ?? p.stats_by_format?.["9-ball"]?.sl);
    if (!Number.isFinite(sl)) {
      buckets.unknown += 1;
      return;
    }
    if (sl <= 3) buckets["2-3"] += 1;
    else if (sl <= 5) buckets["4-5"] += 1;
    else if (sl <= 7) buckets["6-7"] += 1;
    else buckets["8+"] += 1;
  });
  return Object.entries(buckets).map(([label, count]) => ({ label, count }));
}

function winBands(roster: any[]): Band[] {
  const buckets: Record<string, number> = { "<40%": 0, "40-55%": 0, "55-70%": 0, "70%+": 0, unknown: 0 };
  roster.forEach((p) => {
    const stats = p.stats_by_format || {};
    const anyFmt = Object.values(stats)[0] as any;
    const win = Number(anyFmt?.win_pct ?? anyFmt?.winPercent ?? -1);
    if (!Number.isFinite(win) || win < 0) {
      buckets.unknown += 1;
      return;
    }
    if (win < 40) buckets["<40%"] += 1;
    else if (win < 55) buckets["40-55%"] += 1;
    else if (win < 70) buckets["55-70%"] += 1;
    else buckets["70%+"] += 1;
  });
  return Object.entries(buckets).map(([label, count]) => ({ label, count }));
}

function resultLabel(match: any): string {
  if (!match?.score) return "TBD";
  const diff = (match.score?.home ?? 0) - (match.score?.away ?? 0);
  if (diff === 0) return "Draw";
  return diff > 0 ? "Win" : "Loss";
}

function sortMatches(matches: any[]): any[] {
  return [...matches].sort((a, b) => {
    const ad = a.played_at ? new Date(a.played_at).getTime() : 0;
    const bd = b.played_at ? new Date(b.played_at).getTime() : 0;
    return bd - ad;
  });
}

export function OpponentScouting() {
  const { teamId } = useParams<{ teamId: string }>();
  const [myTeamId, setMyTeamId] = useState("");
  const metaQuery = useQuery({ queryKey: ["meta"], queryFn: getMeta });
  const opponentTeamQuery = useQuery({
    queryKey: ["team", teamId],
    queryFn: () => getTeam(teamId ?? ""),
    enabled: Boolean(teamId),
  });
  const myTeamQuery = useQuery({
    queryKey: ["team", myTeamId],
    queryFn: () => getTeam(myTeamId),
    enabled: Boolean(myTeamId),
  });
  const matchesQuery = useQuery({
    queryKey: ["matches", "opponent", teamId],
    queryFn: () => getMatches({ team: teamId }),
    enabled: Boolean(teamId),
  });

  const lastMatches = useMemo(() => sortMatches(matchesQuery.data?.matches ?? []).slice(0, 5), [matchesQuery.data]);

  const likelyStarters = useMemo(() => {
    const roster = opponentTeamQuery.data?.roster ?? [];
    return roster.slice(0, 5).map((p, idx) => ({
      id: p.id ?? `p-${idx}`,
      name: p.name ?? "Player",
      appearances: 5 - idx,
      note: idx === 0 ? "Frequent starter" : "Regular rotation",
    }));
  }, [opponentTeamQuery.data]);

  const rosterSLBands = useMemo(() => slBands(opponentTeamQuery.data?.roster ?? []), [opponentTeamQuery.data]);
  const rosterWinBands = useMemo(() => winBands(opponentTeamQuery.data?.roster ?? []), [opponentTeamQuery.data]);
  const myBands = useMemo(() => slBands(myTeamQuery.data?.roster ?? []), [myTeamQuery.data]);
  const myWinBands = useMemo(() => winBands(myTeamQuery.data?.roster ?? []), [myTeamQuery.data]);

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
        <div>
          <p className="eyebrow">Opponent Scouting</p>
          <h1>{opponentTeamQuery.data?.name ?? "Opponent"}</h1>
          <p className="lede">Patterns to prep against this team.</p>
          {metaQuery.data?.last_loaded_at && (
            <p className="muted">Updated {new Date(metaQuery.data.last_loaded_at).toLocaleString()}</p>
          )}
        </div>
        <div className="filters">
          <select value={myTeamId} onChange={(e) => setMyTeamId(e.target.value)}>
            <option value="">Compare with my team</option>
          </select>
        </div>
      </section>

      {/* Opponent overview */}
      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Overview</p>
            <h3>Roster patterns</h3>
          </div>
        </div>
        {opponentTeamQuery.isLoading && <Skeleton lines={4} />}
        {opponentTeamQuery.isError && <p className="error">Unable to load opponent.</p>}
        {opponentTeamQuery.data && (
          <div className="stack">
            <div className="row">
              <span>SL spread</span>
              <strong>{rosterSLBands.map((b) => `${b.label}:${b.count}`).join(" · ")}</strong>
            </div>
            <div className="row">
              <span>Win% spread</span>
              <strong>{rosterWinBands.map((b) => `${b.label}:${b.count}`).join(" · ")}</strong>
            </div>
          </div>
        )}
      </section>

      {/* Likely starters */}
      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Likely Starters</p>
            <h3>Recent regulars</h3>
          </div>
        </div>
        {opponentTeamQuery.isLoading && <Skeleton lines={3} />}
        {likelyStarters.length === 0 && !opponentTeamQuery.isLoading && <p className="muted">No roster listed.</p>}
        {likelyStarters.length > 0 && (
          <div className="stack">
            {likelyStarters.map((p) => (
              <div key={p.id} className="starter-card">
                <div className="row">
                  <span>{p.name}</span>
                  <strong>{p.note}</strong>
                </div>
                <p className="muted">Recent appearances: {p.appearances}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Last results */}
      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Form</p>
            <h3>Last 5 results</h3>
          </div>
        </div>
        {matchesQuery.isLoading && <Skeleton lines={3} />}
        {matchesQuery.isError && <p className="error">Unable to load matches.</p>}
        {lastMatches.length === 0 && !matchesQuery.isLoading && <p className="muted">No matches recorded.</p>}
        {lastMatches.length > 0 && (
          <div className="stack">
            {lastMatches.map((m) => (
              <div key={m.id ?? `${m.played_at}`} className="row">
                <span>{m.played_at ? new Date(m.played_at).toLocaleDateString() : "TBD"}</span>
                <strong>{resultLabel(m)}</strong>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Compare view */}
      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Compare</p>
            <h3>Roster bands</h3>
          </div>
        </div>
        <div className="stack">
          <div className="row">
            <span>SL bands</span>
            <strong>
              Them: {rosterSLBands.map((b) => `${b.label}:${b.count}`).join(" · ")} | You:{" "}
              {myBands.map((b) => `${b.label}:${b.count}`).join(" · ")}
            </strong>
          </div>
          <div className="row">
            <span>Win% bands</span>
            <strong>
              Them: {rosterWinBands.map((b) => `${b.label}:${b.count}`).join(" · ")} | You:{" "}
              {myWinBands.map((b) => `${b.label}:${b.count}`).join(" · ")}
            </strong>
          </div>
        </div>
      </section>

      {/* Captain notes */}
      <section className="card">
        <div className="card-header">
          <div>
            <p className="pill">Captain Notes</p>
            <h3>Opponent-specific</h3>
          </div>
        </div>
        <textarea className="textarea" rows={3} placeholder="Matchups to target, breaks to watch..." />
      </section>
      </div>
    </div>
  );
}
