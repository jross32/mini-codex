import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMatch } from "../api/client";
import { Skeleton } from "../components/Skeleton";

type TeamTotals = {
  label: "Home" | "Away";
  id: string | null | undefined;
  subtotal: number;
  bonus: number;
  total: number;
};

export function MatchDetail() {
  const { matchId } = useParams<{ matchId: string }>();

  const matchQuery = useQuery({
    queryKey: ["match", matchId],
    queryFn: () => getMatch(matchId ?? ""),
    enabled: Boolean(matchId),
  });

  const match = matchQuery.data;

  const teamTotals = useMemo<TeamTotals[]>(() => {
    if (!match) return [];
    const homeSubtotal = match.totals.home.points;
    const awaySubtotal = match.totals.away.points;
    const homeScore = match.teams.home.score ?? homeSubtotal;
    const awayScore = match.teams.away.score ?? awaySubtotal;
    const homeBonus = Math.max(homeScore - homeSubtotal, 0);
    const awayBonus = Math.max(awayScore - awaySubtotal, 0);
    return [
      { label: "Home", id: match.teams.home.id, subtotal: homeSubtotal, bonus: homeBonus, total: homeSubtotal + homeBonus },
      { label: "Away", id: match.teams.away.id, subtotal: awaySubtotal, bonus: awayBonus, total: awaySubtotal + awayBonus },
    ];
  }, [match]);

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
        <div>
          <p className="eyebrow">Match</p>
          <h1>Scorecard</h1>
          <p className="lede">{match?.played_at ? new Date(match.played_at).toLocaleString() : "Date TBD"}</p>
        </div>
        <Link to="/matches" className="ghost-button">
          Back to matches
        </Link>
      </section>

      {matchQuery.isLoading && <Skeleton lines={4} />}
      {matchQuery.isError && <p className="error">Unable to load this match.</p>}

      {match && (
        <>
          <section className="card">
            <div className="card-header">
              <div>
                <p className="pill">Totals</p>
                <h3>Team points</h3>
              </div>
            </div>
            <div className="table">
              <div className="table-head totals-head">
                <div>Team</div>
                <div>Subtotal</div>
                <div>Bonus</div>
                <div>Total</div>
              </div>
              <div className="table-body">
                {teamTotals.map((row, idx) => (
                  <div key={row.id ?? `team-${idx}`} className="table-row totals-row">
                    <div>{row.id ?? row.label}</div>
                    <div>{row.subtotal}</div>
                    <div>{row.bonus}</div>
                    <div>{row.total}</div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="card">
            <div className="card-header">
              <div>
                <p className="pill">Sets</p>
                <h3>Racks</h3>
              </div>
            </div>
            {match.sets.length === 0 ? (
              <p className="muted">No sets recorded.</p>
            ) : (
              <div className="table">
                <div className="table-head sets-head">
                  <div>#</div>
                  <div>Home players</div>
                  <div>Away players</div>
                  <div>Score</div>
                  <div>SL</div>
                  <div>Innings</div>
                  <div>Def shots</div>
                  <div>Special</div>
                </div>
                <div className="table-body">
                  {match.sets.map((set) => (
                    <div key={set.index} className="table-row sets-row">
                      <div>{set.index + 1}</div>
                      <div>{(set.home_player_ids ?? []).join(", ") || "—"}</div>
                      <div>{(set.away_player_ids ?? []).join(", ") || "—"}</div>
                      <div>
                        {set.home_score} - {set.away_score}
                      </div>
                      <div>
                        {set.home_sl ?? "—"} / {set.away_sl ?? "—"}
                      </div>
                      <div>{set.innings ?? "—"}</div>
                      <div>{set.defensive_shots ?? "—"}</div>
                      <div>{set.special ?? "—"}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        </>
      )}
      </div>
    </div>
  );
}
