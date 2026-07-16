---

# Phase 0 — Environment & Project Scaffold

Set up a FastAPI project skeleton (`app/models`, `app/schemas`, `app/services`,
`app/api`, `data`, `tests`, `docs`), a Python virtual environment, baseline
dependencies (fastapi, sqlalchemy, pydantic, pymupdf, pdfplumber, pytest,
python-dotenv, requests/groq/huggingface_hub), and git initialized with a
`.gitignore` excluding `venv/`, `__pycache__/`, `*.pyc`, `.env`, `*.db`, and
`.pytest_cache/`.

**Lesson learned (see Debugging Notes further down):** `.gitignore` only
prevents *new* files from being tracked — it does not retroactively untrack
files already committed. This mattered twice in this project (`.pyc`/`.db`
files in Phase 3, and `.env` itself in Phase 5) and both required
`git rm --cached` plus a commit amend to fully resolve. This is documented
in more detail under Phase 5.

---

# Phase 1 — PDF Inspection

## Objective

Before implementing any parser, the PDF's actual structure was inspected —
not assumed — to catch irregularities before writing hierarchy-reconstruction
logic.

## OCR / Document Parsing Approach

**PyMuPDF (fitz)** — used for raw text extraction, font size, font family,
bold detection, and text block/span structure. Exposes formatting metadata
alongside text, which later heading detection depends on.

**pdfplumber** — used only for table extraction, since it provides better
row/column detection than PyMuPDF for tabular content.

## PDF Structural Inconsistencies Discovered

**1. Font hierarchy** — a small, consistent set of font sizes maps cleanly
to document structure at first glance:

| Font Size | Observation | Planned Meaning |
|-----------|-------------|------------------|
| 22.0 | Document title | Document Title |
| 16.5 | Major numbered sections | Level 1 Heading |
| 12.9 | Subsections | Level 2 Heading |
| 11.0 | Body text / tables / deep headings | Ambiguous — see below |

Bold font is consistently used for headings, but size 11pt/bold is shared
by BOTH level-4 headings (e.g. "2.1.1.1 Battery Life Under Typical Use")
and table header cells (e.g. "Parameter", "Code") — font metadata alone
cannot disambiguate at that tier.

**2. Numbering style** — observed numbering includes single-level (`1`),
two-level (`1.1`), and four-level (`2.1.1.1`) depth, with no `2.1.1` node
ever appearing between them — a skipped numbering level. The parser must
support arbitrary-depth hierarchical numbering, not a fixed 2–3 level
assumption.

**3. Out-of-order sections** — section `3.4` (Auto Shutoff) appears
physically before `3.3` (Result Display and Classification) in the PDF's
reading order. Document order cannot be reconstructed solely from section
numbers; physical reading order must be preserved independently.

**4. Character encoding issues** — several words extracted with corrupted
characters: broken "fi"/"ff" ligatures (e.g. "profile" → "pro∩¼üle", "cuff"
→ "cu∩¼Ç"), mis-decoded en/em-dashes, and a mangled plus-minus sign. These
are PDF font-encoding extraction artifacts, not real document content, and
require a normalization pass before storage or hashing.

**5. Tables** — pdfplumber detects the correct primary table per page, but
also returns several fragmented "tables" that are column-slice artifacts
of its layout heuristic (e.g. a two-word wrapped cell misread as a 1×2
table). Not every detected table can be treated as valid; only the largest
table by cell count per page is kept.

**6. Paragraph layout** — mostly extracted correctly, though some
hyphenated/Unicode words split into multiple spans due to font switching
mid-word (the ligature character uses a different font than surrounding
text).

**7. Figures** — none present in this document version; parser ignores
images for now.

**8. Headers/footers** — none observed; no filtering needed.

## Heading Detection Strategy (Decision)

Chosen: **regex-first, font-size as a secondary signal, not primary.** A
block is treated as a heading only if it (1) is bold, (2) is short (under
~15 words), and (3) matches a numeric-prefix pattern at the start of the
line (`^\d+(\.\d+)*\.?\s+`). This sidesteps the font-size ambiguity
entirely — a table header cell like "Parameter" is bold/11pt but does not
match the numeric-prefix pattern, so it's correctly excluded.

## What Phase 1 Does Not Implement

No tree construction, no database models/persistence, no version
comparison, no APIs, no LLM integration — those are Phases 2–5.

---

# Phase 2 — Tree Data Model & Hierarchy Reconstruction

## Tree Data Model

Nodes use a self-referential `parent_id` foreign key (not a materialized
path like `"1/3/4"`). This is simpler to reason about and test at this
document's scale (~30 nodes); a materialized path would pay off at much
larger scale where "fetch whole subtree in one query" matters more than
the cost of path updates — that tradeoff isn't relevant here (see Decision
Log for more on this tradeoff).

Each `Node` stores:
- `heading_number` (e.g. `"2.1.1.1"`) and `heading_text` separately from
  `order_index`, because these can disagree — section `3.4` physically
  precedes `3.3` in reading order. `order_index` preserves physical
  document position for faithful rendering; `heading_number` drives parent
  assignment for a logically correct tree.
- `content_hash`: SHA-256 over *normalized* `body_text`. Normalization
  runs first so that PDF-extraction artifacts (broken ligatures,
  mis-decoded dashes) are never mistaken for real content changes later
  during version comparison.
- `level`: derived from the count of dot-separated segments in
  `heading_number` (e.g. `"2.1"` → level 2, `"2.1.1.1"` → level 4).

## Hierarchy Reconstruction Strategy

Heading detection is regex-first, not font-size-first (see Phase 1
rationale). Parent assignment looks up the ancestor by walking up the
**numeric prefix chain** (e.g. parent of `"2.1.1.1"` is found by trying
`"2.1.1"`, then `"2.1"`, then `"2"`, using whichever actually exists as a
node) — not by "whichever heading was last seen in the stream." This
was necessary for two real cases:
1. **Out-of-order siblings**: `3.4` physically precedes `3.3`.
2. **Skipped numbering levels**: `"2.1.1.1"` appears with no `"2.1.1"`
   node anywhere in the document — the fallback walks up to the nearest
   existing ancestor (`"2.1"`) instead of requiring an exact one-level-up
   parent.

## Table Extraction

pdfplumber returns one correct table per page plus several noise "tables"
(column-slice artifacts). The extraction pipeline keeps only the largest
table by cell count per page and discards the rest, logging the count
discarded for transparency.

## Text Normalization

`text_normalize.py` fixes a **fixed table** of known bad character
sequences (broken ligatures, mis-decoded dashes, mangled plus-minus)
before any text is stored, hashed, or used for heading detection. This is
intentionally a fixed-mapping fix for THIS document, not a general Unicode
repair library, per the assignment's explicit scope limits.

## Debugging Notes (Phase 2)

- **Bug 1:** Initial heading regex required whitespace directly after the
  numeric prefix (matched `"2.1 Title"` but not `"2. Title"` — number,
  period, space). Top-level headings using the `"N. Title"` format
  silently fell through as body text of the currently-open node, rather
  than erroring. Caught by unit tests targeting the real irregularities,
  not by manual inspection — reinforcing why explicit irregularity-
  targeted tests were required, not optional coverage. Fixed with an
  optional `\.?` in the regex before the whitespace.
- **Bug 2:** `"2.1.1.1"` has no `"2.1.1"` ancestor anywhere in the source
  document (a skipped numbering level). The initial ancestor-lookup
  required an exact one-level-up match and raised an error on this case.
  Fixed by walking up the numeric prefix chain to the nearest existing
  ancestor instead of requiring an exact parent match.
  ---

# Phase 3 — Document Versioning & Change Detection

## Re-ingestion Flow

Re-ingesting a new PDF version requires no special-cased logic beyond
Phase 2's existing pipeline: `persist_tree()` always creates a fresh
`DocumentVersion` row and a fresh set of `Node` rows on every call — it
never updates or deletes prior rows. Running
`python -m app.services.run_ingest data/ct200_manual_v2.pdf v2` after v1
has already been ingested simply adds `DocumentVersion id=2` alongside
`id=1`, leaving v1's rows completely untouched. This was a deliberate
outcome of Phase 2's design, not something built new in Phase 3.

## Version-Matching Strategy and Known Failure Modes

**Primary matching key: `heading_number` (path-based).** For this
document's actual v1→v2 diff — body text edits (battery life estimate,
inflation increment, E3 timing), a new error code row (E6), and a new
subsection (Data Export) — heading numbers remain stable across versions,
making path-based matching reliable and cheap.

**Fallback: `heading_text`.** If a v2 node's `heading_number` has no v1
counterpart, the matcher tries `heading_text` as a weaker signal before
classifying the node as NEW. This fallback assumes heading text is unique
within a version; Phase 2's duplicate-heading test proves that assumption
can be false in general (two "Error Codes" sections under different
parents), so this fallback is a **known, accepted risk** — not a solved
problem — because it does not affect the actual v1/v2 pair used for
grading.

**Rejected alternative: full content-similarity/fuzzy matching** (e.g.
TF-IDF or embedding cosine similarity between v1 and v2 body text) would
be more robust to simultaneous renaming+renumbering, but adds real
complexity (threshold tuning, false-positive matches between unrelated
sections of similar length) for a document where the simpler strategy
already handles every real case present. This is a deliberate
simplicity-over-robustness tradeoff (see Decision Log).

### Known failure mode (by design, not a bug)

If a node's `heading_number` AND `heading_text` both change between
versions in the same release, the matcher has no remaining signal to link
the old and new node. It will report the v1 node as REMOVED and the v2
node as NEW, rather than CHANGED. A production system would need fuzzy
content-similarity matching or human review to catch this case. This
directly answers the Decision Log question about where simplicity was
chosen over correctness due to time — full fuzzy matching is the more
correct approach but was skipped because the actual grading document
never exercises this failure mode.

### Diff Summary

Uses Python's stdlib `difflib.unified_diff` — a line-based, git-style
diff. This is a **lightweight summary, not a semantic diff**: it cannot
distinguish a meaningful spec change (e.g. "40 mmHg" → "30 mmHg", a real
behavioral threshold change) from a purely cosmetic wording edit. Both
surface identically as changed lines. A user relying on the CHANGED flag
alone, without reading the diff text, could miss that some changes matter
more than others — this limitation resurfaces directly in Phase 5's
staleness signal.

---

# Phase 4 — Browse API & Selection API

## Browse API Design

`version="latest"` resolves to the highest `DocumentVersion.id` (most
recently ingested), so callers never need to track version numbers to see
current content — they can also pass an explicit label (e.g. `"v1"`) to
view a prior version.

Search uses SQLite's `LIKE` (case-insensitive via `ilike`), not FTS5 —
the document is small enough (~30 nodes) that full-text indexing overhead
isn't justified. This would need revisiting if the document set grew
significantly (see Decision Log).

The `/browse/nodes/{node_id}/diff` endpoint reuses Phase 3's
`version_matcher` and `diff_summary` logic, scoped down to a single node —
comparing it against whichever adjacent version exists (next version if
the node is from an older version, previous version if it's from the
latest).

## Selection Model & Version-Pinning

A `Selection` has an `id`, `name`, `created_at`, and a list of
`SelectionItem` rows, each storing an explicit `(node_id,
document_version_id)` pair.

**Why store `document_version_id` explicitly, rather than deriving it from
the node at read time:** this is the mechanism that satisfies the
assignment's requirement that old selections resolve to the exact text
they were created against, even after later re-ingestion. Since
re-ingestion creates entirely new `Node` rows (Phase 3) rather than
mutating existing ones, a `SelectionItem`'s pinned `node_id` permanently
points at the original row — whose `body_text`/`content_hash` never
change — regardless of how many later versions are ingested. Storing
`document_version_id` redundantly (rather than relying on a join through
`node_id`) also makes each pin self-documenting and protects against any
future change to node-mutation rules silently breaking the pin's
intent.

`POST /selections` resolves each submitted `node_id` to its **current**
`document_version_id` at creation time and stores that pin immediately —
the pin is fixed at creation, not re-evaluated later.

---

# Debugging Notes (Phase 4)

- **Directory/environment confusion:** several `ModuleNotFoundError`
  issues during this phase traced back to running Python commands from
  the parent folder (`AI_OCR`) instead of the project root
  (`AI_OCR/tri9t-ct200-backend`), and/or with the venv not activated.
  Lesson: always verify both the working directory AND the `(venv)`
  prefix are correct before debugging an import error as a code problem.
- **Missing table on server start:** `POST /selections` initially failed
  with `sqlite3.OperationalError: no such table: selections`. Table
  creation (`Base.metadata.create_all`) had only ever been called inside
  `run_ingest.py`, never on FastAPI startup — so the new `Selection`/
  `SelectionItem` models were never materialized as real tables when
  running the server directly. Fixed by calling `create_all` in
  `app/main.py` on startup (safe to call repeatedly — it only creates
  missing tables, never touches existing data) and ensuring all model
  modules are imported before that call so SQLAlchemy's metadata actually
  knows about them.
- **Pydantic response validation:** `_to_selection_out` initially returned
  plain dicts inside a field typed as a list of `SelectionItemOut`
  objects, which failed response serialization. Fixed by constructing
  explicit `SelectionItemOut(...)` instances instead of raw dicts.
  ---

# Phase 5 — LLM Generation, Staleness Detection, Retrieval API

## LLM Provider Choice (and a mid-project switch)

Originally implemented against **Groq's API** (chosen for its free tier
and OpenAI-compatible interface). After extensive debugging of a
persistent `401 expired_api_key` error that survived multiple key
rotations, direct raw-HTTP verification of the same key succeeding
outside the app, and ruling out stale processes/terminal sessions, the
root cause was eventually identified: a **stale Windows User-level
environment variable** named `GROQ_API_KEY` was silently taking
precedence over the value in `.env`, because `python-dotenv`'s
`load_dotenv()` does not override variables that already exist in
`os.environ` by default. The app was therefore always sending an old,
invalid key, regardless of how many times `.env` was corrected.

Given the time already spent, the decision was made to **switch to
Hugging Face's Inference API** instead — same architecture, cleaner
environment (no lingering OS-level variable conflict), and a comparable
free tier. This is documented as a real engineering decision, not just a
technical footnote: knowing when to cut losses on a specific tool/vendor
and switch rather than continuing to debug indefinitely is itself part of
good engineering judgment under time constraints.

## LLM Prompt Design

The system prompt instructs the model to act as a QA engineer and return
**only valid JSON** (no prose, no markdown fences) matching an explicit
schema: `test_cases: [{id, title, steps, expected_result}]`, with 3–5
entries required. The user message contains the reconstructed selection
text (concatenated node headings + body text). `temperature=0.3` is used
to favor consistent, concrete output over creative variation, appropriate
for QA test case generation rather than open-ended writing.

## Structured-Output Validation & Retry Strategy

Raw LLM output is first passed through `_extract_json()`, which strips
common wrapping artifacts (markdown code fences) before parsing. The
parsed JSON is then validated against a Pydantic model (`TestCaseList`,
which enforces `min_length=3, max_length=5` on `test_cases`).

**Retry policy: retry once, then fail with a clear error** — not zero
retries, not infinite retries. Rationale: a single malformed response is
often a one-off sampling glitch (the model occasionally adds stray text
despite instructions); retrying once catches that cheaply. If it fails
twice, that signals something structural (bad prompt, provider issue,
genuine schema mismatch) — looping further burns time/cost without fixing
the underlying problem. The API endpoint converts a final failure into an
HTTP 502, so the caller gets a clear, actionable error rather than a
silent empty response or an infinite hang.

## NoSQL Store Design

Generated test cases are stored in a flat JSON file
(`data/generations.json`) rather than MongoDB. **Justification:** this
project is scoped for local development and grading; a JSON file avoids
requiring the grader to provision a MongoDB/Atlas instance just to run the
demo. A real NoSQL store would matter at higher write volume or under
concurrent access — this is an explicit, acknowledged simplification (see
Decision Log), not a claim that a JSON file is the "correct" choice at
scale.

Each stored record: `generation_id`, `selection_id`, `generated_at`,
`source_nodes` (list of `{node_id, content_hash}` — the hash **at
generation time**), and `test_cases`.

## Duplicate-Submission Policy

`POST /generations/selections/{id}` defaults to **returning the existing
generation** if one already exists for that selection, rather than
regenerating. Rationale: a selection is pinned to specific node+version
text (Phase 4); resubmitting the same selection means re-deriving output
from **identical** source text, so regenerating by default would burn
LLM API cost/time for no new information. A `force=true` query parameter
allows an explicit fresh generation (e.g. to get different phrasing, or
after a prompt improvement) — confirmed working via manual testing
(second POST to the same selection returned
`"status":"existing_generation_returned"` without a new LLM call).

## Staleness Detection

For each source node recorded at generation time, the system finds that
node's **current counterpart in the latest ingested version** (via Phase
3's `version_matcher`, matching on `heading_number` with `heading_text`
fallback) and compares its **current** `content_hash` against the hash
stored at generation time. If any source node's hash has changed, the
whole generation is flagged `is_stale: true`, with a per-node reason
(`content_changed`, `node_removed_in_latest_version`, or `node_deleted`).

**KNOWN LIMITATION (stated honestly, as required):** this is a binary
hash comparison. A one-word wording fix and a safety-critical threshold
change (e.g. "40 mmHg" → "30 mmHg") both flip the hash identically and
are reported with the same "stale" severity — the system has no way to
distinguish cosmetic edits from substantive ones without semantic
diffing, which is out of scope here. A user should always read the
accompanying diff text (Phase 3/4) rather than trusting the stale flag's
severity implicitly.

## Debugging Notes (Phase 5)

- **Staleness bug (found via manual testing, not a test suite):** the
  initial `check_staleness` implementation re-queried the **same**
  `node_id` recorded at generation time and compared its hash to itself —
  since re-ingestion creates entirely new `Node` rows rather than
  mutating existing ones (Phase 2/3 design), that original row's hash
  never changes, making `is_stale` **permanently false** regardless of
  real document changes. This was caught by manually re-ingesting v2 and
  observing staleness incorrectly stayed `false` for a node with a known
  text change (Battery Life: "300 cycles/15%" → "250 cycles/10%"). Fixed
  by routing the comparison through `version_matcher` to find the node's
  current counterpart in the latest version before comparing hashes. This
  is a strong example of "what's most likely to silently give wrong
  results without erroring" (see Decision Log) — the bug produced a valid
  HTTP 200 with a plausible-looking but incorrect `is_stale: false` on
  every request, with no exception anywhere in the stack.
- **Secrets accidentally committed (twice):** a GitHub Personal Access
  Token was pasted into `README.md` and committed (Phase 3), and later a
  Hugging Face token was committed via a tracked `.env` file (Phase 5).
  Both were caught by GitHub's push protection before reaching the
  public repo. Both tokens were revoked immediately upon discovery.
  Resolution in both cases: since neither commit had been successfully
  accepted by the remote, `git commit --amend` (after removing the secret
  and, for `.env`, running `git rm --cached .env` to stop tracking it
  going forward) was sufficient — no destructive history rewrite was
  needed. **Lesson reinforced twice:** `.gitignore` only prevents
  *untracked* files from being added; it does not retroactively untrack
  files already committed, which is why `.env` still needed an explicit
  `git rm --cached` even after being correctly listed in `.gitignore`.

---

# Decision Log

**1. What's the one part of this system most likely to silently give
wrong results without erroring? How would I catch it?**

The staleness check — and this isn't hypothetical, it happened during
development (see Phase 5 Debugging Notes above). The initial
implementation returned a confident `is_stale: false` on every single
request, with a valid HTTP 200 and no exception anywhere, while being
completely wrong. It was only caught by deliberately re-ingesting a
changed document and manually checking whether the flag actually flipped
— nothing in the test suite or normal operation would have surfaced it
otherwise. Beyond this specific bug, the underlying signal itself remains
a *silent* risk even now that it's fixed: a binary content_hash comparison
cannot distinguish a cosmetic wording change from a safety-critical
threshold change, and a user trusting `is_stale` alone (without reading
the diff) could miss something important. I'd catch both classes of risk
the same way going forward: by writing explicit regression tests that
re-ingest a document with a KNOWN change and assert the exact expected
staleness result, rather than only testing the "happy path" of generation
succeeding.

**2. Where did I choose simplicity over correctness because of time, and
what would break first if this went to production as-is?**

Two clear examples: (a) the version-matcher's `heading_text` fallback
assumes unique heading text per version, which Phase 2's own tests prove
can be false — accepted because it doesn't affect the actual grading
document. (b) The Phase 5 NoSQL store is a flat JSON file with **no
concurrency control** — two simultaneous requests writing generations
could race and corrupt or overwrite each other's data, since read-modify-
write isn't atomic. The JSON store would break first in production: the
moment more than one request can arrive concurrently (which is normal for
any real deployment), this needs to become an actual database (MongoDB,
or at minimum file locking) rather than a plain file.

**3. Name one input I did not handle, and what my system does when it
sees it.**

A selection containing `node_ids` from **two different document
versions** simultaneously is never validated against. The generation
endpoint will happily combine text from a v1 node and a v2 node into one
LLM prompt without flagging the mismatch, potentially producing a test
case grounded in internally inconsistent source text (e.g. mixing an old
threshold from v1 with a new error code introduced only in v2). Given
more time, I'd add a check in `POST /selections` or the generation
endpoint that all `node_ids` in one selection resolve to the same
`document_version_id`, and reject or warn otherwise.

---

# What I'd Do Differently With More Time

- Add semantic/severity-aware staleness detection (e.g. flag numeric
  value changes as higher severity than pure wording edits) rather than
  a flat binary hash comparison.
- Add fuzzy content-similarity matching as a second-tier fallback in
  `version_matcher`, for the case where both heading number and heading
  text change simultaneously.
- Validate that all nodes in a single selection share the same
  `document_version_id`.
- Replace the flat-JSON generation store with a real NoSQL store (or add
  file locking) once concurrent access becomes a real concern.
- Extend the ligature/encoding normalization table in
  `text_normalize.py` — it currently only fully covers headings; some
  raw ligature artifacts still surface in body text passed to the LLM
  (visible in generated test case text, e.g. "cuï¬" instead of "cuff").