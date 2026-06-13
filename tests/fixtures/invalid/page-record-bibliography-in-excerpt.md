---
record_type: page_record
schema_version: 2
title: "Invalid Fixture - Bibliography In Excerpt"
source:
  source_id: "fixture-source"
  source_title: "Fixture Source"
  source_pdf: "fixture.pdf"
  page_file: "page_0998.pdf"
  page_number: 998
  printed_page_label: "998"
  total_pages: 999
publication:
  access_level: "restricted"
  web_readable: true
  release_notes: "Synthetic invalid fixture."
rights:
  source_rights_status: "copyrighted"
  output_mode: "limited_quote"
  public_release: false
  rights_evidence: "Synthetic fixture."
agent:
  agent_name: "fixture"
  generated_at: "2026-06-05T00:00:00Z"
  confidence: "high"
layout:
  extraction_method: "synthetic"
  column_count: 1
  reading_order: "normalized:top-to-bottom"
  reading_order_confidence: "high"
  needs_layout_review: false
  layout_notes: "Invalid fixture."
content:
  primary_type: "excerpt"
  types: ["excerpt"]
  page_kind: "unknown"
  contains_excerpt: true
  contains_source_notes: false
  contains_bibliography: false
  contains_editorial_apparatus: false
structure:
  author_name: "Fixture Author"
  author_slug: "fixture-author"
  work_title: "Invalid Work"
  work_slug: "invalid-work"
  section_title: "Invalid"
  section_type: "excerpt"
  starts_new_author: false
  continues_previous_author: false
  page_role: "invalid"
  previous_page_context:
  next_page_context:
---

# Invalid Fixture - Bibliography In Excerpt

## Page Summary

This fixture is intentionally invalid because it places a bibliography item inside the excerpt section.

## Layout and Reading Order

- Column count: 1
- Reading order: normalized:top-to-bottom
- Reading order confidence: high
- Normalization notes: Invalid fixture.
## Bibliographic Signals

- Bibliography present: unknown
- Source note markers present: unknown
- Editorial apparatus present: unknown
- Printed page label: fixture

## Excerpt Candidates

### Excerpt Card

- Source page: 998
- Rights mode: limited_quote
- Excerpt role: invalid
- Selection rationale: Demonstrates validator rejection.

> Short invalid quotation.

### Bibliography Item 1

- Cited author: Should Not Be Here
- Cited title: Invalid Placement
- Citation text: This bibliography item is inside Excerpt.
- Citation role: invalid
- Related excerpt: Excerpt Card

## Source Notes

No source notes recorded for this page.

## Bibliography Items

No bibliography items recorded for this page.

## Assembly Hints

- Suggested author file: `fixture-author.md`
- Suggested work grouping: Invalid Work
- Start/end boundary evidence: invalid
- Continuity with previous page: invalid
- Continuity with next page: invalid


## Quality Checks

- [x] Page number recorded.
- [x] Rights status recorded.
- [x] Output mode obeyed.
- [ ] Content types separated into excerpt, source notes, bibliography, and editorial apparatus.
- [x] Multi-column layout recorded and normalized if needed.
- [x] Author/work boundary marked if visible.
- [x] Ambiguities noted.

## Notes

No editorial apparatus or extraction uncertainty recorded.
