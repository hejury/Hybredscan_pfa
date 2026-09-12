"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { LogOut, Menu, Search, ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthProvider";
import { fetchProtectionStatus } from "@/lib/api/protection";
import type { ProtectionStatus } from "@/lib/types/backend";

function initials(username: string): string {
  const parts = username.trim().split(/[\s._-]+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

export function Topbar({ onMenuClick }: { onMenuClick?: () => void }) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [status, setStatus] = useState<ProtectionStatus | null>(null);
  const [searchValue, setSearchValue] = useState("");

  function handleSearchSubmit(event: FormEvent) {
    event.preventDefault();
    const query = searchValue.trim();
    router.push(query ? `/historique?search=${encodeURIComponent(query)}` : "/historique");
  }

  useEffect(() => {
    let cancelled = false;
    fetchProtectionStatus()
      .then((s) => {
        if (!cancelled) setStatus(s);
      })
      .catch(() => {
        if (!cancelled) setStatus(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-4 border-b border-border bg-surface px-4 sm:px-6">
      <button
        type="button"
        onClick={onMenuClick}
        aria-label="Ouvrir le menu"
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-sm text-ink-secondary hover:bg-canvas-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary lg:hidden"
      >
        <Menu className="h-5 w-5" aria-hidden="true" />
      </button>

      {/* Submits into Historique's real search filter (history.csv, via
          the API) — never fabricated results (cahier des charges §22). */}
      <form onSubmit={handleSearchSubmit} className="relative w-full max-w-md" role="search">
        <Search
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted"
          aria-hidden="true"
        />
        <input
          type="search"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          placeholder="Rechercher une analyse, un fichier, un hachage..."
          aria-label="Rechercher dans l'historique"
          className="w-full rounded-sm border border-border bg-canvas-subtle py-2 pl-9 pr-3 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </form>

      <div className="flex shrink-0 items-center gap-4">
        {status === null ? (
          <span className="hidden items-center gap-1.5 rounded-full bg-canvas-subtle px-3 py-1.5 text-xs font-bold text-ink-muted sm:flex">
            <ShieldQuestion className="h-3.5 w-3.5 animate-pulse" aria-hidden="true" />
            Vérification…
          </span>
        ) : status.active ? (
          <span className="hidden items-center gap-1.5 rounded-full bg-healthy-bg px-3 py-1.5 text-xs font-bold text-healthy sm:flex">
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
            Système protégé
          </span>
        ) : (
          <span className="hidden items-center gap-1.5 rounded-full bg-warning-bg px-3 py-1.5 text-xs font-bold text-warning sm:flex">
            <ShieldAlert className="h-3.5 w-3.5" aria-hidden="true" />
            Protection inactive
          </span>
        )}

        {/* The local-bypass session (server-side decision via
            user.isLocalSession) has no real session to show or log out
            of — the user area is omitted entirely, not left as empty
            space. */}
        {user && !user.isLocalSession ? (
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-sm font-bold text-white">
              {initials(user.username)}
            </span>
            <p className="hidden text-sm font-bold text-ink sm:block">{user.username}</p>
            <button
              type="button"
              onClick={() => void logout()}
              aria-label="Se déconnecter"
              className="flex h-9 w-9 items-center justify-center rounded-sm text-ink-muted hover:bg-canvas-subtle hover:text-malicious focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
}
