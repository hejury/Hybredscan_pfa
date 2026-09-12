# CIC-PDF-DATA-QUALITY.md — class-conditional data-quality analysis

Status: **analysis only. No model trained.** Produced entirely by running
`document_ml/pdf/cic_cleaning.py` (the deterministic cleaning layer) against
`datasets/pdf/PDFMalware2022.parquet` (frozen, immutable — SHA-256
`25db2059d59207d2040c5a999838514579ed4667b2b7fa39f2398dee484caf65`) and
tallying, per feature and per `Class` label, how many values fell into each
of the 5 required categories: **valid, missing/-1, malformed
Count(HexcodeCount), leaked-text, other-invalid**.

This document is the evidence base for two decisions made elsewhere:
excluding `Header` from the training subset (§2 below), and the overall
`B` status in the phase's final report (pervasive, class-correlated
missingness — not a per-feature problem isolated to a few columns).

---

## 1. Dataset-level summary

- Total rows: **10,023**. Malicious: **5,555**. Benign: **4,468**.
- Every one of the 20 candidate keyword/size features shows the **same
  systematic pattern**: valid-value rate is high and uniform for Benign
  rows (99.26%–99.91%), but meaningfully and consistently lower for
  Malicious rows (79.23%–94.64%). This is not a handful of noisy columns
  among otherwise-clean ones — it is a dataset-wide characteristic.
- Overall (all 20 mapped features, diagnostic-only aggregate, **not** a
  trained feature — see `cic_cleaning.calculer_diagnostics`):
  `extraction_failed` (at least one missing/invalid mapped field in that
  row) is true for **19.30%** of Malicious rows vs. **0.83%** of Benign
  rows — a ~23x rate difference.

## 2. Full class-conditional table (all 20 candidate features + Header)

"Malicious/Benign valid%" = share of rows in that class with a clean,
usable value for that feature. "Gap" = Benign valid% − Malicious valid%,
in percentage points — the higher this number, the more a model could use
"was this field missing/corrupt" as a de facto label proxy for that
feature alone. Sentinel/compound/leaked-text percentages shown are for the
**Malicious** class specifically (the class where essentially all of the
dirtiness concentrates — Benign-class dirtiness is consistently ≤0.74%
sentinel and 0% compound/leaked-text across every feature, omitted from
the table for space; full numbers are in
`quality_analysis.json`-equivalent detail reproducible by re-running the
analysis script against `cic_cleaning.py`).

| Feature (cic_schema name) | Real column | Malicious valid% | Benign valid% | Gap (pp) | Malicious sentinel% | Malicious compound% | Malicious leaked-text% |
|---|---|---|---|---|---|---|---|
| `pdf_size` | `PdfSize` | 94.64% | 99.91% | 5.27 | 5.36% | 0.00% | 0.00% |
| `is_encrypted` | `isEncrypted` | 94.64% | 99.91% | 5.27 | 5.36% | 0.00% | 0.00% |
| `nb_stream_kw` | `Stream` | 90.86% | 99.26% | 8.40 | 9.14% | 0.00% | 0.00% |
| `nb_endstream_kw` | `Endstream` | 90.84% | 99.26% | 8.42 | 8.75% | 0.02% | 0.40% |
| `nb_objstm_kw` | `ObjStm` | 90.86% | 99.26% | 8.40 | 9.14% | 0.00% | 0.00% |
| `nb_trailer_kw` | `Trailer` | 90.86% | 99.26% | 8.40 | 9.14% | 0.00% | 0.00% |
| `nb_xref_kw` | `Xref` | 90.86% | 99.26% | 8.40 | 8.75% | 0.00% | 0.40% |
| `nb_startxref_kw` | `StartXref` | 90.86% | 99.26% | 8.40 | 8.75% | 0.00% | 0.40% |
| `nb_obj_kw` | `Obj` | 86.30% | 99.26% | 12.96 | 13.30% | 0.00% | 0.40% |
| `nb_page_approx` | `PageNo` | 88.78% | 99.26% | 10.48 | 8.75% | 2.07% | 0.40% |
| `nb_embeddedfile_kw` | `EmbeddedFile` | 90.03% | 99.26% | 9.23 | 9.38% | 0.59% | 0.00% |
| `nb_js_kw` | `JS` | 86.73% | 99.26% | 12.53 | 9.14% | 4.12% | 0.00% |
| `nb_javascript_kw` | `Javascript` | 88.75% | 99.26% | 10.51 | 9.14% | 1.87% | 0.23% |
| `nb_aa_kw` | `AA` | 90.37% | 99.26% | 8.89 | 9.38% | 0.25% | 0.00% |
| `nb_openaction_kw` | `OpenAction` | 89.04% | 99.26% | 10.22 | 9.38% | 1.58% | 0.00% |
| `nb_launch_kw` | `Launch` | 90.44% | 99.26% | 8.82 | 9.38% | 0.18% | 0.00% |
| `nb_acroform_kw` | `Acroform` | 90.39% | 99.26% | 8.87 | 9.38% | 0.23% | 0.00% |
| `nb_xfa_kw` | `XFA` | 90.26% | 99.26% | 9.00 | 9.38% | 0.36% | 0.00% |
| `nb_jbig2decode_kw` | `JBIG2Decode` | 90.51% | 99.26% | 8.75 | 9.38% | 0.11% | 0.00% |
| `nb_richmedia_kw` | `RichMedia` | 90.55% | 99.26% | 8.71 | 9.38% | 0.07% | 0.00% |
| `header_present` (**EXCLUDED**) | `Header` | 79.23% | 99.26% | **20.03** | 0.04% | 0.00% | 20.50% |

All figures reproducible deterministically: `document_ml/pdf/cic_cleaning.py`
does the parsing, the analysis script simply tallies its output — this
table is not hand-computed or estimated.

## 3. Interpretation — this is a systemic pattern, not isolated columns

Three observations, in order of importance:

1. **The gap is universal.** Every single one of the 20 candidate features
   shows Benign validity ≥99.26% and Malicious validity in the 79–95%
   range. There is no subset of "clean" features hiding among "dirty"
   ones — trimming down to a smaller feature list would not meaningfully
   reduce this risk, because the missingness co-occurs at the **row**
   level: a row with `PdfSize == -1` overwhelmingly also has `Stream`,
   `Trailer`, `ObjStm` missing (the same 302- and 541-row failure batches
   identified in `CIC-PDF-FEATURE-COMPATIBILITY.md` §8.4). Removing
   individual columns doesn't remove the affected rows.
2. **Two distinct dirtiness mechanisms, both class-correlated, arguably
   for different reasons:**
   - The **`-1` sentinel** (missing/failed extraction) is essentially pure
     **tooling artifact** — a PDF being hard for some parser to open
     doesn't intrinsically make it malicious, so this correlation most
     plausibly reflects "evasive/malformed malicious PDFs are
     disproportionately likely to crash whatever tool(s) produced this
     CSV," which is itself a real (if indirect) property of the malicious
     class in this dataset, but not a property of PDF structure a
     from-scratch extractor should be expected to reproduce faithfully.
   - The **compound `"N(M)"` notation** (`compose_malforme`) is different:
     M is PDFiD's own `HexcodeCount` — literally a count of
     hex-obfuscated keyword occurrences. Its near-total concentration in
     the Malicious class (0% in Benign for every affected feature) is
     plausibly a **genuine structural signal** — obfuscating PDF
     keywords to evade naive AV/keyword scanners is a documented evasion
     technique (see `CIC-PDF-FEATURE-COMPATIBILITY.md` §3's citation of
     the ICISSP 2022 paper's own discussion of PDF obfuscation) — not
     merely a parsing bug. This is why `cic_cleaning.py` retains the `N`
     (Count) component as a usable value rather than discarding the whole
     cell as invalid: doing so preserves a plausibly-real signal while
     still never feeding the raw text or the M component into training.
   - **Leaked literal text** (`"pdfid.py"`, `"bytes[endHeader]"`, filename
     fragments) is unambiguously a **pipeline bug**, not a security
     signal, and is treated as invalid/missing accordingly, never coerced
     to 0 or any other number.
3. **`Header` is categorically worse and structurally different** — its
   20.03-point gap is roughly double the typical ~8–13 point gap seen
   elsewhere, and unlike the keyword-count columns, its "dirty" values
   (`"\ta"`, `"\tyour"`, `"\t%PDF-11113"`) aren't a parseable
   count-with-known-alternate-format; they're free-text corruption with no
   documented recovery rule. Combined with the runtime-reproducibility gap
   already identified in `CIC-PDF-FEATURE-COMPATIBILITY.md` §8.6, this is
   why `Header`/`header_present` is excluded outright rather than merely
   flagged.

## 4. Features where missingness most resembles an obvious label shortcut

Ranked by gap (highest risk first) among the **retained** (non-Header)
features:

1. `nb_obj_kw` (12.96pp) — also has genuine leaked-text corruption (filename
   fragments), not just sentinel/compound.
2. `nb_js_kw` (12.53pp) — driven mostly by the compound-notation mechanism
   (§3.2), arguably partly real signal, not purely artifact.
3. `nb_javascript_kw` (10.51pp)
4. `nb_page_approx` (10.48pp)
5. `nb_openaction_kw` (10.22pp)

None of these are excluded outright (§6 of the final report explains why:
removing them doesn't fix the row-level co-occurrence of missingness), but
they are flagged here as the features most worth extra scrutiny if a future
phase decides to explicitly downweight, re-derive, or exclude specific
rows.

## 5. What this analysis does NOT do

- It does not impute any missing value.
- It does not train or evaluate any model.
- It does not decide the imputation strategy for a future training phase
  (see `validation/CIC-PDF-FEATURE-COMPATIBILITY.md` and the final report's
  recommendation — imputation parameters must be fit on a train split
  only, never on the full dataset before splitting).
- It does not hide or soften the finding that missingness is strongly
  label-correlated — that finding is the main output of this document.
