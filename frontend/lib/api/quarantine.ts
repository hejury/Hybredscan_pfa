import { apiGet, ApiError } from "@/lib/api/client";
import { mapQuarantineEntry, type RawQuarantineEntry } from "@/lib/api/mappers";
import type { QuarantineEntry } from "@/lib/types/backend";

interface RawQuarantineListResponse {
  total: number;
  isolated: number;
  incomplete: number;
  warnings: string[];
  items: RawQuarantineEntry[];
}

/** api/routers/quarantine.py -> quarantine_manager.list_quarantine_items()
 * — metadata only, never the isolated .quarantine payload. */
export async function fetchQuarantineList(): Promise<QuarantineEntry[]> {
  const response = await apiGet<RawQuarantineListResponse>("/api/v1/quarantine");
  return response.items.map(mapQuarantineEntry);
}

/** api/routers/quarantine.py -> quarantine_manager.get_quarantine_details().
 * Returns null on 404, matching the Python function's own null-on-not-found
 * contract. */
export async function fetchQuarantineDetails(id: string): Promise<QuarantineEntry | null> {
  try {
    return mapQuarantineEntry(
      await apiGet<RawQuarantineEntry>(`/api/v1/quarantine/${encodeURIComponent(id)}`)
    );
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}
