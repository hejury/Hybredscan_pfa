# Model Reconciliation — HybridScan

Read-only forensic reconciliation. No training was run, `model.pkl` was not replaced, and feature
extraction was not modified to produce this document.

## Evidence inspected

1. **`model.pkl` structure**, loaded directly via `pickle.load()`:
   - Bundle keys: `model`, `features`, `seuil`, `source` — **two more keys than previously
     inspected in any earlier phase of this engagement** (only `model`/`features` had ever been
     read, since that's all `analyze.py`'s `etape2_ia()` actually uses).
   - `bundle["seuil"] = 0.45` (float).
   - `bundle["source"] = "EMBER-2018 (20000)"` (string) — a direct, self-declared provenance label
     embedded in the artifact itself.
   - `model` is a `sklearn.ensemble.RandomForestClassifier`, `n_estimators=200`, `criterion="gini"`,
     `max_depth=None`, `random_state=42`, `n_features_in_=29`, `classes_=[0, 1]`.
   - `features`: exactly 29 names, identical to the list `analyze.extraire_features()` produces.
   - SHA-256 of `model.pkl`: `4c0f8b73382febd1ef17deb3d81e3c8fda48a36fd1e6f561080b8619fb30622f`.
2. **`train_model.py`** (currently checked into the repo): its `pickle.dump(...)` call writes
   **exactly two keys** — `{"model": clf, "features": list(X.columns)}`. No `seuil`, no `source`.
3. **`dataset.csv`**: 830 data rows (796 healthy / 34 malicious), read directly.
4. **`resultats_modeles.csv`** / **`resultats_seuil.csv`**: preliminary-experiment metrics computed
   against `dataset.csv` (Random Forest: recall 0.7524/precision 0.9667/AUC 0.9825 unthresholded;
   recall 0.7647/precision 0.963/F1 0.8525 at threshold 0.45).
5. **File timestamps** (supporting evidence only, not proof): `train_model.py` 2026-07-15 11:20;
   `resultats_modeles.csv`/`resultats_seuil.csv` 2026-07-17 10:xx; `dataset.csv` 2026-07-17 11:41;
   **`model.pkl` 2026-07-23 15:30** — six days after every preliminary-experiment artifact.
6. **Repository-wide search for "EMBER"** (case-insensitive): matches only in this project's own
   design-system documentation (written during this engagement, not independent evidence) and one
   false positive in `unzip_samples.py` (the substring "ember" inside the word "member" — not a
   real reference). **No raw EMBER-2018 corpus file, extraction, or download artifact exists
   anywhere in this repository.**
7. **`exp_seuil.py`/`exp_modeles.py`**: both use `StratifiedKFold` with `k = min(5, n_malicious // 2)`
   against `dataset.csv` — consistent with "stratified five-fold cross-validation" claimed for the
   preliminary experiment, not directly informative about the final EMBER run since no equivalent
   script for that run exists in this repo.
8. **`design-system/malware-detection/AUDIT.md`/`IMPLEMENTATION-PLAN.md`**: record the original
   Decision #1 conflict (preliminary 830-sample vs. final 20,000-sample EMBER claims) — background,
   not new evidence.

## Matching characteristics (support provenance B — the final EMBER experiment)

- `bundle["source"]` explicitly states `"EMBER-2018 (20000)"` — matching, word-for-word in intent,
  the project report's description of the final model (EMBER-2018 corpus, 20,000 samples).
- `bundle["seuil"] = 0.45` exactly matches the threshold hardcoded in `analyze.py`'s `SEUIL`
  constant — internally consistent, not a coincidental mismatch.
- `model.pkl`'s timestamp postdates every preliminary-experiment artifact by six days, consistent
  with a distinct, later training run.
- The bundle's richer schema (4 keys, including provenance fields) is consistent with a more
  mature/final training pipeline than the one currently checked into `train_model.py`.

## Conflicting / gap characteristics (prevent full, independent proof)

- **`train_model.py`, as it exists in this repository right now, cannot have produced this exact
  `model.pkl`** — its `pickle.dump` call only ever writes two keys, never `seuil`/`source`. The
  actual script that produced the deployed artifact is not present anywhere in this repository.
- **No raw EMBER-2018 corpus, extraction script output, or intermediate dataset file exists in this
  repository** to let a hash, sample count, or feature distribution be independently cross-checked
  against the `source` label's claim.
- **`dataset.csv` (830 rows) cannot be reconciled with "20000"** — confirming the deployed model was
  *not* trained from the dataset file currently sitting in this repo, which is expected if `source`
  is accurate, but also means there is no local, inspectable training data to verify against.
- The `source` field is a **self-declared string**, written by whoever ran that training script, at
  a point in time before this repository's current state. It is evidence of intent/labeling, not a
  cryptographic guarantee — a mislabeled or copy-pasted string cannot be distinguished from a
  correct one using only what's in this repository.

## Conclusion

**Closest to (B) — the final 20,000-sample EMBER-2018 experiment — but not independently
verifiable from repository contents alone.** This is a materially different, stronger position than
this engagement's earlier "inconclusive" assessment (made before `bundle["seuil"]`/`bundle["source"]`
had ever been read): a direct, internally-consistent, embedded provenance label now exists, and
nothing in the repository contradicts it. However, it falls short of independently-verified proof,
because the exact script and dataset that produced the artifact are absent from this repository and
cannot be cross-checked.

## Confidence level

**MODERATE**, leaning toward (B). Not LOW (there is real, specific, internally-consistent embedded
evidence — this is not "no provenance at all"). Not HIGH/conclusive (no hash-chain, signature, or
reproducible training script ties the artifact to a verifiable EMBER-2018 sample set).

## Exact next action required

1. The project owner should locate the actual training script/run that produced the current
   `model.pkl` (it is not in this repository) and check it in, so `bundle["seuil"]`/`bundle["source"]`
   can be reproduced and the true sample composition inspected.
2. Produce a signed model manifest (see `validation/model-manifest.example.json` for the proposed
   shape) that includes a hash of the exact training dataset used, so a future artifact swap can be
   verified rather than re-trusted on a string label alone.
3. Until such a manifest exists, **experimental metrics remain hidden from the UI**, per standing
   Decision #1 and this task's explicit instruction not to add metrics to the UI even if provenance
   were judged conclusive during this task. This is unchanged by today's finding — the finding
   strengthens the *evidence toward B*, it does not itself authorize showing any metric.
