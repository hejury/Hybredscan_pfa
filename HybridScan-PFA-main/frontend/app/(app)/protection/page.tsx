"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, ShieldOff, FolderOpen, Archive } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Checkbox } from "@/components/ui/Checkbox";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Table, TableHead, TableHeadCell, TableBody, TableRow, TableCell, TableEmptyState } from "@/components/ui/Table";
import { VerdictBadge } from "@/components/analysis/VerdictBadge";
import {
  fetchProtectionStatus, fetchProtectionEvents, startProtection, stopProtection,
} from "@/lib/api/protection";
import { friendlyErrorMessage } from "@/lib/api/errorMessage";
import { formatConfidence } from "@/lib/utils";
import type { ProtectionEvent, ProtectionStatus } from "@/lib/types/backend";

export default function ProtectionPage() {
  const [status, setStatus] = useState<ProtectionStatus | null>(null);
  const [events, setEvents] = useState<ProtectionEvent[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadToken, setLoadToken] = useState(0);
  const [autoQuarantine, setAutoQuarantine] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- deliberate: clears a stale error from a previous attempt before this retry's fetch starts; a single clean transition, not a cascading update.
    setError(null);
    Promise.all([fetchProtectionStatus(), fetchProtectionEvents()])
      .then(([s, e]) => {
        if (!cancelled) {
          setStatus(s);
          setEvents(e);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(friendlyErrorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [loadToken]);

  async function handleActivate() {
    setToggling(true);
    setActionError(null);
    try {
      const next = await startProtection(autoQuarantine);
      setStatus(next);
    } catch (e) {
      setActionError(friendlyErrorMessage(e));
    } finally {
      setToggling(false);
    }
  }

  async function handleDeactivate() {
    if (!window.confirm("Désactiver la protection en temps réel ? La surveillance des dossiers configurés s'arrêtera immédiatement.")) {
      return;
    }
    setToggling(true);
    setActionError(null);
    try {
      const next = await stopProtection();
      setStatus(next);
    } catch (e) {
      setActionError(friendlyErrorMessage(e));
    } finally {
      setToggling(false);
    }
  }

  if (error) {
    return (
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-xl font-bold text-ink">Protection</h1>
        </div>
        <Card>
          <ErrorState message={error} onRetry={() => setLoadToken((t) => t + 1)} />
        </Card>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-xl font-bold text-ink">Protection</h1>
        </div>
        <Card>
          <LoadingState label="Chargement de l'état de la protection…" />
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-bold text-ink">Protection</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          État de la surveillance des dossiers HybridScan (watcher).
        </p>
      </div>

      <Card>
        <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
          <div className="flex items-center gap-3">
            <span
              className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-md ${
                status.active ? "bg-healthy-bg text-healthy" : "bg-canvas-subtle text-ink-muted"
              }`}
            >
              {status.active ? (
                <ShieldCheck className="h-5 w-5" aria-hidden="true" />
              ) : (
                <ShieldOff className="h-5 w-5" aria-hidden="true" />
              )}
            </span>
            <div>
              <p className="text-sm font-bold text-ink">{status.active ? "Surveillance active" : "Surveillance inactive"}</p>
              <p className="text-xs text-ink-secondary">Statut de la protection en temps réel</p>
            </div>
          </div>

          <div className="flex flex-col items-start gap-3 sm:items-end">
            {!status.active ? (
              <Checkbox
                id="protection-auto-quarantine"
                label="Quarantaine automatique"
                checked={autoQuarantine}
                onChange={(e) => setAutoQuarantine(e.target.checked)}
              />
            ) : null}
            {status.active ? (
              <Button variant="danger" loading={toggling} onClick={() => void handleDeactivate()}>
                Désactiver la protection
              </Button>
            ) : (
              <Button variant="primary" loading={toggling} onClick={() => void handleActivate()}>
                Activer la protection
              </Button>
            )}
          </div>
        </div>
        {actionError ? <p className="mt-3 text-sm font-bold text-malicious">{actionError}</p> : null}
      </Card>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card className="flex items-center gap-4">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-primary-soft text-primary">
            <FolderOpen className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-bold text-ink">
              {status.monitoredDirectories.length} dossier(s) {status.active ? "surveillé(s)" : "configuré(s)"}
            </p>
            <p className="text-xs text-ink-secondary">
              {status.active ? "Répertoires sous protection continue" : "Seront surveillés une fois la protection activée"}
            </p>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-warning-bg text-warning">
            <Archive className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-bold text-ink">
              Quarantaine automatique{" "}
              {status.autoQuarantine === null ? "non déterminée" : status.autoQuarantine ? "activée" : "désactivée"}
            </p>
            <p className="text-xs text-ink-secondary">Comportement appliqué aux détections du watcher</p>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader title="Dossiers configurés" />
        {status.monitoredDirectories.length > 0 ? (
          <ul className="flex flex-col gap-2">
            {status.monitoredDirectories.map((dir) => (
              <li key={dir} className="rounded-sm bg-canvas-subtle px-3 py-2 font-technical text-xs text-ink break-all">
                {dir}
              </li>
            ))}
          </ul>
        ) : (
          <p className="py-6 text-center text-sm text-ink-muted">Aucun dossier surveillé actuellement.</p>
        )}
      </Card>

      <Card>
        <CardHeader
          title="Événements récents"
          subtitle="Dernières détections du watcher (rafraîchi périodiquement, pas de flux temps réel)"
          action={<Badge tone="neutral">{events?.length ?? 0} événement(s)</Badge>}
        />
        <Table>
          <TableHead>
            <TableHeadCell>Heure</TableHeadCell>
            <TableHeadCell>Fichier</TableHeadCell>
            <TableHeadCell>Verdict</TableHeadCell>
            <TableHeadCell>Confiance</TableHeadCell>
          </TableHead>
          <TableBody>
            {!events || events.length === 0 ? (
              <TableEmptyState colSpan={4} message="Aucun événement récent." />
            ) : (
              events.map((event) => (
                <TableRow key={`${event.fileName}-${event.time}`}>
                  <TableCell className="text-ink-secondary">{event.time}</TableCell>
                  <TableCell className="font-bold">{event.fileName}</TableCell>
                  <TableCell>
                    {event.verdict === "erreur" ? <Badge tone="warning">Erreur</Badge> : <VerdictBadge verdict={event.verdict} />}
                  </TableCell>
                  <TableCell>{formatConfidence(event.confidence)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
