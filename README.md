# Alternative History

Alternative History is a freely available online book project centered on theory, criticism, historiography, and the writers who disturb the easy version of the past.

The aim is not to build a conspiracy archive, a novelty collection of counterfactuals, or a general scrape of whatever can be found online. The aim is to build an intentional reader: selected thinkers, texts, passages, historical problems, narratives, and interpretive traditions that force readers to rethink history and their relationship to it.

This project treats "alternative history" as a critical practice:

- Theory and criticism that reveal how history is narrated, authorized, translated, archived, and taught.
- Counter-histories written from colonized, enslaved, exiled, working-class, Indigenous, diasporic, feminist, queer, and other marginalized positions.
- Primary texts whose form or argument changes how a reader understands memory, power, interpretation, and evidence.
- Historiography that shows how archives, empires, institutions, maps, monuments, and schools shape public memory.
- Disciplined speculation only when it clarifies contingency, not when it replaces evidence.

## Repository Structure

- `docs/` - the book manuscript and publishable site pages.
- `docs/chapters/` - long-form chapters and thematic essays.
- `docs/catalog/` - thinkers, texts, constellations, historical problems, excerpts, and bibliography pages.
- `docs/templates/` - reusable templates for adding new entries.
- `docs/_meta/` - editorial, rights, style, and publishing guidance.
- `data/` - structured source metadata for future tooling.
- `scripts/` - auditable automation for PDF slicing, layout extraction, record generation, validation, and assembly.
- `work/` - ignored intermediate extraction artifacts.
- `generated/` - ignored restricted drafts assembled from page records.

## Working Method

1. Add a named candidate text, thinker, or edition to `docs/catalog/sources.md` or `data/source-register.yml`.
2. Explain why it belongs in this curated theory-and-criticism collection.
3. Confirm the rights status before copying text into the book.
4. Create a thinker, text, constellation, historical problem, or excerpt entry from the relevant template.
5. Write a short "what this changes" note for every item.
6. Link the item into one or more chapters.

The strongest public pages should make texts interact. A good entry does more than summarize a thinker or source; it shows how one text changes the way another can be read.

Broad scraping, topic crawling, and unsupervised harvesting are out of scope. Discovery can use catalogs and archives, but selection happens text by text.

## Rights First

The book should prefer public-domain texts, openly licensed work, and original commentary. Copyrighted works can still be discussed, cited, and summarized, but copied excerpts require a clear basis: permission, an open license, public-domain status, or a deliberately limited fair-use rationale.

Before public launch, choose a license for original project prose and metadata. A good default to consider is Creative Commons Attribution-ShareAlike 4.0 for original writing, while preserving the original rights status of quoted sources.

## Local Preview

The manuscript is plain Markdown. If you want a local website preview with MkDocs:

```bash
make setup
.venv/bin/mkdocs serve
```

Then open `http://127.0.0.1:8000`.

## Extraction Pipeline

`make` is the canonical interface for reproducing the restricted PDF-to-author-draft workflow:

```bash
make setup
make slice
make validate-fixtures
make extract-layout LIMIT=5
make classify-pages LIMIT=5
make generate-page-records LIMIT=5
make validate-page-records
make assemble-authors LIMIT=5
make validate-authors
make audit
make build
```

The Norton anthology PDF is configured in `data/extraction-sources.yml` as restricted material. Pipeline output stays in ignored directories and is not published into `docs/` unless it is manually rights-cleared and promoted.

Known author/work ranges can be corrected with tracked override files in `data/classification-overrides/`. These overrides are written into audit manifests so a later reviewer can recreate and inspect the grouping decisions.
