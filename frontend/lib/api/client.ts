/**
 * Centralized HTTP client for the real HybridScan FastAPI bridge.
 * Every lib/api/*.ts adapter goes through this — no component calls
 * fetch() directly, and no other file hardcodes the API base URL.
 *
 * Auth uses an HttpOnly session cookie set by the API (never a token in
 * localStorage) — `credentials: "include"` sends it on every request.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_HYBRIDSCAN_API_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function extractErrorMessage(res: Response): Promise<string> {
  try {
    const data = await res.json();

    if (typeof data?.detail === "string") {
      return data.detail;
    }

    if (Array.isArray(data?.detail)) {
      return data.detail
        .map((d: { msg?: string }) => d.msg)
        .filter(Boolean)
        .join(" ");
    }
  } catch {
    // Corps non-JSON — retombe sur le statut HTTP.
  }

  return res.statusText || "Une erreur est survenue.";
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;

  let res: Response;

  try {
    res = await fetch(url, {
      ...options,
      credentials: "include",
      headers:
        options.body && !(options.body instanceof FormData)
          ? {
              "Content-Type": "application/json",
              ...options.headers,
            }
          : options.headers,
    });
  } catch (error) {
    // DEBUG: afficher l'erreur réelle dans la console du navigateur.
    console.error("HYBRIDSCAN API ERROR:", error);
    console.error("HYBRIDSCAN API URL:", url);
    console.error("HYBRIDSCAN API OPTIONS:", options);

    throw new ApiError(
      0,
      "Impossible de contacter le serveur HybridScan."
    );
  }

  if (!res.ok) {
    throw new ApiError(
      res.status,
      await extractErrorMessage(res)
    );
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

export const apiGet = <T>(
  path: string
): Promise<T> =>
  request<T>(path, {
    method: "GET",
  });

export const apiPost = <T>(
  path: string,
  body?: unknown
): Promise<T> =>
  request<T>(path, {
    method: "POST",
    body:
      body === undefined
        ? undefined
        : JSON.stringify(body),
  });

export const apiPostForm = <T>(
  path: string,
  formData: FormData
): Promise<T> =>
  request<T>(path, {
    method: "POST",
    body: formData,
  });