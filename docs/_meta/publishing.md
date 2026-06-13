# Publishing

The project is currently Markdown-first. That keeps the source readable in GitHub, easy to audit, and easy to migrate.

The local site has two different meanings:

- **Private workspace:** a local knowledge base for restricted extraction artifacts, reading notes, review queues, and generated scaffolds.
- **Public book:** a rights-cleared site made from original commentary, public-domain/open material, citations, and approved excerpts.

Do not treat a successful local MkDocs build as public-clearance approval.

## Option 1: MkDocs

MkDocs is the simplest path for a static book site.

```bash
make setup
make serve
```

Build the site with:

```bash
make build
make smoke-site
```

The generated site will appear in `site/`.

## Private-First Workflow

Use the private site for work that is not ready to publish:

1. Add or update source metadata in tracked files.
2. Generate restricted page records and workspace notes through `make`.
3. Keep generated source drafts in ignored directories such as `work/` and `generated/`.
4. Mark private workspace pages as restricted when they depend on copyrighted or uncertain sources.
5. Use issue labels to decide model level before major curation, rights, or synthesis work.

Private pages may describe restricted source artifacts and link to local generated drafts. They should not silently become public pages.

## Public Promotion Checklist

Before promoting any page, passage, image, or source-derived text into a public build:

- Confirm the edition or translation being used.
- Record rights status and evidence.
- Decide whether the page may quote, paraphrase, cite, or only summarize.
- Remove copied restricted prose unless it has a documented public-use basis.
- Add source, page, edition, and rights information near every copied passage.
- Make sure bibliography and source-note material are not mixed into excerpt text.
- Run `make build` and `make smoke-site`.
- Create or update the relevant GitHub issue with the publication decision.

If any of those items are unresolved, keep the page private.

## Option 2: GitHub Pages From Markdown

The `docs/` folder can also be used directly with GitHub Pages, though navigation and styling will be more limited unless a static-site generator is added.

## Option 3: Future Static Book Stack

If the project grows, consider:

- MkDocs Material for search, navigation, and readable docs styling.
- Quartz if the project becomes networked notes.
- Astro or Eleventy if custom visual design becomes important.
- Pandoc if PDF, EPUB, and print export become priorities.

## Publication Checklist

- Choose license.
- Confirm rights for every excerpt and image.
- Add a bibliography page for every chapter.
- Use GitHub issue templates for curation tasks, rights review, pipeline work, and site/UI follow-up.
- Configure GitHub Pages or another static host.
