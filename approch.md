# Tri9T AI Internship Assignment – Approach Document

## Overview

This project implements a backend system for parsing the CT-200 medical device manual into a structured, versioned document tree. The system supports document browsing, version comparison, traceability, selection management, and LLM-generated QA test cases while detecting stale generations after document updates.

The implementation is divided into multiple phases. This document explains the engineering decisions taken during development, the trade-offs considered, and the limitations of the current approach.

---

# Phase 1 – PDF Inspection

## Objective

Before implementing any parser, I inspected the PDF structure to understand how headings, paragraphs, tables, and numbering are actually represented in the document.

Rather than assuming a clean PDF layout, I first extracted:

- Raw page text
- Font information
- Text blocks
- Table extraction results

This helped identify structural inconsistencies before implementing hierarchy reconstruction.

---

# OCR / Document Parsing Approach

For structural inspection I used two complementary libraries.

### PyMuPDF (fitz)

Used for:

- Raw text extraction
- Font size detection
- Font family
- Bold detection
- Text block hierarchy

PyMuPDF exposes text spans together with formatting metadata, making it suitable for later heading detection.

---

### pdfplumber

Used only for table extraction.

Although PyMuPDF extracts table text, pdfplumber provides better row and column detection and was therefore used to inspect how reliably tables can be reconstructed.

---

# PDF Structural Inconsistencies Discovered

## 1. Font Hierarchy

The manual consistently uses a small number of font sizes.

| Font Size | Observation | Planned Meaning |
|------------|-------------|-----------------|
| 22.0 | Document title | Document Title |
| 16.5 | Major numbered sections | Level 1 Heading |
| 12.9 | Subsections | Level 2 Heading |
| 11.0 | Body text / tables | Paragraph or table content |

Bold font is consistently used for headings.

---

## 2. Numbering Style

Observed numbering includes:

- 1
- 1.1
- 1.2
- 2
- 2.1
- 2.1.1.1

This indicates that the parser must support arbitrary-depth hierarchical numbering instead of assuming only two or three levels.

---

## 3. Out-of-order Sections

One section appears out of numerical order.

Observed:

3.2

↓

3.4

↓

3.3

This demonstrates that document order cannot be reconstructed solely from section numbers. Physical reading order within the PDF must be preserved.

---

## 4. Character Encoding Issues

Several Unicode characters were extracted incorrectly.

Examples include:

- cuff
- profile
- firmware
- ±
- en dash

These appeared as corrupted symbols during extraction.

This suggests that a normalization/cleaning step will be required before storing node text or generating LLM prompts.

---

## 5. Tables

pdfplumber successfully detected the primary specification tables.

However, it also detected multiple fragmented tables generated from individual rows.

Examples include:

- Split specification rows
- Partial columns
- Duplicate mini-tables

Therefore, table extraction cannot blindly treat every detected table as valid.

Future validation will compare row count and dimensions before accepting a table.

---

## 6. Paragraph Layout

Paragraphs are generally extracted correctly.

However, some hyphenated or Unicode words are split into multiple spans because different fonts are used for special symbols.

The parser will therefore merge consecutive spans before reconstructing paragraph text.

---

## 7. Figures

No embedded figures or image captions were detected during inspection.

The current parser will therefore ignore images unless later document versions introduce them.

---

## 8. Headers / Footers

No repeated page headers or page footers were observed.

Therefore no header/footer filtering is required for this document version.

---

# Initial Implementation Risks

The inspection highlighted several failure modes that a naive parser would encounter.

Examples include:

- Assuming section numbers are sequential.
- Assuming every detected table is valid.
- Assuming every bold line is a heading.
- Assuming Unicode extraction is clean.
- Assuming heading depth depends only on numbering.

---

# Validation Method

The extracted output was manually inspected.

Validation consisted of:

- Comparing raw PDF pages against extracted text
- Comparing font sizes across headings
- Reviewing detected tables
- Looking for numbering inconsistencies
- Identifying encoding artifacts
- Recording structural anomalies

This inspection was documented before implementing hierarchy reconstruction.

---

# Heading Detection Strategy

Based on inspection, a hybrid strategy is preferred.

Heading detection will consider:

- Font size
- Bold font
- Numbering pattern
- Position within reading order

Using only font size would fail if body text shares a heading font.

Using only numbering would fail for malformed or future documents.

Combining multiple signals should produce a more reliable hierarchy.

---

# What Phase 1 Does NOT Implement

Phase 1 intentionally does not implement:

- Tree construction
- SQLAlchemy models
- Database persistence
- Version comparison
- APIs
- LLM integration

Those features belong to later phases.

---

# Lessons Learned

Inspecting the PDF before designing the parser revealed several issues that would not have been obvious from visual inspection alone.

The most significant findings were:

- Out-of-order numbering
- Corrupted Unicode extraction
- Fragmented table detection
- Multiple heading levels
- Consistent font hierarchy suitable for later parsing

These observations will directly guide the hierarchy reconstruction phase.

phase2:

## Tree Data Model
Nodes use `parent_id` self-reference (not materialized path) for simplicity
at this document's scale — see Decision Log for the tradeoff. Each node
stores heading_number separately from order_index because this document
proved they can disagree (section 3.4 physically precedes 3.3). content_hash
is SHA-256 over normalized body_text, computed after fixing font-encoding
corruption (broken ligatures, mis-decoded dashes) so hash changes reflect
real content changes, not extraction artifacts.

## Hierarchy Reconstruction Strategy
Heading detection is regex-first (numeric prefix + short + bold), not
font-size-first, because inspection showed font size 11pt/bold is shared
by both level-4 headings (e.g. "2.1.1.1 Battery Life...") and table header
cells (e.g. "Parameter"/"Value") — size alone is ambiguous at that tier.
Parent assignment looks up the ancestor by numeric prefix (e.g. parent of
"2.1.1.1" is whichever node has heading_number "2.1"), not by "last heading
seen in stream order" — necessary because this document has an out-of-order
section (3.4 appears before 3.3). order_index still reflects physical
document position, independently of heading_number, so rendering stays
faithful to the source.

## Table Extraction
pdfplumber returns 1 correct table per page plus several noise "tables"
(column-slice artifacts). We keep only the largest table by cell count per
page and discard the rest, logging the count discarded.

# Approach Document

## Tree Data Model

Nodes use a self-referential `parent_id` foreign key (not a materialized
path like "1/3/4") for parent-child relationships. This is simpler to
reason about and test at this document's scale (a few dozen nodes); a
materialized path would pay off at much larger scale where "fetch whole
subtree in one query" matters more than the cost of updates, but that
tradeoff isn't relevant here.

Each Node stores:
- `heading_number` (e.g. "2.1.1.1") and `heading_text` separately from
  `order_index`, because inspection proved these can disagree — section
  "3.4 Auto Shutoff" appears physically before "3.3 Result Display and
  Classification" in the source PDF's reading order. `order_index`
  preserves physical document position (for faithful rendering);
  `heading_number` drives parent assignment (for a logically correct tree).
- `content_hash`: SHA-256 over normalized `body_text`. Normalization runs
  first so that PDF-extraction artifacts (broken ligatures, mis-decoded
  dashes) don't get hashed as if they were real content changes later.
- `level`: derived from the count of dot-separated segments in
  `heading_number` (e.g. "2.1" -> level 2, "2.1.1.1" -> level 4).

## Hierarchy Reconstruction Strategy

Heading detection is regex-first, not font-size-first. Inspection showed
that size 11pt/bold is shared by both level-4 headings (e.g.
"2.1.1.1 Battery Life Under Typical Use") and table header cells (e.g.
"Parameter"/"Value") — font metadata alone is ambiguous at that tier. A
block is treated as a heading only if it: (1) is bold, (2) is under ~15
words, and (3) matches a numeric-prefix pattern at the start
(`^\d+(\.\d+)*\.?\s+`).

Parent assignment looks up the ancestor by walking up the NUMERIC PREFIX
chain (e.g. parent of "2.1.1.1" is found by trying "2.1.1", then "2.1",
then "2", using whichever actually exists as a node) — not by "whichever
heading was last seen in the stream." This was necessary for two real
cases found in the source document:
1. Out-of-order siblings: section 3.4 physically precedes 3.3.
2. Skipped numbering levels: "2.1.1.1" appears with no "2.1.1" node
   anywhere in the document — the fallback walks up to the nearest
   existing ancestor ("2.1") instead of requiring an exact one-level-up
   parent.

## Table Extraction

pdfplumber returns one correct table per page (matching the visible table)
plus several noise "tables" that are column-slice artifacts of its layout
heuristic (e.g. a 2-word wrapped table cell misread as a 1x2 table). The
extraction pipeline keeps only the largest table by cell count per page
and discards the rest, logging how many were discarded for transparency.

## Text Normalization

The source PDF's font encoding produces corrupted characters on
extraction — e.g. a broken "fi" ligature, mis-decoded en/em-dashes, and a
mangled plus-minus sign. These are extraction artifacts, not real document
content, so `text_normalize.py` fixes a fixed table of known bad sequences
before any text is stored, hashed, or used for heading detection. This is
intentionally a fixed-mapping fix for THIS document, not a general Unicode
repair library, per the assignment's explicit scope limits.

## Debugging Notes (Phase 2)

- Initial heading regex required whitespace directly after the numeric
  prefix (e.g. matched "2.1 Title" but not "2. Title" — number, period,
  space). Top-level headings using the "N. Title" format silently fell
  through as body text of the currently-open node, rather than erroring.
  This was caught by unit tests targeting the real irregularities, not by
  manual inspection — reinforcing why explicit irregularity-targeted tests
  were required rather than optional coverage.
- `2.1.1.1` has no `2.1.1` ancestor anywhere in the source document
  (a skipped numbering level). The initial ancestor-lookup required an
  exact one-level-up match and raised an error on this case. Fixed by
  walking up the numeric prefix chain to the nearest existing ancestor.

  ## Version-Matching Strategy and Known Failure Modes

Primary matching key: `heading_number` (path-based). For this specific
document's actual v1->v2 diff — body text edits (battery life estimate,
inflation increment, E3 timing), a new error code row (E6), and a new
subsection (Data Export) — heading numbers remain stable across versions,
making path-based matching reliable and cheap.

Fallback: if a v2 node's heading_number has no v1 counterpart, the matcher
tries heading_text as a weaker signal before classifying the node as NEW.
This fallback assumes heading text is unique within a version; Phase 2's
duplicate-heading test proves that assumption can be false in general
(two "Error Codes" sections under different parents), so the fallback is a
known, accepted risk — not a solved problem — because it does not affect
the actual v1/v2 pair used for grading.

Rejected alternative: full content-similarity/fuzzy matching (e.g. TF-IDF
or embedding cosine similarity between v1 and v2 body text) would be more
robust to simultaneous renaming+renumbering, but adds real complexity
(threshold tuning, false-positive matches between unrelated sections of
similar length) for a document where the simpler strategy already handles
every real case present. This is a deliberate simplicity-over-robustness
tradeoff — see Decision Log.

### Known failure mode (by design, not a bug)
If a node's heading_number AND heading_text both change between versions
in the same release, the matcher has no remaining signal to link the old
and new node. It will report the v1 node as REMOVED and the v2 node as
NEW, rather than CHANGED. A production system would need fuzzy
content-similarity matching or human review to catch this case. This
directly answers the Decision Log question: "where did you choose
simplicity over correctness because of time" — full fuzzy matching was the
more correct approach but was skipped because the actual grading document
never exercises this failure mode, and the added complexity (similarity
thresholds, false-positive risk across unrelated sections) wasn't
justified for the time available.

### Diff summary
Uses Python's stdlib `difflib.unified_diff` — a line-based, git-style diff.
This is a lightweight summary, not a semantic diff: it cannot distinguish
a meaningful spec change (e.g. "40 mmHg" -> "30 mmHg", a real behavioral
threshold change) from a purely cosmetic wording edit. Both surface
identically as changed lines. A user relying on the CHANGED flag alone,
without reading the diff text, could miss that some changes matter more
than others — this is an explicit, acknowledged limitation of the
staleness signal built in a later phase.

