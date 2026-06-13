---
record_type: page_record
schema_version: 2
title: "Fixture Source - Mixed Page"
source:
  source_id: "fixture-source"
  source_title: "Fixture Source"
  source_pdf: "fixture.pdf"
  page_file: "page_0005.pdf"
  page_number: 5
  printed_page_label: "5"
  total_pages: 6
publication:
  access_level: "restricted"
  web_readable: true
  release_notes: "Synthetic fixture."
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
  column_count: 2
  reading_order: "ambiguous"
  reading_order_confidence: "medium"
  needs_layout_review: false
  layout_notes: "Mixed page with two columns, notes, bibliography, and editorial apparatus signals."
content:
  primary_type: "mixed"
  types: ["mixed", "excerpt", "source_note", "bibliography", "editorial_apparatus"]
  page_kind: "unknown"
  contains_excerpt: true
  contains_source_notes: true
  contains_bibliography: true
  contains_editorial_apparatus: true
structure:
  author_name: "Fixture Author"
  author_slug: "fixture-author"
  work_title: "Mixed Work"
  work_slug: "mixed-work"
  section_title: "Mixed Materials"
  section_type: "mixed"
  starts_new_author: false
  continues_previous_author: true
  page_role: "mixed"
  previous_page_context: "Work continues from previous page."
  next_page_context: "Bibliography continues."
---

# Fixture Source - Mixed Page

## Page Summary

This synthetic page combines a short excerpt, a source note, a bibliography item, and an editorial-apparatus signal.

## Layout and Reading Order

- Column count: 2
- Reading order: ambiguous
- Reading order confidence: medium
- Normalization notes: Mixed layout requires manual review before publication.
## Bibliographic Signals

- Bibliography present: unknown
- Source note markers present: unknown
- Editorial apparatus present: unknown
- Printed page label: fixture

## Excerpt Candidates

### Excerpt Card

- Source page: 5
- Rights mode: limited_quote
- Excerpt role: mixed-page signal
- Selection rationale: Demonstrates excerpt separation from notes and bibliography.

> Mixed pages need explicit separation of each source signal.

**Project commentary:** This keeps assembly predictable.

## Source Notes

### Source Note 1

- Marker: a
- Location: lower margin
- Note type: editor note
- Related excerpt: Excerpt Card

The source note is summarized separately from the excerpt.

## Bibliography Items

### Bibliography Item 1

- Cited author: Fixture Bibliographer
- Cited title: Mixed Citation
- Citation text: Summarized fixture citation.
- Citation role: related bibliography
- Related excerpt: Excerpt Card

## Assembly Hints

- Suggested author file: `fixture-author.md`
- Suggested work grouping: Mixed Work
- Start/end boundary evidence: running head continues author
- Continuity with previous page: continuation
- Continuity with next page: bibliography continues


## Quality Checks

- [x] Page number recorded.
- [x] Rights status recorded.
- [x] Output mode obeyed.
- [x] Content types separated into excerpt, source notes, bibliography, and editorial apparatus.
- [x] Multi-column layout recorded and normalized if needed.
- [x] Author/work boundary marked if visible.
- [x] Ambiguities noted.

## Notes

This fixture confirms mixed-content pages keep source-provided editorial apparatus separate from project notes.
