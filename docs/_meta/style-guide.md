# Style Guide

## Voice

Write with clarity and pressure. The book should feel public-facing and serious, not academic for its own sake and not sensational.

Prefer:

- "This source complicates the usual account by..."
- "The evidence suggests..."
- "A counterfactual reading helps expose..."

Avoid:

- "History books never tell you..."
- "The real truth is..."
- "Everything you know is wrong..."

## Structure

Most entries should use this order:

1. Context.
2. Source or event.
3. What this changes.
4. Open questions.
5. Further reading.

## Dates

Use specific dates when known. For ranges, use `1865-1877`, not vague phrasing like "after the war" unless the context is obvious.

## Names

Use the name most appropriate to the historical context, and add alternatives where useful for search and recognition.

## Quotations

Keep quotations purposeful. A quotation should do work that a summary cannot do.

Use curated excerpt cards for source quotations:

### Excerpt Card

- Source page:
- Rights mode:
- Excerpt role:
- Selection rationale:

> Add only approved excerpt text here.

**Project commentary:** Explain why this excerpt matters.

## Generated Page Records

Generated PDF page records should use one `#` title, required `##` sections, and `###` headings only for repeatable cards or items.

Keep these content types separate:

- Excerpts in `## Excerpt Candidates`.
- Source footnotes and endnotes in `## Source Notes`.
- Bibliography entries in `## Bibliography Items`.
- Source-provided editor, translator, headnote, and glossary material in `## Notes`.
- Project uncertainty and extraction notes in `## Notes`.

Do not mix bibliography into excerpt cards.

For multi-column pages, normalize text into readable order and document the order in `## Layout and Reading Order`.

## Footnotes

Source footnotes, endnotes, and editor notes belong in a `Source Notes` section. Do not convert source notes into Markdown footnotes. Markdown footnotes are reserved for project-authored notes.

## Bibliography

Bibliography entries belong in `Bibliography Items` on page records and `Bibliography` on author pages. Do not place bibliography entries inside excerpt cards or running prose.

## Multi-Column Pages

Normalize multi-column source pages into readable order. Record `layout.extraction_method`, `layout.column_count`, `layout.reading_order`, `layout.reading_order_confidence`, `layout.needs_layout_review`, and `layout.layout_notes`; use `reading_order: ambiguous` when column order is uncertain.

## Links

Prefer stable archive, publisher, library, or project URLs over blog reposts and unsourced scans.
