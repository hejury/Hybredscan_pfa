"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { fetchCurrentUser, login as apiLogin, logout as apiLogout } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import type { AuthenticatedUser } from "@/lib/types/backend";

interface AuthContextValue {
  user: AuthenticatedUser | null;
  /** True until the initial session check (GET /auth/me) has completed. */
  loading: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Session lives entirely server-side behind an HttpOnly cookie (api/
 * routers/auth.py) — this provider never reads/writes localStorage or
 * sessionStorage. On mount it asks the API who (if anyone) the current
 * cookie belongs to; `loading` gates any redirect decision until that
 * one round trip finishes, so a refresh on an authenticated page doesn't
 * flash a redirect to /login.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchCurrentUser()
      .then((u) => {
        if (!cancelled) setUser(u);
      })
      .catch(() => {
        if (!cancelled) setUser(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    try {
      const authenticated = await apiLogin(username, password);
      setUser(authenticated);
      return true;
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) return false;
      throw e;
    }
  }, []);

  const logout = useCallback(async () => {
    await apiLogout().catch(() => {
      // Le cookie peut deja etre expire/invalide cote serveur -- l'etat
      // local est efface dans tous les cas (jamais de session fantome
      // affichee comme active).
    });
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
