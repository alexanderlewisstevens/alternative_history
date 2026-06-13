# Extraction Status

This page is generated from audit artifacts. It intentionally contains metadata only, not Norton-derived source text.

<div class="ah-metric-grid">
<div class="ah-metric-card">
  <div class="ah-metric-label">Classified Pages</div>
  <div class="ah-metric-value">71-447</div>
</div>
<div class="ah-metric-card">
  <div class="ah-metric-label">Page Records</div>
  <div class="ah-metric-value">377</div>
</div>
<div class="ah-metric-card">
  <div class="ah-metric-label">Thinker Drafts</div>
  <div class="ah-metric-value">25</div>
</div>
<div class="ah-metric-card">
  <div class="ah-metric-label">Review Rows</div>
  <div class="ah-metric-value">290</div>
</div>
</div>

## Local Workflow

- Use [Review Dashboard](review-dashboard.md) to choose the next editorial checks.
- Use this page to confirm artifact counts after extraction and assembly.
- Keep restricted generated drafts out of public catalog pages until rights review is complete.

## Current Restricted Source

| Field | Value |
| --- | --- |
| Source ID | `norton-theory-criticism` |
| Source title | The Norton Anthology of Theory and Criticism |
| Rights status | `copyrighted` |
| Public release | `false` |
| Default output mode | `summary_only` |
| Access level | `restricted` |
| Source config | `data/extraction-sources.yml` |
| Classification overrides | `data/classification-overrides/norton-theory-criticism.yml` |

## Artifact Counts

| Artifact | Count | Location |
| --- | ---: | --- |
| Sliced PDFs | 2668 | `Norton_Anthology_Sliced_Author` |
| Layout records | 377 | `work/layout/norton-theory-criticism/layout.jsonl` |
| Classification records | 377 | `work/classification/norton-theory-criticism/page-classifications.jsonl` |
| Review queue rows | 290 | `work/review/norton-theory-criticism/page-records-needing-review.csv` |
| Page records | 377 | `work/page-records/norton-theory-criticism` |
| Page-generation audit rows | 377 | `work/audit/norton-theory-criticism/page-record-generation.csv` |
| Thinker drafts | 25 | `generated/authors/norton-theory-criticism` |
| Thinker-assembly audit rows | 25 | `work/audit/norton-theory-criticism/author-assembly.csv` |

## Classified Range

| Field | Value |
| --- | --- |
| Classified source pages | `71-447` |
| Status page generated at | `2026-06-13T04:29:45Z` |
| Git commit | `1665a30` |
| Script version | `1` |
| Output path | `docs/_meta/extraction-status.md` |

## Thinker Draft Inventory

| Thinker slug | Pages | Source page range | Validation | Restricted draft |
| --- | ---: | --- | --- | --- |
| aphra-behn | 11 | 430-440 | ok | generated/authors/norton-theory-criticism/aphra-behn.md |
| aristotle | 35 | 128-162 | ok | generated/authors/norton-theory-criticism/aristotle.md |
| augustine-of-hippo | 11 | 227-237 | ok | generated/authors/norton-theory-criticism/augustine-of-hippo.md |
| christine-de-pizan | 8 | 305-312 | ok | generated/authors/norton-theory-criticism/christine-de-pizan.md |
| dante-alighieri | 7 | 288-294 | ok | generated/authors/norton-theory-criticism/dante-alighieri.md |
| geoffrey-of-vinsauf | 14 | 268-281 | ok | generated/authors/norton-theory-criticism/geoffrey-of-vinsauf.md |
| giacopo-mazzoni | 23 | 342-364 | ok | generated/authors/norton-theory-criticism/giacopo-mazzoni.md |
| giambattista-giraldi | 8 | 313-320 | ok | generated/authors/norton-theory-criticism/giambattista-giraldi.md |
| giambattista-vico | 7 | 441-447 | ok | generated/authors/norton-theory-criticism/giambattista-vico.md |
| giovanni-boccaccio | 10 | 295-304 | ok | generated/authors/norton-theory-criticism/giovanni-boccaccio.md |
| gorgias-of-leontini | 4 | 71-74 | ok | generated/authors/norton-theory-criticism/gorgias-of-leontini.md |
| horace | 14 | 163-176 | ok | generated/authors/norton-theory-criticism/horace.md |
| hugh-of-st-victor | 10 | 243-252 | ok | generated/authors/norton-theory-criticism/hugh-of-st-victor.md |
| joachim-du-bellay | 12 | 321-332 | ok | generated/authors/norton-theory-criticism/joachim-du-bellay.md |
| john-dryden | 9 | 421-429 | ok | generated/authors/norton-theory-criticism/john-dryden.md |
| longinus | 20 | 177-196 | ok | generated/authors/norton-theory-criticism/longinus.md |
| macrobius | 5 | 238-242 | ok | generated/authors/norton-theory-criticism/macrobius.md |
| moses-maimonides | 15 | 253-267 | ok | generated/authors/norton-theory-criticism/moses-maimonides.md |
| pierre-corneille | 16 | 405-420 | ok | generated/authors/norton-theory-criticism/pierre-corneille.md |
| pierre-de-ronsard | 9 | 333-341 | ok | generated/authors/norton-theory-criticism/pierre-de-ronsard.md |
| plato | 53 | 75-127 | ok | generated/authors/norton-theory-criticism/plato.md |
| plotinus | 14 | 213-226 | ok | generated/authors/norton-theory-criticism/plotinus.md |
| quintilian | 16 | 197-212 | ok | generated/authors/norton-theory-criticism/quintilian.md |
| sir-philip-sidney | 40 | 365-404 | ok | generated/authors/norton-theory-criticism/sir-philip-sidney.md |
| thomas-aquinas | 6 | 282-287 | ok | generated/authors/norton-theory-criticism/thomas-aquinas.md |

## Review Queue Summary

| Review reason | Pages |
| --- | ---: |
| multi_column_layout | 190 |
| source_notes_detected | 167 |
| transition_from_previous_author | 60 |
| author_boundary_without_life_dates | 9 |
| mixed_excerpt_and_bibliography | 7 |
| layout_review_required | 6 |
| transition_from_previous_work | 2 |

## Publication Boundary

The thinker drafts listed above are restricted working artifacts. They should not be copied into public catalog pages until rights review, excerpt selection, and original project commentary are complete.
