# Security note — VirusTotal API key

**Action required from the project owner (manual, not automated by this change):**

A VirusTotal API key was previously hardcoded in plaintext in `analyze.py` and `vt_check.py`.
As of this change it has been removed from both files and is no longer present in any tracked
application source file. It has been relocated to `.streamlit/secrets.toml`, which is now listed
in `.gitignore` and must never be committed.

This repository had zero git commits and no remote configured at the time this was found, so the
key was not exposed via version control. However, **the key was sitting in plaintext on disk for
an extended period and should be treated as potentially compromised as a precaution.**

**You should manually:**
1. Log into the VirusTotal account that issued this key.
2. Revoke/regenerate the API key.
3. Update the value in your local `.streamlit/secrets.toml` (or the `VT_API_KEY` environment
   variable) to the new key.

This tool did not attempt to revoke or rotate the key automatically, and the key's value is not
repeated anywhere in this document, in `design-system/`, or in any other file this change touched.

## How the key is loaded now

`analyze.py` and `vt_check.py` each resolve the key at import time, in this order:
1. the `VT_API_KEY` environment variable;
2. `st.secrets["VT_API_KEY"]` (i.e. `.streamlit/secrets.toml`), only when running under Streamlit.

If neither is available, `etape1_virustotal()` / `check()` return `{"statut": "erreur_cle_absente"}`
immediately — no network call is attempted, no exception is raised, and no secret or traceback is
shown to the user. The existing fallback behavior already in `analyze.py` (any non-`malveillant`/
non-`sain` VirusTotal status falls through to the static ML stage) applies unchanged, so a missing
key degrades to "static analysis only," not a crash or a false "healthy" result.

See `.streamlit/secrets.toml.example` for the expected local config shape (placeholder only).

---

## Manual VirusTotal key-rotation checklist (production-hardening phase)

**VirusTotal key rotation requires a manual action by the project owner.** This tool did not
access, rotate, or invalidate the key — only the checklist below is provided.

1. Revoke the previously exposed VirusTotal key from the VirusTotal account that issued it.
2. Generate a new key from that same account.
3. Replace the value in the local, gitignored secret store (`.streamlit/secrets.toml`'s
   `VT_API_KEY`, or the `VT_API_KEY` environment variable — the environment variable takes
   precedence when both are set, per `analyze.py:_charger_cle_vt()`).
4. Restart the Streamlit application so the new value is picked up (the key is only read once, at
   import time).
5. Execute a safe signature-lookup test (e.g. analyze a known-benign file on the Analyse page and
   confirm the result shows `"Détection par signature (VirusTotal)"` rather than falling back to
   `"Analyse statique par modèle"`).
6. Confirm the previous key no longer authenticates (e.g. temporarily restore the old value and
   confirm VirusTotal now returns an auth error, which the app already handles safely as
   `erreur_cle`/`erreur_quota`/`erreur_api` — falls back to the ML stage, never a crash) — then put
   the new key back.

This checklist was verified functionally during the production-hardening phase: the application was
confirmed to work correctly with the key loaded from `.streamlit/secrets.toml`, to work correctly
with the key loaded from the `VT_API_KEY` environment variable (which takes precedence), and to
degrade safely (no traceback, no secret shown, automatic ML fallback) when neither is configured.
No key value is repeated anywhere in this checklist.

## Administrator authentication (added in the production-hardening phase)

The application now requires login before any page renders (see `validation/PRODUCTION-HARDENING.md`
for full detail). Credentials are configured the same way as the VirusTotal key — via
`.streamlit/secrets.toml`'s `[auth]` section (`username`, `password_hash`) or the
`HYBRIDSCAN_AUTH_USERNAME`/`HYBRIDSCAN_AUTH_PASSWORD_HASH` environment variables — never hardcoded
in `auth.py` or any tracked file. `password_hash` reuses the pre-existing salted SHA-256 scheme
already implemented in `auth.py` (`salt$hash` format), not a new hashing scheme. No credential value
is repeated anywhere in this document, in `design-system/`, or in `validation/`.
