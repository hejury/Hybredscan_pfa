"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { ShieldCheck, ShieldAlert, ShieldQuestion, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "@/lib/navigation";
import { fetchProtectionStatus } from "@/lib/api/protection";
import type { ProtectionStatus } from "@/lib/types/backend";

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const [status, setStatus] = useState<ProtectionStatus | null>(null);
  const [errored, setErrored] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchProtectionStatus()
      .then((s) => {
        if (!cancelled) setStatus(s);
      })
      .catch(() => {
        if (!cancelled) setErrored(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <div className="flex items-center gap-2.5 px-2">
        <Image
          src="/branding/hybridscan-mark.png"
          alt="HybridScan"
          width={79}
          height={44}
          className="h-11 w-auto shrink-0 object-contain"
          priority
        />
        <div>
          <p className="text-sm font-bold leading-tight">
            <span className="text-ink-inverse">Hybrid</span>
            <span className="text-primary">Scan</span>
          </p>
          <p className="text-xs text-ink-inverse-muted">Malware Analysis Platform</p>
        </div>
      </div>

      <nav className="mt-8 flex flex-1 flex-col gap-1" aria-label="Navigation principale">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-sm px-3 py-2.5 text-sm font-bold transition-colors",
                active
                  ? "bg-primary/20 text-ink-inverse"
                  : "text-ink-inverse-muted hover:bg-sidebar-hover hover:text-ink-inverse"
              )}
            >
              <Icon className="h-4.5 w-4.5 shrink-0" aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="rounded-md bg-sidebar-hover px-3 py-3">
        <div className="flex items-center gap-2">
          {errored ? (
            <ShieldQuestion className="h-4 w-4 text-ink-inverse-muted" aria-hidden="true" />
          ) : status === null ? (
            <ShieldQuestion className="h-4 w-4 text-ink-inverse-muted animate-pulse" aria-hidden="true" />
          ) : status.active ? (
            <ShieldCheck className="h-4 w-4 text-primary" aria-hidden="true" />
          ) : (
            <ShieldAlert className="h-4 w-4 text-warning" aria-hidden="true" />
          )}
          <p className="text-xs font-bold text-ink-inverse">
            {errored ? "État indisponible" : status === null ? "Vérification…" : status.active ? "Système protégé" : "Protection inactive"}
          </p>
        </div>
        <p className="mt-1 text-[0.7rem] text-ink-inverse-muted">
          {errored
            ? "Impossible de contacter le serveur"
            : status === null
              ? "Chargement de l'état de protection"
              : status.active
                ? "Toutes les défenses actives"
                : "Surveillance des dossiers désactivée"}
        </p>
      </div>
    </>
  );
}

export function Sidebar({
  mobileOpen = false,
  onCloseMobile,
}: {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}) {
  return (
    <>
      {/* Desktop: fixed, always visible. */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col bg-sidebar px-4 py-6 lg:flex">
        <SidebarContent />
      </aside>

      {/* Mobile: drawer + backdrop, only rendered below the lg breakpoint. */}
      {mobileOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-ink/50"
            onClick={onCloseMobile}
            aria-hidden="true"
          />
          <aside className="relative flex h-full w-72 max-w-[80vw] flex-col bg-sidebar px-4 py-6 shadow-overlay">
            <button
              type="button"
              onClick={onCloseMobile}
              aria-label="Fermer le menu"
              className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-sm text-ink-inverse-muted hover:bg-sidebar-hover hover:text-ink-inverse focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
            <SidebarContent onNavigate={onCloseMobile} />
          </aside>
        </div>
      ) : null}
    </>
  );
}
