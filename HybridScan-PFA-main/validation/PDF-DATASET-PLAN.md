# PDF dataset selection — research findings (dataset selection phase)

Status: **research only. No dataset downloaded, no code changed, no
training run.** This document is additive to (does not replace)
`validation/DOCUMENT-DATASET-PLAN.md`, which covered the general PDF/Office
scoping decision; this file is the deeper, verified dataset-selection
research requested for the PDF pipeline specifically.

Nothing in `analyze.py`, `app.py`, `model.pkl`, `document_ml/pdf/features.py`,
`document_ml/pdf/train.py`, `document_ml/pdf/predict.py`,
`document_ml/pdf/evaluate.py`, or `history.csv` was touched to produce this
document.

---

## 0. HybridScan's current PDF feature schema (read from source, not memory)

Read directly from `document_ml/pdf/schema.py` / `document_ml/pdf/features.py`
before any dataset research began. 21 features, all extracted by reading raw
bytes and counting regex/substring matches — **no PDF parsing library is
used at inference time**, deliberately, to avoid running a parser (itself a
CVE-prone attack surface) on hostile input:

`file_size, entropy, pdf_version, nb_obj, nb_endobj, nb_stream, nb_endstream,
obj_stream_ratio, nb_page, has_javascript, has_js, has_openaction, has_aa,
has_launch, nb_uri, has_embeddedfile, has_acroform, has_xfa,
nb_suspicious_actions, has_encryption, nb_obfuscated_names`

This schema is the fixed reference point for every compatibility judgment
below.

---

## 1. Candidate datasets investigated

### 1.1 CIC-Evasive-PDFMal2022 (primary academic candidate)

| Field | Value |
|---|---|
| Official name | CIC-Evasive-PDFMal2022 |
| Institution | Canadian Institute for Cybersecurity (CIC), University of New Brunswick (UNB) |
| Original publication | Issakhani, Victor, Tekeoglu, Lashkari — *"PDF Malware Detection Based on Stacking Learning"*, 8th Intl. Conf. on Information Systems Security and Privacy (ICISSP), Feb 2022 |
| Official source | https://www.unb.ca/cic/datasets/pdfmal-2022.html (fetched directly and verified) |
| Year | 2022 |
| Benign samples | 4,468 |
| Malicious samples | 5,557 |
| Total | 10,025 |
| Class balance | 44.6% benign / 55.4% malicious — reasonably balanced |
| Raw PDFs or features? | **Extracted features only** (37 static features: 12 general + 25 structural) — the official page does not offer a raw-PDF download |
| Registration required | No apparent registration wall on the official page for the feature CSV |
| License / usage | Official page: *"You may redistribute, republish, and mirror the Evasive-PDFMal2022 dataset in any form. However, any use or redistribution of data must include a citation"* to the ICISSP 2022 paper |
| Download size | Not stated on the official page (feature CSV, so expected to be small — low tens of MB at most for ~10k rows × 37 columns) |
| Raw malicious binaries involved? | Not distributed as such by CIC's official artifact; **but** its underlying source material (11,173 malicious files from Contagio + 20,000 malicious files from VirusTotal) *is* raw malware — CIC did the raw-file handling and feature extraction on its own infrastructure, not on ours |
| Safe to use locally as-is? | Yes — because CIC only ships extracted features, no raw malware ever needs to touch this machine to use this particular artifact |

**Important characteristic, not just a footnote:** this dataset is
deliberately **evasive-biased by construction**. CIC's own methodology:
cluster all records with k-means into two groups; samples that land in the
"wrong" cluster relative to their true label are kept as the "evasive" set.
This means the dataset is not a representative sample of "PDFs in general"
— it is adversarially selected to be the *hard* boundary cases. Training
exclusively on it risks a model tuned to boundary-case discrimination while
under-weighting the many "easy," obviously-benign or obviously-malicious
files a real deployment will mostly see. This is a data-quality point, not
just a compatibility one — see §4.

Mirrors exist on Kaggle (`dhoogla/cic-evasive-pdfmal2022`,
`satyaprakash138/cleaned-cic-pdf-malware-2022-dataset`) but their pages are
JavaScript-rendered and could not be fetched/verified in this session
(WebFetch returned only the page title, no content, for both). Per the
brief's own instruction not to rely on random mirrors when an official
source exists, **the UNB CIC page is treated as the source of truth here**;
the Kaggle copies are noted only as a convenience-access possibility whose
fidelity to the original was **not** independently verified.

### 1.2 Contagio ("Malicious Documents Archive for Signature Testing and Research")

| Field | Value |
|---|---|
| Official name | Contagio Malware Dump (PDF subset) |
| Maintainer | Mila Parkour (independent security researcher, not an institution) |
| Original publication | No single paper — an ongoing, informally maintained research blog/archive since ~2010 |
| Official source | http://contagiodump.blogspot.com/2010/08/malicious-documents-archive-for.html — access to the raw archive is gated behind contacting the maintainer directly for the password scheme |
| Year | Malicious-document archive dated from 2010 onward |
| Benign samples | Reported inconsistently across secondary sources: 9,000 (per Liu & Nicholas, arXiv:2308.04704, which used Contagio directly and reports **successfully parsing** 7,396 of them) vs. 16,800 "clean" files across *all* formats, not just PDF, per one aggregator description (IMPACT/CyberTrust). **This inconsistency itself is a data-provenance flag** — I could not resolve it without downloading the archive, which this task explicitly defers. |
| Malicious samples | 10,982 (Liu & Nicholas; 10,814 successfully parsed) vs. 11,960 across all formats (IMPACT aggregator) |
| Raw PDFs or features? | **Raw PDF files** (both benign and malicious) |
| Registration required | Informal — direct contact with the maintainer for access credentials, not a self-service form |
| License / usage | One secondary aggregator (IMPACT) lists it as "Unrestricted," commercial use allowed; this was not independently confirmed against Contagio's own terms, since the primary source was not fetched (gated) |
| Download size | Not stated; likely low hundreds of MB to a few GB, typical for a PDF corpus of this size |
| Raw malicious binaries involved? | **Yes — this is a raw malware corpus.** Per this task's explicit instruction, it was **not downloaded**. |
| Safe to use locally as-is? | Only inside an isolated environment — see §3. Not safe to fetch onto the Windows host used for day-to-day HybridScan development. |

**Temporal bias:** the archive's malicious-document collection dates to
~2010–2013-era PDF exploitation techniques (this era's PDF malware
predominantly abused specific Adobe Reader JavaScript-engine
vulnerabilities that have long since been patched). A model trained purely
on Contagio risks learning signatures of a threat landscape roughly 15
years out of date relative to 2026 PDF malware, which increasingly favors
social-engineering/phishing payloads (malicious links, embedded
form-submission targets) over the classic JS-exploit pattern Contagio is
best known for.

### 1.3 PdfRep (2023, addresses known Contagio/CIC bias)

| Field | Value |
|---|---|
| Official name | PdfRep |
| Institution / authors | Academic (IEEE Big Data 2023 paper: *"Evaluating Representativeness in PDF Malware Datasets: A Comparative Study and a New Dataset"*) |
| Original publication | 2023 IEEE International Conference on Big Data (BigData), Sorrento, Italy |
| Official source | https://github.com/thanlau/PdfRep (primary, free); also listed on IEEE DataPort (https://ieee-dataport.org/documents/pdfrep) — **DataPort requires a paid/institutional subscription**, but the GitHub copy is the actual data location and is free |
| Year | 2023 |
| Benign / malicious / total counts | **Not disclosed** on the GitHub README as fetched — the repo points to `feature_file.csv` (via a Dropbox link) for per-file labels rather than stating aggregate counts directly. This is a real gap in what I could verify without downloading. |
| Raw PDFs or features? | **Both** — raw files are referenced via links to the four original source repositories (Contagio, CIC, VirusShare, Govdocs), and a separately hosted `feature_file.csv` provides pre-extracted features (schema not yet compared here — see §2 caveat) |
| Registration required | GitHub: no. IEEE DataPort mirror: yes (subscription) — irrelevant since GitHub is the real source |
| License / usage | **CC0-1.0 (public domain dedication)** — the most permissive of any candidate here |
| Download size | Not stated |
| Raw malicious binaries involved? | Yes, indirectly — PdfRep does not host the malicious raw files itself, it points back to Contagio/CIC/VirusShare for them. So using PdfRep's raw-file composition still means separately obtaining raw malware from those same gated/raw sources. **Not downloaded in this session.** |
| Safe to use locally as-is? | The `feature_file.csv` alone (no raw files) would be safe to fetch onto the host, subject to the same schema-compatibility caveat as CIC (§2) — this was not fetched in this session since the task says stop before downloading. |

This is the most scientifically interesting candidate precisely *because*
its stated purpose is fixing the representativeness problems in Contagio
and CIC — the same problems flagged independently in §1.1/§1.2 above. Its
benign source, **Govdocs** (a subset of the "Digital Corpora" project), is a
well-known, broad, U.S. government-document-derived benign corpus widely
used in digital-forensics research — better source diversity than
Contagio's benign set alone.

### 1.4 Large-scale composite datasets reported in the recent literature (identified, not independently verified)

Two secondary-source claims surfaced during research, both from papers I
did not fully read (only search-result summaries), so these are reported
with appropriately lower confidence:

- A 2024 study ("Evaluation of Malware Classification Models for
  Heterogeneous Data," PMC) reportedly used a dataset of 407,037 benign and
  32,567 malicious PDFs — heavily benign-skewed (92.6% benign).
- Another cited composite: 262,113 total PDFs (128,876 malicious / 133,237
  benign), malicious side aggregated from VirusTotal, VirusShare,
  MalwareBazaar, and URLHaus plus CIC; benign side from government
  publications, academic papers, e-books, and open-source document
  archives.

Neither of these is a single citable, official, directly downloadable
dataset artifact as far as this research could determine — they read as
per-paper aggregations assembled by each paper's authors from multiple raw
sources (several of which are themselves raw-malware repositories), not a
one-stop dataset with its own official page. Treated here as **evidence
that large aggregated corpora exist in the literature**, not as immediately
actionable candidates, since reconstructing them would mean independently
re-aggregating from the same raw-malware sources already flagged above.

---

## 2. Feature compatibility — critical section

### 2.1 Method and a necessary caveat

CIC's official page describes its 37 features only by **category**, not by
publishing an authoritative column-by-column CSV header on the page itself.
To build a concrete compatibility table, this research cross-referenced the
official category descriptions against a third-party open-source
reproduction (`Mathys-Rituper/PDF-feature-extractor` on GitHub, which
explicitly aims to reproduce CIC-Evasive-PDFMal2022's feature set) for
plausible exact column names. **That reproduction is not the official CIC
artifact** — treat the exact names below as illustrative of the *category*
each HybridScan feature would map to, not as a verified byte-for-byte match
to CIC's actual CSV header. This must be re-verified against the real CSV
header before any training run.

### 2.2 Compatibility table — HybridScan (21) vs. CIC-Evasive-PDFMal2022 (~37)

| HybridScan feature | CIC category / likely equivalent | Compatibility |
|---|---|---|
| `file_size` | `pdf_size` (general) | Equivalent |
| `entropy` | *(none)* | **Missing** — CIC has no Shannon-entropy feature |
| `pdf_version` | *(none identified — CIC has a boolean "header presence," not a numeric version)* | **Missing / incompatible** |
| `nb_obj` | `object_count` / `indirect_object_count` (structural) | Equivalent — but CIC's counting method (likely parser-based) may differ numerically from our regex-on-raw-bytes count |
| `nb_endobj` | `endobj` keyword count (structural) | Equivalent |
| `nb_stream` | `stream` keyword count (structural) | Equivalent |
| `nb_endstream` | `endstream` keyword count (structural) | Equivalent |
| `obj_stream_ratio` | *(none — not a published ratio feature)* | **Missing** (derivable if both `nb_stream`- and `nb_obj`-equivalents are confirmed reliable) |
| `nb_page` | `pages` (general) | Equivalent |
| `has_javascript` | JavaScript keyword indicator/count (structural) | Equivalent (ours is boolean, CIC's may be a count — derivable either way) |
| `has_js` | `/JS` keyword indicator (structural) | Equivalent |
| `has_openaction` | `OpenAction` keyword indicator | Equivalent |
| `has_aa` | `AA` keyword indicator | Equivalent |
| `has_launch` | `Launch` keyword indicator | Equivalent |
| `nb_uri` | `URI` keyword count | Equivalent |
| `has_embeddedfile` | `embedded_files_count` (general) | Equivalent |
| `has_acroform` | `Acroform` keyword indicator | Equivalent |
| `has_xfa` | `XFA` keyword indicator | Equivalent |
| `nb_suspicious_actions` | *(none — this is our own derived sum)* | **Derivable** from the individual equivalents above, not a native CIC column |
| `has_encryption` | `encryption` (general, boolean) | Equivalent |
| `nb_obfuscated_names` | "obfuscation counts" (structural) | Equivalent **in concept only** — CIC's exact obfuscation-detection method is not publicly documented at the byte level; must be verified, not assumed identical to our `#xx`-hex-escape regex |

**CIC features with no HybridScan equivalent at all** (would be discarded
under an intersection strategy): title character count, metadata size,
image count, text-presence, font-object count, average embedded-media
size, filter count, nested-filter object count, `SubmitForm` keyword count,
`JBIG2Decode` keyword count, `RichMedia` keyword count, `Xref`/`StartXref`/
`trailer` keyword counts, generic `/Action` keyword count.

### 2.3 What this means

Roughly a third of HybridScan's own features (`entropy`, `pdf_version`,
`obj_stream_ratio`, and the derived `nb_suspicious_actions`) have **no**
CIC equivalent, and CIC carries well over a dozen features HybridScan does
not extract at all. Even the "equivalent" columns are not guaranteed
numerically identical, since CIC's extraction is presumed parser-based
(unconfirmed) while HybridScan's is deliberately raw-byte/regex-based (a
security-motivated design choice documented in `features.py`, not
something to change lightly).

### 2.4 Strategy evaluation (A/B/C/D)

- **A — adapt the extractor to reproduce CIC's schema:** rejected. This
  would mean rewriting `document_ml/pdf/features.py`/`schema.py` to chase an
  unofficial, third-party-reproduced feature definition, contradicting the
  deliberate "no PDF-parsing-library, byte/regex-only" security posture the
  current extractor documents, for a dataset whose own exact extraction
  code isn't publicly canonical. Also out of scope for a "documentation
  only" task in any case.
- **B — intersection of compatible features:** rejected as primary
  strategy. Even the "equivalent" columns carry a real risk of train/
  inference distributional skew (CIC's numbers computed one way, our
  `predict.py` computing the same-named feature a different way at
  inference time) — training on one measurement process and predicting
  with another is a subtle but real correctness bug waiting to happen, not
  just a minor accuracy loss.
- **C — reject CIC entirely:** too strong. CIC remains valuable as an
  independent **benchmark/sanity-check** — comparing HybridScan's own
  from-scratch-trained model's reported metrics against CIC-based published
  results is a legitimate, low-risk way to contextualize our numbers in a
  PFA/PFE report, precisely *because* we would not be training on it.
- **D — labeled raw PDFs run through HybridScan's own 21-feature
  extractor:** **recommended.** This is the only strategy that guarantees,
  by construction, that the training-time feature computation and the
  `predict.py` inference-time feature computation are identical — the
  train/inference schema-identity requirement the brief itself insists on
  (§2 of the original phase-2 task: *"Training and inference feature
  schemas MUST be identical"*). It does mean CIC's own artifact (features
  only, no raw files) cannot directly be used this way — see §5.

---

## 3. Raw-PDF safety (no downloads performed)

Both realistic raw-file candidates for strategy D (Contagio, and PdfRep's
underlying raw sources) involve **real malicious PDF binaries**. None were
downloaded. If/when the user decides to proceed:

- **Security risks:** a malicious PDF is an executable-adjacent artifact —
  opening it in any PDF reader, or in a browser's built-in PDF viewer, can
  trigger exploitation (parser vulnerabilities, embedded JavaScript,
  `/Launch` actions). The risk is in *rendering/opening* it, not in merely
  possessing the bytes on disk.
- **Isolation requirements:** raw malicious samples should never be stored
  or processed on the Windows host currently used for HybridScan
  day-to-day development and testing (the same machine running Streamlit,
  a browser, email, etc.). An isolated VM or container with no shared
  clipboard, no shared folders mounted read-write, and ideally no network
  access (or network access routed only to what's strictly needed for the
  download itself, then disabled) is the appropriate environment.
- **Storage requirements:** samples should be kept as inert bytes —
  ideally in a password-protected/renamed archive (the common convention,
  e.g. renaming `.pdf` to `.bin` or storing inside a password-locked ZIP,
  which is exactly why Contagio itself gates access behind a password
  scheme) so that no file-indexing service, antivirus quick-scan, or
  accidental double-click can trigger a render.
- **How files would be processed statically:** exactly as HybridScan's
  `document_ml/pdf/features.py` already does — open the file in binary
  mode, read bytes, regex/substring count — never call a PDF rendering or
  parsing library on them, and never open them in a reader application, not
  even "just to look."
- **Why they must never be executed/opened interactively:** the entire
  point of a static-analysis pipeline is to avoid the conditions under
  which a malicious PDF's payload activates (JS execution, form
  auto-submission, `/Launch` triggering an external program). Opening one
  "just to check" defeats that guarantee and risks compromising whatever
  machine does it.
- **Is Windows host use appropriate?** Not for the malicious portion. The
  current HybridScan development machine is a general-purpose Windows
  environment; the brief itself already declined a request to disable
  antivirus protection to make a download "work" (that is exactly the kind
  of request this document explicitly will not make, per its own
  instructions), and disabling AV/Defender specifically to ease a malware
  download is not recommended here either.
- **Isolated VM/container preferred?** **Yes.** A disposable VM snapshot
  (revert after use), or a rootless container with no persistent volume
  mounted beyond an explicitly designated "quarantine" read-only bind for
  the resulting extracted-feature CSV (never the raw PDFs themselves)
  crossing back out, is the right shape for this work.

No malware execution is recommended or was performed. No request to
disable protections was made or would be made.

---

## 4. Data-quality assessment

| Dimension | Finding |
|---|---|
| Label quality | CIC: labels come from VirusTotal/Contagio's own community-vetted labeling, generally considered reasonable for research use, but not independently re-verified here. Contagio: labels are the maintainer's own long-standing curation, also not independently re-verified. |
| Class balance | CIC: 44.6/55.4 — good. Contagio: roughly balanced per the counts found (9,000/10,982), though exact figures conflict across secondary sources (see §1.2) — an unresolved discrepancy. |
| Duplicated samples | CIC: the official description states the CIC team **deduplicated** before combining Contagio+VirusTotal sources — a positive signal. Contagio and PdfRep: deduplication methodology not documented in what was fetched — **unverified**, and a real risk given PdfRep explicitly merges four separately-sourced pools (Contagio, CIC, VirusShare, Govdocs) that could easily share overlapping files. |
| Train/test leakage | Not assessable without the actual files/hashes in hand. The general risk with any multi-source aggregate (PdfRep in particular) is the same file appearing via two different source pools and landing on both sides of a naive train/test split — must be deduplicated by content hash *before* splitting, not after (see §6). |
| Source bias | CIC is explicitly evasive-biased by construction (§1.1) — not representative of "typical" incoming files. Contagio's malicious side is a single-curator archive from one specific era/toolset generation. |
| Temporal bias | Contagio: malicious samples date to ~2010s-era PDF exploitation techniques — a real generalization risk against 2026 threats (see §1.2). CIC (2022) and PdfRep (2023) are newer but still pull heavily from the same older Contagio malicious pool underneath. |
| Benign-document diversity | Contagio's benign set: single-source, unclear diversity. PdfRep's benign set (Govdocs/Digital Corpora): broad, well-established, diverse U.S. government document corpus — a meaningfully stronger benign source. |
| Malware diversity | Not independently assessed (would require family/campaign labels not confirmed present in any candidate here). A known open question for all three. |
| Filename/hash duplicate risk | Elevated for PdfRep specifically, given its four-source aggregation, until deduplication is confirmed (see above). |
| Designed for PDF malware classification? | CIC: yes, explicitly. Contagio: general malware research archive, PDF is one subset among several formats it hosts. PdfRep: yes, explicitly, and specifically designed to correct known bias in the other two. |

**Honest summary:** every candidate here has real, documented limitations.
None should be presented as a ready-made, unimpeachable ground truth —
this is squarely in "PFA/research-prototype" territory, not
production-grade threat intelligence.

---

## 5. Recommendation

### 5.1 Primary recommendation: **raw-PDF strategy D, sourced from PdfRep's underlying raw-file pool (Contagio + CIC-malicious + VirusShare + Govdocs), re-extracted through HybridScan's own `document_ml/pdf/features.py`**

- **Why it fits HybridScan:** guarantees byte-for-byte identical feature
  computation between training and `predict.py` inference — the one
  non-negotiable requirement the brief itself states. It also directly
  benefits from PdfRep's own stated purpose (representativeness) and its
  much stronger, CC0-licensed benign source (Govdocs) compared to relying
  on Contagio's benign set alone.
- **Does it match our feature schema?** Not automatically — it matches by
  construction *because* we would run our own extractor on the raw files,
  rather than trying to reuse anyone else's CSV.
- **Do we need raw files?** Yes — this is the one strategy that requires
  them, and per §3, that means an isolated VM/container, never the
  Windows development host, and no execution.
- **Extractor changes needed?** **None.** `document_ml/pdf/features.py` is
  already schema-complete for this path; it was designed exactly for "raw
  PDF in, `schema.FEATURES` out."
- **Expected workflow:** obtain raw benign+malicious PDFs (Govdocs subset +
  Contagio/CIC/VirusShare malicious subset) in an isolated environment →
  deduplicate by SHA-256 across the *combined* pool → run
  `document_ml/pdf/features.py::extraire_features_pdf` on each surviving
  file → assemble the resulting feature+label CSV → hand that CSV to
  `document_ml/pdf/train.py --data ... --provenance ...` (already built,
  see phase-2 report) → `model_pdf.pkl`.

### 5.2 Fallback recommendation: **CIC-Evasive-PDFMal2022's own feature CSV, used only as an external benchmark/sanity-check — not as HybridScan's training data**

If obtaining and safely processing raw files turns out to be impractical in
the available time/infrastructure, CIC's official, no-registration,
citation-only-licensed feature CSV is the safest **fallback for a
literature-comparison benchmark**: download only the feature CSV (never
raw malware), acknowledge the schema mismatch documented in §2, and — if a
from-scratch HybridScan model is eventually trained on a §5.1-style raw
dataset — report both models' metrics side by side rather than trying to
merge or intersect the two schemas.

---

## 6. Proposed training plan (not executed)

```
Raw labeled PDFs (benign: Govdocs; malicious: Contagio/CIC/VirusShare — isolated VM)
    ↓
Validation/cleaning  — confirm each file actually parses as a PDF at all
                        (reuse analyze.identifier_fichier()'s %PDF- check);
                        drop files that fail even that minimal check
    ↓
Deduplication  — SHA-256 across the ENTIRE combined pool (not per-source),
                  BEFORE any split, so the same file can never appear on
                  both sides of train/val/test
    ↓
Feature extraction  — document_ml/pdf/features.py::extraire_features_pdf,
                        the exact function predict.py uses at inference
    ↓
Train / validation / held-out test split
    — stratified on label, seeded (seed=42, matching train.py's default)
    — proposed ratio: 60/20/20 for a dataset in the low-to-mid thousands
      (comparable order of magnitude to CIC's ~10k); for a smaller raw
      pool (a few hundred to low thousands after dedup — realistic if
      only a modest slice of Contagio/Govdocs is used), consider 70/15/15
      or 5-fold cross-validation on the train+val pool instead of a single
      fixed validation split, to avoid an unstably small validation set
    ↓
Random Forest baseline  — document_ml/pdf/train.py already implements this
                            (class_weight="balanced", n_estimators=300)
    ↓
Threshold selection on validation set  — train.py already implements this
                                           (F1-maximizing sweep over
                                           validation-set probabilities;
                                           NOT copied from the PE model's
                                           0.45)
    ↓
Held-out evaluation  — document_ml/pdf/evaluate.py, or train.py's own
                         held-out test split — never the validation set
                         used for threshold selection
    ↓
model_pdf.pkl
    ↓
Model metadata  — train.py already writes: model family, supported
                    formats, feature-schema version, training date, class
                    distribution, threshold, evaluation metrics, library
                    versions, dataset provenance (a provenance.json
                    documenting exactly what's in §1 for whichever
                    dataset is actually used is a REQUIRED input to
                    train.py, not optional)
    ↓
HybridScan integration tests  — extend the phase-2 test suite
                                  (test_phase2_pdf.py-style) to cover a
                                  real model_pdf.pkl once one exists:
                                  confirm predict.py loads it, confirm
                                  analyser() surfaces its verdict/
                                  confidence correctly, confirm quarantine
                                  still triggers only on a genuine
                                  malicious verdict
```

`document_ml/pdf/train.py` and `document_ml/pdf/evaluate.py` already
implement everything from "feature extraction" onward (verified working via
a synthetic smoke test in the prior phase — see the phase-2 final report);
nothing in this plan requires new code, only a dataset.

---

## 7. Model acceptance criteria (proposed, not achieved — no model exists yet)

For a PFA/research-prototype PDF classifier, the following should be
**reported**, not assumed or pre-guessed:

- Confusion matrix (TN/FP/FN/TP) on the held-out test set
- Precision, recall, F1 (both classes, not just the malicious class)
- ROC-AUC
- False-positive rate (benign files wrongly flagged malicious — the more
  operationally costly error for a tool users will actually run against
  their own legitimate documents)
- False-negative count (malicious files missed — the more security-costly
  error)
- Class distribution of the actual held-out test set used (not the full
  dataset) — small/imbalanced test sets produce metrics that look
  impressive but are not statistically meaningful, and `evaluate.py`
  already warns about this below a 30-sample floor

No specific accuracy/F1/AUC number is predicted or promised here. Given
this is a genuinely different, harder feature space than the PE model
(byte/regex counts on a loosely-structured text+binary format, vs. PE's
well-defined header fields), and given every candidate dataset above has
documented representativeness caveats, the honest expectation is that the
PDF model's real-world performance is unknown until it is actually trained
and evaluated on a held-out set — and should be reported exactly as
measured, including if it turns out mediocre.

---

## 8. Summary — is a defensible dataset "in hand"?

**No.** Every candidate identified requires further action before training
can start responsibly:

- CIC: obtainable now (official, no registration, cited use permitted),
  but schema-incompatible with HybridScan's extractor for direct training
  use — usable only as a benchmark (§5.2).
- Contagio / PdfRep raw files: the scientifically preferred path (§5.1),
  but require raw malicious PDFs, an isolated VM/container, and — for
  Contagio — direct contact with the maintainer for access. **Not
  downloaded in this session**, per the explicit stop condition.

This document stops here, as instructed.
