/**
 * CSRF-aware API client for reliable mutating requests.
 * Handles token refresh and automatic retry on CSRF failures.
 */

import { z } from "zod";

// Use proxy path in development (served via Vite proxy), absolute URL in production
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (typeof import.meta.env.DEV !== 'undefined' && import.meta.env.DEV ? "/api" : "http://localhost:5000/api");

interface RequestOptions extends RequestInit {
  requiresCsrf?: boolean;
  retryOnCsrfFailure?: boolean;
}

class CSRFClient {
  private csrfToken: string | null = null;
  private csrfPromise: Promise<string> | null = null;

  /**
   * Fetch a fresh CSRF token from the server.
   * Ensures concurrent requests don't create duplicate fetches.
   */
  async fetchCsrfToken(): Promise<string> {
    if (this.csrfPromise) {
      return this.csrfPromise;
    }

    this.csrfPromise = (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/csrf`, {
          credentials: "include",
          headers: { Accept: "application/json" },
        });

        if (!response.ok) {
          throw new Error(`CSRF fetch failed: ${response.status}`);
        }

        const data = await response.json();
        const token = data.csrf_token as string;

        if (!token) {
          throw new Error("No CSRF token in response");
        }

        this.csrfToken = token;
        return token;
      } finally {
        this.csrfPromise = null;
      }
    })();

    return this.csrfPromise;
  }

  /**
   * Get the current CSRF token, fetching if necessary.
   */
  async getCsrfToken(): Promise<string> {
    if (this.csrfToken) {
      return this.csrfToken;
    }
    return this.fetchCsrfToken();
  }

  /**
   * Clear the cached CSRF token (called on 403 to force refresh).
   */
  clearCsrfToken(): void {
    this.csrfToken = null;
  }

  /**
   * Make an API request with optional CSRF handling and retry logic.
   */
  async request<T>(
    path: string,
    schema: z.ZodSchema<T>,
    options: RequestOptions = {},
  ): Promise<T> {
    const { requiresCsrf = true, retryOnCsrfFailure = true, ...fetchOptions } = options;

    // Set default method
    const method = (fetchOptions.method || "GET").toUpperCase();

    // Prepare headers
    const headers: Record<string, string> = {
      Accept: "application/json",
      ...(fetchOptions.headers as Record<string, string> | undefined),
    };

    // Add CSRF token for mutating requests
    if (requiresCsrf && !["GET", "HEAD", "OPTIONS"].includes(method)) {
      const csrfToken = await this.getCsrfToken();
      headers["X-CSRF-Token"] = csrfToken;
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
      credentials: "include",
      ...fetchOptions,
      headers,
    });

    // Handle CSRF failure with retry
    if (
      retryOnCsrfFailure &&
      (response.status === 403 || response.status === 401) &&
      requiresCsrf &&
      !["GET", "HEAD", "OPTIONS"].includes(method)
    ) {
      const body = await response.text();

      // Check if it's a CSRF error
      if (body.includes("csrf")) {
        // Refresh CSRF token
        this.clearCsrfToken();
        const newToken = await this.fetchCsrfToken();

        // Retry the request once
        const retryHeaders: Record<string, string> = {
          Accept: "application/json",
          ...(fetchOptions.headers as Record<string, string> | undefined),
          "X-CSRF-Token": newToken,
        };

        const retryResponse = await fetch(`${API_BASE_URL}${path}`, {
          credentials: "include",
          ...fetchOptions,
          headers: retryHeaders,
        });

        return this.parseResponse(retryResponse, schema, path);
      }
    }

    return this.parseResponse(response, schema, path);
  }

  private async parseResponse<T>(
    response: Response,
    schema: z.ZodSchema<T>,
    path: string,
  ): Promise<T> {
    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText} at ${path}`);
    }

    const text = await response.text();
    let data: unknown;

    try {
      data = JSON.parse(text);
    } catch {
      throw new Error(`Invalid JSON response from ${path}`);
    }

    const parsed = schema.safeParse(data);
    if (!parsed.success) {
      console.error("Schema validation failed:", parsed.error);
      throw new Error(`Invalid response shape from ${path}`);
    }

    return parsed.data;
  }
}

/**
 * Global CSRF client instance.
 * Shared across all API calls to maintain token state.
 */
export const csrfClient = new CSRFClient();

/**
 * Initialize CSRF token on app startup.
 * Call this during app initialization (e.g., in AuthProvider or AppGate).
 */
export async function initializeCsrfToken(): Promise<void> {
  try {
    await csrfClient.fetchCsrfToken();
  } catch (err) {
    console.warn("Failed to initialize CSRF token:", err);
    // Don't throw—requests will attempt to fetch on demand
  }
}
