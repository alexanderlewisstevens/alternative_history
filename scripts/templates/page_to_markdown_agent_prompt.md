# Page-To-Markdown Agent Task

You are converting one PDF page into a structured Markdown page record for the Alternative History project. The result must be web-readable and must preserve the distinction between excerpt text, source notes, bibliography, source editorial apparatus, and project notes.

## Non-Negotiable Rights Rule

Obey `rights.output_mode`.

- `metadata_only`: do not reproduce prose from the page. Record bibliographic signals, structure, author/work guesses, and assembly hints only.
- `summary_only`: write an original factual summary and metadata. Do not transcribe the page or copy extended prose.
- `limited_quote`: include only short necessary quotations, with a note explaining why each quote is needed.
- `transcription`: full transcription is allowed only when the source is public domain, openly licensed for reuse, permission-granted, or otherwise approved.

If rights are unclear or copyrighted, default to `summary_only`.

## Web Access Rule

Use `publication.access_level` to describe the intended deployment:

- `public`: safe for a public website.
- `restricted`: intended for an access-controlled deployment.
- `private`: local-only draft or review artifact.

Do not mark `rights.public_release` as true unless the record is safe for unrestricted public publication.

## Source Context

- Source ID: `{{ source_id }}`
- Source title: `{{ source_title }}`
- Source PDF: `{{ source_pdf }}`
- Page file: `{{ page_file }}`
- Page path: `{{ page_path }}`
- Page number: `{{ page_number }}`
- Total pages: `{{ total_pages }}`
- Rights status: `{{ source_rights_status }}`
- Output mode: `{{ output_mode }}`
- Public release allowed: `{{ public_release }}`
- Access level: `{{ access_level }}`

## Neighbor Context

- Previous page context: `{{ previous_page_context }}`
- Next page context: `{{ next_page_context }}`

## Layout Signals

These signals were generated before agent review. Verify them against the page image/text and keep uncertainty visible.

- Column count: `{{ layout_column_count }}`
- Reading order: `{{ layout_reading_order }}`
- Reading order confidence: `{{ layout_reading_order_confidence }}`
- Needs layout review: `{{ layout_needs_layout_review }}`
- Layout notes: `{{ layout_notes }}`

## Preliminary Classification

These classifier signals are heuristics. Correct them in frontmatter when the source page shows better evidence.

- Page kind: `{{ classification_page_kind }}`
- Confidence: `{{ classification_confidence }}`
- Visible author guess: `{{ classification_author_name }}`
- Work title guess: `{{ classification_work_title }}`
- Starts new author: `{{ classification_starts_new_author }}`
- Continues previous author: `{{ classification_continues_previous_author }}`
- Review reasons: `{{ classification_review_reasons }}`

## Title Rule

Choose a sensible page title in this order:

1. `Author Name - Work Title - Page N`, if author and work are visible.
2. `Author Name - Page N`, if only author is visible.
3. `Work Title - Page N`, if only work is visible.
4. `Source Title - Page N`, if no author or work is visible.

Use title case for the Markdown `#` heading. Use lowercase kebab-case for slugs.

## Layout and Multiple Columns

Detect the page column count and whether the reading order can be normalized.

Record:

- `layout.extraction_method`
- `layout.column_count`
- `layout.reading_order`
- `layout.reading_order_confidence`
- `layout.needs_layout_review`
- `layout.layout_notes`

When a page has multiple columns, normalize the readable output into the intended reading order. Do not interleave left and right columns. In `## Layout and Reading Order`, explain the order used, such as "left column top-to-bottom, then right column top-to-bottom."

If the reading order is uncertain, set `layout.reading_order` to `ambiguous`, lower the confidence, and explain the ambiguity.

## Content Separation

Classify the page using:

- `content.primary_type`
- `content.types`
- `content.page_kind`
- `content.contains_excerpt`
- `content.contains_source_notes`
- `content.contains_bibliography`
- `content.contains_editorial_apparatus`

Use these sections consistently:

- `## Bibliographic Signals`: visible bibliography, source note, printed page, or editorial-apparatus signals only.
- `## Excerpt Candidates`: primary source text or approved excerpt cards only.
- `## Source Notes`: source footnotes or endnotes only.
- `## Bibliography Items`: bibliography or works-cited entries only.
- `## Notes`: extraction uncertainty, OCR/layout issues, project-side notes, and source editorial-apparatus summaries only.

Never put bibliography inside an excerpt card. Never convert source footnotes into Markdown footnotes.

## Boundary Detection

Pay special attention to:

- Author names.
- Work titles.
- Section headings.
- Table of contents entries.
- Running headers.
- Biographical introductions.
- Footnotes or editorial notes.
- Whether this page starts, continues, or ends an author section.

The later assembler will group page records into one Markdown file per author using:

- `structure.author_slug`
- `structure.work_slug`
- `structure.starts_new_author`
- `structure.page_role`
- page number continuity

## Required Output

Return one Markdown document matching `docs/templates/extraction/page-record.md` exactly:

- One `#` heading only.
- Required top-level sections are `##` headings.
- Cards and individual notes use `###` headings.
- Preserve all required sections even when the page has no excerpt, notes, bibliography, or editorial apparatus.

Do not add commentary outside the Markdown document.
