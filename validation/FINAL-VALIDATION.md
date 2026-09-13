# Final Validation Report — HybridScan

Phase: complete final global review, after all six page-redesign slices were approved.

## 1. Environment

- OS: Windows 10 Pro (build 19045), accessed via a Git Bash / PowerShell shell.
- Python 3.14.3. Key installed packages actually imported by the app (no lockfile/`requirements.txt`
  exists in this repo, confirmed absent again in this phase): `streamlit 1.61.1`, `pandas 3.0.5`,
  `pefile 2024.8.26`, `shap 0.52.0`, `scikit-learn 1.9.0`, `requests 2.34.2`, `watchdog` (version
  not exposed by the package).
- **Playwright** (`playwright`, Chromium build) installed via `pip install playwright` +
  `python3 -m playwright install chromium`, strictly as **isolated, dev-only validation tooling**:
  not imported anywhere in `app.py`/`style.py`/`analyze.py`/`explain.py`/`watcher.py` (confirmed by
  grep), not added to any dependency manifest (none exists to add it to), used only from standalone
  scratch scripts outside the repository to drive a real Chromium instance against a locally running
  `streamlit run` process.
- Real project directory: `c:\Users\tmt\Desktop\project_pfa\pfe`. Git repository root is actually
  the user's home directory (`C:\Users\tmt`), confirmed via `git rev-parse --show-toplevel` — `pfe/`
  is a subdirectory within a much larger, uncommitted repository, not its own repo root. Zero
  commits exist anywhere in that repository at any point in this engagement.
- An isolated synthetic environment (`HYBRIDSCAN_BASE_DIR` pointing at a temp directory containing
  a copy of the real `model.pkl`, a synthetic `history.csv` covering all verdict/source/quarantine
  combinations including one deliberately-unrecognized verdict value, and a synthetic `quarantine/`
  directory covering all five record-consistency states) was used for all browser-based visual and
  functional testing, so that the real project's `history.csv` and `quarantine/` directory were
  never at risk during interactive testing.

## 2. Commands executed

| Command | Purpose | Result |
|---|---|---|
| `python3 -m py_compile app.py style.py analyze.py explain.py watcher.py auth.py vt_check.py` | Syntax validation of every active Python file | OK, no errors |
| `python3 -m compileall -q . -x "__pycache__"` | Whole-repository byte-compile check | exit 0 |
| `streamlit run app.py --server.headless true --server.port <N>` (several dedicated validation ports used across the session) | Boot the app | Started clean every time, no traceback in server logs |
| `curl -s -o ... -w "HTTP %{http_code}"` against the running app | HTTP health check | `HTTP 200` every time, including the final check against the real (non-isolated) project directory |
| `grep -rln "<former plaintext VT key>" .` (excluding `__pycache__`) | Repository-wide secret search | Only `.streamlit/secrets.toml` (confirmed gitignored) |
| `git check-ignore -v .streamlit/secrets.toml` | Confirm the secrets file is actually ignored | Matched `pfe/.gitignore:2`, exit 0 (ignored) |
| `grep` sweep for `/home/`, `C:\Users\`, `chemin_origine`, `st.json(meta`, raw `action` display, `st.exception`/`traceback.` | Path/secret/raw-dump leak search across `app.py`/`style.py`/`analyze.py`/`explain.py`/`watcher.py`/`auth.py` | Zero true leaks (the one `/home/` hit is a generic illustrative placeholder string in the Scan de dossier input, not a real path) |
| `sha256sum model.pkl history.csv analyze.py watcher.py explain.py` (before and after the entire test pass) | Data-integrity checksums | Identical before/after (§9) |
| `git status --short` | Repository status | `?? ./` (whole tree untracked, unchanged in shape throughout) |
| Playwright scripts (screenshots, DOM/network inspection, watcher lifecycle, end-to-end Analyse run) | Real-browser verification | See §5–§8 below |

No TypeScript validation, ESLint, Next.js build, frontend test suite, or CI was run or claimed —
none of these tools exist in this repository. **No automated unit-test suite exists for this
project**; all functional verification in this report and throughout the engagement was performed
via targeted isolated-environment Python scripts and, in this final phase, real browser sessions.

## 3. Pages tested

All six: Tableau de bord, Analyser un fichier, Historique des analyses, Quarantaine, Protection,
Scanner un dossier.

## 4. Viewports tested

1440×900, 1024×768, 768×1024, 390×844 — real Chromium renders (not simulated), full-page
screenshots captured for every page at every viewport. Index in §12.

## 5. Functional scenarios (final consolidated pass)

Each of the six pages had 15–26 scenario-level tests already executed and documented in its own
redesign-slice report (isolated `HYBRIDSCAN_BASE_DIR`, synthetic data, never touching the real
project files) — those results still hold, since no logic in `analyze.py`/`explain.py`/`watcher.py`
changed after those slices, and `app.py`'s changes in this final phase were limited to the
already-described dead-code/contrast fixes. This phase added:

- **Real end-to-end Analyse run**, driven by an actual browser: uploaded a genuine copy of
  `notepad.exe`, clicked "Lancer l'analyse", and confirmed a real, live VirusTotal signature match
  rendered correctly (`SAIN`, "Fichier connu de VirusTotal, aucune détection (75 moteurs).",
  "Conclu par : étape 1 (signature)") with the file-selected summary cards, enabled submit button,
  and result banner all rendering as designed. Screenshot: `analyse-1440-resultat.png`.
- **Watcher lifecycle**, driven by an actual browser (§7).
- Visual confirmation, via screenshots, of previously-tested-but-not-visually-verified states:
  Historique/Quarantaine data-quality warnings rendering with real synthetic incoherent records,
  Dashboard's detection-source bars and recent-analyses list with a realistic 13-row dataset,
  Protection's pipeline/capability/limitation sections, Scan de dossier's disabled/enabled button
  states and placeholder-only (non-resolved-path) input field.

## 6. Accessibility results

Practical, not certified (no formal WCAG audit tool was run — none is installed, and none was
represented as available):

| Check | Result |
|---|---|
| One `<h1>` per page | Confirmed — each destination renders its own `_TITRES`-driven heading |
| Visible upload/directory-input labels | Confirmed (`"Choisir un fichier à analyser"`, `"Chemin du dossier à analyser"`) |
| Explicit filter labels | Confirmed on Historique/Quarantaine (no `label_visibility="collapsed"` remains on any filter) |
| Keyboard-visible focus | `*:focus-visible { outline: 2px solid var(--focus) }` present and not overridden anywhere found in `style.py` |
| Text + color for every status | Confirmed — every verdict/quarantine/record badge pairs a text label with its color, never color alone |
| Reduced motion | `@media (prefers-reduced-motion: reduce)` present, unchanged since the stabilization slice |
| Long content wrapping | Confirmed visually at 390px: filenames, hashes, and step/row detail text all wrap rather than overflow |
| Charts with textual values | Dashboard's detection-source bars show label + count + percentage as text alongside the bar; the 14-day activity chart has an accompanying text summary sentence |
| Disabled controls remain legible | Confirmed visually ("Lancer l'analyse"/"Lancer le scan" both render distinctly in their disabled vs. enabled state, per the Analyse before/after screenshots) |
| Icon-only meaning | None found — every icon-bearing control (file drop zone, sidebar collapse) also has adjacent or native text |

**Not verified**: actual screen-reader output, 200% zoom/reflow, or keyboard-only tab-order
end-to-end — these require assistive-technology testing this review did not have the tooling for.
Stated as a limitation, not claimed as passing.

## 7. Watcher lifecycle validation (real browser)

| Step | Result |
|---|---|
| 1. Open Protection | "Surveillance non activée" shown (correct initial state) |
| 2. Click "Activer" | "Surveillance activée pour cette session." shown; a real `watchdog.PollingObserver` thread started in-process |
| 3. Trigger a normal rerun (click "Rafraîchir", unrelated to the watcher controls) | Still shows active — `st.session_state.protection` was **not** recreated |
| 4–5. Navigate away to Dashboard, then back to Protection | Still shows active — same instance persists across destination changes |
| 6. Click "Désactiver" | Returns to "Surveillance non activée." — `observer.stop()`/`.join()` completed |

**Conclusion: no lifecycle bug exists.** The existing `if "protection" not in st.session_state:`
guard is correct and sufficient; Streamlit's session state genuinely persists the same object
across reruns and navigation within a session, exactly as the code already assumed. No `watcher.py`
or `app.py` logic change was needed or made as a result of this test.

## 8. Security validation

- Repository-wide grep for the former plaintext VirusTotal key: found only in the gitignored
  `.streamlit/secrets.toml`.
- `.streamlit/secrets.toml.example` contains only `VT_API_KEY = "REPLACE_WITH_YOUR_VIRUSTOTAL_API_KEY"`.
- `SECURITY-NOTE.md` contains zero occurrences of the real key value.
- `.gitignore` correctly lists `.streamlit/secrets.toml`; `git check-ignore -v` confirms it matches.
- No `st.json(meta)`/raw metadata dump, no raw `action` display outside `etat_quarantaine()`, no
  `chemin_origine` reference, no `st.exception`/`traceback.` call, and no debug `print()` found
  anywhere in `app.py`.
- Confirmed via the real end-to-end Analyse browser run: the rendered page text contained none of
  the former key value, no `C:\Users\tmt`, and no "Traceback" substring.
- Confirmed no page load performs a VirusTotal request, ML inference, or quarantine-directory
  creation as a side effect of merely opening it (`charger_quarantaine()` uses `.is_dir()` only;
  `charger_historique()` uses `.exists()` only; the real `quarantine/` directory remained absent
  throughout every boot and every browser session in this final phase).
- Scan de dossier boundary re-verified: root-like paths, the real quarantine directory, and the
  `.streamlit` config directory are all rejected by `_cible_interdite()` with a generic message;
  the resolved path is never echoed back in any error or result.

**Confirmed unresolved, classified as instructed — see §18.**

## 9. Data-integrity validation

SHA-256 checksums, computed immediately before this final-review phase began and again after every
test in it completed:

| File | Before | After | Match |
|---|---|---|---|
| `model.pkl` | `4c0f8b73...30622f` | `4c0f8b73...30622f` | ✅ identical |
| `history.csv` | `bdbf1dea...58277b` | `bdbf1dea...58277b` | ✅ identical |
| `analyze.py` | `7b0fff24...ad4066` | `7b0fff24...ad4066` | ✅ identical |
| `watcher.py` | `48dc8b11...8aabea7` | `48dc8b11...8aabea7` | ✅ identical |
| `explain.py` | `1ea778c2...da77fb3dd` | `1ea778c2...da77fb3dd` | ✅ identical |

Real `quarantine/` directory: absent before, absent after — never created by any read-only page
visit or by the real end-to-end Analyse run (which used `isoler=` per the checkbox state and, since
the test file was classified `sain`, never triggered a real quarantine event). Dashboard's counts
were verified to equal the real `history.csv`'s actual row-derived totals (49 real rows outside the
isolated test: 26 malveillant / 18 sain / 5 indéterminé / 6 quarantined, all summing correctly).

## 10. Design-system documentation updated

`design-system/malware-detection/AUDIT.md`, `MASTER.md`, `PAGE-SPECIFICATIONS.md`, and
`IMPLEMENTATION-PLAN.md` were each updated with a "Final review addendum" recording completed
slices, the two bugs found and fixed in this phase, the watcher-lifecycle confirmation, and the
production-security-blocker classification.

## 11. Code-quality cleanup performed this phase

- Removed the unused `couleur()` wrapper function from `app.py` (confirmed zero call sites; all
  live code already calls `info_verdict(...)["couleur"]` directly).
- Removed the dead `.hash`/`.hash b` CSS rule from `style.py` (confirmed zero usages — superseded
  by `hash_display()`/`st.code()` since the Analyse-page redesign slice).
- Fixed a missing-accent typo in the Historique page's subtitle (`"effectuees et journalisees"` →
  `"effectuées et journalisées."`).
- Fixed `carte()`'s default text color (`#E4E9EF` → `var(--txt)`) — see §14 for why this mattered.
- Fixed the expander-icon/font-family regression — see §14.
- No broad rewrite performed; `app_ok.py`, `app.py.bak*`, and the old `style_*` variants were left
  untouched, per standing instruction — flagged again as a future maintenance cleanup candidate.

## 12. Screenshots produced

All under `validation/screenshots/`:

`dashboard-1440.png`, `dashboard-1024.png`, `dashboard-768.png`, `dashboard-390.png`,
`analyse-1440.png`, `analyse-1024.png`, `analyse-768.png`, `analyse-390.png`,
`analyse-1440-resultat.png` (real end-to-end result state),
`historique-1440.png`, `historique-1024.png`, `historique-768.png`, `historique-390.png`,
`quarantaine-1440.png`, `quarantaine-1024.png`, `quarantaine-768.png`, `quarantaine-390.png`,
`scan-dossier-1440.png`, `scan-dossier-1024.png`, `scan-dossier-768.png`, `scan-dossier-390.png`,
`protection-1440.png`, `protection-1024.png`, `protection-768.png`, `protection-390.png`,
`protection-watcher-lifecycle.png` (post-deactivation state).

No secrets or absolute local paths appear in any screenshot — all were captured against the
isolated synthetic environment (except the real end-to-end Analyse result, which was checked
programmatically for leaks before being kept).

## 13. Failures encountered during this phase (and how they were resolved)

1. An early screenshot run showed a raw `"keyboard_double_..."` ligature string in the sidebar on
   the very first page load only — this self-resolved on later pages within the same run and was
   traced to the *same* underlying issue as item 2 below, not a separate transient network delay.
2. Expander summaries across Historique/Quarantaine rendered their toggle icon as literal text
   (`"arrow_down"`/`"keyboard_arrow_down"`) instead of a chevron glyph. Root-caused via DOM
   inspection (`data-testid="stIconMaterial"`) and a network-log check (the icon font itself loaded
   successfully — `MaterialSymbols-Rounded.woff2`, HTTP 200 — ruling out a network/CDN cause) to a
   CSS rule in `style.py` forcing `font-family:'Inter' !important` onto every `<span>`/`<div>`,
   including native icon elements. Fixed (see §11, and `MASTER.md`'s addendum for the fix pattern
   and a specificity pitfall caught mid-fix before it shipped).
3. `carte()`'s neutral value-text color was unreadable (1.22:1 contrast) against the light
   workspace — a leftover from the pre-redesign dark theme never updated. Fixed.

No other failures. No test was skipped or reported as passing without being run.

## 14. Remaining limitations

- No formal WCAG conformance tool was run; accessibility results above are a practical review, not
  a certification.
- No screen-reader or keyboard-only end-to-end pass was performed.
- Symbolic-link scan behavior (Scan de dossier) was not experimentally reproduced in this sandbox
  (Windows privilege restrictions); confirmed unchanged by code inspection only.
- `app_ok.py`/`app.py.bak*`/old `style_*` variants remain in the repository, unused but present —
  a maintenance cleanup, not a functional risk.
- This repository has zero git commits at any point in the engagement; "before/after diff" in every
  report in this project (including this one) has necessarily been a manual change summary, not a
  real `git diff`.

## 15. Unresolved blockers

See §18 below (Production blockers) — carried here for completeness of this checklist: (1)
unauthenticated access to a page that can trigger real analysis/quarantine on arbitrary
server-readable directories; (2) the model-metrics reconciliation question from Decision #1 remains
open (no experimental metrics are shown anywhere as a direct, correct consequence).

## 16. Files modified during this final-review phase

- `app.py`: removed `couleur()`; fixed `carte()`'s default color; fixed the Historique subtitle
  accent typo. No page logic changed.
- `style.py`: removed dead `.hash`/`.hash b`; fixed the icon-font-clobbering rule (with the
  specificity-safe restoration pattern); removed the `summary > *` over-broad selector for
  expander-label styling (kept `summary p`).
- `design-system/malware-detection/AUDIT.md`, `MASTER.md`, `PAGE-SPECIFICATIONS.md`,
  `IMPLEMENTATION-PLAN.md`: final-review addenda appended (no prior content removed).

## 17. Files created during this final-review phase

- `validation/FINAL-VALIDATION.md` (this file).
- `validation/screenshots/*.png` (26 files, listed in §12).

## 18. Production blockers (see also the final report, §18)

1. **Unauthenticated arbitrary server-path scanning — Production security blocker.**
   `auth.py`/`users.json` implement a real salted-hash mechanism but are not called anywhere in
   `app.py` (confirmed by grep). Every page — including Scan de dossier, which can trigger real
   signature lookups, ML inference, and quarantine moves on any directory the server process can
   read — is reachable without any login. `_cible_interdite()` blocks three specific targets
   (filesystem root, the app's own quarantine directory, its `.streamlit` config directory) but
   is not a general-purpose access-control mechanism, nor was it ever meant to be one.
2. **Model-metrics reconciliation still open.** No experimental validation numbers (from either the
   830-sample repo data or the 20,000-sample EMBER claim) are shown anywhere in the application, as
   decided earlier in the engagement — this remains correct and unchanged, but it does mean the
   product still cannot show users any validated accuracy/recall/precision figure until the
   underlying model-provenance question is resolved by the project owner.

## Final recommendation

**Ready for controlled local use; not ready for production.** The frontend redesign itself is
complete, internally consistent, verified across real browser renders at four breakpoints, and free
of the security/path/secret leaks it set out to fix — including two additional real rendering bugs
found and fixed only because of this phase's browser-based verification. It should not be
represented as production-ready while (a) any user reachable to the app's URL can trigger analysis
and quarantine actions across arbitrary server-readable directories with no authentication gate,
and (b) the model's validation metrics remain unreconciled with the project report. Both are
pre-existing conditions this frontend-only engagement was explicitly not scoped to fix.

## Addendum — Production Hardening phase

Both blockers named above have since been addressed in a follow-on production-hardening phase: see
`validation/PRODUCTION-HARDENING.md`, `validation/MODEL-RECONCILIATION.md`, and
`validation/production-hardening-integrity.json` for full detail, evidence, and updated status.
