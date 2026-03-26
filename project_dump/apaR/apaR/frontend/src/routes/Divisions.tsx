import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getDivisions, getMeta } from "../api/client";
import { Skeleton } from "../components/Skeleton";
import { EmptyState } from "../components/EmptyState";

const FORMATS = [
  { label: "All", value: "all" },
  { label: "8-ball", value: "8-ball" },
  { label: "9-ball", value: "9-ball" },
];

export function Divisions() {
  const divisionsQuery = useQuery({ queryKey: ["divisions"], queryFn: getDivisions });
  const metaQuery = useQuery({ queryKey: ["meta"], queryFn: getMeta });

  const [format, setFormat] = useState("all");
  const [night, setNight] = useState("all");

  const nights = useMemo(() => {
    const set = new Set<string>();
    divisionsQuery.data?.divisions.forEach((div) => {
      if (div.night) set.add(div.night);
    });
    return Array.from(set).sort();
  }, [divisionsQuery.data]);

  const filtered = useMemo(() => {
    if (!divisionsQuery.data?.divisions) return [];
    return divisionsQuery.data.divisions.filter((division) => {
      const matchesFormat = format === "all" || division.format?.toLowerCase() === format;
      const matchesNight = night === "all" || division.night === night;
      return matchesFormat && matchesNight;
    });
  }, [divisionsQuery.data, format, night]);

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
        <div>
          <p className="eyebrow">Divisions</p>
          <h1>Sessions, nights, and formats</h1>
          <p className="lede">Filter by format or night and tap through to standings.</p>
          {metaQuery.data?.last_loaded_at && (
            <p className="muted">Last updated: {new Date(metaQuery.data.last_loaded_at).toLocaleString()}</p>
          )}
        </div>
        <div className="filters stacked">
          <div className="segmented">
            {FORMATS.map((option) => (
              <button
                key={option.value}
                className={option.value === format ? "active" : ""}
                onClick={() => setFormat(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>
          <select value={night} onChange={(e) => setNight(e.target.value)}>
            <option value="all">All nights</option>
            {nights.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>
      </section>

      <section className="grid">
        {divisionsQuery.isLoading && (
          <article className="card">
            <Skeleton lines={4} />
          </article>
        )}
        {divisionsQuery.isError && <p className="error">Unable to load divisions</p>}
        {filtered.length === 0 &&
          divisionsQuery.isSuccess && (
            <EmptyState
              title="No divisions match"
              message="Reset filters or refresh your data."
              action={
                <>
                  <button className="button small ghost" onClick={() => { setFormat("all"); setNight("all"); }}>
                    Reset filters
                  </button>
                  <Link to="/settings" className="button small primary">
                    Upload data
                  </Link>
                </>
              }
            />
          )}

        {filtered.map((division) => (
          <article key={division.id ?? `division-${Math.random()}`} className="card link-card">
            <Link to={`/divisions/${division.id ?? ""}`}>
              <div className="card-header">
                <div>
                  <p className="pill">{division.night ?? "Night TBD"}</p>
                  <h3>{division.name ?? "Untitled division"}</h3>
                  <p className="muted">
                    {division.format ?? "Format TBD"} · {division.session ?? "Session TBD"}
                  </p>
                </div>
                <div className="badge">Teams: {division.team_ids?.length ?? 0}</div>
              </div>
              <div className="stack">
                <div className="row">
                  <span>Format</span>
                  <strong>{division.format ?? "TBD"}</strong>
                </div>
                <div className="row">
                  <span>Session</span>
                  <strong>{division.session ?? "TBD"}</strong>
                </div>
                <div className="row">
                  <span>Night</span>
                  <strong>{division.night ?? "TBD"}</strong>
                </div>
              </div>
            </Link>
          </article>
        ))}
      </section>
      </div>
    </div>
  );
}
