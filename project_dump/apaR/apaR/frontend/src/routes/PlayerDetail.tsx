import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMatches, getMeta, getPlayer } from "../api/client";
import { Skeleton } from "../components/Skeleton";

type StatBlock = Record<string, unknown>;

function StatTable({ stats }: { stats: StatBlock }) {
  const entries = Object.entries(stats);
  if (entries.length === 0) {
    return <p className="muted">No stats available.</p>;
  }
  return (
    <div className="table compact">
      <div className="table-body">
        {entries.map(([key, value]) => (
          <div key={key} className="table-row two-col">
            <div className="muted">{key}</div>
            <div>{String(value)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function PlayerDetail() {
  const { playerId } = useParams<{ playerId: string }>();
  const [activeTab, setActiveTab] = useState<"8-ball" | "9-ball" | "all">("all");

  const playerQuery = useQuery({
    queryKey: ["player", playerId],
    queryFn: () => getPlayer(playerId ?? ""),
    enabled: Boolean(playerId),
  });

  const matchesQuery = useQuery({
    queryKey: ["matches", "player", playerId],
    queryFn: () => getMatches({ player: playerId }),
    enabled: Boolean(playerId),
  });

  const metaQuery = useQuery({ queryKey: ["meta"], queryFn: getMeta });

  const statsByFormat = playerQuery.data?.stats_by_format ?? {};
  const eightBall = statsByFormat["8-ball"] as StatBlock | undefined;
  const nineBall = statsByFormat["9-ball"] as StatBlock | undefined;

  const availableTabs = useMemo<Array<{ label: string; value: "8-ball" | "9-ball" | "all" }>>(() => {
    const tabs: Array<{ label: string; value: "8-ball" | "9-ball" | "all" }> = [{ label: "All", value: "all" }];
    if (eightBall) tabs.push({ label: "8-ball", value: "8-ball" });
    if (nineBall) tabs.push({ label: "9-ball", value: "9-ball" });
    if (!eightBall && !nineBall) {
      return [{ label: "All", value: "all" }];
    }
    return tabs;
  }, [eightBall, nineBall]);

  const matchHistory = matchesQuery.data?.matches ?? [];

  const tabStats = useMemo(() => {
    if (activeTab === "8-ball") return eightBall ?? {};
    if (activeTab === "9-ball") return nineBall ?? {};
    return statsByFormat;
  }, [activeTab, eightBall, nineBall, statsByFormat]);

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
          <div>
            <p className="eyebrow">Player</p>
            <h1>{playerQuery.data?.name ?? "Player details"}</h1>
            <p className="lede">Team {playerQuery.data?.team_id ?? "TBD"} · Division {playerQuery.data?.division_id ?? "TBD"}</p>
            {metaQuery.data?.last_loaded_at && (
              <p className="muted">Last updated: {new Date(metaQuery.data.last_loaded_at).toLocaleString()}</p>
            )}
          </div>
        <Link to="/players" className="ghost-button">
          Back to players
        </Link>
      </section>

      {playerQuery.isLoading && <Skeleton lines={4} />}
      {playerQuery.isError && <p className="error">Unable to load this player.</p>}

      {playerQuery.data && (
        <>
          <section className="card">
            <div className="card-header">
              <div>
                <p className="pill">Profile</p>
                <h3>{playerQuery.data.name ?? "Player"}</h3>
                <p className="muted">Team {playerQuery.data.team_id ?? "TBD"}</p>
              </div>
            </div>
          </section>

          <section className="card">
            <div className="card-header">
              <div>
                <p className="pill">Stats</p>
                <h3>Performance</h3>
              </div>
              <div className="segmented">
                {availableTabs.map((tab) => (
                  <button
                    key={tab.value}
                    className={tab.value === activeTab ? "active" : ""}
                    onClick={() => setActiveTab(tab.value)}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>
            <StatTable stats={tabStats} />
          </section>

          <section className="card">
            <div className="card-header">
              <div>
                <p className="pill">Matches</p>
                <h3>History</h3>
              </div>
            </div>
            {matchesQuery.isLoading && <Skeleton lines={3} />}
            {matchesQuery.isError && <p className="error">Unable to load match history.</p>}
            {matchHistory.length === 0 && matchesQuery.isSuccess && <p className="muted">No matches found.</p>}
            {matchHistory.length > 0 && (
              <div className="table">
                <div className="table-head">
                  <div>Date</div>
                  <div>Division</div>
                  <div>Teams</div>
                  <div>Score</div>
                </div>
                <div className="table-body">
                  {matchHistory.map((match) => (
                    <Link
                      key={match.id ?? `pmatch-${Math.random()}`}
                      to={`/matches/${match.id ?? ""}`}
                      className="table-row link-row"
                    >
                      <div>{match.played_at ? new Date(match.played_at).toLocaleDateString() : "TBD"}</div>
                      <div>{match.division_id ?? "TBD"}</div>
                      <div>
                        {match.home_team_id ?? "Home"} vs {match.away_team_id ?? "Away"}
                      </div>
                      <div>
                        {match.score.home} - {match.score.away}
                      </div>
                    </Link>
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
