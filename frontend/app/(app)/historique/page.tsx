"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { RecentActivityTable } from "@/components/dashboard/RecentActivityTable";
import { familyOf } from "@/lib/api/dashboard";
import { fetchHistory } from "@/lib/api/history";
import { friendlyErrorMessage } from "@/lib/api/errorMessage";
import type { HistoryEntry } from "@/lib/types/backend";

const PAGE_SIZE = 5;

export default function HistoriquePage() {
  return (
    // useSearchParams() opts this page out of static rendering unless it is
    // wrapped in a Suspense boundary (Next.js App Router requirement) --
    // required for `next build`/production mode (desktop packaging), no
    // effect on `next dev`. No loading UI needed: the initial render is
    // synchronous (searchParams is already available client-side).
    <Suspense>
      <HistoriqueContent />
    </Suspense>
  );
}

function HistoriqueContent() {
  const searchParams = useSearchParams();
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadToken, setLoadToken] = useState(0);
  const [search, setSearch] = useState(() => searchParams.get("search") ?? "");
  const [verdict, setVerdict] = useState<string>("all");
  const [type, setType] = useState<"all" | "pe" | "pdf" | "docx">("all");
  const [date, setDate] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- deliberate: clears a stale error from a previous attempt before this retry's fetch starts; a single clean transition, not a cascading update.
    setError(null);
    fetchHistory()
      .then((data) => {
        if (!cancelled) setEntries(data);
      })
      .catch((e) => {
        if (!cancelled) setError(friendlyErrorMessage(e));
      });
    return () => {
      cancelled = true;
    };
  }, [loadToken]);

  const filtered = useMemo(() => {
    if (!entries) return [];
    return entries.filter((entry) => {
      if (search.trim()) {
        const query = search.trim().toLowerCase();
        if (!entry.fileName.toLowerCase().includes(query) && !entry.sha256.toLowerCase().includes(query)) {
          return false;
        }
      }
      if (verdict !== "all" && entry.verdict !== verdict) return false;
      if (type !== "all" && familyOf(entry) !== type) return false;
      if (date && !entry.date.startsWith(date)) return false;
      return true;
    });
  }, [entries, search, verdict, type, date]);

  const filtersActive = Boolean(search.trim() || verdict !== "all" || type !== "all" || date);
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const pageEntries = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  function updateFilter<T>(setter: (value: T) => void, value: T) {
    setter(value);
    setPage(1);
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-bold text-ink">Historique</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          Toutes les analyses enregistrées, telles qu&apos;issues du journal HybridScan.
        </p>
      </div>

      <Card>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-[38px] h-4 w-4 -translate-y-1/2 text-ink-muted" aria-hidden="true" />
            <Input
              id="history-search"
              label="Recherche"
              placeholder="Nom de fichier ou hachage"
              className="pl-9"
              value={search}
              onChange={(e) => updateFilter(setSearch, e.target.value)}
            />
          </div>
          <Select
            id="history-verdict"
            label="Verdict"
            value={verdict}
            onChange={(e) => updateFilter(setVerdict, e.target.value)}
          >
            <option value="all">Tous</option>
            <option value="sain">Sain</option>
            <option value="malveillant">Malveillant</option>
            <option value="indetermine">Indéterminé</option>
          </Select>
          <Select
            id="history-type"
            label="Type"
            value={type}
            onChange={(e) => updateFilter(setType, e.target.value as "all" | "pe" | "pdf" | "docx")}
          >
            <option value="all">Tous</option>
            <option value="pe">Exécutable (PE)</option>
            <option value="pdf">PDF</option>
            <option value="docx">DOCX</option>
          </Select>
          <Input
            id="history-date"
            label="Date"
            type="date"
            value={date}
            onChange={(e) => updateFilter(setDate, e.target.value)}
          />
        </div>
      </Card>

      <Card>
        {error ? (
          <ErrorState message={error} onRetry={() => setLoadToken((t) => t + 1)} />
        ) : entries === null ? (
          <LoadingState label="Chargement de l'historique…" />
        ) : (
          <>
            <CardHeader title={`${filtered.length} résultat(s)`} />
            {filtered.length === 0 ? (
              <p className="py-10 text-center text-sm text-ink-muted">
                {filtersActive ? "Aucun résultat pour ces filtres." : "Aucune analyse enregistrée."}
              </p>
            ) : (
              <>
                <RecentActivityTable entries={pageEntries} />
                <div className="mt-4 flex items-center justify-between">
                  <p className="text-sm text-ink-secondary">
                    Page {currentPage} sur {totalPages}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage <= 1}
                    >
                      <ChevronLeft className="h-4 w-4" aria-hidden="true" />
                      Précédent
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={currentPage >= totalPages}
                    >
                      Suivant
                      <ChevronRight className="h-4 w-4" aria-hidden="true" />
                    </Button>
                  </div>
                </div>
              </>
            )}
          </>
        )}
      </Card>
    </div>
  );
}
