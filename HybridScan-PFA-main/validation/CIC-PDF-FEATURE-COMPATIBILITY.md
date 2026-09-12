# CIC-Evasive-PDFMal2022 feature-schema compatibility investigation

Status: **UPDATED — the real dataset has now been imported and inspected
(§8 below). No model trained.** Sections 1–7 below are the original
abstract, documentation-only investigation (before the real file was
available); §8 reports what was actually found in the real Parquet file
supplied by the user at `datasets/pdf/PDFMalware2022.parquet`, which
supersedes some of the assumptions made in §1–7 while confirming the
overall shape of the analysis.

The existing PE pipeline (`model.pkl`, `train_model.py`,
`extract_features.py`) was not touched. `analyze.py`, `app.py`, and
`history.csv` were not touched. `document_ml/pdf/schema.py` and
`document_ml/pdf/features.py` (HybridScan's existing 21-feature PDF
extractor) were **read only, not modified**. `document_ml/pdf/cic_schema.py`
and `cic_features.py` were also **not modified** in this update pass — only
read/validated against the real file; any corrections they need are
recommended, not applied (see §8.6).

---

## 1. CIC dataset availability — corrected finding

The prior dataset-selection phase (`PDF-DATASET-PLAN.md`) reported "no
apparent registration wall" for the CIC feature CSV, based on the summary
page at `unb.ca/cic/datasets/pdfmal-2022.html`. That summary undersold the
real requirement. Following the actual download link from that page
(`http://cicresearch.ca/CICDataset/CIC-EvasivePDF2022/`, which redirects to
`https://cicresearch.ca/CICDataset/CIC-EvasivePDF2022/`), the destination is
**a data-request form**, not a direct file listing. Fetching and inspecting
its raw HTML (safe — plain markup, no executable content) shows required
fields:

```
First Name (text, required)
Last Name (text, required)
Email (email, required)
Organization/Company (text, required, max 100 chars)
Job Title (text, required)
Country (select, required)
[Submit] [Clear]
```

This is a normal, lightweight academic-dataset request form (not a
malware-specific gate, not an IRB-style application) — but it does require
disclosing real identity/organization/email on someone's behalf.
**This was not submitted.** Submitting it is a decision for the user to
make with their own information, not something to do autonomously.
Consequently: **no CIC feature CSV was obtained in this session.** Every
finding below about CIC's exact feature semantics comes from the dataset's
official documentation page and its associated peer-reviewed paper (both
freely and directly fetchable), not from inspecting the actual data file.

## 2. Sources used (all fetched directly this session)

1. Official dataset page: `https://www.unb.ca/cic/datasets/pdfmal-2022.html`
2. The paper that introduced this dataset (open-access, fetched directly,
   no paywall): Issakhani, Victor, Tekeoglu, Lashkari — *"PDF Malware
   Detection based on Stacking Learning"*, ICISSP 2022, pp. 562–570.
   `https://www.scitepress.org/PublishedPapers/2022/109084/109084.pdf`
   (DOI: 10.5220/0010908400003120)
3. Didier Stevens' `pdfid.py` — the publicly documented tool the paper
   states was used for structural-feature extraction — source fetched
   directly from
   `https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/pdfid.py`
   and read in full.

**Important, honestly-reported discrepancy across sources 1 and 2:** the
paper's body text says *"28 static representative features... 10 general
features and 18 structural features"* (its own Table 1 lists closer to
~24 named structural items, which doesn't cleanly match its own "18"
either), while the official dataset page (source 1) describes the actual
**distributed CSV** as having **37 features (12 general + 25
structural)**, and gives a final sample count of "10,025" records vs. the
paper's own "10,022 samples with no duplicate records." These are not
resolvable without the actual file — they read as the dataset having been
revised after the paper's publication, which is common but means **the
paper's Table 1 is not a fully authoritative description of the final,
distributed CSV's exact column set.** Every feature classification below
notes which source it comes from.

## 3. How CIC actually extracted these features (directly stated in the paper)

Section 5.1 of the paper: *"We utilized the python PyMuPDF library and
PDFid (developed by Didier Stevens) to develop our feature extraction
module."*

This single sentence is the most load-bearing fact in this whole
investigation:

- **PyMuPDF** (`fitz`) is a **real PDF parsing/rendering library** — it
  builds an actual object model of the document (pages, fonts, images,
  metadata dictionary, etc.). HybridScan's `features.py` deliberately does
  **not** use a PDF-parsing library at all (documented reasoning: a PDF
  parser is itself a CVE-prone attack surface to run against untrusted
  input). Any CIC feature that requires PyMuPDF's object model to compute
  correctly is **not reproducible** by HybridScan's current
  byte/regex-only design without reversing that deliberate security
  decision.
- **PDFiD** is a **public, well-documented, pure string-search tool** —
  confirmed by reading its actual source: it scans the raw file for a
  fixed keyword list, counts total and "obfuscated" (hex-escaped)
  occurrences of each, and — critically — **never decompresses stream
  content** (`grep`-verified: no `zlib`/`FlateDecode`/decompress call
  anywhere in the ~1,090-line source). This is methodologically
  **identical in spirit** to HybridScan's own `features.py` approach.
  Its author states the design goal explicitly in the tool's own docstring:
  *"An important design criterium for this program is simplicity. Parsing
  a PDF document completely requires a very complex program, and hence it
  is bound to contain many (security) bugs."* — the same reasoning
  documented in HybridScan's `features.py`.

PDFiD's actual, canonical base keyword list (read directly from its
source, `PDFiD()` function):

```
obj, endobj, stream, endstream, xref, trailer, startxref, /Page,
/Encrypt, /ObjStm, /JS, /JavaScript, /AA, /OpenAction, /AcroForm,
/JBIG2Decode, /RichMedia, /Launch, /EmbeddedFile, /XFA
```

Notably, **this base list does not include** `/URI`, `/submitForm`,
`/Action`, or a general `/Colors` keyword count (PDFiD does have
CVE-2009-3459-specific logic that fires when a `/Colors` value exceeds
2²⁴, which is a narrow anomaly check, not a general keyword-occurrence
count). Since CIC's Table 1 lists `/URI`, `/submitForm`, and `Colors` as
separate features, and the tool's own default keyword list doesn't cover
them, **CIC must have used a customized/extended keyword list** (PDFiD
supports this via an external `pdfid.ini` file) or additional custom code
alongside PDFiD/PyMuPDF for those specific columns. That extension is not
publicly published anywhere found in this research. **This is treated as
an unverifiable extraction method for those specific features — see the
"C. Ambiguous" classifications below.**

## 4. Full feature compatibility table

Columns: **CIC feature** (name as given by the official page / paper, best
available) · **Source category** (per UNB page: General or Structural) ·
**Likely extraction tool** (per the paper's stated toolchain) · **Meaning**
· **Reproducible from HybridScan's current byte/regex approach?**
**Classification (A/B/C/D)**.

### General features (12, per official page)

| CIC feature | Tool | Meaning | Class | Reasoning |
|---|---|---|---|---|
| PDF size | trivial | File size in bytes | **A** | Identical to HybridScan's existing `file_size` (`os.path.getsize`) |
| Header | PDFiD-style | Presence/well-formedness of the `%PDF-x.y` header | **A** | HybridScan already checks this for routing (`_a_entete_pdf`); trivially exposable as a feature |
| Encryption | PDFiD (`/Encrypt` keyword) | Whether `/Encrypt` is present | **A** | Matches HybridScan's existing `has_encryption` exactly (same token, same raw-byte search) |
| Object number | PDFiD (`obj` keyword count) | Count of indirect objects | **A/B** | Matches HybridScan's existing `nb_obj` closely; PDFiD counts the literal `obj` token, our regex requires `\d+\s+\d+\s+obj` — usually equivalent, rare edge-case divergence on malformed files |
| Page number | Likely PyMuPDF (true page-tree count) | Number of pages | **B** | HybridScan's `nb_page` (regex count of `/Type/Page` tokens) is a reasonable *approximation*, but a true parser's page-tree traversal can differ (inherited attributes, malformed trees) — reproducible with a documented caveat that it's an approximation, not identical |
| Number of embedded files | PDFiD (`/EmbeddedFile` keyword **count**) | Count of embedded-file markers | **B** | HybridScan currently stores this as a **boolean** (`has_embeddedfile`); trivial code change (count instead of presence) using the exact same token |
| Title characters | Likely PyMuPDF (`/Title` metadata value length) | Character count of the document title | **C** | A regex could extract a `/Title (...)` or `/Title <hex>` literal's raw length, but exact PDF string-literal decoding (escaped parens, hex strings, UTF-16 encoding) has real edge cases a simple regex won't handle identically to a real parser — undocumented which convention CIC used |
| Metadata size | Ambiguous | Size of *some* metadata region | **D** | Not documented whether this means the `/Info` dictionary's serialized size, an XMP metadata stream's size, or something else — genuinely undefined without the extraction source, and isolating "the metadata" from raw bytes without a parser is unreliable regardless |
| Image number | PyMuPDF (XObject/Image enumeration) | Count of embedded images | **D** | Requires object-model traversal (`/Subtype /Image` XObjects reachable from page resources); a raw regex proxy would both over-count (unreferenced/duplicate definitions) and under-count (compressed cross-reference streams) relative to a true parser |
| Text | PyMuPDF (content-stream text extraction) | Whether the document contains extractable text | **D** | Requires interpreting page content-stream operators (`Tj`, `TJ`, etc.), not a byte-pattern match |
| Font objects | PyMuPDF (`/Type /Font` object enumeration) | Count of font resources | **C** | A regex for `/Type/Font` / `/Type /Font` is a plausible proxy but unverified against the real parser's resolution of indirect references |
| Average size of all embedded media | PyMuPDF (per-object stream length) | Mean byte size of embedded media streams | **D** | Requires associating exact stream byte-boundaries with specific embedded-file/media objects — not reliably regex-approximable given nested/malformed structures |

### Structural features (~24–25, per official page and paper Table 1)

| CIC feature | Tool | Meaning | Class | Reasoning |
|---|---|---|---|---|
| "streams" keyword count | PDFiD (`stream`) | Count of `stream` tokens | **A** | Identical to HybridScan's existing `nb_stream` |
| "endstreams" keyword count | PDFiD (`endstream`) | Count of `endstream` tokens | **A** | Identical to HybridScan's existing `nb_endstream` |
| Stream objects (`/ObjStm`) | PDFiD (`/ObjStm`) | Count of object-stream markers | **A** | New for HybridScan, but a trivial addition — same raw-byte substring-count technique already used for every other `has_*` feature |
| `/JS` | PDFiD (`/JS`) | Keyword count | **B** | HybridScan has this as boolean `has_js`; count-vs-boolean is a documented, trivial transformation |
| `/JavaScript` | PDFiD (`/JavaScript`) | Keyword count | **B** | Same as above, from `has_javascript` |
| `/AA` | PDFiD (`/AA`) | Keyword count | **B** | Same, from `has_aa` |
| `/OpenAction` | PDFiD (`/OpenAction`) | Keyword count | **B** | Same, from `has_openaction` |
| `/launch` | PDFiD (`/Launch`) | Keyword count | **B** | Same, from `has_launch` |
| `/Acroform` | PDFiD (`/AcroForm`) | Keyword count | **B** | Same, from `has_acroform` |
| `/XFA` | PDFiD (`/XFA`) | Keyword count | **B** | Same, from `has_xfa` |
| `/JBig2Decode` | PDFiD (`/JBIG2Decode`) | Keyword count | **B** | Not currently in HybridScan's schema at all, but trivially addable with the exact same technique |
| `/RichMedia` | PDFiD (`/RichMedia`) | Keyword count | **B** | Same — new, but trivially addable |
| `/Trailer` (keyword) | PDFiD (`trailer`) | Count of the literal `trailer` token | **A** | New for HybridScan, trivial substring count |
| `/Xref` (keyword) | PDFiD (`xref`) | Count of the literal `xref` token | **A** | New for HybridScan, trivial substring count — **note this is explicitly distinct from "No. of Xref entries" below**, confirming CIC itself treats the raw keyword count and the parsed entry count as two different features |
| `/Startxref` | PDFiD (`startxref`) | Count of the literal `startxref` token | **A** | New for HybridScan, trivial substring count |
| No. of Xref **entries** | PyMuPDF (parsed xref table) | Actual number of entries recorded in the cross-reference table | **D** | Requires real xref-table parsing (classic or cross-reference-stream form) — not the same as counting the word "xref"; genuinely needs a parser |
| Total number of filters used | PyMuPDF (`/Filter` array resolution per object) | Count of filter usages across all streams | **D** | Requires associating `/Filter` dictionary entries with their owning objects — real parsing |
| Objects with nested filters | PyMuPDF | Count of objects using filter *arrays* (chained filters) | **D** | Same reasoning, plus array-structure awareness |
| Average stream size | Ambiguous (PyMuPDF likely) | Mean byte length of stream content | **C** | Regex-approximable (measure spans between `stream`/`endstream` token pairs), but undocumented whether CIC measures raw/compressed bytes or decompressed content, and how malformed/unmatched pairs are handled |
| No. of name obfuscations | PDFiD-adjacent, but scope unclear | Count of hex-escaped (`#xx`) PDF names | **C** | PDFiD tracks obfuscation **per tracked keyword only** (its `HexcodeCount`), a narrower scope than HybridScan's existing `nb_obfuscated_names`, which scans **every** name in the file regardless of which keyword. Whether CIC's column is the PDFiD-style narrow sum or a file-wide count (closer to HybridScan's own) is not documented — genuinely ambiguous, not guessable |
| `/URI` | Not in PDFiD's base list — custom/PyMuPDF | Keyword or annotation count | **C** | HybridScan's own `nb_uri` (regex on `/URI\b`) is a plausible proxy, but since this keyword isn't in PDFiD's documented default list, CIC's actual extraction method for it is unverified |
| `/Action` | Not in PDFiD's base list | Generic action-object count | **C** | HybridScan does not currently track a generic `/Action` count at all (only the more specific `/AA`, `/OpenAction`, `/Launch`); undocumented what CIC counts here and how it avoids double-counting the more specific action types |
| `/submitForm` | Not in PDFiD's base list | Keyword count | **C** | Same reasoning as `/URI` — not in the documented default keyword set, extraction method unverified |
| `Colors` | Ambiguous — PDFiD has only a narrow CVE-2009-3459 check, not a general count | Unclear | **D** | PDFiD's actual `/Colors`-related logic only flags an anomalously large numeric value following a `/Colors` token (a CVE-specific heuristic), **not** a general "how many times does `/Colors` appear" count. CIC's Table 1 phrasing ("Colors" listed alongside plain keyword-count features) suggests a different, undocumented definition. This is the single most ambiguous feature in the whole schema — explicitly **not guessed** |

## 5. Tally

| Classification | Count | Meaning |
|---|---|---|
| **A — exactly reproducible** | 9 | `PDF size`, `Header`, `Encryption`, `streams`, `endstreams`, `/ObjStm`, `/Trailer`(kw), `/Xref`(kw), `/Startxref`(kw) |
| **B — reproducible with documented transformation** | 12 | `Object number`, `Page number`(approx.), `Embedded files count`, `/JS`, `/JavaScript`, `/AA`, `/OpenAction`, `/launch`, `/Acroform`, `/XFA`, `/JBig2Decode`, `/RichMedia` — one of these (Page number) carries an explicit approximation caveat |
| **C — ambiguous / extraction method unclear** | 8 | `Title characters`, `Font objects`, `Average stream size`, `No. of name obfuscations`, `/URI`, `/Action`, `/submitForm` |
| **D — not reproducible without adding real PDF parsing** | 7 | `Metadata size`, `Image number`, `Text`, `Average size of embedded media`, `No. of Xref entries`, `Total filters used`, `Objects with nested filters`, `Colors` *(8 listed)* |

(37 total is the official page's count; this table accounts for 36 named
items given the sourcing gaps described in §2 — the discrepancy itself is
reported, not silently resolved.)

**Nothing in class C or D was guessed.** Every C/D classification above
states exactly which fact is missing (undocumented aggregation scope,
ambiguous metric definition, or a genuine requirement for real PDF
parsing) rather than assuming a semantics that can't be verified.

## 6. Decision

**A defensible subset exists — 21 of ~36 features (classes A+B) — but it
does not cover the majority of CIC's "general" category**, which leans
heavily on PyMuPDF's real parser for things a byte/regex extractor cannot
safely or reliably reproduce (image count, text presence, metadata size,
average embedded-media size). Per this task's explicit instruction ("Do
not keep the existing 21-feature model schema merely for backward
compatibility if it is scientifically incompatible with CIC" / "It is
acceptable to create `cic_schema.py`/`cic_features.py` instead of
replacing the existing extractor"), the class A+B subset is implemented as
a **new, separate, CIC-oriented schema** — see §7 — rather than forcing it
into or replacing `document_ml/pdf/schema.py`.

This subset is **not** presented as "the CIC dataset, minus a few
columns." It is presented for what it actually is: a set of ~20 PDFiD-style
structural keyword counts that *probably* line up with CIC's own columns
of the same conceptual kind, extracted using the same raw-byte,
no-decompression methodology CIC itself used for its PDFiD-derived columns
— but this alignment is **not yet verified against the real CSV header**,
because the real CSV was not obtained (§1). That verification is the
concrete next step (see final report, item 10).

## 7. What was and was not built

- **Built:** `document_ml/pdf/cic_schema.py` and
  `document_ml/pdf/cic_features.py` — a new, independent extractor
  implementing only the 21 class-A/B features, using the exact same
  static, no-parsing, no-decompression discipline as HybridScan's existing
  `features.py`. Not wired into `analyze.py`/`predict.py`/`analyser()` —
  this task is investigation and schema preparation only, not integration.
- **Not built:** anything for the class C/D features. Building those would
  require either (a) adding a real PDF-parsing library — a deliberate
  architecture change outside this task's authority to make unilaterally
  — or (b) guessing undocumented extraction semantics, which this task
  explicitly forbids.
- **Not trained:** `model_pdf.pkl` / any CIC-based model. No CIC data was
  ever obtained (§1).

---

## 8. Real dataset import & validation (this update)

The user supplied the actual dataset locally at
`C:\Users\user\Downloads\PDFMalware2022.parquet`. Per instruction, no other
dataset was downloaded, no raw malicious PDFs were downloaded, and
`model_pdf.pkl` was **not** trained.

### 8.1 Import

- Copied to `datasets/pdf/PDFMalware2022.parquet` inside the project.
- File size: **885,132 bytes**.
- SHA-256 (identical for both the original `Downloads` copy and the
  project copy — copy integrity verified byte-for-byte):
  `25db2059d59207d2040c5a999838514579ed4667b2b7fa39f2398dee484caf65`
- Read successfully with `pyarrow` 23.0.1 / `pandas` 3.0.1. No read errors.

### 8.2 Shape and raw schema

- **10,023 rows.**
- **34 stored columns**, one of which (`__index_level_0__`, `int64`) is a
  pandas serialization artifact (a leftover row-index column from however
  this Parquet file was produced), not a real feature — **33 meaningful
  columns** after excluding it.
- Exact columns and dtypes (as read into pandas; Parquet's own storage
  types were `dictionary<string>` for everything pandas resolves to
  `category` below):

| Column | Pandas dtype | Column | Pandas dtype |
|---|---|---|---|
| FileName | category | Encrypt | float32 |
| PdfSize | float32 | ObjStm | float32 |
| MetadataSize | float32 | JS | category |
| Pages | float32 | Javascript | category |
| XrefLength | float32 | AA | category |
| TitleCharacters | float32 | OpenAction | category |
| isEncrypted | float32 | Acroform | category |
| EmbeddedFiles | float32 | JBIG2Decode | category |
| Images | category | RichMedia | category |
| Text | category | Launch | category |
| Header | category | EmbeddedFile | category |
| Obj | category | XFA | category |
| Endobj | category | Colors | float32 |
| Stream | float32 | Class | category |
| Endstream | category | | |
| Xref | category | | |
| Trailer | float32 | | |
| StartXref | category | | |
| PageNo | category | | |

Note the exact capitalization differs in places from what §4's abstract
table assumed: the real columns are **`Javascript`** (not `JavaScript`)
and **`Acroform`** (not `AcroForm`). `FileName` holds a SHA-256-shaped hex
identifier, unique per row (10,023 unique values — presumably the original
raw PDF sample's hash) — an identifier, not a feature.

### 8.3 Label column and class distribution

**`Class`** is the label column. Exactly two values, no missing:

- Malicious: **5,555** (55.4%)
- Benign: **4,468** (44.6%)

This is very close to — but not identical to — the official UNB page's
stated "5,557 malicious and 4,468 benign" (off by 2 on the malicious
count) and the paper's own "10,022 samples." All three counts (10,023 here
vs. 10,025 official page vs. 10,022 paper) are close but distinct,
consistent with §2's already-flagged observation that the dataset has been
revised more than once. This file is best treated as **"a" version of
PDFMalware2022 / Evasive-PDFMal2022, not verified to be byte-identical to
whatever the official page currently distributes** — reasonable to use,
but this minor provenance discrepancy should be recorded, not glossed over.

### 8.4 Missing values, duplicates, constant columns

- **No true NaN/null values anywhere** — but see below, missingness is
  encoded differently.
- **Zero duplicate rows**, including zero duplicate `FileName` hashes —
  consistent with the paper's claim of deduplication.
- **No constant columns.**
- **A `-1` sentinel value is used in place of NULL** across most numeric
  columns, on two different row-subsets that line up neatly with the
  paper's stated two-tool extraction pipeline (§3):
  - **302 rows** have `-1` across the "general" columns (`PdfSize`,
    `MetadataSize`, `Pages`, `XrefLength`, `TitleCharacters`,
    `isEncrypted`, `EmbeddedFiles`) — plausibly files PyMuPDF failed to
    parse.
  - **541 rows** have `-1` across `Stream`, `Trailer`, `Encrypt`,
    `ObjStm` — plausibly a separate PDFiD-side failure set.
  - `Colors` has 564 negative values on its own.
  - Combined, **837 of 10,023 rows (8.35%)** carry a `-1` sentinel in at
    least one of the 6 float-typed columns this investigation's 21-feature
    subset maps to.

- **Important, concrete finding — missingness correlates strongly with the
  label:** of the 837 rows with a `-1` sentinel in a mapped float column,
  the label breaks down heavily toward malicious (checked directly:
  `PdfSize == -1` → 298 malicious / 4 benign; `Stream == -1` → 508
  malicious / 33 benign). **A classifier could trivially learn "did
  feature extraction fail" as a near-perfect proxy for "is malicious,"**
  without learning any real structural signal — this is a genuine
  shortcut-learning / leakage risk specific to this file's `-1`-sentinel
  encoding, not a hypothetical concern. It must be explicitly handled
  (e.g., an explicit `extraction_failed` indicator feature, or documented
  row exclusion) before training, not silently imputed.

- **The `category`-typed (string) columns carry additional, separate
  dirtiness** beyond the `-1` sentinel — confirmed by direct inspection of
  unique values:
  - A **compound `"N(M)"` notation** (e.g. `"1(1)"`, `"12(2)"`) appears in
    `JS`, `Javascript`, `AA`, `OpenAction`, `Acroform`, `JBIG2Decode`,
    `RichMedia`, `Launch`, `EmbeddedFile`, `XFA`, `PageNo`, `Endstream`.
    This matches PDFiD's own output format exactly — recall §3's fetched
    XML example: `<Keyword Count="7" HexcodeCount="0" .../>` — this looks
    like an un-split `"Count(HexcodeCount)"` string that was never
    separated into two numeric columns before this file was produced.
  - **Literal leaked text fragments** appear in supposedly-numeric
    columns: `Xref` contains the literal string `"pdfid.py"` (22 rows);
    `StartXref` contains `"bytes[endHeader]"` (22 rows); `Obj` contains
    filename-looking fragments like `"_Pro_Rodeo_Pix_"` (24 rows);
    `Javascript` contains a bare `">"` (part of the 117 dirty rows);
    `PageNo` contains the literal word `"list"` (part of 137 dirty rows).
    These read as an upstream CSV/column-alignment bug (e.g. an unescaped
    delimiter in a filename or error message spilling into the next
    column), not intentional encoding.
  - Total non-clean-integer rows across the 14 mapped `category` columns:
    **348 of 10,023 (3.47%)**, of which **346 are Malicious, 2 are
    Benign** — again heavily skewed, reinforcing the leakage concern above.
  - Combined with the float-sentinel rows: **1,127 of 10,023 rows
    (11.24%) need some form of cleaning** across the 20 non-`Header`
    mapped columns, and of those, **1,090 are Malicious vs. 37 Benign**
    (96.7% malicious) — the dirtiness itself is almost a malicious-class
    marker.

- **`Header`** (mapped from this investigation's `header_present`) is the
  single messiest column: only **8,836 of 10,023 rows (88.2%)** contain a
  cleanly-parseable `"\t%PDF-x.y"` string (note: every value has a leading
  tab character). The remaining 11.8% include genuinely malformed/garbage
  values: `"\ta"`, `"\tyour"`, `"\t2]"`, `"\t%PDF-1."` (truncated),
  `"\t%PDF-aaa"`, `"\t%PDF-11113"` (nonsensical version numbers), plus
  bare `"0"`, `"1"`, `"-1"`. This is not a boolean-friendly column at all
  in its raw form — reproducing even a simple `header_present` boolean
  from it requires a real cleaning decision (e.g., regex-match a
  well-formed version string; treat anything else, including `-1`/`0`/`1`,
  as "malformed/unknown"), not a straight rename.

- **`Text`** (excluded from the 21-feature subset already, classed D) is
  confirmed genuinely mixed-type in practice: `No` (5,398), `Yes` (3,761),
  `unclear` (549), `-1` (302), `0` (13) — five different value kinds in one
  column, validating the earlier "ambiguous/ D" classification concretely.

### 8.5 Comparison against `document_ml/pdf/cic_schema.py`

**All 21 features in `CIC_FEATURES` have a real, identifiable counterpart
column in this file** — the abstract compatibility analysis in §4–§6 is
directionally confirmed. However, none of the 20 numeric-intended mapped
columns are usable **as-is**, and one (`Header`) needs real derivation
logic rather than a rename:

| `cic_schema.py` name | Real column | Present? | Usable as-is? |
|---|---|---|---|
| `pdf_size` | `PdfSize` | Yes | No — `-1` sentinel (302 rows) |
| `header_present` | `Header` | Yes, but semantically different (raw string, not boolean) | No — needs regex derivation; 11.8% malformed even then |
| `is_encrypted` | `isEncrypted` | Yes | No — `-1` sentinel; also **range is 0–4, not boolean 0/1 as assumed** (new discrepancy found) |
| `nb_stream_kw` | `Stream` | Yes | No — `-1` sentinel (541-row group) |
| `nb_endstream_kw` | `Endstream` | Yes | No — compound `N(M)` notation present |
| `nb_objstm_kw` | `ObjStm` | Yes | No — `-1` sentinel |
| `nb_trailer_kw` | `Trailer` | Yes | No — `-1` sentinel |
| `nb_xref_kw` | `Xref` | Yes | No — contains literal `"pdfid.py"` (22 rows) |
| `nb_startxref_kw` | `StartXref` | Yes | No — contains literal `"bytes[endHeader]"` (22 rows) |
| `nb_obj_kw` | `Obj` | Yes | No — filename-fragment junk (24 rows) |
| `nb_page_approx` | `PageNo` (**not** `Pages` — see below) | Yes | No — compound `N(M)` notation, plus literal `"list"` |
| `nb_embeddedfile_kw` | `EmbeddedFile` | Yes | No — compound `N(M)` notation |
| `nb_js_kw` | `JS` | Yes | No — compound `N(M)` notation (worst affected: 229 dirty rows) |
| `nb_javascript_kw` | `Javascript` | Yes (note capitalization) | No — compound notation + stray `">"` |
| `nb_aa_kw` | `AA` | Yes | No — compound notation (14 rows) |
| `nb_openaction_kw` | `OpenAction` | Yes | No — compound notation (88 rows) |
| `nb_launch_kw` | `Launch` | Yes | No — compound notation (10 rows) |
| `nb_acroform_kw` | `Acroform` | Yes (note capitalization) | No — compound notation (13 rows) |
| `nb_xfa_kw` | `XFA` | Yes | No — compound notation (20 rows) |
| `nb_jbig2decode_kw` | `JBIG2Decode` | Yes | No — compound notation (6 rows) |
| `nb_richmedia_kw` | `RichMedia` | Yes | No — compound notation (4 rows) |

**One mapping correction found:** this investigation's `nb_page_approx`
(a regex-based approximate page/`"/Type /Page"` count) conceptually
matches the real dataset's **`PageNo`** column (structural, `/Page`
keyword count — PDFiD's own base keyword list includes `/Page`, confirmed
in §3), **not** `Pages` (which is a separate, "general"-category float
column, presumably a true PyMuPDF page-tree count, and was never part of
the 21-feature subset). Both `PageNo` and `Pages` exist as distinct real
columns, confirming §4's General-vs-Structural distinction was correct in
substance, and refining exactly which one `nb_page_approx` should target.

**New discrepancy found, not previously known:** `isEncrypted`'s real
range is **0 to 4**, not a clean boolean — meaning HybridScan's own
`is_encrypted`/`has_encryption`-style boolean features are a
simplification relative to what this real column actually encodes; the
exact meaning of values 2–4 is undocumented and not guessed here.

### 8.6 Is the proposed 21-feature subset genuinely compatible?

**Conceptually yes, mechanically no — yet.** Every proposed feature maps
to a real column (a meaningfully stronger result than §4–§6's
documentation-only analysis could prove), but **every single one of those
20 numeric-intended columns requires a cleaning/coercion step before it
can be used**, and the dirtiness is not random — it is concentrated
overwhelmingly in the malicious class (up to 99.4% malicious among dirty
rows in some columns), which is a **leakage risk that must be designed
around, not casually cleaned away**. Recommended (not applied — out of
this task's scope):

1. Update `cic_schema.py`'s documentation to record the **exact** real
   column names (fixing `Javascript`/`Acroform` capitalization, and
   redirecting `nb_page_approx` to `PageNo` instead of `Pages`).
2. Write an explicit cleaning step — not part of `cic_features.py` (which
   extracts from raw PDFs, a different job) but a **dataset-preparation**
   step operating on this CSV/Parquet before it reaches `train.py`:
   coerce each mapped column to numeric, treating `-1` and non-numeric
   junk as missing; parse the compound `"N(M)"` notation into (at minimum)
   the leading count; decide and document how missing values are handled
   (impute? drop the row? add an explicit `extraction_failed` flag column
   so the model can't silently key off it as a shortcut?).
3. Re-derive `header_present` from `Header` via an explicit regex against
   the well-formed `"\t%PDF-x.y"` pattern, with malformed/anomalous values
   treated as `0` (or a third documented state), not silently coerced.
4. Explicitly decide the leakage question in §8.4 before training — this
   is the single most important open item, more consequential than any
   individual column's cleaning.

None of this was implemented in this pass — this task was import and
validation only.
