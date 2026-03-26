import { useState } from "react";

type DataStatusPillProps = {
  isLoading?: boolean;
  isError?: boolean;
  data?: {
    source?: "mock" | "real" | string | null;
    meta_banner?: string;
    counts?: {
      divisions?: number;
      teams?: number;
      players?: number;
      matches?: number;
      locations?: number;
    };
  };
};

export function DataStatusPill({ isLoading, isError, data }: DataStatusPillProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  if (isLoading) {
    return <div className="pill soft">Loading data...</div>;
  }

  if (isError) {
    return <div className="pill error-pill">Data unavailable</div>;
  }

  if (!data) {
    return null;
  }

  const source = (data.source as string) ?? "unknown";
  const isMock = source === "mock";
  const counts = data.counts || {};

  return (
    <div className="data-status-pill-wrapper">
      <button
        className={`pill ${isMock ? "info-pill" : "success-pill"}`}
        onClick={() => setShowTooltip(!showTooltip)}
        title={data.meta_banner}
      >
        {isMock ? "🔧 Mock data" : "✓ Live data"}
      </button>
      {showTooltip && (
        <div className="data-status-tooltip">
          <div className="tooltip-content">
            <div className="tooltip-header">{data.meta_banner}</div>
            <div className="tooltip-counts">
              <div>Divisions: {counts.divisions ?? 0}</div>
              <div>Teams: {counts.teams ?? 0}</div>
              <div>Players: {counts.players ?? 0}</div>
              <div>Matches: {counts.matches ?? 0}</div>
              <div>Locations: {counts.locations ?? 0}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
