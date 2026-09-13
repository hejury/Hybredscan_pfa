"use client";

import { useState, type ReactNode } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

/**
 * No login gate here: the API always authenticates requests coming from a
 * local host (127.0.0.1/localhost/::1 — see api/dependencies.py's
 * always-on local bypass), so running the app locally never needs a
 * session to reach the dashboard. AuthProvider still fetches /auth/me in
 * the background purely to feed the topbar's user area (real logins stay
 * possible and take priority — see /login), but the shell itself never
 * blocks on it or redirects away.
 */
export function AppShell({ children }: { children: ReactNode }) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen bg-canvas">
      <Sidebar mobileOpen={mobileNavOpen} onCloseMobile={() => setMobileNavOpen(false)} />
      <div className="flex min-h-screen flex-col lg:pl-64">
        <Topbar onMenuClick={() => setMobileNavOpen(true)} />
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
