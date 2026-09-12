import { apiGet } from "@/lib/api/client";

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  models: { pe: boolean; pdf: boolean; docx: boolean };
}

/** api/main.py::GET /api/v1/health — never loads/analyzes a file, only
 * reports whether the model artifacts exist on disk. */
export async function fetchHealth(): Promise<HealthStatus> {
  return apiGet<HealthStatus>("/api/v1/health");
}
