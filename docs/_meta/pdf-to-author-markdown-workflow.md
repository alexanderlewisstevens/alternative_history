# PDF To Author Markdown Workflow

This workflow converts sliced PDF pages into structured page records first, then assembles those records into one Markdown file per author.

The process is intentionally two-stage. Page-level extraction is noisy; author-level assembly needs continuity across pages.

## Directory Plan

| Path | Purpose | Commit? |
| --- | --- | --- |
| `Norton_Anthology_Sliced_Author/` | One PDF per page. | No |
| `work/classification/<source_id>/` | Page-kind, author-boundary, and assembly-group classifications. | No |
| `work/review/<source_id>/` | Review queues for uncertain pages. | No |
| `work/page-records/<source_id>/` | Generated page-level Markdown records. | No, until rights-reviewed |
| `generated/authors/<source_id>/` | Generated one-file-per-author drafts. | No, until rights-reviewed |
| `docs/catalog/authors/` | Curated public author entries. | Yes |
| `docs/templates/extraction/` | Templates and schema expectations. | Yes |

## Stage 1: Layout And Classification

Each sliced PDF page first gets layout metadata, then a page classification record.

The classifier records:

- Page kind: front matter, table of contents, author intro, excerpt, bibliography, notes, index/appendix, mixed excerpt/bibliography, or unknown.
- Visible author and work-title guesses.
- Author-boundary signals such as `starts_new_author` and `continues_previous_author`.
- Assembly group slug for later author-page grouping.
- Review reasons for uncertain pages.

The classifier writes `work/classification/<source_id>/page-classifications.jsonl`, a CSV manifest, and `work/review/<source_id>/page-records-needing-review.csv`.

Sources may define a manual classification override file in `data/extraction-sources.yml` with `classification_overrides`. Override files live under `data/classification-overrides/` and are tracked. They are used for known author/work ranges that heuristic classification cannot infer reliably from running heads alone. Overrides are recorded in the classification manifest with `override_applied`, `override_id`, and `override_source`; an override by itself is audit evidence, not a reason to put a page in the review queue.

## Stage 2: Page Records

Each sliced PDF page becomes one page record using `docs/templates/extraction/page-record.md`.

The page record must capture:

- Source metadata.
- Rights status and output mode.
- Web access level.
- Visible author/work/section signals.
- Content classification.
- Multi-column layout and normalized reading order.
- Page summary.
- Excerpt, source notes, bibliography, and source editorial apparatus as separate sections.
- Assembly hints.
- Quality checks and uncertainty.

For copyrighted or unclear sources, page records should stay in `summary_only` or `metadata_only` mode. Do not mass-transcribe copyrighted book pages into Markdown.

## Stage 3: Validation

Generated page records should pass `scripts/validate_page_records.py` before assembly.

The validator checks:

- Required frontmatter fields.
- Allowed rights and output modes.
- Allowed publication access level.
- Allowed layout and content classifications.
- Required Markdown sections.
- Separation between excerpts, source notes, bibliography, and source editorial apparatus.
- Multi-column records include a normalized or explicitly ambiguous reading order.
- Obvious conflicts, such as public full transcription for unclear/copyrighted sources.

## Stage 4: Author Assembly

The assembler should group records by:

- `structure.author_slug`
- classifier `assembly_group_slug`
- page order
- `structure.starts_new_author`
- classifier `starts_new_author`
- classifier `continues_previous_author`
- `structure.work_slug`
- `structure.page_role`
- `content.primary_type`
- `content.types`
- `layout.reading_order`

The author draft should use `docs/templates/extraction/author-file.md`.

Author pages are the primary web-readable output. Page records are auditable intermediate artifacts.

## Stage 4.5: Restricted Deployment Boundary

Restricted or copyrighted outputs stay in ignored work directories until a separate deployment process adds access controls. Collapsing content in a public web page does not count as restricting access.

## Stage 5: Human Review

Before moving any generated author file into the public `docs/` tree:

- Confirm rights.
- Remove prohibited verbatim text.
- Fix author/work boundaries.
- Add original project commentary.
- Add citations and source links.
- Mark unresolved uncertainty.

## Multi-Column Pages

Multi-column pages should be normalized into one readable flow. The page record must retain `layout.extraction_method`, `layout.column_count`, `layout.reading_order`, `layout.reading_order_confidence`, `layout.needs_layout_review`, and `layout.layout_notes`.

## Footnotes

Source notes, footnotes, and endnotes belong in `Source Notes`. Project-authored commentary should remain in summaries, excerpt-card commentary, or `Notes`.

## Bibliography

Bibliographic entries belong in `Bibliography Items` on page records and `Bibliography` on author pages. They must not be mixed into excerpt cards.

## Web Template Rules

Every generated page record uses the same heading hierarchy:

- `#` page title.
- `##` required sections.
- `###` excerpt cards, source notes, bibliography items, and other repeatable units.

Source footnotes and endnotes belong in `## Source Notes`, not Markdown footnotes. Bibliography entries belong in `## Bibliography Items`, not excerpt cards. Anthology introductions, headnotes, translator notes, editor notes, and glosses belong in `## Notes`.

For multi-column pages, the generated Markdown should be normalized into readable order while preserving layout metadata and a note explaining the reading order.

## Norton Anthology Constraint

The local Norton anthology PDF should be treated as copyrighted unless proven otherwise. Use `publication.access_level: restricted` for access-controlled web-readable drafts and keep `rights.public_release: false` unless a record is safe for unrestricted public release.

For public-domain or openly licensed sources, the same pipeline can run in `transcription` mode and produce reusable text.
