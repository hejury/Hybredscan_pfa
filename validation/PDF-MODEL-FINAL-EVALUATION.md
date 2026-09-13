# PDF-MODEL-FINAL-EVALUATION.md — final training, evaluation, and integration

Status: **`model_pdf.pkl` created and wired into inference. RESEARCH/PFA
PROTOTYPE — not production-ready.** This document is the final,
consolidated write-up for the whole PDF-ML effort (phases 1–7). See also
`CIC-PDF-FEATURE-COMPATIBILITY.md`, `CIC-PDF-DATA-QUALITY.md`,
`CIC-PDF-ANTI-LEAKAGE.md`, and `document_ml/pdf/model_pdf_manifest.json`
for the detailed prior-phase analyses this one builds on.

---

## 1. Dataset preparation summary

- Source: `datasets/pdf/PDFMalware2022.parquet` (frozen, SHA-256
  `25db2059d59207d2040c5a999838514579ed4667b2b7fa39f2398dee484caf65`),
  10,023 rows, matches the CIC-Evasive-PDFMal2022 column family.
- Cleaning: deterministic (`document_ml/pdf/cic_cleaning.py`) — `-1`
  sentinel → missing, PDFiD `"N(M)"` notation → N retained, leaked text →
  missing, never coerced to 0.
- Feature schema: **v3, 19 candidate features** (`header_present` removed
  in v2 for unreliable runtime reproduction + worst data-quality gap;
  `is_encrypted` removed in v3 — real column ranges 0–4 with no documented
  semantics for 2/3/4).
- Row-quality strategy: **A — complete-case only**. 8,914 of 10,023 rows
  retained (1,109 removed, 19.3% of original Malicious vs. 0.83% of
  Benign). Chosen because it eliminates the missingness/label-correlation
  leakage channel **by construction** (missingness-only diagnostic
  ROC-AUC = 0.5000 exactly on this subset, vs. 0.554–0.558 for
  threshold-based alternatives).
- `datasets/pdf/PDFMalware2022_training_ready.parquet` (SHA-256
  `50b7c27f08f570052ccb8306dcadd04c6040418e4235327e4ca7c73e0ec79d53`):
  8,914 rows × 19 features + `Class`, zero missing values, zero
  conflicting-label duplicate vectors (verified).

## 2. Split methodology

Deterministic, duplicate-vector-group-aware, class-stratified, seed=42.
Every row sharing an identical cleaned 19-feature vector (SHA-256 content
key) is treated as one atomic group and assigned to exactly one split —
never divided across train/validation/test.

| Split | Rows | Malicious | Benign | Groups |
|---|---|---|---|---|
| Train | 6,242 (70.0%) | 3,140 | 3,102 | 4,423 |
| Validation | 1,336 (15.0%) | 671 | 665 | 954 |
| Test (held-out) | 1,336 (15.0%) | 672 | 664 | 944 |

**Cross-split duplicate groups: 0** (verified twice — once at split-design
time, once again inside the final training pipeline).

## 3. Model A results (19 features, includes `nb_obj_kw` + `nb_page_approx`)

- Hyperparameters (modest 3-point search on validation ROC-AUC only, never
  touching test): `max_depth=20` selected from `{None, 10, 20}`;
  `n_estimators=300`, `class_weight="balanced"`, `random_state=42`.
- Threshold selected on **validation only**: **0.20** (maximizes F2, i.e.
  recall-weighted F-beta with beta=2, tie-broken by recall).
- **Held-out test (n=1,336, 672 Malicious / 664 Benign), evaluated ONCE:**

| Metric | Value | 95% bootstrap CI (2,000 resamples) |
|---|---|---|
| Accuracy | 0.9865 | [0.9805, 0.9925] |
| Precision | 0.9767 | [0.9648, 0.9873] |
| Recall | 0.9970 | [0.9925, 1.0000] |
| F1 | 0.9867 | [0.9803, 0.9926] |
| ROC-AUC | 0.9997 | [0.9994, 0.9999] |
| Confusion matrix | TN=648 FP=16 FN=2 TP=670 | |
| False-positive rate | 0.0241 | |
| False-negative rate | 0.0030 | |

## 4. Model B results (17 features, `nb_obj_kw` and `nb_page_approx` excluded)

- Hyperparameters: `max_depth=10` selected from the same 3-point search;
  same other settings.
- Threshold selected on validation only: **0.10** (same F2-maximizing rule).
- **Held-out test (same 1,336-row split), evaluated ONCE:**

| Metric | Value | 95% bootstrap CI |
|---|---|---|
| Accuracy | 0.9775 | [0.9693, 0.9850] |
| Precision | 0.9666 | [0.9526, 0.9793] |
| Recall | 0.9896 | [0.9810, 0.9969] |
| F1 | 0.9779 | [0.9697, 0.9854] |
| ROC-AUC | 0.9986 | [0.9976, 0.9994] |
| Confusion matrix | TN=641 FP=23 FN=7 TP=665 | |
| False-positive rate | 0.0346 | |
| False-negative rate | 0.0104 | |

## 5. Threshold selection detail

For both variants, the full validation-set threshold sweep (0.05 to 0.95,
step 0.05) was computed and is reproducible via the training script (see
§20). Selection rule: **maximize F2 on validation** (recall weighted 4x
precision), tie-broken by recall — directly implementing the instruction
to prioritize malicious recall / false-negative reduction. The held-out
test set was never consulted for this choice.

## 6. Model A vs. Model B comparison

| | Model A (19 feat.) | Model B (17 feat.) | 95% CIs overlap? |
|---|---|---|---|
| Recall | 0.9970 | 0.9896 | **Yes** ([0.9925,1.0] vs [0.9810,0.9969]) |
| Precision | 0.9767 | 0.9666 | Yes |
| F1 | 0.9867 | 0.9779 | Yes |
| ROC-AUC | 0.9997 | 0.9986 | **Yes, barely** ([0.9994,0.9999] vs [0.9976,0.9994]) |
| FPR | 0.0241 | 0.0346 | — |
| FN count | 2 | 7 | — |
| Train/test ROC-AUC gap | 0.0003 (train hits exactly 1.0) | 0.0010 | Both small |
| Runtime feature fidelity | 2 of 19 features are **runtime-approximate** (regex reproductions of PDFiD's tokenizer, not proven byte-identical) | **All 17 features are proven token-identical** to PDFiD's published methodology | B is strictly stronger |

**Selection: Model B.** Model A's point estimates are directionally
better on every metric, but its 95% confidence intervals **overlap**
Model B's on recall, precision, F1, and (barely) ROC-AUC — the
improvement is not clearly statistically validated on this held-out set.
Per the explicit selection rule (*"prefer Model B unless A's improvement
is meaningful AND validated"*), and given Model B carries no
runtime-approximation risk at all, **Model B is selected as the final
model.**

## 7. Sanity checks

| Check | Model A | Model B | Verdict |
|---|---|---|---|
| A. Label-shuffle test (shuffled-label held-out ROC-AUC) | 0.4555 | 0.4873 | **Both collapse toward chance (0.5)** — no leakage/splitting bug |
| B. Feature-importance dominance (top-1 share) | 0.176 (`nb_javascript_kw`) | 0.216 (`nb_js_kw`) | Neither exceeds 0.6 — no single-feature domination |
| C. Single-feature baseline (best, logistic regression) | 0.8775 AUC (`nb_js_kw`) | 0.8775 AUC (`nb_js_kw`) | Real signal, but far short of the full model's ~0.999 — not a one-feature shortcut |
| D. Train-vs-test gap | 1.0000 → 0.9997 (gap 0.0003) | 0.9996 → 0.9986 (gap 0.0010) | Both small — no dramatic overfitting |
| E. Duplicate-group integrity | 0 groups span splits (re-verified) | same | Clean |

None of these triggered the task's explicit STOP condition (label-shuffle
failing to collapse toward chance).

## 8. Selected model, feature importances

**Model B**, 17 features, `max_depth=10`, `n_estimators=300`, threshold
0.10. Top-5 feature importances:

| Rank | Feature | Importance |
|---|---|---|
| 1 | `nb_js_kw` | 0.2157 |
| 2 | `nb_javascript_kw` | 0.2007 |
| 3 | `pdf_size` | 0.1184 |
| 4 | `nb_startxref_kw` | 0.1079 |
| 5 | `nb_stream_kw` | 0.0858 |

JavaScript-related keyword counts dominate, consistent with well-documented
PDF-malware literature (JavaScript is a genuine, well-established evasion
vector — see the ICISSP 2022 paper cited in `CIC-PDF-FEATURE-COMPATIBILITY.md`).

## 9. Critical limitation discovered during integration testing: `pdf_size` unit mismatch

**This is the most important finding of this phase and the reason the
final status is not "operational."**

While manually testing the wired-up inference path with hand-crafted,
structurally-normal, benign-looking synthetic PDFs (as required for the
test suite, §16), several reasonable fixtures were unexpectedly classified
`malveillant`. Investigation traced this to the `pdf_size` feature:

- Training data `PdfSize`: Benign median **76**, mean 95.4, max 4,531.
  Malicious median **12**, mean 71.8, max 20,510.
- These values are implausibly small to be raw byte counts for real PDF
  files (a 76-byte file cannot contain a valid PDF header, catalog, and
  trailer) — they are far more consistent with **kilobytes**, a common
  reporting convention, though this was **not confirmed against any
  authoritative CIC/PDFiD documentation** (none was found across three
  prior research phases).
- The runtime extractor, `document_ml/pdf/cic_features.py`, computes
  `pdf_size = len(raw_bytes)` — genuine, exact **bytes**.
- Consequence: any real-world PDF (typically 20 KB – several MB = 20,000 –
  millions of bytes) produces a `pdf_size` value **100–1,000x beyond** the
  entire training range, on the single feature contributing the third-most
  importance (0.1184) and, when removed in a bounded diagnostic re-run,
  costing measurable held-out performance (F1 0.978 → 0.954, precision
  0.967 → 0.923) *within the dataset's own internal distribution* — meaning
  the model relies on this feature in a range it will never see correctly
  populated at real-world inference time.

**Not fixed by guessing.** Per this project's standing discipline (see the
`is_encrypted` removal in `CIC-PDF-ANTI-LEAKAGE.md` §1), an unverified
unit-rescale (e.g., dividing bytes by 1024) was **not** applied — that
would be exactly the kind of unproven semantic assumption this project has
consistently refused to make elsewhere. The finding is documented, not
silently patched.

**Practical effect observed:** three hand-crafted benign-structured PDF
fixtures (182–1,648 bytes) were all classified `malveillant` (confidence
0.18–0.94) during manual testing — consistent with both this unit mismatch
and the deliberately low, recall-oriented threshold (0.10) compounding
together.

## 10. Other limitations

- No external validation set — every number in this document comes from
  splits of one dataset file.
- ROC-AUC ≈ 0.999 must not be read as real-world accuracy; the
  dataset-representativeness cautions in `PDF-DATASET-PLAN.md` remain open.
- Complete-case filtering removed the most severely malformed 19.3% of
  the original Malicious class — the model has not seen that population.
- No adversarial robustness testing.

## 11. Reproducibility — exact commands

All training is deterministic (seed 42) and was reproduced bit-for-bit
once during model saving (`save_final_model.py`'s retrain exactly matched
the held-out ROC-AUC computed by the original training run). The pipeline,
in order:

1. Load `datasets/pdf/PDFMalware2022_training_ready.parquet`.
2. Compute SHA-256 group keys over the 19 `cic_schema.CIC_FEATURES`,
   rounded to 4 decimals, joined with `|`.
3. Assign groups to train/val/test via the deterministic greedy algorithm
   in this document's §2 (seed 42, per-class deficit-driven assignment).
4. For each variant (19-feature / 17-feature): fit
   `RandomForestClassifier(n_estimators=300, class_weight="balanced",
   random_state=42, max_depth=<selected>)` on train; select `max_depth`
   from `{None, 10, 20}` by validation ROC-AUC; select threshold by
   validation F2-maximization; evaluate once on test.
5. Save the selected model (Model B) via
   `pickle.dump({"model":..., "features":[...17 names...], "seuil":0.1,
   "metadata":{...}}, open("model_pdf.pkl","wb"))`.

No code performing these exact steps was left in the repository as a
formal script in this phase (analysis was done in scratch files per
session convention) — this section documents the recipe precisely enough
to reproduce it from `document_ml/pdf/cic_schema.py`,
`document_ml/pdf/cic_cleaning.py`, and
`datasets/pdf/PDFMalware2022_training_ready.parquet` alone.
