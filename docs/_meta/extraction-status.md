# Extraction Status

This page is generated from audit artifacts. It intentionally contains metadata only, not Norton-derived source text.

<div class="ah-metric-grid">
<div class="ah-metric-card">
  <div class="ah-metric-label">Classified Pages</div>
  <div class="ah-metric-value">71-367</div>
</div>
<div class="ah-metric-card">
  <div class="ah-metric-label">Page Records</div>
  <div class="ah-metric-value">297</div>
</div>
<div class="ah-metric-card">
  <div class="ah-metric-label">Thinker Drafts</div>
  <div class="ah-metric-value">21</div>
</div>
<div class="ah-metric-card">
  <div class="ah-metric-label">Review Rows</div>
  <div class="ah-metric-value">219</div>
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
| Layout records | 297 | `work/layout/norton-theory-criticism/layout.jsonl` |
| Classification records | 297 | `work/classification/norton-theory-criticism/page-classifications.jsonl` |
| Review queue rows | 219 | `work/review/norton-theory-criticism/page-records-needing-review.csv` |
| Page records | 297 | `work/page-records/norton-theory-criticism` |
| Page-generation audit rows | 297 | `work/audit/norton-theory-criticism/page-record-generation.csv` |
| Thinker drafts | 21 | `generated/authors/norton-theory-criticism` |
| Thinker-assembly audit rows | 21 | `work/audit/norton-theory-criticism/author-assembly.csv` |

## Classified Range

| Field | Value |
| --- | --- |
| Classified source pages | `71-367` |
| Status page generated at | `2026-06-13T04:26:18Z` |
| Git commit | `383dabc` |
| Script version | `1` |
| Output path | `docs/_meta/extraction-status.md` |

## Thinker Draft Inventory

| Thinker slug | Pages | Source page range | Validation | Restricted draft |
| --- | ---: | --- | --- | --- |
| aristotle | 35 | 128-162 | ok | generated/authors/norton-theory-criticism/aristotle.md |
| augustine-of-hippo | 11 | 227-237 | ok | generated/authors/norton-theory-criticism/augustine-of-hippo.md |
| christine-de-pizan | 8 | 305-312 | ok | generated/authors/norton-theory-criticism/christine-de-pizan.md |
| dante-alighieri | 7 | 288-294 | ok | generated/authors/norton-theory-criticism/dante-alighieri.md |
| geoffrey-of-vinsauf | 14 | 268-281 | ok | generated/authors/norton-theory-criticism/geoffrey-of-vinsauf.md |
| giacopo-mazzoni | 23 | 342-364 | ok | generated/authors/norton-theory-criticism/giacopo-mazzoni.md |
| giambattista-giraldi | 8 | 313-320 | ok | generated/authors/norton-theory-criticism/giambattista-giraldi.md |
| giovanni-boccaccio | 10 | 295-304 | ok | generated/authors/norton-theory-criticism/giovanni-boccaccio.md |
| gorgias-of-leontini | 4 | 71-74 | ok | generated/authors/norton-theory-criticism/gorgias-of-leontini.md |
| horace | 14 | 163-176 | ok | generated/authors/norton-theory-criticism/horace.md |
| hugh-of-st-victor | 10 | 243-252 | ok | generated/authors/norton-theory-criticism/hugh-of-st-victor.md |
| joachim-du-bellay | 12 | 321-332 | ok | generated/authors/norton-theory-criticism/joachim-du-bellay.md |
| longinus | 20 | 177-196 | ok | generated/authors/norton-theory-criticism/longinus.md |
| macrobius | 5 | 238-242 | ok | generated/authors/norton-theory-criticism/macrobius.md |
| moses-maimonides | 15 | 253-267 | ok | generated/authors/norton-theory-criticism/moses-maimonides.md |
| pierre-de-ronsard | 9 | 333-341 | ok | generated/authors/norton-theory-criticism/pierre-de-ronsard.md |
| plato | 53 | 75-127 | ok | generated/authors/norton-theory-criticism/plato.md |
| plotinus | 14 | 213-226 | ok | generated/authors/norton-theory-criticism/plotinus.md |
| quintilian | 16 | 197-212 | ok | generated/authors/norton-theory-criticism/quintilian.md |
| sir-philip-sidney | 3 | 365-367 | ok | generated/authors/norton-theory-criticism/sir-philip-sidney.md |
| thomas-aquinas | 6 | 282-287 | ok | generated/authors/norton-theory-criticism/thomas-aquinas.md |

## Review Queue Summary

| Review reason | Pages |
| --- | ---: |
| multi_column_layout | 135 |
| source_notes_detected | 119 |
| transition_from_previous_author | 49 |
| author_boundary_without_life_dates | 6 |
| layout_review_required | 6 |
| mixed_excerpt_and_bibliography | 5 |
| transition_from_previous_work | 2 |

## Publication Boundary

The thinker drafts listed above are restricted working artifacts. They should not be copied into public catalog pages until rights review, excerpt selection, and original project commentary are complete.
