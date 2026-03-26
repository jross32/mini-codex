import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  authLogin,
  authLogout,
  authMe,
  authSignup,
  updateUserContext,
  initializeCsrfToken,
  type AuthResponse,
  type User,
  type UserContext,
  type AuthSession,
} from "../api/client";

type AuthContextValue = {
  user: User | null;
  context: UserContext | null;
  initializing: boolean;
  login: (input: { email: string; password: string }) => Promise<AuthResponse>;
  signup: (input: { email: string; password: string; username?: string | null }) => Promise<AuthResponse>;
  logout: () => Promise<void>;
  refresh: () => Promise<AuthSession>;
  updateContext: (
    input: Partial<Pick<UserContext, "league_id" | "division_id" | "team_id" | "role">>,
  ) => Promise<UserContext>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [context, setContext] = useState<UserContext | null>(null);
  const [initializing, setInitializing] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const res = await authMe();
      setUser(res.user);
      setContext(res.context ?? null);
      return res;
    } catch {
      setUser(null);
      setContext(null);
      return { user: null, context: null };
    } finally {
      setInitializing(false);
    }
  }, []);

  // Initialize CSRF token on app start
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Start CSRF token fetch in parallel with user refresh
        const csrfPromise = initializeCsrfToken();
        const userPromise = refresh();
        
        await Promise.all([csrfPromise, userPromise]);
      } catch (err) {
        console.error("Failed to initialize app:", err);
        // Still continue if CSRF fails—requests will fetch on demand
        await refresh();
      }
    };

    void initializeApp();
  }, [refresh]);

  const login = useCallback(
    async (input: { email: string; password: string }) => {
      const res = await authLogin(input);
      if (res.ok) {
        setUser(res.user ?? null);
        setContext(res.context ?? null);
      }
      return res;
    },
    [],
  );

  const signup = useCallback(
    async (input: { email: string; password: string; username?: string | null }) => {
      const res = await authSignup(input);
      if (res.ok) {
        setUser(res.user ?? null);
        setContext(res.context ?? null);
      }
      return res;
    },
    [],
  );

  const logout = useCallback(async () => {
    try {
      await authLogout();
    } finally {
      setUser(null);
      setContext(null);
    }
  }, []);

  const updateContext = useCallback(
    async (input: Partial<Pick<UserContext, "league_id" | "division_id" | "team_id" | "role">>) => {
      const res = await updateUserContext(input);
      setContext(res.context ?? null);
      return res.context;
    },
    [],
  );

  const value = useMemo(
    () => ({ user, context, initializing, login, signup, logout, refresh, updateContext }),
    [user, context, initializing, login, signup, logout, refresh, updateContext],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
