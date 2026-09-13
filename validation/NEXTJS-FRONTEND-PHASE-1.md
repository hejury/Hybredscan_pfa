# Next.js Frontend — Design Phase 1

## Location and stack

- Frontend directory: `frontend/` (new, sibling to the existing Python/Streamlit app — no Node files were mixed into the Python package).
- Next.js 16.3.1, App Router, TypeScript (strict mode), Tailwind CSS v4 (CSS-first `@theme`/`@theme inline` tokens, no `tailwind.config.js`).
- Fonts: `next/font/google` Inter (sans) + JetBrains Mono (technical values, e.g. hashes).
- Icons: `lucide-react`. Charts: `recharts` (donut only; bars are plain CSS).
- `clsx` for conditional class composition (`lib/utils.ts::cn`).
- No UI framework beyond hand-built primitives in `components/ui/` (no shadcn/ui import was needed).

## Routes (final)

| Route | Page | Default |
|---|---|---|
| `/` | Tableau de bord | Yes, post-login |
| `/analyse` | Analyse (file upload + folder scan, one page) | |
| `/historique` | Historique | |
| `/quarantaine` | Quarantaine | |
| `/protection` | Protection | |
| `/parametres` | Paramètres | |
| `/login` | Login (unauthenticated) | |

No `/scan-dossier` route exists. Folder scanning lives entirely inside `/analyse` as the right-hand panel.

Route group `app/(app)/` wraps all six authenticated routes with a shared `AppShell` (sidebar + topbar + auth gate); `app/login/page.tsx` is outside the group. The scaffolded default `app/page.tsx` was removed and replaced by `app/(app)/page.tsx` (the dashboard) to avoid a route collision.

## Sidebar / navigation

`lib/navigation.ts::NAV_ITEMS` is the single source of the menu, in the exact required order: Tableau de bord, Analyse, Historique, Quarantaine, Protection, Paramètres. No "Scan de dossier" entry. Verified at runtime (see below) that the rendered nav text matches this list exactly.

Sidebar bottom status card ("Système protégé" / "Toutes les défenses actives", or the inactive variant) is driven by `fetchProtectionStatus()` (`lib/api/protection.ts`), not hardcoded — it currently reads mock data but the component itself has no hardcoded copy of the state.

Logo: the existing `logo.png` from the project root was copied (not moved) into `frontend/public/logo.png`; original file at the project root is untouched.

## Design system

Tokens live in `app/globals.css` as CSS custom properties re-exposed through `@theme inline`, generating Tailwind utilities directly (`bg-canvas`, `bg-sidebar`, `bg-primary`, `rounded-md`, etc.):

- Canvas/surface: light gray canvas (`#F4F6FA`), white cards, subtle borders.
- Sidebar: dark navy-green (`#0B1B17`), NOT the main content background — main content is always light.
- Primary/action: emerald/teal (`#0D9488` / hover `#0F766E` / active `#115E59` / soft bg `#ECFDF5`), replacing an earlier blue-accented internal design-system draft that was never applied to Streamlit.
- Status colors: healthy green, malicious red, warning amber, info blue — each reused consistently across `Badge`, `VerdictBadge`, KPI cards, and chart legends, and every verdict is always paired with a text label ("Sain"/"Malveillant"/"Indéterminé"), never color alone.
- Radii (6/10/14/999px), two shadow levels (raised/overlay, no glow), spacing/typography scale reused from the prior Streamlit design-system draft (`design-system/malware-detection/MASTER.md`).

No dark mode / no `prefers-color-scheme` toggle for the main content — the dark sidebar is a fixed brand element, not a theme.

## Components

`components/ui/`: `Card`, `Button`, `Badge`, `Input`, `Checkbox`, `Select`, `Table` (+ `TableHead/Body/Row/Cell/EmptyState`).

`components/analysis/`: `VerdictBadge`, `DetectionSourceBadge`, `HashField` (with copy-to-clipboard), `AnalysisProgress` (pipeline stepper, steps adapted per file family — Identification → SHA-256 → VirusTotal → Analyse IA → Résultat — never inventing stages the backend doesn't run), `TechnicalDetails`, `AnalysisResultCard`, `FileUploadPanel`, `FolderScanPanel`, `AboutAnalysisCard`.

`components/dashboard/`: `KpiCard`, `VerdictDonut`, `FileTypeBars`, `RecentActivityTable`, `QuickActions`.

`components/quarantine/`: `QuarantineStatusBadge`, `QuarantineSummaryCards`, `QuarantineList`, `QuarantineDetail`.

`components/layout/`: `Sidebar`, `Topbar`, `AppShell`.

## Data layer: real vs. mocked

**No FastAPI/HTTP bridge was built or is required for this phase** — the Python backend architecture was not modified. All data currently flows through `lib/api/*.ts` typed adapter functions, each `async` and each carrying a doc comment naming the exact Python function/file it must call once a real endpoint exists:

| Adapter | Backs onto (real, future) |
|---|---|
| `lib/api/analysis.ts::submitFileForAnalysis` | `analyze.analyser(path, isoler, source_context=SOURCE_UPLOAD)` |
| `lib/api/folderScan.ts::fetchFolderScanConfig` / `launchFolderScan` | `app.py::_racines_autorisees()` / `valider_dossier_scan()` + looped `analyser(..., source_context=SOURCE_FOLDER_SCAN)` |
| `lib/api/history.ts::fetchHistory` | `history.csv` |
| `lib/api/quarantine.ts::fetchQuarantineList` / `fetchQuarantineDetails` | `quarantine_manager.list_quarantine_items` / `get_quarantine_details` (metadata only, never the `.quarantine` payload) |
| `lib/api/protection.ts::fetchProtectionStatus` / `fetchProtectionEvents` | `watcher.py` state / `detections_rt.json` |
| `lib/api/auth.ts::login` | `auth.py::verify_compte_configure` (explicitly NOT reproduced — accepts any non-empty credentials, loudly documented as a visual-phase stand-in) |
| `lib/api/dashboard.ts::fetchDashboardSummary` | no backend aggregation endpoint exists yet; KPIs/verdict/file-type breakdowns are computed client-side from `MOCK_HISTORY`/`MOCK_QUARANTINE` rather than invented as separate numbers |

All fabricated values live in exactly one file, `lib/data/mock.ts`, headed with an explicit "⚠️ MOCK DATA — NOT REAL BACKEND OUTPUT" warning. Every field in it matches the real shape defined in `lib/types/backend.ts`, which in turn traces every field to its Python source via inline comments.

**Login is mock-only and must not be mistaken for the real thing**: `lib/api/auth.ts` accepts any non-empty username/password. It does not reproduce or bypass `auth.py`'s real single-account, constant-time-comparison logic, and no real or fake credentials are exposed in the UI. This is the one place in the app that is a placeholder rather than a faithful (if data-mocked) representation of backend behavior, and it is documented as such at its call site.

## Analyse page specifics

- Left panel "Analyser un fichier": drag-and-drop + click-to-browse, accepts `.exe/.dll/.pdf/.docx/.doc` (from `SUPPORTED_EXTENSIONS`), rejects other types and oversized files (200 MB, the real Streamlit `st.file_uploader` default — no invented limit) client-side before calling the adapter. Shows the `AnalysisProgress` stepper while "analyzing," then the full `AnalysisResultCard`.
- Right panel "Scanner un dossier": path input pre-filled with the real configured allowed root (`fetchFolderScanConfig()`, mock-backed but shaped exactly like `FOLDER-SCAN-CONFIG.md`'s contract), explicit warning banner stating the scan only covers `.exe`/`.dll` and that PDF/DOCX require the file-upload panel instead, checkboxes "Inclure les sous-dossiers" / "Quarantaine automatique" preserving the existing backend meaning (recursive, auto-quarantine).
- Below both: "Résultats récents" (from `fetchHistory()`) with a "Voir tout" link to `/historique`, and "À propos de l'analyse" with only technically accurate claims (static analysis, not "sandboxed"; DOCX flagged as a research prototype, not production-certified).

## Quarantine page specifics

Metadata-only throughout — no download/open link to any `.quarantine` payload exists anywhere in the UI (verified at runtime, see below). Legacy/malformed records (`metadonnees_illisibles`, etc.) render safely with "Fichier non identifié" / em-dash placeholders instead of crashing or fabricating values. No Restore/Delete actions are present.

## Accessibility / responsiveness

- Verdicts always show icon + color + French text label, never color alone.
- All form inputs have associated `<label>` elements; icon-only buttons carry `aria-label`.
- Focus-visible rings on all interactive elements using the primary color.
- Sidebar is fixed on desktop (`lg:` breakpoint) and hidden below it (no collapsible mobile drawer was built this phase — flagged as a known limitation below); tables scroll horizontally inside their own container rather than overflowing the page.

## Quality checks

- `npm run lint` (ESLint via `eslint-config-next`): **0 errors, 0 warnings** on final state. One `react-hooks/set-state-in-effect` error was hit and fixed (see below).
- `npx tsc` (via `next build`'s TypeScript pass): **0 errors**.
- `npm run build`: **succeeds**, all 8 routes (`/`, `/_not-found`, `/analyse`, `/historique`, `/login`, `/parametres`, `/protection`, `/quarantaine`) compile and prerender as static content.

### Bug found and fixed during verification

An initial implementation of `AuthProvider` used `useSyncExternalStore` to read the session from `sessionStorage`, intended to avoid a lint-flagged `setState`-in-`useEffect` pattern. Runtime (Playwright) verification caught a real regression from this: navigating directly to `/analyse` (or any authenticated route) briefly bounced through `/login` back to `/` before settling, because the layout's redirect effect could observe the pre-hydration `null` snapshot before the corrected client value landed. Reverted to a plain `useState` + `useEffect` read of `sessionStorage` gated by an explicit `loading` flag (the redirect effect only fires once `loading` is `false`), which is the functionally correct pattern here. The one resulting lint rule (`react-hooks/set-state-in-effect`) is suppressed on that single line with an inline comment explaining why it's safe (one-time mount read of an external store, gated by `loading`).

## Runtime verification (dev server, Playwright-driven)

Dev server started on `localhost:3100`; verified with a Playwright script driving a real Chromium browser (not just `curl`), then removed after use. 15/15 checks passed:

- Unauthenticated `/` correctly redirects to `/login`.
- Login (mock, any non-empty credentials) redirects to `/`, and `/` renders the "Tableau de bord" heading — confirming it is the default post-login route.
- Sidebar nav text matches the exact required order (Tableau de bord, Analyse, Historique, Quarantaine, Protection, Paramètres) with no "Scan de dossier" entry anywhere.
- All 6 authenticated routes load without a Next.js crash/error page.
- `/analyse` renders both "Analyser un fichier" and "Scanner un dossier" panels.
- `/quarantaine` has zero `.quarantine`/download links.
- Zero browser console/page errors across the entire run.

Screenshots were additionally captured and visually reviewed (dashboard, analyse, quarantaine) to confirm the dark-sidebar/light-workspace/emerald-accent design renders as intended, verdict badges carry both color and text, and the donut chart / bar chart render correctly.

## Backend integrity

- Model files re-hashed before and after this phase — byte-identical:
  - `model.pkl`: `4c0f8b73382febd1ef17deb3d81e3c8fda48a36fd1e6f561080b8619fb30622f`
  - `model_pdf.pkl`: `be1ade69e5acdc130478dac6dbe904fa557eb53a93bdfa9140fc9097a9b3a8bc`
  - `model_docx.pkl`: `7ef9f2702af4e7fa28bbf61eb9a88cb08f698ab3e64d7bb6e95c6a3a50f9dde9`
- No Python file (`app.py`, `analyze.py`, `auth.py`, `quarantine_manager.py`, `watcher.py`, etc.) was edited or written to this phase — only read for reference. `history.csv` and `quarantine/` contents were only read, never modified.
- The Streamlit app (`app.py` and its dependencies) is untouched and remains runnable exactly as before; it is the fallback until this Next.js frontend is validated and a real API bridge is built.

## Known limitations / pending backend integration work

1. No FastAPI (or other HTTP) bridge exists yet. Every adapter in `lib/api/` is mock-backed; swapping to real `fetch()` calls is localized to those files (by design) but has not been done.
2. Login is not real authentication — it must be replaced with a call into (or a thin HTTP wrapper around) `auth.py::verify_compte_configure` before this frontend can be used for anything beyond internal review.
3. No mobile collapsible sidebar drawer was built — the sidebar is desktop-only (`lg:` breakpoint) for this phase; below that breakpoint the app has no navigation chrome yet.
4. The dashboard's KPIs/verdict/file-type breakdowns are computed from the single mock history array — once a real history/aggregation endpoint exists, `lib/api/dashboard.ts` is the only file that needs to change.
5. Search in the topbar is visual-only (no backend search exists) — clearly a placeholder, not wired to any fake results.
6. Protection/watcher data assumes periodic polling, not a live stream — the UI explicitly labels events as not real-time to avoid overclaiming.

---

**A. NEXT.JS FRONTEND DESIGN PHASE 1 COMPLETE**
