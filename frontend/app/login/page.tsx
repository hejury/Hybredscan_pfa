"use client";

import { useEffect, useState, type FormEvent } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { AlertCircle, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthProvider";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

export default function LoginPage() {
  const { user, loading, login } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) {
      router.replace("/");
    }
  }, [loading, user, router]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    const ok = await login(username, password);
    setSubmitting(false);
    if (!ok) {
      setError("Identifiant ou mot de passe incorrect.");
      return;
    }
    router.replace("/");
  }

  // Covers both the initial GET /auth/me round trip and the always-on
  // local bypass (api/dependencies.py, 127.0.0.1/localhost/::1): when
  // reached locally, `user` resolves to a synthetic session almost
  // immediately, so this page must never flash the real login form before
  // the redirect above fires (cahier des charges §8 — "prefer redirecting
  // directly").
  if (loading || user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-canvas">
        <Loader2 className="h-6 w-6 animate-spin text-primary" aria-hidden="true" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4">
      <div className="w-full max-w-sm rounded-md border border-border bg-surface p-8 shadow-raised">
        <div className="mb-6 flex flex-col items-center text-center">
          <Image
            src="/branding/hybridscan-mark.png"
            alt="HybridScan"
            width={86}
            height={48}
            className="mb-3 h-12 w-auto object-contain"
            priority
          />
          <h1 className="text-lg font-bold">
            <span className="text-ink">Hybrid</span>
            <span className="text-primary">Scan</span>
          </h1>
          <p className="mt-1 text-sm text-ink-secondary">Plateforme d&apos;analyse de malwares</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            id="username"
            label="Identifiant"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <Input
            id="password"
            label="Mot de passe"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error ? (
            <p className="flex items-center gap-2 text-sm font-bold text-malicious">
              <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
              {error}
            </p>
          ) : null}

          <Button type="submit" loading={submitting} className="mt-2 w-full">
            Se connecter
          </Button>
        </form>
      </div>
    </div>
  );
}
