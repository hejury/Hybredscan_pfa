import { apiGet } from "@/lib/api/client";
import { mapHistoryEntry, type RawHistoryEntry } from "@/lib/api/mappers";
import type { HistoryEntry } from "@/lib/types/backend";

export interface HistoryFilters {
  search?: string;
  verdict?: string;
  family?: string;
  limit?: number;
  offset?: number;
}

interface RawHistoryResponse {
  total: number;
  warnings: string[];
  items: RawHistoryEntry[];
}

/** api/routers/history.py -> backend_shared.charger_historique() (history.csv). */
export async function fetchHistory(filters: HistoryFilters = {}): Promise<HistoryEntry[]> {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.verdict) params.set("verdict", filters.verdict);
  if (filters.family) params.set("type", filters.family);
  if (filters.limit !== undefined) params.set("limit", String(filters.limit));
  if (filters.offset !== undefined) params.set("offset", String(filters.offset));

  const query = params.toString();
  const response = await apiGet<RawHistoryResponse>(`/api/v1/history${query ? `?${query}` : ""}`);
  return response.items.map(mapHistoryEntry);
}
