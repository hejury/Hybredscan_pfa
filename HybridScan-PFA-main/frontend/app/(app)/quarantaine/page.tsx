"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader } from "@/components/ui/Card";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { QuarantineSummaryCards } from "@/components/quarantine/QuarantineSummaryCards";
import { QuarantineList } from "@/components/quarantine/QuarantineList";
import { QuarantineDetail } from "@/components/quarantine/QuarantineDetail";
import { fetchQuarantineList } from "@/lib/api/quarantine";
import { friendlyErrorMessage } from "@/lib/api/errorMessage";
import type { QuarantineEntry } from "@/lib/types/backend";

export default function QuarantinePage() {
  const [entries, setEntries] = useState<QuarantineEntry[] | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchQuarantineList()
      .then((items) => {
        if (cancelled) return;

        setEntries(items);
        setSelectedId(items[0]?.id ?? null);
      })
      .catch((e) => {
        if (cancelled) return;

        setError(friendlyErrorMessage(e));
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const selected =
    entries?.find((entry) => entry.id === selectedId) ?? null;

  return (
    <div className="flex flex-col gap-6">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-bold text-ink">
          Quarantaine
        </h1>

        <p className="mt-1 text-sm text-ink-secondary">
          Consultez les fichiers isolés et les éléments nécessitant une vérification.
        </p>
      </div>

      {/* Loading */}
      {entries === null && !error ? (
        <LoadingState label="Chargement de la quarantaine…" />
      ) : error ? (
        <ErrorState message={error} />
      ) : (
        <>
          {/* Summary */}
          <QuarantineSummaryCards entries={entries ?? []} />

          {/* Main content */}
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <Card className="xl:col-span-2">
              <CardHeader
                title="Éléments en quarantaine"
                subtitle={`${entries?.length ?? 0} élément(s)`}
              />

              <QuarantineList
                entries={entries ?? []}
                selectedId={selectedId}
                onSelect={setSelectedId}
              />
            </Card>

            <QuarantineDetail entry={selected} />
          </div>
        </>
      )}
    </div>
  );
}