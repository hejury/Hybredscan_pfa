# Next.js ↔ FastAPI Real Integration

## 1. FastAPI structure

New package `api/` at the project root (sibling to `analyze.py`, `app.py`):

```
api/
  main.py                  FastAPI app, CORS, health endpoint, global error handler
  config.py                CORS origins, cookie settings, upload limits, extensions
  dependencies.py          get_current_user (session cookie -> 401 if absent/invalid)
  routers/
    auth.py  analysis.py  folder_scan.py  history.py  quarantine.py  protection.py  dashboard.py
  schemas/
    auth.py  analysis.py  folder_scan.py  history.py  quarantine.py  protection.py  dashboard.py
  services/
    auth_service.py  analysis_service.py  folder_scan_service.py  history_service.py
    quarantine_service.py  protection_service.py  dashboard_service.py
```

Every service module imports and calls the existing, already-tested Python functions (`analyze.analyser`, `auth.verify`/`verify_compte_configure`/`register`, `quarantine_manager.list_quarantine_items`/`get_quarantine_details`, `watcher.Protection`/`journal`/`DOSSIERS`, `backend_shared.*`). No malware-detection or path-security logic was reimplemented in `api/` — every router is a thin translation layer between HTTP/JSON and the existing function calls.

### Shared helper extraction (the one backend change)

`backend_shared.py` (new, project root) now holds `_cible_interdite`, `_config_racines_scan`, `_racines_autorisees`, `_cible_dans_racines_autorisees`, `valider_dossier_scan`, and `charger_historique` — moved **verbatim** out of `app.py`, which previously defined them inline, interleaved with Streamlit rendering code executed at import time (`st.set_page_config`, the auth gate's `st.stop()`, the sidebar, etc.). Importing `app.py` directly for these pure helpers was not possible without triggering that rendering. `app.py` now imports the same functions from `backend_shared.py`; **both** Streamlit and the FastAPI bridge call the identical code.

The only line-level behavior change: `_config_racines_scan()`'s `import streamlit as st` moved from module-level (already present in `app.py` for everything else) to a local import inside a `try/except`, matching the exact pattern already used by `analyze.py::_charger_cle_vt()` and `auth.py::_compte_configure()` for the same reason (stay importable without an active Streamlit run). Behavior (env var first, then `st.secrets`, else `""`) is unchanged.

## 2. Endpoints (`/api/v1` prefix)

| Method | Path | Wraps |
|---|---|---|
| GET | `/health` | file-existence check only, no analysis |
| POST | `/auth/login` | `auth.verify` OR `auth.verify_compte_configure` |
| GET | `/auth/me` | current session lookup |
| POST | `/auth/logout` | session invalidation |
| POST | `/auth/register` | `auth.register` |
| POST | `/analysis/file` | `analyze.analyser` (upload) |
| GET | `/scan/folder/config` | `backend_shared._racines_autorisees` |
| POST | `/scan/folder` | `backend_shared.valider_dossier_scan` + `analyze.analyser` loop |
| GET | `/history` | `backend_shared.charger_historique` |
| GET | `/quarantine` | `quarantine_manager.list_quarantine_items` |
| GET | `/quarantine/{id}` | `quarantine_manager.get_quarantine_details` |
| GET | `/protection/status` | `watcher.Protection.active` / `DOSSIERS` |
| GET | `/protection/events` | `watcher.journal()` |
| POST | `/protection/start` / `/stop` | `watcher.Protection.demarrer()` / `.arreter()` |
| GET | `/dashboard` | aggregates the three sources above |

## 3. Authentication

Login accepts the same two credential paths `app.py::page_connexion()` already accepts: a `users.json` account (`auth.verify`, created via `/auth/register` — the same `auth.register()` Streamlit's "Créer un compte" tab uses) **or** the single configured admin account (`auth.verify_compte_configure`, via `.streamlit/secrets.toml` / env vars). No new credential store, no weakened hashing, no hardcoded account.

**Session**: an in-memory dict (`api/services/auth_service.py::_SESSIONS`) keyed by a `secrets.token_urlsafe(32)` token, set as an **HttpOnly, SameSite=Lax** cookie (`hybridscan_session`, 8h max-age, `Secure` only when `HYBRIDSCAN_COOKIE_SECURE=1`). The frontend never sees or stores this token — no `localStorage`/`sessionStorage` use anywhere in `lib/auth/AuthProvider.tsx`. `GET /auth/me` is how the frontend discovers "am I logged in" on mount and after a refresh.

**Known limitation**: sessions are process-local memory — they don't survive an API restart and wouldn't be shared across multiple uvicorn workers. Documented as the deliberately smallest solution for this phase (explicitly not building OAuth/an external session store).

## 4. CORS / cookie / CSRF strategy

- `CORSMiddleware(allow_origins=CORS_ORIGINS, allow_credentials=True, allow_methods=["GET","POST"])`. `CORS_ORIGINS` defaults to `http://localhost:3000,http://127.0.0.1:3000`, overridable via `HYBRIDSCAN_CORS_ORIGINS`. Never `"*"` — incompatible with `allow_credentials=True` anyway.
- **Real bug found and fixed during E2E testing**: the frontend's API base URL originally pointed at `http://127.0.0.1:8000` while the dev server ran at `http://localhost:3000`. Although both resolve to the same machine, browsers treat `localhost` and `127.0.0.1` as different **sites** for `SameSite=Lax` purposes, so the cookie was silently dropped on every request after login. Fixed by pointing `NEXT_PUBLIC_HYBRIDSCAN_API_URL` at `http://localhost:8000` (same hostname as the frontend, different port = same-site). Documented inline in `frontend/.env.local`.
- CSRF: `SameSite=Lax` already blocks the classic cross-site `<form>` POST vector for cookie-authenticated state-changing requests (the browser won't attach the cookie to a cross-site POST at all). Combined with the explicit CORS origin allowlist (a cross-origin `fetch` from anywhere else can't even read the response, and cross-site credentialed requests are blocked at the preflight), no separate CSRF token was added — this is the "smallest clean solution" called for, not a general-purpose public API.

## 5. File upload lifecycle

`POST /analysis/file` (multipart): extension checked against `SUPPORTED_UPLOAD_EXTENSIONS` (`.exe .dll .pdf .doc .docx`, matching `analyze.py`'s own routing) → size checked against `MAX_UPLOAD_SIZE_BYTES` (200 MB, the same figure already advertised in the frontend and matching Streamlit's default `st.file_uploader` limit — never two different advertised limits) → written to a **dedicated temp directory** (`tempfile.mkdtemp`) under a **server-generated filename** (`<8-hex>_<sanitized-basename-of-the-browser-supplied-name>`) → `analyze.analyser(path, isoler, source_context=SOURCE_UPLOAD)` → temp directory removed in a `finally` block (success and error paths both).

The browser-supplied filename is never used as a path — only its `os.path.basename()` (which already strips any `../` or absolute-path component) is kept, then further sanitized to `[A-Za-z0-9._-]`, then prefixed with a random token. This was **tightened during testing**: the first version wrote the upload as `hybridscan_upload_<random>.<ext>`, discarding the original name entirely, which meant `history.csv` (populated by `analyze.py::journaliser()` from the temp path's own basename — logic never modified) showed an unreadable temp name instead of anything resembling the uploaded file. The fix keeps a sanitized copy of the real name in the temp filename itself, so history stays both safe and legible (e.g. `a1b2c3d4_rapport.docx`).

The API's JSON response's `filename` field is always the real browser-supplied name (never the temp name) — this matches the existing Streamlit app, whose `bandeau()` result view never shows `res["fichier"]` either, always the separately-tracked `fichier.name` from the upload widget.

## 6. Folder-scan security model

Identical boundary to the existing Streamlit page: `backend_shared.valider_dossier_scan()` (env var `HYBRIDSCAN_ALLOWED_SCAN_DIRS` → `.streamlit/secrets.toml`, `Path.relative_to()`-based confinement) is the single source of truth for both `app.py` and `POST /scan/folder`. A path outside the configured root, or a `..` traversal attempt, returns `403` with the same French error message the Streamlit page already shows — verified against the real configured root (`C:\Users\user\Desktop\HybridScan-Scan`) during testing. Candidate extension list (originally `.exe`/`.dll` only, later extended to also include `.pdf`/`.docx` on 2026-08-19 — see `backend_shared.EXTENSIONS_SCAN_DOSSIER`) only decides which files are *submitted* to `analyser()`; the path-security logic itself never changed.

This is architecturally distinct from the upload endpoint: uploads never accept a client-supplied path (server temp file only); folder scan validates a server-side path against a configured allowlist. The two are never mixed.

## 7. Quarantine — metadata only

`GET /quarantine` and `GET /quarantine/{id}` return exactly what `quarantine_manager.list_quarantine_items()`/`get_quarantine_details()` already return, minus nothing and plus nothing — no route anywhere serves `.quarantine` payload bytes or a filesystem path to one (verified by an automated test that inspects the FastAPI route table for `download`/`payload`/`content` paths). Legacy/malformed records (`metadonnees_illisibles`, etc.) pass straight through with `None` fields, matching the existing normalization contract.

## 8. Protection integration

`api/services/protection_service.py` holds a single module-level `watcher.Protection()` instance, created lazily on first access, **never started automatically on import** (verified by a dedicated test: hitting `/health` and `/protection/status` never flips `active` to `True`). `/protection/start` and `/stop` wrap `Protection.demarrer()`/`.arreter()` unchanged. `/protection/status` reports the real `active` flag plus the configured `DOSSIERS` entries that currently exist on disk — the frontend never shows "Système protégé" unless the API actually reports `active: true` (previously hardcoded in the topbar; now fetched, verified via screenshot showing "Protection inactive" in amber when the watcher isn't running).

## 9. Dashboard metric definitions

Computed server-side in `api/services/dashboard_service.py` from `history.csv` + `quarantine/` + the watcher status — no separate datastore:

- `analyses_today` — history rows whose `date` falls on today's calendar date.
- `threats_detected` — history rows with `verdict == "malveillant"`.
- `quarantine_count` — total quarantine records (`null` if the directory couldn't be read).
- `total_analyzed` — total history rows.
- `protection_active` — the live watcher status.
- `verdict_breakdown` / `file_type_breakdown` — direct counts, family inferred from filename extension (history.csv has no family column).

**No "taux de détection" / ML accuracy metric exists anywhere** — `history.csv` carries no ground-truth labels, so no such number could be honest. The frontend's fourth dashboard KPI card was changed from the old mock's fabricated "Taux de détection" to a real "Protection" status card (Active/Inactive), matching the constraint verbatim.

## 10. Frontend integration

- `frontend/lib/api/client.ts` — single fetch wrapper (`credentials: "include"`, JSON/FormData handling, `ApiError`). Every adapter goes through it; no component calls `fetch` directly.
- `frontend/lib/api/mappers.ts` — the one place snake_case API JSON is translated into the existing camelCase domain types (`lib/types/backend.ts`). `analyze.py`'s `r["action"]` string (`"quarantaine : x"`, `"echec quarantaine : y"`, etc.) is parsed **once**, server-side (`api/services/analysis_service.py::parse_action`), into the same `QuarantineAction` discriminated union the frontend already modeled.
- `frontend/lib/auth/AuthProvider.tsx` — rewritten to call `GET /auth/me` on mount (session cookie only, zero client-side storage) instead of the Phase 1 mock's `sessionStorage` stand-in.
- `frontend/.env.local` — `NEXT_PUBLIC_HYBRIDSCAN_API_URL=http://localhost:8000` (the only place the API base URL is configured).
- Type adjustments for real-world data: `HistoryEntry.verdict`/`detectionSource` relaxed from strict unions to `string` (a legacy/malformed CSV row can carry an unrecognized value — it must stay visible, not fail type validation); `VerdictBadge`/`DetectionSourceBadge` now render an explicit "Erreur technique" / "Non disponible" state for values outside the known set, rather than silently mislabeling bad data as a real verdict. `AuthenticatedUser.role` was removed — `auth.py` has no role concept, and the old mock's `"Administrateur"` was fabricated.
- Mobile sidebar drawer added (`components/layout/Sidebar.tsx` + `Topbar.tsx` hamburger + `AppShell.tsx` state) — hamburger visible below `lg`, backdrop + slide-in panel, closes on navigation.

### Mock data removal

`frontend/lib/data/mock.ts` is **deleted**. `grep -r "lib/data/mock" frontend/` returns nothing. No production route depends on it. `frontend/lib/api/auth.ts`'s mock (accept-any-credentials) is deleted; login now calls `POST /api/v1/auth/login` for real and fails with a real 401 on bad credentials.

## 11. Development commands

```
# Backend engine + API (from the project root, the directory containing analyze.py)
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend
cd frontend
npm run dev            # http://localhost:3000

# Streamlit fallback (unchanged)
streamlit run app.py
```

`NEXT_PUBLIC_HYBRIDSCAN_API_URL` must share the frontend's hostname (both `localhost`, different ports) — see §4.

## 12. Tests

### New: `tests/test_api.py` (pytest + FastAPI `TestClient`, 27 tests)

Unlike the rest of `tests/` (standalone scripts with their own `run_all()`), this file uses genuine pytest fixtures — a natural fit for `TestClient`. Each test gets an isolated `HYBRIDSCAN_BASE_DIR` (`tmp_path`) with the **real** `model.pkl`/`model_pdf.pkl`/`model_docx.pkl` copied in (never the repo's own `history.csv`/`quarantine/`), plus `auth.py`'s `_USERS_FILE` monkeypatched into the same tmp dir (it's normally hardcoded next to `auth.py`, not `BASE`-relative — patched for test isolation only, `auth.py` itself is untouched). Run: `python -m pytest tests/test_api.py -v`.

Coverage: health (200, never analyzes), auth (invalid/valid login, `/me` 401→200, logout invalidation, all protected routes reject unauthenticated requests), analysis (real DOCX/fake-PE fixtures routed correctly, PE-renamed-`.docx` anti-spoofing preserved, unsupported extension rejected, hostile filename doesn't escape temp handling, temp files cleaned up), folder scan (allowed path, outside-root rejection, traversal rejection, recursive flag), history (real data after analysis, malformed row doesn't crash), quarantine (list/detail metadata-only, invalid id → 404, no payload route exists), protection (safe status, never auto-started), dashboard (reflects real analysis, no fabricated detection-rate field).

**Result: 27/27 passed.**

### Existing regression suite

All 7 files are standalone scripts (`python3 tests/test_X.py`, not pytest-collected — confirmed by inspecting their own `run_all()`/`__main__` blocks; an earlier `pytest tests/` invocation errors on a `tmp` fixture these scripts were never meant to receive that way). Run individually:

| File | Result |
|---|---|
| `test_docx_features.py` | 8/8 |
| `test_docx_model_integration.py` | 11/11 |
| `test_docx_regression.py` | 4/4 |
| `test_docx_security.py` | 6/6 |
| `test_docx_validate.py` | 11/11 |
| `test_folder_scan_config.py` | 7/7 |
| `test_quarantine_manager.py` | 21/21 |
| **Total** | **68/68** |

Run both before and after all backend changes in this phase — identical 68/68 pass in both runs.

### Streamlit smoke test

`streamlit.testing.v1.AppTest` driven against all 6 pages (`dashboard`, `analyse`, `historique`, `quarantaine`, `protection`, `parametres`) with a synthetic authenticated session — zero exceptions on any page, both before and after the `backend_shared.py` extraction.

### Frontend

`npm run lint` — 0 errors/warnings. `npm run build` — succeeds, all 8 routes compile and prerender.

### Playwright end-to-end (real browser, real API, real data)

Full flow driven against the actual running `uvicorn` + `next dev` processes, no mocks: register a real account → login → dashboard KPIs resolve to real numbers → refresh stays authenticated (cookie, not localStorage) → upload a real harmless PDF fixture through the real pipeline (genuine SHA-256 + verdict returned) → real folder scan against the configured allowed root → Historique shows the just-analyzed file → Quarantaine shows real records with zero payload-download links → Protection shows real (non-hardcoded) status → logout invalidates the session → a protected route visited afterward redirects back to `/login`. **16/16 checks passed.**

Two real bugs were caught and fixed by this E2E pass (beyond the SameSite issue in §4): a React key collision in `RecentActivityTable` (two folder-scanned files with identical content legitimately share `sha256`+`date`, so the key needed an index tiebreaker), and the upload-temp-filename legibility issue described in §5.

## 13. Model integrity

SHA-256 recomputed after all changes — byte-identical to the phase-start baseline:

- `model.pkl`: `4c0f8b73382febd1ef17deb3d81e3c8fda48a36fd1e6f561080b8619fb30622f`
- `model_pdf.pkl`: `be1ade69e5acdc130478dac6dbe904fa557eb53a93bdfa9140fc9097a9b3a8bc`
- `model_docx.pkl`: `7ef9f2702af4e7fa28bbf61eb9a88cb08f698ab3e64d7bb6e95c6a3a50f9dde9`

`analyze.py`, `auth.py`, `quarantine_manager.py`, `watcher.py` — also byte-identical to baseline (untouched). Only `app.py` changed (the documented helper extraction in §1).

## 14. Remaining limitations

1. **Sessions are in-process memory** — restart the API and every user is logged out. Acceptable for this phase; a real deployment would need a shared session store (Redis, DB-backed, or signed stateless tokens) if run with multiple workers.
2. **No registration UI** — `POST /auth/register` works (it's the same `auth.register()` Streamlit's "Créer un compte" tab already used) but the Next.js login page has no signup form; this phase's E2E tests seed accounts via a direct API call. Adding a signup tab mirroring Streamlit's is a small follow-up.
3. **Protection start/stop has no frontend UI** — the API supports it (`POST /protection/start|stop`), and `/protection` reads real status, but no button was wired up yet; the page remains read-only from the browser (starting a real filesystem watcher from a button click deserved explicit user sign-off beyond this phase's scope).
4. ~~**Folder-scan scope is still `.exe`/`.dll` only**~~ — **outdated as of 2026-08-19**: folder scan now also covers `.pdf`/`.docx` through the same `analyser()` pipeline as single-file analysis (`backend_shared.EXTENSIONS_SCAN_DOSSIER`, the shared source of truth for both Streamlit and this API). Accurate as written at the time this document described (items 1–3, 5, 6 below are still current).
5. **Global search stays visual-only** — no backend search endpoint was requested or built; the topbar field is explicitly a placeholder.
6. A stray orphaned Python multiprocessing child process was found holding the API's dev port across a `taskkill` during this phase's testing (a local Windows/dev-environment quirk, not an application bug) — noted here only because it caused a confusing stale-code symptom during E2E testing before being tracked down; not something `api/main.py` itself does or needs to guard against.
