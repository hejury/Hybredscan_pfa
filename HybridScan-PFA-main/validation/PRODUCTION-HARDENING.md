# Production Hardening — HybridScan

Phase: authentication, action protection, folder-scan allowlist, secret rotation preparation, and
model-metrics forensic reconciliation, following the completed frontend redesign and final review.

## 1. Authentication implementation

**Contract discovered in `auth.py` before any change** (see full detail in this file's original
form): `register(username, password)`/`verify(username, password)` operate against `users.json`
(salted SHA-256 via `_hash_password(password, salt)`, salt generated with `secrets.token_hex(16)`).
No Streamlit integration existed at all — no session state, no logout, no wiring from `app.py`.
`users.json` already contained one real, previously-registered account (username present, only its
salted hash — not its plaintext password — is known). No hardcoded credential existed inside
`auth.py`'s source code itself.

**What was added** (auth.py): `verify_compte_configure(username, password)` — loads a single
configured admin account from `st.secrets["auth"]` (`username`, `password_hash`), falling back to
`HYBRIDSCAN_AUTH_USERNAME`/`HYBRIDSCAN_AUTH_PASSWORD_HASH` environment variables. `password_hash`
is parsed as `"<salt>$<sha256-hex>"` and verified by reusing the **existing** `_hash_password()`
function — no new hashing algorithm was introduced. Both the username and the computed hash are
compared using `hmac.compare_digest` (constant-time), so a timing side-channel cannot reveal which
of the two fields was wrong. Any missing/malformed configuration returns `False` unconditionally —
the system fails closed; there is no code path that authenticates a session from absent config.
`register()`, `verify()`, and `users.json` were left completely untouched and are simply no longer
called by `app.py` — nothing was deleted.

**What was added** (app.py): an authentication gate immediately after `st.set_page_config`/CSS load
and before the sidebar, `_pages`/`_TITRES` setup, or any `if _actif(...)` block. If
`st.session_state.authentifie` is not `True`, the app renders **only** the login form and calls
`st.stop()` — no further script execution occurs in that run, so no page code (upload handling,
folder enumeration, watcher instantiation, exports) ever executes pre-authentication. Session state
stores only two things: `authentifie` (bool) and `compte` (the username string) — the password is
never written to session state or logged.

## 2. Login page

French, restrained, reuses existing tokens/typography (`.hdr`/`.sub`, existing button/input styles)
— no new CSS was needed (confirmed via real screenshots, `validation/screenshots/login-*.png`).
H1 "Connexion à HybridScan", subtitle "Accédez à la plateforme d'analyse de fichiers.", labeled
Identifiant/Mot de passe fields (the latter `type="password"`, confirmed masked in the live DOM),
a note that this is a restricted local admin interface with no public registration, and a single
"Se connecter" primary action inside an `st.form` (so Enter submits — confirmed via the acceptance
test). On failure: exactly `"Identifiants incorrects."`, identical wording regardless of whether the
username or password was wrong, and the password field clears (`clear_on_submit=True`).

## 3. Logout and watcher behavior

A "Se déconnecter" button in the sidebar (visible only once authenticated, i.e. always in the
authenticated render path) does exactly this, in order: (1) checks `st.session_state.get("protection")`
and, if it exists and `.active`, calls its **existing** `arreter()` method — no `watcher.py` change;
(2) deletes every key from `st.session_state` (clearing `authentifie`, `compte`, the watcher
reference, navigation state, filters, pagination — a full reset); (3) reruns, landing back on the
login screen. Verified via a real browser session (`validation/screenshots` +
`test_watcher_auth_lifecycle.py`, see §9) that the watcher's real observer thread is stopped before
the session is cleared, and that logging back in starts from a clean, inactive watcher state with
no duplicate/orphaned observer.

## 4. Route and action protection

The auth check occurs before the sidebar is rendered at all, so unauthenticated users see no
navigation buttons, no page titles, and no page bodies — confirmed live (an unauthenticated page
load contains none of "Tableau de bord"/"Historique"/"Quarantaine"/"Scanner un dossier" anywhere in
the rendered text). Streamlit's `session_state` is server-side only (tied to the websocket session,
never exposed to browser-side storage/cookies/JS), so there is no client-side value a user could
edit to "manually change the destination" and bypass the gate — this is an architectural property of
Streamlit, not something this change had to defend against separately.

## 5. Folder-scan allowlist

Replaces the previous "any server-readable directory except three specific blocked targets" policy
with an explicit, administrator-configured allowlist:

- `HYBRIDSCAN_ALLOWED_SCAN_DIRS`, split on `os.pathsep` (never a hardcoded separator — `;` on
  Windows, `:` on POSIX, verified via `os.pathsep` in code).
- Each configured root is expanded (`~`), resolved canonically with `Path.resolve(strict=True)`, and
  silently dropped if it doesn't exist or isn't a directory — a bad entry never crashes the page, it
  is simply excluded (fail-safe, not fail-open).
- Containment is checked with `Path.relative_to()` on the fully-resolved (symlink-following) target
  path against each fully-resolved root — **not** string-prefix matching, so `C:\SafeBackup` is
  correctly rejected when only `C:\Safe` is configured (verified, §9).
- The pre-existing `_cible_interdite()` guards (filesystem root, the real quarantine directory, the
  `.streamlit` directory) are preserved and checked in addition to, not instead of, the allowlist.
- No configured/valid root at all → "Lancer le scan" is disabled, the directory input and both
  checkboxes are disabled, and `"Le scan de dossiers n'est pas configuré par l'administrateur."` is
  shown — fails closed, does not fall back to unrestricted access.
- A directory outside every allowed root → `"Ce dossier n'est pas autorisé pour l'analyse."` — the
  submitted path is never echoed back.
- A safe hint (`"Dossiers autorisés : <basenames only>"`) is shown so an operator knows roughly what
  is scannable without the full server path being displayed.
- No allowed directory is ever created automatically.

## 6. Allowlist security-test results

20 scenarios run against isolated temp directories (`validation/logs/` holds the redacted security
scan; full functional results are in the final report's test table). Summary: 17 PASS, 2 BLOCKED
(symlink creation requires elevated privileges not available in this Windows sandbox — code path
itself, using `Path.resolve(strict=True)` before containment check, correctly handles symlink
escapes by construction, but could not be experimentally exercised here), 1 NOT APPLICABLE
(POSIX-specific separator behavior — this validation machine is Windows). Zero FAILs.

## 7. VirusTotal key handling

Verified this phase: no real key exists in tracked source or documentation; `.streamlit/secrets.toml`
remains gitignored; `.streamlit/secrets.toml.example` contains placeholders only; the app works with
the key loaded from `st.secrets`; the app works with the key loaded from `VT_API_KEY` (which takes
precedence per `analyze.py`); a missing key triggers the existing `erreur_cle_absente` safe fallback;
no key appears in any log or UI text (confirmed via the redacted security scan and the real
end-to-end browser test's rendered-text assertions). **VirusTotal key rotation requires a manual
action by the project owner** — see `SECURITY-NOTE.md`'s checklist. This tool did not access the
user's VirusTotal account and does not claim the key was rotated.

## 8. Model-metrics reconciliation summary

See `validation/MODEL-RECONCILIATION.md` for the full forensic writeup. Headline finding: `model.pkl`'s
bundle contains two previously-unread keys, `seuil` (`0.45`, exactly matching the deployed threshold)
and `source` (`"EMBER-2018 (20000)"`) — direct, embedded, internally-consistent evidence pointing
toward the final EMBER experiment, **but not independently verifiable** (the current `train_model.py`
provably did not produce this exact artifact — its dump schema only has two keys — and no raw
EMBER-2018 corpus exists anywhere in this repository to cross-check). Confidence: **MODERATE**,
leaning toward the final-model hypothesis. Per this task's explicit instruction, **no metric is
added to the UI regardless of this finding** — a proposed model-manifest schema
(`validation/model-manifest.example.json`) is provided for a future, separately-approved step.

## 9. Test evidence index

- `validation/logs/production-security-scan.log` — redacted repository-wide secret/path/bypass scan.
- `validation/production-hardening-baseline.json` — pre-phase sanitized state.
- `validation/production-hardening-integrity.json` — post-phase checksum comparison.
- `validation/screenshots/login-{1440,1024,768,390}.png` — login page, all four viewports.
- `validation/screenshots/dashboard-authenticated-{1440,1024,768,390}.png` — authenticated app, all
  four viewports.
- `validation/screenshots/scan-allowlist-blocked-1440.png` — allowlist not configured (scan disabled).
- `validation/screenshots/scan-allowed-1440.png` — allowlist configured, an allowed directory entered,
  eligible files detected, submit enabled.
- `validation/screenshots/protection-authenticated-1440.png` — Protection page post-login, showing
  the "ADMIN — Se déconnecter" sidebar section.

## 10. Remaining production limitations

- Single shared admin account, no per-user roles — matches this task's explicit "do not build a new
  user-management system" boundary; not a multi-user access-control system.
- No account lockout/rate-limiting on repeated failed logins — `Identifiants incorrects.` is
  returned generically and quickly every time; a brute-force-throttling layer was not requested and
  was not added.
- The allowlist protects **which directories can be scanned**; it does not add authorization tiers
  within the app (any authenticated user can use every page, including Scan de dossier) — this
  matches "one configured admin account," not a permissions system.
- Model-metrics provenance remains at MODERATE confidence, not fully proven — metrics stay hidden.
