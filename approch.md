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