import { apiGet, apiPost, ApiError } from "@/lib/api/client";
import type { AuthenticatedUser } from "@/lib/types/backend";

interface RawUserResponse {
  username: string;
  is_local_session: boolean;
}

function mapUser(raw: RawUserResponse): AuthenticatedUser {
  return { username: raw.username, isLocalSession: raw.is_local_session };
}

/**
 * Real HybridScan authentication (api/routers/auth.py -> auth.py::verify /
 * verify_compte_configure). The API sets an HttpOnly session cookie on
 * success — this module never stores a token or password client-side.
 */
export async function login(username: string, password: string): Promise<AuthenticatedUser> {
  return mapUser(await apiPost<RawUserResponse>("/api/v1/auth/login", { username, password }));
}

/** Returns the current session's user, or null if unauthenticated (401) —
 * never throws for the expected "not logged in" case. When the API is
 * reached from a local host (127.0.0.1/localhost/::1, server-side
 * decision — see api/dependencies.py), this resolves to a synthetic user
 * with isLocalSession: true instead of 401. */
export async function fetchCurrentUser(): Promise<AuthenticatedUser | null> {
  try {
    return mapUser(await apiGet<RawUserResponse>("/api/v1/auth/me"));
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) return null;
    throw e;
  }
}

export async function logout(): Promise<void> {
  await apiPost<{ success: boolean }>("/api/v1/auth/logout");
}

export async function register(username: string, password: string): Promise<string> {
  const result = await apiPost<{ success: boolean; message: string }>("/api/v1/auth/register", {
    username,
    password,
  });
  return result.message;
}
