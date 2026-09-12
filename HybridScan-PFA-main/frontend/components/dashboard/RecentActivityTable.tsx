import { Table, TableHead, TableHeadCell, TableBody, TableRow, TableCell, TableEmptyState } from "@/components/ui/Table";
import { VerdictBadge } from "@/components/analysis/VerdictBadge";
import { DetectionSourceBadge } from "@/components/analysis/DetectionSourceBadge";
import { familyOf } from "@/lib/api/dashboard";
import { formatDateTime, FAMILY_LABELS } from "@/lib/utils";
import type { HistoryEntry } from "@/lib/types/backend";

export function RecentActivityTable({ entries }: { entries: HistoryEntry[] }) {
  return (
    <Table>
      <TableHead>
        <TableHeadCell>Fichier</TableHeadCell>
        <TableHeadCell>Type</TableHeadCell>
        <TableHeadCell>Verdict</TableHeadCell>
        <TableHeadCell>Source</TableHeadCell>
        <TableHeadCell>Heure</TableHeadCell>
      </TableHead>
      <TableBody>
        {entries.length === 0 ? (
          <TableEmptyState colSpan={5} message="Aucune analyse récente." />
        ) : (
          entries.map((entry, index) => {
            const family = familyOf(entry);
            return (
              // sha256+date isn't guaranteed unique — two identical files
              // analyzed within the same second (e.g. a folder scan of
              // duplicate fixtures) legitimately collide; index breaks the tie.
              <TableRow key={`${entry.sha256}-${entry.date}-${index}`}>
                <TableCell className="font-bold">{entry.fileName}</TableCell>
                <TableCell>{family ? FAMILY_LABELS[family] : "—"}</TableCell>
                <TableCell>
                  <VerdictBadge verdict={entry.verdict} />
                </TableCell>
                <TableCell>
                  <DetectionSourceBadge source={entry.detectionSource} />
                </TableCell>
                <TableCell className="text-ink-secondary">{formatDateTime(entry.date)}</TableCell>
              </TableRow>
            );
          })
        )}
      </TableBody>
    </Table>
  );
}
