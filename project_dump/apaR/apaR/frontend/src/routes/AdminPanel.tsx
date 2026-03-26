import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getAdminStatus, getMeta, importFile, runAdminStep } from "../api/client";
import { Skeleton } from "../components/Skeleton";

const pipelineSteps = [
  { key: "url_discovery", label: "Run URL Discovery" },
  { key: "apa_sniffer", label: "Run APA Sniffer" },
  { key: "translate", label: "Translate/Structure Data" },
  { key: "full_pipeline", label: "Run Full Pipeline" },
];

export function AdminPanel() {
  const [enabled, setEnabled] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<string | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    setEnabled(window.localStorage.getItem("ADMIN_ENABLED") === "true");
  }, []);

  const metaQuery = useQuery({ queryKey: ["meta"], queryFn: getMeta, enabled });
  const adminStatusQuery = useQuery({ queryKey: ["admin-status"], queryFn: getAdminStatus, enabled });

  const importMutation = useMutation({
    mutationFn: importFile,
    onSuccess: (res) => {
      setImportResult(`Imported ${res.source ?? "latest"} at ${res.last_loaded_at ?? ""}`);
      queryClient.invalidateQueries({ queryKey: ["meta"] });
    },
    onError: () => setImportResult("Import failed"),
  });

  const runMutation = useMutation({
    mutationFn: (step: string) => runAdminStep(step),
    onSuccess: (_, step) => {
      queryClient.invalidateQueries({ queryKey: ["admin-status"] });
      setImportResult((prev) => prev ?? `Triggered ${step}`);
    },
  });

  const workerState = adminStatusQuery.data?.worker?.state ?? "unknown";
  const pipeline = adminStatusQuery.data?.pipeline ?? {};
  const lastRuns = adminStatusQuery.data?.last_runs ?? [];

  const headerStatus = useMemo(() => {
    return {
      api: metaQuery.isError ? "offline" : "online",
      data: metaQuery.data?.last_loaded_at ?? "unknown",
      worker: workerState,
    };
  }, [metaQuery, workerState]);

  if (!enabled) {
    return (
      <div className="page-container">
        <div className="page">
          <section className="hero">
            <p className="eyebrow">404</p>
            <h1>Not found</h1>
            <p className="lede">This page is gated for admins. Enable via localStorage.ADMIN_ENABLED.</p>
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page">
        <section className="page-header">
          <div>
            <p className="eyebrow">Admin</p>
            <h1>Admin Control Center</h1>
            <p className="lede">Internal imports, pipelines, and activity.</p>
          </div>
          <div className="status-chips">
          <span className={`pill ${headerStatus.api === "online" ? "yes" : "no"}`}>API {headerStatus.api}</span>
          <span className="pill soft">Data {headerStatus.data}</span>
          <span className="pill soft">Worker {headerStatus.worker}</span>
          </div>
        </section>

      <div className="grid admin-grid">
        <section className="card">
          <div className="card-header">
            <div>
              <p className="pill">Data Imports</p>
              <h3>Upload & import</h3>
            </div>
          </div>
          <div className="stack">
            <input
              type="file"
              accept=".json"
              onChange={(e) => {
                const file = e.target.files?.[0];
                setUploadFile(file ?? null);
              }}
            />
            <button
              className="button primary"
              disabled={!uploadFile || importMutation.isPending}
              onClick={() => uploadFile && importMutation.mutate(uploadFile)}
            >
              {importMutation.isPending ? "Importing..." : "Import Now"}
            </button>
            {importResult && <p className="muted">{importResult}</p>}
            {importMutation.isError && <p className="error">Import failed</p>}
          </div>
        </section>

        <section className="card">
          <div className="card-header">
            <div>
              <p className="pill">Pipeline Runner</p>
              <h3>Steps</h3>
            </div>
          </div>
          {adminStatusQuery.isLoading && <Skeleton lines={3} />}
          {adminStatusQuery.isError && <p className="error">Unable to load admin status.</p>}
          <div className="stack">
            {pipelineSteps.map((step) => {
              const state = pipeline[step.key]?.state ?? "idle";
              const lastRun = pipeline[step.key]?.last_run;
              return (
                <div key={step.key} className="runner-row">
                  <div>
                    <p className="muted">{step.label}</p>
                    <strong>{state}</strong>
                    <p className="muted">{lastRun ? new Date(lastRun).toLocaleString() : "Never"}</p>
                  </div>
                  <button className="button small primary" onClick={() => runMutation.mutate(step.key)}>
                    Run
                  </button>
                </div>
              );
            })}
          </div>
        </section>

        <section className="card">
          <div className="card-header">
            <div>
              <p className="pill">Activity + Runs</p>
              <h3>History</h3>
            </div>
          </div>
          {adminStatusQuery.isLoading && <Skeleton lines={4} />}
          {adminStatusQuery.isError && <p className="error">Unable to load runs.</p>}
          <div className="stack">
            {lastRuns.length === 0 && !adminStatusQuery.isLoading ? <p className="muted">No runs yet.</p> : null}
            {lastRuns.map((run, idx) => (
              <details key={idx} className="starter-card">
                <summary>
                  <div className="row">
                    <span>{run.step}</span>
                    <strong>{run.status}</strong>
                  </div>
                  <p className="muted">{new Date(run.timestamp).toLocaleString()}</p>
                </summary>
                <div className="stack">
                  <p className="muted">Duration: {run.duration_sec ?? "n/a"}s</p>
                  <p className="muted">{run.logs ?? "No logs"}</p>
                </div>
              </details>
            ))}
          </div>
        </section>
      </div>
      </div>
    </div>
  );
}
