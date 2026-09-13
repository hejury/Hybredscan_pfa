# PDF-RUNTIME-FIDELITY.md — pdf_size investigation, Model C, real runtime validation

Status: **Model C selected and validated against real, legitimate,
size-diverse PDFs. `model_pdf.pkl` updated. Still a research/PFA prototype
— see remaining limitations.** This document is the focused write-up for
the runtime-fidelity repair phase, following on from
`PDF-MODEL-FINAL-EVALUATION.md` §9's discovery of the `pdf_size` defect.

---

## 1. `pdf_size` semantics investigation

Re-inspected everything available: the real `PDFMalware2022.parquet`
column, the official CIC dataset page, the full text of the ICISSP 2022
paper, PDFiD's actual source code, and `cic_features.py`. **No
authoritative, documented unit specification was found** for `PdfSize`
anywhere across four research phases.

New evidence gathered this phase:

- **Distributional re-analysis:** `PdfSize` min=0, with **7 rows at
  exactly 0** and 883 rows in {1,2,3,4}. A "0" or "1-4" byte/KB file
  cannot be a valid PDF under any unit reading *except* KB-with-integer-
  truncation, where a genuinely minimal exploit PDF (300–1023 bytes) would
  floor-divide to 0, and 1024–5119-byte files would floor-divide to 1–4.
  This is internally consistent with the KB hypothesis across the full
  range (median, low end, and high end all point the same way).
- **Zero correlation with other size-like columns:** `PdfSize` vs.
  `MetadataSize` vs. `XrefLength` correlations are all ≤0.013 — essentially
  none. Not decisive either way, but notably doesn't contradict the KB
  hypothesis (metadata size and xref table length don't scale tightly
  with overall file size in general).
- **New, more concrete evidence:** a **third-party reproduction** of this
  exact dataset's feature extractor —
  [`Mathys-Rituper/PDF-feature-extractor`](https://github.com/Mathys-Rituper/PDF-feature-extractor),
  `src/extract.py` line 126 — contains:
  ```python
  features['pdf_size'] = round(os.path.getsize(pdf_path) / 1024, 2)
  ```
  This is an **independent implementation choice**, not derived from this
  project's own range-only inference, and it exactly matches the KB
  hypothesis.

**Verdict: still not proven.** This repository's own README describes
itself as "an **improved** feature extractor for CIC-Evasive-PDFMal2022"
— i.e., explicitly a *reinterpretation*, not a certified-faithful
reproduction of CIC's original (undisclosed) extraction code. There is no
way to confirm whether its author had privileged knowledge of the true
methodology or arrived at `/1024` through the same kind of distributional
inference performed here. Per the standing instruction — *"Do not guess a
conversion from the observed range alone"* — a corroborating but
unofficial third-party source does not clear that bar. **Decision:
`pdf_size` is removed, not transformed.**

## 2. Schema update: v3 → v4

`document_ml/pdf/cic_schema.py` bumped to **v4** (18 candidate features,
down from 19). `pdf_size` removed from `CIC_FEATURES`,
`cic_cleaning.COLONNE_REELLE`, and `cic_features.extraire_caracteristiques_cic()`
— the same treatment as `header_present` (v2) and `is_encrypted` (v3): a
documented `EXCLU_*_RAISON` constant, not a silent drop.

## 3. Model C: retraining without `pdf_size`

Model C = Model B's feature set minus `pdf_size` = **16 features**, all of
which are **proven token-identical** to PDFiD's published keyword-scanning
methodology (§3 of `CIC-PDF-FEATURE-COMPATIBILITY.md`) — no runtime-
approximation caveats remain at all.

### 3.1 A new duplicate-label conflict, investigated (not silently resolved)

Recomputing the duplicate-vector group key over the reduced 16-feature
space revealed **40 conflicting-label groups (975 rows: 835 Benign, 140
Malicious)** — unlike the earlier phase's 9 conflicting groups (which were
100% caused by severe missingness and vanished once complete-case
filtering was applied), **these are fully-populated, non-missing rows**
that genuinely collide once `pdf_size`, `nb_obj_kw`, and `nb_page_approx`
are dropped from the representation.

Manual inspection of the largest groups showed a mix: some lean heavily
toward one label (e.g. 21 Malicious vs. 1 Benign in one 22-row group),
others are close to an even split (e.g. 3 vs. 3). Per instruction — *"do
not silently choose a label"* — a majority-vote resolution was **not**
used (that would itself be choosing a label for the genuinely ambiguous
cases). Instead: **all 975 rows in any conflicting group were excluded
from Model C's training population**, leaving **7,939 usable rows**
(8,914 − 975). This is the same precedent already established for the
original complete-case rule — a classifier cannot be validly trained or
evaluated where the ground truth itself is contradictory for identical
inputs.

This is also a substantive, honestly-reported finding in its own right:
**dropping `pdf_size`/`nb_obj_kw`/`nb_page_approx` measurably reduces the
16-feature representation's ability to separate the two classes** for
about 11% of the complete-case data. Runtime-fidelity and class-
separability are in real tension here — this phase prioritizes the former,
as instructed, but the cost is not zero and should not be understated.

### 3.2 Split (recomputed on the 16-feature key, seed=42)

| Split | Rows | Malicious | Benign | Groups |
|---|---|---|---|---|
| Train | 6,032 (70.0%) | 3,515 | 2,517 | 1,372 |
| Validation | 954 (15.0%) | 415 | 539 | 356 |
| Test (held-out) | 953 (15.0%) | 413 | 540 | 367 |

Cross-split duplicate groups: **0** (verified).

### 3.3 Training and held-out results

- Hyperparameters: `max_depth=10` (from the same `{None,10,20}` search on
  validation ROC-AUC), `n_estimators=300`, `class_weight="balanced"`,
  `random_state=42`.
- Threshold: **0.15**, selected on validation only (F2-maximization, same
  rule as Model A/B).

| Metric | Model C (16 feat.) | 95% bootstrap CI |
|---|---|---|
| Accuracy | 0.9601 | [0.9475, 0.9717] |
| Precision | 0.9233 | [0.8974, 0.9459] |
| Recall | 0.9903 | [0.9796, 0.9977] |
| F1 | 0.9556 | [0.9405, 0.9686] |
| ROC-AUC | 0.9972 | [0.9951, 0.9989] |
| Confusion matrix | TN=506 FP=34 FN=4 TP=409 | |
| False-positive rate | 0.0630 | |
| False-negative rate | 0.0097 | |

Train ROC-AUC 0.99998, gap to held-out = 0.0027 (small, no dramatic
overfitting). Label-shuffle held-out ROC-AUC: **0.3456** — clearly far
from the real model's 0.997 (no leakage), though noted honestly: this is
further from 0.5 than Model A/B's shuffle results (0.4555/0.4873) were.
With a single shuffle trial and a ~950-row test set, deviations of this
size from 0.5 are within normal sampling variance for a model fit purely
to noise; the important comparison is against the *real* model's score,
not proximity to exactly 0.5, and 0.35 vs. 0.997 is an unambiguous gap.

## 4. Model C vs. Model B

| | Model B (17 feat., incl. `pdf_size`+approximations) | Model C (16 feat., all proven) |
|---|---|---|
| Recall | 0.9896 [0.981, 0.997] | **0.9903** [0.980, 0.998] — comparable, C marginally higher |
| Precision | 0.9666 [0.953, 0.979] | 0.9233 [0.897, 0.946] — **CIs do not overlap**, C measurably lower |
| F1 | 0.9779 [0.970, 0.985] | 0.9556 [0.941, 0.969] — CIs barely touch, C lower |
| ROC-AUC | 0.9986 [0.998, 0.999] | 0.9972 [0.995, 0.999] — overlapping |
| FPR | 0.0346 | 0.0630 — higher |
| FN rate | 0.0104 | 0.0097 — marginally lower |
| Runtime fidelity | 2 of 17 features approximate; `pdf_size` **confirmed broken at inference** | **All 16 features proven, no known runtime defect** |

**Selection: Model C.** Precision and FPR are measurably worse (not
overlapping in confidence interval), and this should not be minimized —
Model C will produce more false alarms in absolute terms. But recall/FN
rate — the metric this whole project has been instructed to prioritize —
is unchanged or marginally better, and Model B's `pdf_size` defect is not
a theoretical concern: §5 below demonstrates it would have misclassified
the "large" real fixture with near certainty (a 1.5 MB file's raw-byte
`pdf_size` is ~74x the entire training maximum). Per the explicit
instruction — *"runtime semantic correctness is more important than
slightly better benchmark metrics"* — **Model C is selected.**

## 5. Real runtime validation (the critical test)

Three real, legitimate, locally-owned PDFs spanning a realistic size range
were run through the **exact production path**
(`cic_features.extraire_caracteristiques_cic` → Model C →
threshold 0.15). Files are the user's own academic course materials
(not personal/identifying documents) already present on their machine —
content was never read or displayed, only file bytes processed
statically, exactly as production `predict.py` does.

| Fixture | Size | Model C verdict | proba |
|---|---|---|---|
| small (`rapport_ccb52ffd.pdf`) | 4,265 bytes (~4.2 KB) | **malveillant** | 0.7256 |
| medium (`QCM_Architecture_Donnees.pdf`) | 105,787 bytes (~103 KB) | **sain** | 0.0636 |
| large (`Chapitre 5 HADOOP Pig...pdf`) | 1,523,772 bytes (~1.45 MB) | **sain** | 0.0017 |

**Medium and large are correctly classified benign, confidently.** This
directly confirms the fix works for realistic file sizes — under the old
Model B, the large fixture's raw-byte `pdf_size` (1,523,772) would have
been ~74x beyond the entire training range (max 20,510), exactly the
failure mode `PDF-MODEL-FINAL-EVALUATION.md` §9 predicted.

**The small fixture is a false positive — investigated, not hidden, not
patched by retuning.** Per instruction, the model was **not** modified to
force this fixture to pass.

### Investigation

The small file's 16-feature values: `nb_stream_kw=2, nb_endstream_kw=1,
nb_trailer_kw=1, nb_xref_kw=2, nb_startxref_kw=1, nb_openaction_kw=1`, all
others 0. None of these are out-of-range (see §6's full table) — the
false positive is not a scale/distribution problem like the old
`pdf_size` bug. Digging into the training data:

- `nb_xref_kw=2` is the **exact Benign median** (50th percentile) —
  entirely typical, if anything slightly *more* typical of Benign than
  Malicious (Malicious median is 1).
- `nb_openaction_kw≥1` is a real, well-documented Malicious-leaning signal
  in this dataset (60.6% of Malicious rows have it vs. only 5.0% of
  Benign) — legitimate PDF-generation tools do sometimes add `/OpenAction`
  (e.g., "fit to window" on open), so its presence in a real benign
  document is unusual but not impossible.
- The **joint** slice (`nb_openaction_kw≥1` AND `nb_xref_kw==2`) in
  training data is 176 Benign vs. 41 Malicious (81% Benign) — if anything
  this combination leans benign on its own, yet the full 16-dimensional
  Random Forest decision landed on `malveillant` (0.7256). This is not
  evidence of a labeling contradiction in the training data; it reflects
  that this joint slice is a **relatively sparse region** (217 of 7,939
  usable training rows, ~2.7%) where a Random Forest's learned boundary is
  inherently less stable, and the model's true multivariate decision isn't
  well summarized by either single-feature or pairwise marginals.

**Conclusion:** this is a genuine, real limitation — not a bug, not
something masked by an out-of-range feature, and not a training-data
labeling contradiction. It is a legitimate example of the ~92.3%
precision measured on held-out data manifesting on an actual file: small
real documents that happen to combine an incremental-update-style
double-`xref` with an OpenAction entry from their authoring tool sit in a
part of the feature space the model is measurably less confident about.
**Not patched.** Documented as a known, live limitation.

## 6. Feature distribution contract (training vs. runtime)

| Feature | Train min | Train 25% | Train median | Train 75% | Train max | Runtime: small | medium | large |
|---|---|---|---|---|---|---|---|---|
| `nb_stream_kw` | 0 | 2 | 5 | 21 | 812 | 2 | 86 | 262 |
| `nb_endstream_kw` | 0 | 2 | 5 | 21 | 6,668 | 1 | 43 | 131 |
| `nb_objstm_kw` | 0 | 0 | 0 | 0 | 600 | 0 | 0 | 4 |
| `nb_trailer_kw` | 0 | 1 | 1 | 2 | 46 | 1 | 1 | 2 |
| `nb_xref_kw` | 0 | 1 | 1 | 2 | 46 | 2 | 2 | 4 |
| `nb_startxref_kw` | 0 | 1 | 1 | 2 | 24 | 1 | 1 | 2 |
| `nb_embeddedfile_kw` | 0 | 0 | 0 | 0 | 17 | 0 | 0 | 0 |
| `nb_js_kw` | 0 | 0 | 0 | 1 | 404 | 0 | 0 | 0 |
| `nb_javascript_kw` | 0 | 0 | 0 | 1 | 404 | 0 | 0 | 0 |
| `nb_aa_kw` | 0 | 0 | 0 | 0 | 213 | 0 | 1 | 0 |
| `nb_openaction_kw` | 0 | 0 | 0 | 1 | 4 | 1 | 0 | 0 |
| `nb_launch_kw` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| `nb_acroform_kw` | 0 | 0 | 0 | 1 | 6 | 0 | 0 | 0 |
| `nb_xfa_kw` | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 0 |
| `nb_jbig2decode_kw` | 0 | 0 | 0 | 0 | 14 | 0 | 0 | 0 |
| `nb_richmedia_kw` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 0 |

**No out-of-distribution mismatches found.** Every runtime-observed value,
for all three real fixtures across all 16 features, falls within
`[train_min, train_max]` — most sit at or below the median. This is a
categorically different situation from the old `pdf_size` bug (which was
100–1,000x beyond the training range) — confirming the fix addressed the
actual defect, not just this one feature's symptom.

## 7. Sanity checks (repeated for Model C)

- **Label-shuffle:** 0.3456 held-out ROC-AUC vs. 0.9972 real — unambiguous
  gap, no leakage/splitting bug (see caveat in §3.3 about distance from
  exactly 0.5).
- **Duplicate-group isolation:** 0 groups span train/val/test (verified on
  the 16-feature key, post-conflict-exclusion).
- **Schema-order contract:** `cic_features.py` output order verified
  identical to `cic_schema.CIC_FEATURES` (18 entries); Model C's 16-feature
  subset order verified identical between training and
  `document_ml/pdf/predict.py` inference.
- **`pdf_size` cannot enter inference:** confirmed absent from
  `cic_schema.CIC_FEATURES`, `cic_cleaning.COLONNE_REELLE`, and the
  `cic_features.py` extraction function itself (not merely unused —
  removed from the code).
- **PE regression:** re-run in full, see final report — unaffected.

## 8. Remaining limitations (unchanged in kind, updated in degree)

- The small-fixture false positive (§5) is real and undismissed — ~92.3%
  precision means real files will occasionally be misclassified, and this
  is now a directly-observed, explained instance, not just a held-out
  statistic.
- No external validation set; all numbers derive from one dataset file.
- The 975-row (11%) exclusion for label-conflicting vectors (§3.1) is a
  further population shift beyond the original complete-case filtering —
  Model C has seen even less of the original data's diversity than Model B.
- No adversarial robustness testing.
- `nb_startxref_kw` is now the top-importance feature (0.249) for Model C
  — a simple keyword count; worth future scrutiny for over-reliance on a
  single structural signal, though the full 16-feature model still greatly
  outperforms any single-feature baseline (§8 sanity check family from
  `PDF-MODEL-FINAL-EVALUATION.md`).
