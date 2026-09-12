# CIC-PDF-ANTI-LEAKAGE.md — anti-leakage review and final training-data design

Status: **review complete. No `model_pdf.pkl` created or persisted anywhere
in this phase.** All classifiers described below are diagnostic-only,
built in-memory during analysis scripts, and discarded immediately after
use — never pickled, never wired into `predict.py`.

This document supersedes nothing in `CIC-PDF-FEATURE-COMPATIBILITY.md` or
`CIC-PDF-DATA-QUALITY.md` — it builds on both, resolves the open
`is_encrypted` question left at the end of `CIC-PDF-DATA-QUALITY.md`, and
turns the "B: leakage risk requires review" status from the prior phase
into a concrete, tested data-preparation design.

---

## 1. `is_encrypted` resolution — REMOVED

Real-data inspection (`isEncrypted` column):

| Value | Row count |
|---|---|
| -1 (sentinel/missing) | 302 |
| 0 | 9,640 |
| 1 | 75 |
| 2 | 1 |
| 3 | 4 |
| 4 | 1 |

99.94% of valid values are 0 or 1 (i.e. it *looks* boolean at a glance),
but 6 rows carry 2/3/4 — and no official CIC or PDFiD documentation
anywhere found in this investigation (across all three prior phases)
defines what those values mean. Two further pieces of evidence rule out
guessing:

- **PDFiD's own base keyword list** (fetched and read directly from
  `pdfid.py`'s source — see `CIC-PDF-FEATURE-COMPATIBILITY.md` §3) tracks
  `/Encrypt` as a plain keyword **count**, not a boolean — consistent with
  the *separate* real column `Encrypt` (not part of this schema), not with
  `isEncrypted`.
- **`isEncrypted` and `Encrypt` disagree** on ~0.86% of rows where both are
  valid (cross-tab: 40 rows `isEncrypted=0` vs `Encrypt=1`; 24 rows the
  reverse; 15 more scattered) — they are not two redundant views of the
  same fact, which rules out simply "borrowing" `Encrypt`'s better-understood
  PDFiD semantics as a documented substitute for `isEncrypted`.

Per the task's explicit instruction — *"Proceed only if the 0..4 values can
be mapped to the runtime boolean with documented semantics. If exact
semantics cannot be proven: REMOVE ... Do not guess."* — **`is_encrypted`
is removed.** The runtime extractor (`cic_features.py`) no longer computes
it; `cic_schema.py` (now **v3**) no longer lists it.
`cic_cleaning.EXCLU_IS_ENCRYPTED_RAISON` documents this decision in code as
well as here.

**Final candidate feature count after this decision: 19** (was 20 in v2, 21
in v1).

---

## 2. Missingness-only diagnostic classifier — quantifying the leakage channel

A `RandomForestClassifier` (200 trees, `class_weight="balanced"`, seed 42)
was trained **exclusively** on a 19-column binary matrix — 1 if a feature's
cleaned value is missing/invalid, 0 if valid — never on the actual feature
values. 70/30 stratified train/test split. Not saved.

| Metric | Value |
|---|---|
| Accuracy | 0.5484 |
| Precision | 0.9640 |
| Recall | 0.1926 |
| F1 | 0.3210 |
| **ROC-AUC** | **0.5922** |
| Confusion matrix (test, n=3,007) | TN=1,328  FP=12  FN=1,346  TP=321 |

The precision/recall split is itself informative: at the default 0.5
threshold, this diagnostic almost never falsely flags a Benign PDF as
Malicious from missingness alone (FP=12), but it also only catches 19.3%
of Malicious rows this way (recall 0.1926) — consistent with the ROC-AUC
reading of "real but modest, not dominant" signal. A different threshold
would trade these differently, but the ROC-AUC (threshold-independent) is
the more meaningful summary number here.

**Interpretation:** 0.59 ROC-AUC is meaningfully above chance (0.5) but far
from a strong classifier — missingness patterns alone carry *real* but
*modest* information about the label. This is neither "no leakage risk"
nor "missingness alone solves the problem" — it's a genuine, quantified,
intermediate signal that must be kept out of any production feature
vector, which is exactly what `cic_schema.CIC_FEATURES` already guarantees
(no `extraction_failed`/`missing_field_count`-style column is ever
included — see `cic_cleaning.calculer_diagnostics`'s own docstring warning).

---

## 3. Row-quality threshold experiments (label-independent)

`observed_feature_ratio` computed **only** from feature availability across
the 19 candidate features — `Class` was never consulted to pick rows.

| Threshold | Rows retained | Malicious | Benign | % Malicious removed | % Benign removed | Dup. groups | Conflicting-label groups | Missingness-only ROC-AUC (on retained set) |
|---|---|---|---|---|---|---|---|---|
| ≥50% | 9,482 | 5,047 | 4,435 | 9.14% | 0.74% | 909 | 0 | 0.5575 |
| ≥70% | 9,469 | 5,034 | 4,435 | 9.38% | 0.74% | 908 | 0 | 0.5543 |
| ≥80% | 9,469 | 5,034 | 4,435 | 9.38% | 0.74% | 908 | 0 | 0.5543 |
| ≥90% | 9,465 | 5,030 | 4,435 | 9.45% | 0.74% | 908 | 0 | 0.5543 |
| =100% (complete case) | 8,914 | 4,483 | 4,431 | 19.30% | 0.83% | 850 | **0** | **0.5000 (exact chance)** |

**The distribution of `observed_feature_ratio` is strongly bimodal**, not a
smooth gradient: 8,914 rows sit at exactly 100%, 551 more at 90–99% (one
feature missing), a **near-empty band** of only 17 rows between 50–90%,
and 541 rows at ≤10% (the severe PDFiD-failure batch, only `pdf_size`
observed). This is why thresholds 50–90% are nearly indistinguishable in
row count and ROC-AUC — the real, data-driven dividing line sits between
roughly 30% and 90% observed, not at any specific human-chosen cut point.

**Only the 100% threshold drives the missingness-only diagnostic to exact
chance level (0.5000)** — a mathematical certainty, not an estimate: with
zero missingness variance left, a classifier trained on an all-zero
indicator matrix has no signal to exploit, by construction.

---

## 4. Duplicate-group issue and conflicting-label resolution

Using a **deterministic, order-independent grouping key** — SHA-256 of the
19 rounded feature values, computed the same way regardless of row order or
pandas internals (`cic_cleaning`-adjacent logic, see the analysis scripts
referenced in the final report) — the full dataset (19-feature schema) has:

- **966 duplicate-vector groups** (4,147 rows) — the same feature vector
  appearing 2+ times.
- **9 conflicting-label groups** (40 rows) — the same vector appearing
  under **both** `Malicious` and `Benign`.

**Investigated, not silently resolved:** every one of the 40
conflicting-label rows has `observed_feature_ratio = 1/19 ≈ 0.053` — i.e.
**only `pdf_size` is populated**, all 18 other features are missing. These
are not "two structurally similar files with different labels" — they are
near-total information voids that happen to collide because almost nothing
is left to distinguish them. Verified computationally (not assumed): 100%
of conflicting rows fall below both the 100% and even a lenient 50%
completeness bar.

**Resolution:** Strategy A (§5, complete-case) removes all 9
conflicting-label groups as a direct, verified side effect of its
label-independent completeness rule — confirmed by recomputing conflicting
groups on the Strategy-A-filtered set: **0 remain** (also reverified inside
the `training_ready` build script and the contract tests, §10 of the final
report). No group was excluded by inspecting its label; the rule that
excludes them never looks at `Class`.

Separately, among the **850 fully-populated duplicate groups** (0 missing
features, 3,439 of the 4,147 duplicate rows), **zero have conflicting
labels** — the 19-feature schema is internally consistent wherever it has
something to work with; the conflicts are entirely confined to the
severely-degenerate tail.

---

## 5. Strategy comparison (A / B / C)

All three trained a **diagnostic-only** `RandomForestClassifier` (200
trees, seed 42, 70/30 split) on the **actual (or train-median-imputed)
feature values** solely to compare against the missingness-only baseline
for the imputation-shortcut check (§6) — none of these were saved.

| | **A: complete-case** | **B: ≥90% observed + train-only median impute** | **C: ≥50% observed + train-only median impute** |
|---|---|---|---|
| Usable rows | 8,914 | 9,465 | 9,482 |
| Malicious / Benign | 4,483 / 4,431 (50.3%/49.7%) | 5,030 / 4,435 (53.1%/46.9%) | 5,047 / 4,435 (53.2%/46.8%) |
| Missing cells before impute | 0 | 551 (all from the 551 rows with exactly 1 of 19 features missing) | 676 (551 + 125 from the 17-row 50–90% band) |
| Missingness-only ROC-AUC | **0.5000 (exact chance)** | 0.5543 | 0.5575 |
| Value-classifier ROC-AUC (diagnostic) | 0.9993 | 0.9992 | 0.9993 |
| Duplicate-vector groups | 850 | 908 | 909 |
| Conflicting-label groups | **0** | 0 | 0 |
| Split feasibility | Trivial — no imputation, no leakage channel | Requires train-only median fit before every split | Same as B |

**Advantages / disadvantages:**

- **A (chosen — see §7):** Eliminates the missingness-leakage channel by
  *construction*, not by mitigation. Best class balance of the three.
  Simplest, most reproducible rule (no threshold to justify). No
  imputation risk at all (§6 is moot for this strategy). Downside: loses
  1,109 rows (11.1%), disproportionately from Malicious (19.3% of
  Malicious removed vs. 0.83% of Benign) — the class-balance side effect
  is actually favorable, but raw sample size is reduced.
- **B:** Retains more data (9,465 rows) at the cost of a real, measured
  residual missingness signal (0.554 AUC) and dependence on a threshold
  choice that, per §3, isn't strongly justified by the data's own
  bimodal structure (90% and 50% barely differ). Requires committing to
  a train-only imputation pipeline.
- **C:** Marginal gain over B (+17 rows) for the same leakage profile.
  Given the bimodal distribution (§3), B and C are nearly the same
  strategy in practice — the extra 17 rows aren't worth carrying a
  second, barely-distinct policy.

---

## 6. Imputation-shortcut diagnostic

For Strategies B and C, after fitting per-feature medians on the **train
split only** and applying them unchanged to test (verified via a unit-level
contract test, §10 of the final report — the median is computed strictly
from `X_train`, confirmed not to shift when `X_test` changes), a
diagnostic `RandomForestClassifier` was trained on the **imputed feature
values** and compared against the missingness-only baseline for the same
retained set:

| Strategy | Missingness-only AUC | Imputed-value AUC | Gap |
|---|---|---|---|
| B | 0.5543 | 0.9992 | +0.4449 |
| C | 0.5575 | 0.9993 | +0.4418 |

**Finding: the imputation-shortcut risk is NOT the dominant driver of
classifier performance.** If the value-classifier's performance were
mostly an artifact of "this feature equals exactly the imputed constant →
infer missingness → infer label," its AUC would sit close to the
missingness-only baseline (~0.55–0.56). Instead it sits dramatically
higher (~0.999), meaning the **actual, valid feature values** — not the
pattern of which cells got imputed — are driving the overwhelming majority
of the classifier's discriminative power. This is a **negative** (i.e.
reassuring) finding for the imputation-shortcut concern specifically, and
it is reported as measured, not softened.

**This number must not be read as a preview of final model accuracy.**
Section 12 of the task explicitly forbids reporting final
malware-classification performance at this stage, and there is a separate,
well-documented reason for caution independent of imputation: the ICISSP
2022 paper that introduced this dataset family (cited in
`CIC-PDF-FEATURE-COMPATIBILITY.md` §3) explicitly describes how the older
Contagio dataset produced deceptively high (>99%) accuracy due to
dataset-construction artifacts (e.g. 74% of its malicious samples sharing
just two trivially-detectable features), which is exactly why
Evasive-PDFMal2022 was built to be harder. A ~0.999 diagnostic AUC on this
dataset, even the "harder" version, does not retire that general
representativeness caution — it only answers the narrower
imputation-shortcut question asked in this section.

---

## 7. Final feature set and data-preparation strategy

**Final schema: `document_ml/pdf/cic_schema.py` v3, 19 features** (v2's 20
minus `is_encrypted`). Full per-feature documentation and
proven/caveated runtime-equivalence status is in `CIC_FEATURE_DOC` and
`CIC-PDF-FEATURE-COMPATIBILITY.md`.

**Final data-preparation strategy: A (complete-case).** Chosen per the
task's own evaluation criteria — *"information sufficiency; reduced
leakage; retained sample size; retained class balance; reproducible
label-independent rule"* — not because it scored best on any downstream
classification metric (§6 already establishes it wasn't even close;
B/C's imputed-value AUCs are statistically indistinguishable from A's).
Strategy A wins on every criterion except raw sample size, and even there
it retains 89% of the original data while producing the best class
balance of the three.

---

## 8. Remaining scientific limitations

- **Diagnostic AUCs (~0.999) should not be treated as an estimate of
  real-world deployment accuracy** — see §6's closing caution. No
  held-out, externally-sourced validation set has been used anywhere in
  this project; every number so far comes from splits of the same single
  dataset file.
- **Dataset representativeness concerns from `PDF-DATASET-PLAN.md` remain
  fully open** — this phase addressed *label leakage within this one
  dataset*, not whether the dataset itself represents real-world PDF
  malware distributions.
- **11.1% of the original data (concentrated in the Malicious class) is
  excluded** by the chosen strategy — a deliberate, documented trade-off,
  not a hidden cost.
- **`nb_obj_kw` and `nb_page_approx` remain runtime-caveated** (approximate
  regex reproduction of PDFiD's tokenizer, not byte-proven identical) even
  though they passed the data-quality bar — this is a *different* kind of
  uncertainty (extraction fidelity, not label leakage) that training on
  `PDFMalware2022_training_ready.parquet` does not resolve.
- **The 850 duplicate-vector groups (3,443 rows) in the training-ready
  file are legitimate** (0 conflicting labels), but mean the effective
  diversity of the training set is smaller than 8,914 independent samples
  — the deterministic group-aware split design (final report §13) exists
  specifically to stop this from becoming a train/test leakage problem,
  but it doesn't increase the data's intrinsic diversity.
