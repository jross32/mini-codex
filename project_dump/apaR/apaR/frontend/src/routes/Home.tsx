import { useEffect, useState } from "react";
import { getHealth, type HealthResponse } from "../api/client";

type Status = {
  state: "loading" | "ready" | "error";
  data?: HealthResponse;
  message?: string;
};

export function Home() {
  const [status, setStatus] = useState<Status>({ state: "loading" });

  useEffect(() => {
    let isMounted = true;

    getHealth()
      .then((data) => {
        if (isMounted) {
          setStatus({ state: "ready", data });
        }
      })
      .catch((error) => {
        if (isMounted) {
          setStatus({ state: "error", message: error.message });
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const health = status.data;

  return (
    <div className="page-container">
      <div className="page">
        <section className="hero">
          <p className="eyebrow">apaR starter</p>
          <h1>React + Flask monorepo starter</h1>
          <p className="lede">
            Mobile-first Vite frontend, Flask API, and Postgres migrations ready to
            ship. Extend routes, wire models, and keep the API contract type-safe.
          </p>
        <div className="hero-actions">
          <a className="button primary" href="http://localhost:5000/api/health" target="_blank" rel="noreferrer">
            Check API
          </a>
          <a className="button ghost" href="https://vite.dev" target="_blank" rel="noreferrer">
            Frontend tooling
          </a>
        </div>
      </section>

      <section className="grid">
        <article className="card">
          <div className="pill">Frontend</div>
          <h2>Clean routing</h2>
          <p>React Router drives page structure; add routes in <code>src/App.tsx</code> and drop in screens.</p>
          <ul>
            <li>Vite + TS + ESLint</li>
            <li>Mobile-first styles</li>
            <li>Typed API client</li>
          </ul>
        </article>
        <article className="card">
          <div className="pill">Backend</div>
          <h2>Flask + Postgres</h2>
          <p>Settings pulled from environment, Postgres wired via SQLAlchemy engine, Alembic scaffolded.</p>
          <ul>
            <li>Health endpoint at <code>/api/health</code></li>
            <li>Database URL from <code>.env</code></li>
            <li>Alembic migrations ready</li>
          </ul>
        </article>
        <article className="card status">
          <div className="pill">Live status</div>
          <h2>API health</h2>
          <div className="status-panel">
            {status.state === "loading" && <p>Loading API status...</p>}
            {status.state === "error" && (
              <p className="error">Unable to reach API: {status.message}</p>
            )}
            {status.state === "ready" && health && (
              <ul>
                <li>
                  <span>Environment</span>
                  <strong>{health.environment}</strong>
                </li>
                <li>
                  <span>Database</span>
                  <strong>{health.database ?? "not configured"}</strong>
                </li>
                <li>
                  <span>Timestamp</span>
                  <strong>{new Date(health.timestamp).toLocaleString()}</strong>
                </li>
              </ul>
            )}
          </div>
        </article>
      </section>
      </div>
    </div>
  );
}
