---
record_type: author_file
schema_version: 2
title: "Fixture Author"
author:
  name: "Fixture Author"
  slug: "fixture-author"
  life_dates: "1900-1999"
source:
  source_id: "fixture-source"
  source_title: "Fixture Source"
  source_pdf: "fixture.pdf"
  first_page: 1
  last_page: 5
publication:
  access_level: "restricted"
  web_readable: true
  release_notes: "Synthetic fixture."
rights:
  source_rights_status: "copyrighted"
  public_release: false
  rights_evidence: "Synthetic fixture."
assembly:
  generated_from_page_records:
    - "tests/fixtures/valid/page-record-single-column.md"
    - "tests/fixtures/valid/page-record-two-column.md"
  generated_at: "2026-06-05T00:00:00Z"
  confidence: "high"
---

# Fixture Author

## Why This Author Matters

This author fixture demonstrates the strict author-page section contract for the Alternative History project.

## Works In This Source

| Work | Page Range | Section Type | Notes |
| --- | --- | --- | --- |
| Fixture Work | 1-5 | excerpt | Synthetic fixture |

## Reader Summary

The author page summarizes records without mixing source notes, bibliography, and excerpts.

## Selected Excerpts

### Excerpt Card

- Work: Fixture Work
- Source pages: 1-2
- Rights mode: limited_quote
- Selection rationale: Validates author excerpt card structure.

> A brief author-page quotation remains short.

**Project commentary:** The selected excerpt is separate from notes and bibliography.

## Source Notes

| Page | Marker | Note summary | Rights mode |
| --- | --- | --- | --- |
| 3 | 1 | Source note summarized separately. | summary_only |

## Bibliography

| Page | Entry | Type | Notes |
| --- | --- | --- | --- |
| 4 | Fixture citation summary. | bibliography | Separate from excerpts. |

## Page Inventory

| Page | Printed Label | Work | Role | Layout | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | Fixture Work | opening | 1 column/normalized:top-to-bottom | synthetic |
| 2 | 2 | Fixture Work | continuation | 2 columns/normalized:left-column-then-right-column | synthetic |

## Open Questions

- Confirm final rights mode before promotion.

## Further Reading

- Add public-domain or openly licensed contextual sources.
