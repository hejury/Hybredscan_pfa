# Dataset plan — PDF static-ML pipeline (document_ml/pdf)

Status: **planning only. No dataset has been downloaded, and no model has
been trained.** This document exists to satisfy the dataset-provenance
requirement (cahier des charges §5/§12) *before* any training is attempted.

Scope note: this phase covers **PDF only**. A prior draft of this task
briefly began touching DOC/DOCX (real structural validation +  a shared
Office ML dispatch path) before being explicitly stopped mid-turn; that work
was reverted (see the "files modified" section of the final report for this
phase). No Office dataset research was performed, and none is documented
here — DOC/DOCX remain on the phase-1 `VirusTotal -> indetermine` path only.

---

## 1. Search performed

Checked this repository for any existing PDF-malware dataset (raw or
feature-level) before looking externally: `find . -iname "*pdf*malware*"`
and a scan of every `*.csv` in the repo. Result: **none exists locally.**
The only dataset present is `dataset.csv` at the repo root, which is the
existing **PE** feature dataset (29 columns matching
`extract_features.py`/`train_model.py` exactly — confirmed by inspecting
its header) — it is unrelated to PDF and must not be reused or relabeled
for this purpose (cahier des charges §1: do not modify the PE pipeline;
this also means not repurposing its data for a different family, which
would not be a truthful "PDF dataset" in any case).

No PDF dataset — raw or feature-level — is present anywhere in this
repository. Nothing was downloaded during this session.

## 2. Candidate reputable sources (identified, not obtained)

These are named from general knowledge of the PDF-malware-detection research
literature, not from having fetched or verified them in this session. Each
requires a deliberate, separate action by the user (registration, license
acceptance, or an account) before it could be used — none of that was done
here.

| Dataset | Type | Access | Notes |
|---|---|---|---|
| **CIC-Evasive-PDFMal2022** (Canadian Institute for Cybersecurity, UNB) | Feature-level CSV (also raw PDFs) | Registration/request form on the CIC datasets portal; academic-use terms | The most commonly cited recent academic PDF-malware dataset with a documented feature schema and an accompanying paper; would need its own feature schema reconciled against `document_ml/pdf/schema.py` (likely different columns — see §6) |
| **Kaggle "PDF Malware Detection" style datasets** | Feature-level CSV | Kaggle account + API token (not configured in this environment) | Several community-published CSVs derived from CIC/other academic sources exist; provenance and exact labeling methodology vary by upload and must be checked per-dataset before trusting it |
| **Contagio PDF malware dump** | Raw malicious + benign PDF samples | Historically vetted/manual access request to the maintainer | This is a **raw malware corpus**. Per the explicit stop condition (cahier des charges §5/§12), this was **not downloaded** |
| **MalwareBazaar / VirusShare (filtered to PDF)** | Raw malware samples | Registration; bulk/API access often gated | Also a **raw malware corpus** — general-purpose, not PDF-specific; **not downloaded**, for the same reason |

None of the feature-level options above were fetched in this session either
— doing so would require creating/using external accounts (Kaggle API
token, CIC registration) on the user's behalf, which was not requested and
was not done autonomously.

## 3. Why no dataset was obtained this session

Two independent constraints stop this task at the planning stage, per the
brief's own stop condition:

1. **The two raw-sample sources (Contagio, MalwareBazaar/VirusShare) are
   malware corpora.** The brief explicitly says: *"If only raw malware
   corpora are available, STOP before downloading them and report what
   would be required."* That applies here.
2. **The two feature-level sources (CIC, Kaggle) require account
   creation/registration that belongs to the user**, not something to do
   silently on their behalf. Even where technically reachable over the
   network, creating accounts or agreeing to dataset licenses is a decision
   for the user to make, not an autonomous action.

## 4. What would be required to proceed (action items for the user)

To move from "architecture ready" to "model trained," one of the following
needs to happen, then handed back to this pipeline:

- **Preferred:** obtain a feature-level PDF dataset (e.g. request access to
  CIC-Evasive-PDFMal2022, or a vetted Kaggle CSV) and place the resulting
  CSV somewhere accessible, e.g. `document_ml/pdf/data/pdfmal_features.csv`.
  Because its column names will almost certainly not match
  `document_ml/pdf/schema.py::FEATURES` (different research groups define
  different PDF feature sets), a small mapping/re-extraction step will be
  needed — see §6.
- **Alternative:** obtain a small, already-labeled set of **raw** PDF
  samples the user has independently verified the legal right to hold
  (e.g. their own institution's malware research collection, not a
  bulk internet download performed by me), placed under
  `document_ml/pdf/data/<label>/*.pdf` per `train.py --pdf-dir`'s expected
  layout (`benign/` and `malicious/` subfolders). `document_ml/pdf/features.py`
  would then extract `schema.FEATURES` directly from those files — this
  still requires the user to source and vet the raw samples; downloading a
  malware corpus is exactly the step this plan stops at.
- Either way, a `provenance.json` (see `train.py --provenance`) documenting
  the source, license, and collection methodology is a required input, not
  optional metadata — `train.py` refuses to run without one.

## 5. Required documentation once a dataset is in hand (template)

To be filled in for whichever dataset is actually used, before training:

- **Dataset name/source:** _(not yet chosen)_
- **Sample counts:** _(benign: ?, malicious: ?)_
- **Class balance:** _(ratio, and whether stratified sampling was applied)_
- **Labels:** _(binary sain/malveillant — confirm the source's own labeling
  methodology, e.g. VT consensus threshold, sandbox detonation, expert
  review)_
- **License/usage constraints:** _(academic-only? redistribution allowed?)_
- **Raw binaries or pre-extracted features:** _(if raw, extracted via
  `document_ml/pdf/features.py`; if pre-extracted, feature names must be
  reconciled against `schema.py`, see §6)_
- **Train/validation/test strategy:** `train.py` already implements
  stratified train/validation/test splitting (default 60/20/20, seeded) —
  the split ratios and seed used for the final model should be recorded
  here.
- **Leakage risks:** e.g. near-duplicate samples across split boundaries,
  a single malware family over-represented in one split, benign PDFs all
  sourced from one narrow origin (making "benign" mean "one specific
  generator's output" rather than "benign PDFs in general").
- **Limitations:** e.g. dataset age relative to current PDF malware
  techniques, family/campaign diversity, whether "benign" samples were
  adversarially screened at all.

## 6. Feature-schema compatibility risk

`document_ml/pdf/schema.py::FEATURES` was designed independently (21
byte/regex-level static features — file size, entropy, object/stream
counts, `/JavaScript`, `/OpenAction`, `/Launch`, `/URI`, `/EmbeddedFile`,
`/AcroForm`, `/XFA`, obfuscated-name count, etc. — see that file's
`FEATURE_DOC` for the full, individually-justified list). External datasets
(CIC or Kaggle-hosted derivatives) typically ship their **own** feature
schema, which will not line up column-for-column with this one. Two paths
once a dataset is chosen:

- If the dataset provides **raw PDF files** (or the license permits
  redistributing/re-deriving from samples the user has legitimately
  obtained): re-extract with `document_ml/pdf/features.py` so the schema
  matches exactly what `predict.py` will use at inference time. This is the
  cleaner path and the one `train.py --pdf-dir` is built for.
- If only **pre-extracted features** are available under a different
  schema: either (a) map the overlapping features and drop/impute the rest
  (weakens the model and needs to be justified/documented), or (b) treat it
  as a schema mismatch and prefer the raw-file path instead. Silently
  training on a different feature set than what `predict.py` extracts at
  inference time would silently break the model — this must never be done
  without updating `schema.py` and re-validating `predict.py` against it.

## 7. Conclusion

No dataset is currently available for `document_ml/pdf`. Per the brief's
stop condition, this phase implements the file validation, feature
extraction, training pipeline (`train.py`), and evaluation pipeline
(`evaluate.py`) — verified end-to-end with synthetic smoke-test data only
(never presented as a real model) — and stops here. **`model_pdf.pkl` does
not exist.** Training becomes possible as soon as one of the paths in §4 is
completed by the user and documented per §5.
