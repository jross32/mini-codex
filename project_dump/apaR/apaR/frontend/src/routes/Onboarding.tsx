import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  getOnboardingDivisions,
  getOnboardingTeams,
  onboardingComplete,
  type OnboardingDivision,
  type OnboardingTeam,
} from "../api/client";
import { useAuth } from "../context/AuthContext";

type Step = 1 | 2 | 3;
type Role = "captain" | "player" | "fan";

const ROLE_OPTIONS = [
  { value: "player" as Role, label: "Player", copy: "Access schedules, rosters, and match info." },
  { value: "captain" as Role, label: "Captain", copy: "Manage lineups, notes, and quick actions." },
  { value: "fan" as Role, label: "Fan", copy: "Follow teams and standings." },
];

export function Onboarding() {
  const navigate = useNavigate();
  const { user, context, updateContext, refresh } = useAuth();
  const [step, setStep] = useState<Step>(1);
  const [divisionSearch, setDivisionSearch] = useState("");
  const [formatFilter, setFormatFilter] = useState<"all" | "8-ball" | "9-ball">("all");
  const [teamSearch, setTeamSearch] = useState("");
  const [selectedDivision, setSelectedDivision] = useState<string | null>(context?.division_id ?? null);
  const [selectedTeam, setSelectedTeam] = useState<string | null>(context?.team_id ?? null);
  const [selectedRole, setSelectedRole] = useState<Role>(context?.role ?? "player");
  const [serverError, setServerError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [didInitStep, setDidInitStep] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (user?.onboarding_completed) {
      navigate("/captain/dashboard", { replace: true });
    }
  }, [user?.onboarding_completed, navigate]);

  useEffect(() => {
    setSelectedDivision(context?.division_id ?? null);
    setSelectedTeam(context?.team_id ?? null);
    setSelectedRole((context?.role as Role) ?? "player");
  }, [context?.division_id, context?.team_id, context?.role]);

  const desiredStep: Step = useMemo(() => {
    if (!selectedDivision) return 1;
    if (!selectedTeam) return 2;
    return 3;
  }, [selectedDivision, selectedTeam]);

  useEffect(() => {
    if (!didInitStep) {
      setStep(desiredStep);
      setDidInitStep(true);
      return;
    }
    if (step > desiredStep) {
      setStep(desiredStep);
    }
  }, [desiredStep, didInitStep, step]);

  const divisionsQuery = useQuery({
    queryKey: ["onboarding", "divisions"],
    queryFn: getOnboardingDivisions,
    staleTime: 60_000,
  });

  const teamsQuery = useQuery({
    queryKey: ["onboarding", "teams", selectedDivision],
    queryFn: () => getOnboardingTeams({ division_id: selectedDivision }),
    enabled: Boolean(selectedDivision),
    staleTime: 30_000,
  });

  const completeMutation = useMutation({
    mutationFn: onboardingComplete,
    onSuccess: async () => {
      setServerError(null);
      setSuccessMessage("All set! 🎉 Taking you to your dashboard...");
      await refresh();
      setTimeout(() => {
        navigate("/captain/dashboard", { replace: true });
      }, 1000);
    },
    onError: (err: Error & { code?: string }) => {
      setServerError(err.message || "Unable to finish onboarding right now.");
    },
  });

  const filteredDivisions = useMemo(() => {
    const all = divisionsQuery.data?.divisions ?? [];
    return all.filter((div: OnboardingDivision) => {
      const matchesTerm =
        divisionSearch.trim().length === 0 ||
        (div.name || "").toLowerCase().includes(divisionSearch.trim().toLowerCase());
      const matchesFormat =
        formatFilter === "all" ||
        (div.format || "").toLowerCase().includes(formatFilter === "8-ball" ? "8" : "9") ||
        (div.format || "").toLowerCase().includes(formatFilter);
      return matchesTerm && matchesFormat;
    });
  }, [divisionsQuery.data?.divisions, divisionSearch, formatFilter]);

  const filteredTeams = useMemo(() => {
    const all = teamsQuery.data?.teams ?? [];
    if (teamSearch.trim().length === 0) return all;
    return all.filter((team: OnboardingTeam) =>
      (team.name || "").toLowerCase().includes(teamSearch.trim().toLowerCase()),
    );
  }, [teamSearch, teamsQuery.data?.teams]);

  const stepCopy = useMemo(() => {
    if (step === 1) return "Choose your division to see the right teams.";
    if (step === 2) return "Select your team to unlock lineup tools.";
    return "Pick your role so we can tune the experience.";
  }, [step]);

  const isNextDisabled = useMemo(() => {
    if (step === 1) return !selectedDivision;
    if (step === 2) return !selectedTeam;
    return completeMutation.isPending;
  }, [step, selectedDivision, selectedTeam, completeMutation.isPending]);

  const goNext = async () => {
    setServerError(null);
    setSaving(true);
    try {
      if (step === 1 && !selectedDivision) {
        setServerError("Choose a division to continue.");
        setSaving(false);
        return;
      }
      if (step === 2 && !selectedTeam) {
        setServerError("Choose a team to continue.");
        setSaving(false);
        return;
      }

      // Save selection to backend before advancing
      if (step === 1) {
        const ok = await persistContext({ division_id: selectedDivision, team_id: null });
        if (!ok) {
          setSaving(false);
          return; // Stay on step if save fails
        }
      } else if (step === 2) {
        const ok = await persistContext({ team_id: selectedTeam });
        if (!ok) {
          setSaving(false);
          return; // Stay on step if save fails
        }
      } else if (step === 3) {
        // Save role and complete onboarding
        await persistContext({ role: selectedRole });
        completeMutation.mutate();
        return;
      }

      // Only advance step after successful save
      setStep((prev) => (prev + 1) as Step);
    } finally {
      setSaving(false);
    }
  };

  const goBack = () => {
    setServerError(null);
    setStep((prev) => (prev > 1 ? ((prev - 1) as Step) : prev));
  };

  const persistContext = useCallback(
    async (payload: Partial<{ division_id: string | null; team_id: string | null; role: Role }>) => {
      setSaving(true);
      setServerError(null);
      try {
        await updateContext(payload);
        return true;
      } catch (err) {
        setServerError((err as Error).message || "Unable to save selection.");
        return false;
      } finally {
        setSaving(false);
      }
    },
    [updateContext],
  );

  const selectDivision = (divisionId: string | null) => {
    setSelectedDivision(divisionId);
    setSelectedTeam(null);
    setServerError(null);
    // Selection updates immediately, no step advance
    // Saving happens when user clicks Next
  };

  const selectTeam = (teamId: string | null) => {
    setSelectedTeam(teamId);
    setServerError(null);
    // Selection updates immediately, no step advance
    // Saving happens when user clicks Next
  };

  const selectRole = (roleValue: Role) => {
    setSelectedRole(roleValue);
    setServerError(null);
    // Selection updates immediately, no step advance
    // Saving happens when user clicks Next
  };
  return (
    <div className="page-container">
      <div className="page onboarding-page">
        {/* Success Screen Overlay */}
        {successMessage && (
          <div className="success-overlay">
            <div className="success-content">
              <div className="success-icon">✓</div>
              <p>{successMessage}</p>
            </div>
          </div>
        )}

        {/* Progress Bar */}
        <div className="progress-container">
          <div className="progress-bar" style={{ width: `${(step / 3) * 100}%` }}></div>
        </div>

        <div className="stepper">
        {[1, 2, 3].map((num) => (
          <div key={num} className={`step-dot ${num === step ? "active" : num < step ? "done" : ""}`}>
            <span>{num}</span>
          </div>
        ))}
        <div className="stepper-text">
          <p className="muted small">Step {step} of 3</p>
          <h1>Onboarding</h1>
          <p className="muted">{stepCopy}</p>
        </div>
        <div className="step-summary">
          <p className="muted small">Selections</p>
          <div className="summary-tags">
            <span className="pill soft">
              Division: {selectedDivision ?? "—"}
            </span>
            <span className="pill soft">
              Team: {selectedTeam ?? "—"}
            </span>
            <span className="pill soft">
              Role: {selectedRole}
            </span>
          </div>
        </div>
      </div>

        <div className="onboarding-grid">
        <div className="onboarding-main">
          <section className="card wizard-card">
            <div className="card-header">
              <div>
                <p className="eyebrow">Step {step}</p>
                <h2>{step === 1 ? "Choose your division" : step === 2 ? "Pick your team" : "Select your role"}</h2>
                <p className="muted small">{stepCopy}</p>
              </div>
            </div>

            {serverError ? <div className="alert error-pill">{serverError}</div> : null}

            {step === 1 && (
              <div className="wizard-section">
                <div className="filters">
                  <input
                    type="search"
                    placeholder="Search divisions"
                    value={divisionSearch}
                    onChange={(e) => setDivisionSearch(e.target.value)}
                  />
                  <div className="filter-pills">
                    {["all", "8-ball", "9-ball"].map((fmt) => (
                      <button
                        key={fmt}
                        className={`chip ${formatFilter === fmt ? "chip-primary" : "chip subtle"}`}
                        onClick={() => setFormatFilter(fmt as "all" | "8-ball" | "9-ball")}
                      >
                        {fmt === "all" ? "All formats" : fmt}
                      </button>
                    ))}
                  </div>
                </div>

                {divisionsQuery.isLoading && <p className="muted">Loading divisions...</p>}
                {divisionsQuery.isError && <p className="error">Unable to load divisions right now.</p>}

                <div className="option-grid cards-grid">
                  {filteredDivisions.map((div) => (
                    <button
                      key={div.id ?? div.name ?? "division"}
                      className={`option-card ${selectedDivision === div.id ? "active" : ""}`}
                      onClick={() => selectDivision(div.id ?? null)}
                    >
                      <div>
                        <p className="pill soft">{div.format ?? "Format TBD"}</p>
                        <h3>{div.name ?? "Unnamed division"}</h3>
                        <p className="muted small">
                          {div.day ?? "Night TBD"} · {div.location_name ?? "Location TBD"}
                        </p>
                      </div>
                      <span className="pill">{selectedDivision === div.id ? "Selected" : "Select"}</span>
                    </button>
                  ))}
                  {filteredDivisions.length === 0 && !divisionsQuery.isLoading && (
                    <div className="empty-state">
                      <div>
                        <h3>No divisions found</h3>
                        <p className="muted small">Try another search or reset filters.</p>
                      </div>
                      <div className="empty-action">
                        <button className="button ghost small" onClick={() => setDivisionSearch("")}>
                          Clear search
                        </button>
                        <Link to="/settings" className="button small primary">
                          Upload data
                        </Link>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="wizard-section">
                <div className="filters">
                  <input
                    type="search"
                    placeholder="Search teams"
                    value={teamSearch}
                    onChange={(e) => setTeamSearch(e.target.value)}
                    disabled={!selectedDivision}
                  />
                  {!selectedDivision && <p className="muted small">Choose a division first.</p>}
                </div>

                {teamsQuery.isLoading && <p className="muted">Loading teams...</p>}
                {teamsQuery.isError && selectedDivision && <p className="error">Unable to load teams.</p>}

                <div className="option-grid cards-grid">
                  {filteredTeams.map((team) => (
                    <button
                      key={team.id ?? team.name ?? "team"}
                      className={`option-card ${selectedTeam === team.id ? "active" : ""}`}
                      onClick={() => selectTeam(team.id ?? null)}
                    >
                      <div>
                        <p className="pill soft">Team</p>
                        <h3>{team.name ?? "Unnamed team"}</h3>
                        <p className="muted small">
                          Home: {team.home_location ?? "TBD"} · Roster: {team.roster_count ?? "?"}
                        </p>
                      </div>
                      <span className="pill">{selectedTeam === team.id ? "Selected" : "Select"}</span>
                    </button>
                  ))}
                  {selectedDivision && filteredTeams.length === 0 && !teamsQuery.isLoading && (
                    <div className="empty-state">
                      <div>
                        <h3>No teams yet</h3>
                        <p className="muted small">Try another division or refresh your data.</p>
                      </div>
                      <div className="empty-action">
                        <button className="button ghost small" onClick={() => setTeamSearch("")}>
                          Clear search
                        </button>
                        <Link to="/settings" className="button small primary">
                          Upload data
                        </Link>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="wizard-section role-grid">
                {ROLE_OPTIONS.map((role) => (
                  <button
                    key={role.value}
                    className={`option-card ${selectedRole === role.value ? "active" : ""}`}
                    onClick={() => selectRole(role.value)}
                  >
                    <div>
                      <p className="pill soft">{role.label}</p>
                      <h3>{role.copy}</h3>
                    </div>
                    <span className="pill">{selectedRole === role.value ? "Selected" : "Choose"}</span>
                  </button>
                ))}
                <div className="inline-text">
                  <p className="muted small">
                    You can change this later in Settings. Finishing will take you to the captain dashboard.
                  </p>
                </div>
              </div>
            )}

            {/* Actions at bottom of card */}
            <div className="card-footer wizard-actions">
              <button className="button ghost small" onClick={goBack} disabled={step === 1}>
                Back
              </button>
              <button
                className="button primary small"
                onClick={goNext}
                disabled={isNextDisabled || saving || completeMutation.isPending}
              >
                {step === 3 ? (completeMutation.isPending ? "Finishing..." : "Finish") : "Next"}
              </button>
            </div>
          </section>
        </div>

        <aside className="card wizard-summary">
          <div className="summary-header">
            <h3>Preview</h3>
            <p className="muted small">Your selections so far.</p>
          </div>
          <div className="summary-list">
            <div className="summary-row">
              <span className="muted">Division</span>
              <strong>{selectedDivision ?? "Not selected"}</strong>
            </div>
            <div className="summary-row">
              <span className="muted">Team</span>
              <strong>{selectedTeam ?? "Not selected"}</strong>
            </div>
            <div className="summary-row">
              <span className="muted">Role</span>
              <strong className="pill soft">{selectedRole}</strong>
            </div>
          </div>
          <div className="stack">
            <p className="muted small">Need to skip for now?</p>
            <Link to="/captain/dashboard" className="button ghost small">
              Skip to dashboard
            </Link>
          </div>
        </aside>
      </div>
      </div>
    </div>
  );
}
