import { z } from "zod";
import { csrfClient, initializeCsrfToken } from "./csrf-client";

// Use proxy path in development (served via Vite proxy), absolute URL in production
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? "/api" : "http://localhost:5000/api");
const ADMIN_API_BASE_URL = `${API_BASE_URL}/admin`;

// Export for use in app initialization
export { initializeCsrfToken, csrfClient };

const healthSchema = z.object({
  status: z.string(),
  timestamp: z.string(),
  environment: z.string(),
  database: z.string().nullable().optional(),
  data: z
    .object({
      status: z.string(),
      last_loaded_at: z.string().nullable().optional(),
      source: z.string().nullable().optional(),
    })
    .optional(),
});

const divisionSchema = z.object({
  id: z.string().nullable(),
  name: z.string().nullable(),
  night: z.string().nullable().optional(),
  format: z.string().nullable().optional(),
  session: z.string().nullable().optional(),
  team_ids: z.array(z.string()).optional().default([]),
  standings: z
    .array(
      z.object({
        rank: z.number().optional(),
        team_id: z.string().nullable().optional(),
        points: z.number().optional(),
        last_week: z.number().optional().or(z.string().nullable()),
      }),
    )
    .optional()
    .default([]),
});

const metaSchema = z.object({
  meta: z.record(z.string(), z.any()),
  league: z.record(z.string(), z.any()),
  counts: z.object({
    divisions: z.number(),
    teams: z.number(),
    players: z.number(),
    matches: z.number(),
    locations: z.number(),
  }),
  last_loaded_at: z.string().nullable(),
  source: z.string().nullable(),
});

const teamSchema = z.object({
  id: z.string().nullable(),
  name: z.string().nullable(),
  division_id: z.string().nullable().optional(),
  location_id: z.string().nullable().optional(),
  roster: z
    .array(
      z.object({
        id: z.string().nullable(),
        name: z.string().nullable(),
        team_id: z.string().nullable().optional(),
        division_id: z.string().nullable().optional(),
      }),
    )
    .optional()
    .default([]),
});

const playerSchema = z.object({
  id: z.string().nullable(),
  name: z.string().nullable(),
  team_id: z.string().nullable().optional(),
  division_id: z.string().nullable().optional(),
  stats_by_format: z.record(z.string(), z.any()).optional().default({}),
});

const matchSchema = z.object({
  id: z.string().nullable(),
  division_id: z.string().nullable().optional(),
  home_team_id: z.string().nullable().optional(),
  away_team_id: z.string().nullable().optional(),
  played_at: z.string().nullable().optional(),
  location_id: z.string().nullable().optional(),
  status: z.string().nullable().optional(),
  score: z.object({ home: z.number(), away: z.number() }),
});

const matchDetailSchema = z.object({
  id: z.string().nullable(),
  division_id: z.string().nullable().optional(),
  played_at: z.string().nullable().optional(),
  location_id: z.string().nullable().optional(),
  teams: z.object({
    home: z.object({ id: z.string().nullable().optional(), score: z.number().optional() }),
    away: z.object({ id: z.string().nullable().optional(), score: z.number().optional() }),
  }),
  sets: z.array(
    z.object({
      index: z.number(),
      home_score: z.number(),
      away_score: z.number(),
      winner_team_id: z.string().nullable().optional(),
      home_player_ids: z.array(z.any()).default([]),
      away_player_ids: z.array(z.any()).default([]),
      home_sl: z.number().optional(),
      away_sl: z.number().optional(),
      innings: z.number().optional(),
      defensive_shots: z.number().optional(),
      special: z.string().nullable().optional(),
    }),
  ),
  totals: z.object({
    home: z.object({ points: z.number(), sets: z.number() }),
    away: z.object({ points: z.number(), sets: z.number() }),
  }),
});

const searchSchema = z.object({
  query: z.string(),
  divisions: z.array(
    z.object({
      id: z.string().nullable(),
      name: z.string().nullable(),
      night: z.string().nullable().optional(),
      format: z.string().nullable().optional(),
      session: z.string().nullable().optional(),
    }),
  ),
  teams: z.array(
    z.object({
      id: z.string().nullable(),
      name: z.string().nullable(),
      division_id: z.string().nullable().optional(),
    }),
  ),
  players: z.array(
    z.object({
      id: z.string().nullable(),
      name: z.string().nullable(),
      team_id: z.string().nullable().optional(),
      division_id: z.string().nullable().optional(),
    }),
  ),
  matches: z
    .array(
      z.object({
        id: z.string().nullable(),
        home_team_id: z.string().nullable().optional(),
        away_team_id: z.string().nullable().optional(),
        played_at: z.string().nullable().optional(),
      }),
    )
    .optional()
    .default([]),
});

const importSchema = z.object({
  status: z.string(),
  last_loaded_at: z.string().nullable().optional(),
  source: z.string().nullable().optional(),
  counts: z.object({
    divisions: z.number(),
    teams: z.number(),
    players: z.number(),
    matches: z.number(),
    locations: z.number(),
  }),
  diffs: z.object({
    teams_moved: z
      .array(
        z.object({
          team_id: z.string(),
          from: z.any().nullable().optional(),
          to: z.any().nullable().optional(),
        }),
      )
      .default([]),
    players_sl_changed: z
      .array(
        z.object({
          player_id: z.string(),
          from: z.any().nullable().optional(),
          to: z.any().nullable().optional(),
        }),
      )
      .default([]),
  }),
});

const updateSnapshotSchema = z.object({
  id: z.number(),
  created_at: z.string(),
  source_file: z.string().nullable(),
  meta: z.record(z.string(), z.any()).optional(),
  counts: z.object({
    divisions: z.number(),
    teams: z.number(),
    players: z.number(),
    matches: z.number(),
    locations: z.number(),
  }),
  diffs: z.object({
    standings_changed: z
      .array(
        z.object({
          division_id: z.any(),
          team_id: z.any(),
          from: z.any().nullable().optional(),
          to: z.any().nullable().optional(),
        }),
      )
      .default([]),
    team_points_changed: z
      .array(
        z.object({
          division_id: z.any(),
          team_id: z.any(),
          from: z.any().nullable().optional(),
          to: z.any().nullable().optional(),
        }),
      )
      .default([]),
    players_sl_changed: z
      .array(
        z.object({
          player_id: z.string(),
          from: z.any().nullable().optional(),
          to: z.any().nullable().optional(),
        }),
      )
      .default([]),
    teams_moved: z
      .array(
        z.object({
          team_id: z.string(),
          from: z.any().nullable().optional(),
          to: z.any().nullable().optional(),
        }),
      )
      .default([]),
    win_pct_swings: z
      .array(
        z.object({
          player_id: z.string(),
          from: z.any().nullable().optional(),
          to: z.any().nullable().optional(),
        }),
      )
      .default([]),
  }),
});

export type HealthResponse = z.infer<typeof healthSchema>;
export type Division = z.infer<typeof divisionSchema>;
export type MetaResponse = z.infer<typeof metaSchema>;
export type Team = z.infer<typeof teamSchema>;
export type Player = z.infer<typeof playerSchema>;
export type MatchSummary = z.infer<typeof matchSchema>;
export type MatchDetail = z.infer<typeof matchDetailSchema>;
export type SearchResponse = z.infer<typeof searchSchema>;
export type ImportResponse = z.infer<typeof importSchema>;
export type UpdateSnapshot = z.infer<typeof updateSnapshotSchema>;
export type AdminStatus = {
  worker: { state: string };
  pipeline: Record<string, { state: string; last_run: string | null }>;
  last_runs: Array<{ timestamp: string; step: string; duration_sec?: number; status: string; logs?: string }>;
};

const userSchema = z.object({
  id: z.string(),
  email: z.string(),
  username: z.string().nullable().optional(),
  is_admin: z.boolean(),
  onboarding_completed: z.boolean(),
  created_at: z.string().nullable().optional(),
  updated_at: z.string().nullable().optional(),
});

const userContextSchema = z.object({
  league_id: z.string().nullable().optional(),
  division_id: z.string().nullable().optional(),
  team_id: z.string().nullable().optional(),
  role: z.enum(["captain", "player", "fan"]).default("captain"),
  created_at: z.string().nullable().optional(),
  updated_at: z.string().nullable().optional(),
});

const onboardingDivisionSchema = z.object({
  id: z.string().nullable().optional(),
  name: z.string().nullable().optional(),
  format: z.string().nullable().optional(),
  day: z.string().nullable().optional(),
  location_name: z.string().nullable().optional(),
});

const onboardingTeamSchema = z.object({
  id: z.string().nullable().optional(),
  name: z.string().nullable().optional(),
  home_location: z.any().nullable().optional(),
  roster_count: z.number().nullable().optional(),
});

const onboardingLeagueSchema = z.object({
  id: z.string().nullable().optional(),
  name: z.string().nullable().optional(),
});

const onboardingSessionSchema = z.object({
  id: z.string().nullable().optional(),
  name: z.string().nullable().optional(),
});

const authResponseSchema = z.object({
  ok: z.boolean(),
  user: userSchema.nullable().optional(),
  context: userContextSchema.nullable().optional(),
  status: z.string().optional(),
  error: z
    .object({
      code: z.string(),
      message: z.string(),
      field: z.string().optional(),
    })
    .optional(),
});

let csrfToken: string | null = null;

const csrfSchema = z.object({ ok: z.boolean().optional(), csrf_token: z.string() });

async function ensureCsrfToken(): Promise<string> {
  if (csrfToken) return csrfToken;
  const response = await fetch(`${API_BASE_URL}/auth/csrf`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  const parsed = csrfSchema.safeParse(await response.json());
  if (!parsed.success) {
    throw new Error("Unable to fetch CSRF token");
  }
  csrfToken = parsed.data.csrf_token;
  return csrfToken;
}

async function request<T>(path: string, schema: z.ZodSchema<T>, init?: RequestInit): Promise<T> {
  const method = (init?.method || "GET").toUpperCase();
  // Use csrfClient for any mutating request (PUT, POST, DELETE, PATCH)
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    return csrfClient.request(path, schema, {
      ...init,
      method,
      requiresCsrf: true,
      retryOnCsrfFailure: true,
    });
  }

  // For read-only requests, use the simpler flow
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers,
    credentials: "include",
    ...init,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const parsed = schema.safeParse(await response.json());
  if (!parsed.success) {
    throw new Error("Response shape did not match expected schema");
  }

  return parsed.data;
}

export function getHealth(): Promise<HealthResponse> {
  return request("/health", healthSchema);
}

export function getMeta(): Promise<MetaResponse> {
  return request("/meta", metaSchema);
}

export function getDivisions(): Promise<{ divisions: Division[] }> {
  return request("/divisions", z.object({ divisions: z.array(divisionSchema) }));
}

export function getDivision(divisionId: string): Promise<Division> {
  return request(`/divisions/${divisionId}`, divisionSchema);
}

export function getTeam(teamId: string): Promise<Team> {
  return request(`/teams/${teamId}`, teamSchema);
}

export function getPlayer(playerId: string): Promise<Player> {
  return request(`/players/${playerId}`, playerSchema);
}

export function getMatches(params?: { division?: string; team?: string; player?: string; from?: string; to?: string }): Promise<{ matches: MatchSummary[] }> {
  const searchParams = new URLSearchParams();
  if (params?.division) searchParams.set("division", params.division);
  if (params?.team) searchParams.set("team", params.team);
  if (params?.player) searchParams.set("player", params.player);
  if (params?.from) searchParams.set("from", params.from);
  if (params?.to) searchParams.set("to", params.to);
  const qs = searchParams.toString();
  const path = qs ? `/matches?${qs}` : "/matches";
  return request(path, z.object({ matches: z.array(matchSchema) }));
}

export function getMatch(matchId: string): Promise<MatchDetail> {
  return request(`/matches/${matchId}`, matchDetailSchema);
}

export function search(term: string): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: term });
  return request(`/search?${params.toString()}`, searchSchema);
}

export function importDataset(): Promise<ImportResponse> {
  return request("/import", importSchema, { method: "POST" });
}

export function getUpdates(): Promise<{ snapshots: UpdateSnapshot[] }> {
  return request("/updates", z.object({ snapshots: z.array(updateSnapshotSchema) }));
}

export async function getAdminStatus(): Promise<AdminStatus> {
  const response = await fetch(`${ADMIN_API_BASE_URL}/status`, { headers: { Accept: "application/json" }, credentials: "include" });
  if (!response.ok) {
    throw new Error("Failed to load admin status");
  }
  return response.json();
}

export async function runAdminStep(step: string): Promise<void> {
  const token = await ensureCsrfToken();
  const response = await fetch(`${ADMIN_API_BASE_URL}/run/${step}`, {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRF-Token": token },
  });
  if (!response.ok) {
    throw new Error("Failed to start step");
  }
}

export type UserContext = z.infer<typeof userContextSchema>;
export async function importFile(file: File): Promise<ImportResponse> {
  const form = new FormData();
  form.append("file", file);
  const token = await ensureCsrfToken();
  const response = await fetch(`${API_BASE_URL}/import`, {
    method: "POST",
    body: form,
    credentials: "include",
    headers: { "X-CSRF-Token": token },
  });
  if (!response.ok) {
    throw new Error("Import failed");
  }
  return importSchema.parse(await response.json());
}

export type User = z.infer<typeof userSchema>;
export type AuthError = { code: string; message: string; field?: string };
export type AuthResponse = { ok: true; user: User | null; context?: UserContext | null } | { ok: false; error: AuthError };
export type AuthSession = { user: User | null; context: UserContext | null };
export type OnboardingDivision = z.infer<typeof onboardingDivisionSchema>;
export type OnboardingTeam = z.infer<typeof onboardingTeamSchema>;
export type OnboardingLeague = z.infer<typeof onboardingLeagueSchema>;
export type OnboardingSession = z.infer<typeof onboardingSessionSchema>;

async function authRequest(path: string, body: object): Promise<AuthResponse> {
  // Use csrfClient to handle CSRF token and fetch with retry logic
  let token: string;
  try {
    token = await csrfClient.getCsrfToken();
  } catch (err) {
    console.error("Failed to get CSRF token:", err);
    throw new Error("Unable to get CSRF token. Check that the server is running.");
  }
  
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRF-Token": token,
      },
      body: JSON.stringify(body),
    });
  } catch (err) {
    console.error("Network error:", err);
    throw new Error(`Network error: ${err instanceof Error ? err.message : "Unknown error"}`);
  }

  let parsedJson: unknown = null;
  let responseText = "";
  try {
    responseText = await response.text();
    parsedJson = responseText ? JSON.parse(responseText) : null;
  } catch (err) {
    console.error("Failed to parse response:", err, "Response text:", responseText);
    throw new Error(`Server returned invalid JSON: ${responseText.substring(0, 100)}`);
  }

  const parsed = authResponseSchema.safeParse(parsedJson);
  if (!parsed.success) {
    // If CSRF token might be stale, clear it
    if (response.status === 403) {
      csrfClient.clearCsrfToken();
    }
    console.error("Schema validation failed:", {
      status: response.statusText,
      code: response.status,
      parsed: parsed.error,
      received: parsedJson,
    });
    throw new Error(`Server error (${response.status}): Invalid response format`);
  }
  const payload = parsed.data;

  // Handle CSRF failure with retry
  if ((response.status === 403 || response.status === 401) && !payload.ok) {
    const errorBody = JSON.stringify(payload.error ?? {});
    if (errorBody.includes("csrf")) {
      // Refresh CSRF token and retry
      csrfClient.clearCsrfToken();
      const newToken = await csrfClient.fetchCsrfToken();

      const retryResponse = await fetch(`${API_BASE_URL}${path}`, {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-CSRF-Token": newToken,
        },
        body: JSON.stringify(body),
      });

      let retryJson: unknown = null;
      try {
        retryJson = await retryResponse.json();
      } catch {
        throw new Error("Failed to parse retry response");
      }

      const retryParsed = authResponseSchema.safeParse(retryJson);
      if (!retryParsed.success) {
        throw new Error("Invalid auth response on retry");
      }
      const retryPayload = retryParsed.data;

      if (!retryPayload.ok) {
        const error: AuthError = retryPayload.error ?? { code: "auth_error", message: "Unable to sign in right now." };
        const authErr = new Error(error.message) as Error & { code?: string; field?: string; payload?: AuthResponse };
        authErr.code = error.code;
        authErr.field = error.field;
        authErr.payload = retryPayload as AuthResponse;
        throw authErr;
      }

      return { ok: true, user: retryPayload.user ?? null, context: retryPayload.context ?? null } as AuthResponse;
    }
  }

  if (!payload.ok) {
    const error: AuthError = payload.error ?? { code: "auth_error", message: "Unable to sign in right now." };
    const authErr = new Error(error.message) as Error & { code?: string; field?: string; payload?: AuthResponse };
    authErr.code = error.code;
    authErr.field = error.field;
    authErr.payload = payload as AuthResponse;
    throw authErr;
  }

  return { ok: true, user: payload.user ?? null, context: payload.context ?? null } as AuthResponse;
}

export function authSignup(input: { email: string; password: string; username?: string | null }): Promise<AuthResponse> {
  return authRequest("/auth/signup", input);
}

export function authLogin(input: { email: string; password: string }): Promise<AuthResponse> {
  return authRequest("/auth/login", input);
}

export function authLogout(): Promise<AuthResponse> {
  return authRequest("/auth/logout", {});
}

export async function authMe(): Promise<AuthSession> {
  await ensureCsrfToken();
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error("Failed to load current user");
  }
  const data = authResponseSchema.safeParse(await response.json());
  if (!data.success || data.data.ok !== true) {
    return { user: null, context: null };
  }
  return { user: data.data.user ?? null, context: data.data.context ?? null };
}

export async function authCompleteOnboarding(): Promise<AuthResponse> {
  const payload = await csrfClient.request<z.infer<typeof authResponseSchema>>("/auth/complete-onboarding", authResponseSchema, {
    method: "POST",
  });
  if (!payload.ok) {
    const error: AuthError = payload.error ?? { code: "onboarding_failed", message: "Unable to finish onboarding." };
    const err = new Error(error.message) as Error & { code?: string };
    err.code = error.code;
    throw err;
  }
  return { ok: true, user: payload.user ?? null };
}

export async function onboardingComplete(): Promise<AuthResponse> {
  const payload = await csrfClient.request<z.infer<typeof authResponseSchema>>("/onboarding/complete", authResponseSchema, {
    method: "POST",
  });
  if (!payload.ok) {
    const error: AuthError = payload.error ?? { code: "onboarding_failed", message: "Unable to finish onboarding." };
    const err = new Error(error.message) as Error & { code?: string };
    err.code = error.code;
    throw err;
  }
  return { ok: true, user: payload.user ?? null, context: payload.context ?? null };
}

export function getUserContext(): Promise<{ ok: boolean; context: UserContext | null }> {
  return request("/user/context", z.object({ ok: z.boolean(), context: userContextSchema.nullable() }));
}

export function updateUserContext(input: Partial<Pick<UserContext, "league_id" | "division_id" | "team_id" | "role">>): Promise<{ ok: boolean; context: UserContext }> {
  return request(
    "/user/context",
    z.object({ ok: z.boolean(), context: userContextSchema }),
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    },
  );
}

export function getOnboardingDivisions(): Promise<{ divisions: OnboardingDivision[] }> {
  return request("/onboarding/divisions", z.object({ divisions: z.array(onboardingDivisionSchema) }));
}

export function getOnboardingTeams(params?: { division_id?: string | null }): Promise<{ teams: OnboardingTeam[] }> {
  const qs = params?.division_id ? `?division_id=${encodeURIComponent(params.division_id)}` : "";
  return request(`/onboarding/teams${qs}`, z.object({ teams: z.array(onboardingTeamSchema) }));
}

export function getOnboardingLeagues(): Promise<{ leagues: OnboardingLeague[] }> {
  return request("/onboarding/leagues", z.object({ leagues: z.array(onboardingLeagueSchema) }));
}

export function getOnboardingSessions(): Promise<{ sessions: OnboardingSession[] }> {
  return request("/onboarding/sessions", z.object({ sessions: z.array(onboardingSessionSchema) }));
}
