import { apiGet, apiPost } from "@/lib/api/client";
import {
  mapProtectionEvent, mapProtectionStatus,
  type RawProtectionEvent, type RawProtectionStatus,
} from "@/lib/api/mappers";
import type { ProtectionStatus } from "@/lib/types/backend";

/** api/routers/protection.py -> watcher.Protection.active / DOSSIERS. */
export async function fetchProtectionStatus(): Promise<ProtectionStatus> {
  return mapProtectionStatus(await apiGet<RawProtectionStatus>("/api/v1/protection/status"));
}

/** api/routers/protection.py -> watcher.journal() (detections_rt.json). */
export async function fetchProtectionEvents() {
  const { events } = await apiGet<{ events: RawProtectionEvent[] }>("/api/v1/protection/events");
  return events.map(mapProtectionEvent);
}

/** Wraps watcher.Protection.demarrer() on the single API-held instance. */
export async function startProtection(autoQuarantine: boolean): Promise<ProtectionStatus> {
  return mapProtectionStatus(
    await apiPost<RawProtectionStatus>("/api/v1/protection/start", { auto_quarantine: autoQuarantine })
  );
}

/** Wraps watcher.Protection.arreter() on the single API-held instance. */
export async function stopProtection(): Promise<ProtectionStatus> {
  return mapProtectionStatus(await apiPost<RawProtectionStatus>("/api/v1/protection/stop"));
}
