# Template Contract

This contract keeps generated page records and author drafts web-readable, auditable, and consistent.

In public-facing catalog pages, "author" should usually be presented as "thinker" unless the entry is specifically about authorship as such. The extraction pipeline still uses author terminology internally because the source anthology is organized that way.

## Page Records

Page records must use schema version 2 and these `##` sections in order:

1. Page Summary
2. Layout and Reading Order
3. Bibliographic Signals
4. Excerpt Candidates
5. Source Notes
6. Bibliography Items
7. Assembly Hints
8. Quality Checks
9. Notes

The frontmatter must include publication access, rights mode, layout extraction method, column count, reading order, layout-review flag, content classification, and author/work boundary hints.

Page-record scaffolds may be generated from classifier metadata before human or agent review. When `content.contains_excerpt`, `content.contains_source_notes`, or `content.contains_bibliography` is true, the matching section must include a placeholder `### Excerpt Card`, `### Source Note`, or `### Bibliography Item` even if source text is not transcribed.

## Classification Records

Classification records are generated intermediate artifacts under `work/classification/<source_id>/`. They are not public pages.

Each record should capture:

- `page_kind`
- `confidence`
- visible author and work-title guesses
- `starts_new_author`
- `continues_previous_author`
- `assembly_group_slug`
- review reasons

Pages needing manual review are listed in `work/review/<source_id>/page-records-needing-review.csv`.

Manual classification overrides are tracked source controls, not hidden corrections. When present, they must come from `data/classification-overrides/<source_id>.yml` and appear in manifests through `override_applied`, `override_id`, and `override_source`.

## Author Pages

Author files must use schema version 2 and these `##` sections in order:

1. Why This Author Matters
2. Works In This Source
3. Reader Summary
4. Selected Excerpts
5. Source Notes
6. Bibliography
7. Page Inventory
8. Open Questions
9. Further Reading

Author pages are the primary web-readable output. Page records are intermediate audit records.

## Excerpts

Excerpts are displayed as curated Markdown cards with source page, rights mode, excerpt role, selection rationale, excerpt text if allowed, and project commentary.

Use this structure:

### Excerpt Card

- Source page:
- Rights mode:
- Excerpt role:
- Selection rationale:

> Add only approved excerpt text here.

**Project commentary:** Explain why this excerpt matters.

Do not place bibliography entries or source notes inside excerpt cards.

## Source Notes

Source footnotes, source endnotes, and visible note markers belong in `Source Notes`. Do not convert source notes into Markdown footnotes.

## Bibliography

Bibliography entries belong in `Bibliography Items` on page records and `Bibliography` on author pages.

## Multi-Column Pages

Multi-column pages are normalized into readable order. The page record must retain `layout.extraction_method`, `layout.column_count`, `layout.reading_order`, `layout.reading_order_confidence`, `layout.needs_layout_review`, and `layout.layout_notes`.
