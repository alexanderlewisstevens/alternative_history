#!/usr/bin/env python3
"""Generate a private workspace reading-path overview from curated metadata."""

from __future__ import annotations

import argparse
import html
from collections import Counter
from pathlib import Path
from typing import Any

from lib.extraction_common import (
    git_commit,
    load_config,
    now_utc,
    read_jsonl,
    relative_to_root,
    resolve_source_paths,
    write_csv,
)
from lib.workspace_components import backlink_list, link, private_banner, provenance_table
from update_workspace_constellations import text_by_id
from update_workspace_map import (
    classification_records_for_text,
    load_source_register,
    page_range_for_records,
    read_csv_rows,
    review_counts_for_records,
)
from update_workspace_text_notes import author_row_for_text


SCRIPT_VERSION = "1"
DEFAULT_OUTPUT = "docs/workspace/reading-paths.md"

FOCUS_LANES = [
    {
        "id": "civic-education",
        "title": "Citizen, Educator, Institution",
        "description": "Education, civic formation, public judgment, and the work of higher education.",
        "constellations": [
            "education-and-civic-life",
            "aesthetic-education-and-citizenship",
            "rhetoric-and-force",
            "theater-and-public-judgment",
        ],
    },
    {
        "id": "work-power",
        "title": "Work, Power, Culture",
        "description": "Labor, institutions, ideology, discipline, public spheres, and cultural production.",
        "constellations": [
            "labor-ideology-and-culture",
            "art-utility-and-modern-life",
            "authorship-and-authority",
            "media-and-form",
        ],
    },
    {
        "id": "reading-method",
        "title": "Reading, Signs, Interpretation",
        "description": "How difficult texts are read, transmitted, misread, and made authoritative.",
        "constellations": [
            "signs-and-reading",
            "commentary-and-afterlife",
            "language-truth-and-fiction",
        ],
    },
    {
        "id": "aesthetic-judgment",
        "title": "Aesthetic Judgment",
        "description": "Taste, beauty, sublimity, usefulness, poetry, and the politics of judgment.",
        "constellations": [
            "poetry-and-judgment",
            "beauty-and-ascent",
            "taste-and-standards",
            "sublime-and-limits",
            "romantic-poetry-and-modernity",
        ],
    },
]


def constellation_title(constellation_id: str) -> str:
    return constellation_id.replace("-", " ").title()


def constellation_href(constellation_id: str) -> str:
    return f"{constellation_id}.md"


def constellation_card_href(constellation_id: str) -> str:
    return f"../{constellation_id}/"


def text_note_href(text_id: str) -> str:
    return f"norton-texts/{text_id}.md"


def metric_card(label: str, value: object) -> str:
    return f"""<div class="ah-metric-card">
  <div class="ah-metric-label">{html.escape(label)}</div>
  <div class="ah-metric-value">{html.escape(str(value))}</div>
</div>"""


def text_stats(
    constellation: dict[str, Any],
    texts: dict[str, dict[str, Any]],
    author_rows: dict[str, dict[str, str] | None],
    classification_records: list[dict[str, Any]],
) -> dict[str, Any]:
    text_ids = [str(value) for value in constellation.get("texts", [])]
    review_total = 0
    assembled_count = 0
    page_ranges: list[str] = []
    theme_counter: Counter[str] = Counter()

    for text_id in text_ids:
        text = texts.get(text_id, {})
        author_row = author_rows.get(text_id)
        records = classification_records_for_text(classification_records, text)
        pages = page_range_for_records(records)
        if not pages and author_row:
            first_page = author_row.get("first_page", "")
            last_page = author_row.get("last_page", "")
            pages = f"{first_page}-{last_page}" if first_page and last_page else ""
        if pages:
            assembled_count += 1
            page_ranges.append(pages)
        review_total += review_counts_for_records(records).get("total", 0)
        theme_counter.update(str(theme) for theme in text.get("themes", []))

    return {
        "text_count": len(text_ids),
        "assembled_count": assembled_count,
        "review_total": review_total,
        "page_ranges": page_ranges,
        "themes": [theme for theme, _count in theme_counter.most_common(5)],
    }


def lane_cards(
    lanes: list[dict[str, Any]],
    constellations: dict[str, dict[str, Any]],
    constellation_stats: dict[str, dict[str, Any]],
) -> str:
    cards = []
    for lane in lanes:
        links = []
        review_total = 0
        text_total = 0
        for constellation_id in lane["constellations"]:
            constellation = constellations.get(constellation_id)
            if not constellation:
                continue
            stats = constellation_stats.get(constellation_id, {})
            review_total += int(stats.get("review_total", 0))
            text_total += int(stats.get("text_count", 0))
            links.append(
                f'<li><a href="{html.escape(constellation_card_href(constellation_id))}">'
                f"{html.escape(constellation_title(constellation_id))}</a></li>"
            )
        cards.append(
            f"""<section class="ah-note-panel">
  <span class="ah-action-kicker">{html.escape(str(text_total))} texts · {html.escape(str(review_total))} review rows</span>
  <h3>{html.escape(lane["title"])}</h3>
  <p>{html.escape(lane["description"])}</p>
  <ul>
    {chr(10).join(links)}
  </ul>
</section>"""
        )
    return "\n".join(cards)


def constellation_rows(
    constellations: list[dict[str, Any]],
    constellation_stats: dict[str, dict[str, Any]],
) -> str:
    rows = []
    for constellation in constellations:
        constellation_id = str(constellation.get("id", ""))
        stats = constellation_stats.get(constellation_id, {})
        themes = ", ".join(str(theme) for theme in stats.get("themes", []))
        rows.append(
            "| "
            + " | ".join(
                [
                    f"[{html.escape(constellation_title(constellation_id))}]({constellation_href(constellation_id)})",
                    html.escape(str(constellation.get("question", ""))),
                    str(stats.get("text_count", 0)),
                    str(stats.get("assembled_count", 0)),
                    str(stats.get("review_total", 0)),
                    html.escape(themes),
                ]
            )
            + " |"
        )
    return "\n".join(rows) or "| No constellations configured |  |  |  |  |  |"


def starter_text_links(
    text_ids: list[str],
    texts: dict[str, dict[str, Any]],
    classification_records: list[dict[str, Any]],
) -> str:
    items = []
    for text_id in text_ids:
        text = texts.get(text_id, {})
        records = classification_records_for_text(classification_records, text)
        pages = page_range_for_records(records) or "pages pending"
        label = f"{text.get('creator', 'Unknown')}, {text.get('title', text_id)}"
        items.append(f"- [{html.escape(str(label))}]({text_note_href(text_id)}) ({html.escape(pages)})")
    return "\n".join(items)


def build_reading_paths_page(
    source: dict[str, Any],
    source_register: dict[str, Any],
    output_path: Path,
) -> tuple[str, list[dict[str, Any]]]:
    paths = resolve_source_paths(source)
    classification_records = read_jsonl(paths["classification_dir"] / "page-classifications.jsonl")
    author_assembly = read_csv_rows(paths["audit_dir"] / "author-assembly.csv")
    curated_texts = [text for text in source_register.get("curated_texts", []) if text.get("id") != source["source_id"]]
    texts = text_by_id(curated_texts)
    constellations = source_register.get("constellations", [])
    constellations_by_id = {str(item.get("id", "")): item for item in constellations}
    author_rows = {
        str(text.get("id", "")): author_row_for_text(text, author_assembly)
        for text in curated_texts
    }
    stats = {
        str(constellation.get("id", "")): text_stats(constellation, texts, author_rows, classification_records)
        for constellation in constellations
    }
    generated_at = now_utc()
    audit_rows = [
        {
            "constellation_id": constellation_id,
            "text_count": value["text_count"],
            "assembled_count": value["assembled_count"],
            "review_total": value["review_total"],
            "themes": ";".join(value["themes"]),
            "generated_at": generated_at,
            "script_version": SCRIPT_VERSION,
            "git_commit": git_commit(),
        }
        for constellation_id, value in sorted(stats.items())
    ]

    total_reviews = sum(int(value["review_total"]) for value in stats.values())
    total_text_refs = sum(int(value["text_count"]) for value in stats.values())

    markdown = f"""# Reading Paths

This page turns the private Norton workspace into a few usable routes through the material. It is generated from curated metadata and extraction audits, not copied anthology prose.

{private_banner("Private reading-path desk", "Use this page to choose what to read, compare, and annotate next. Keep restricted source material inside the private workspace until rights are reviewed.")}

<div class="ah-metric-grid">
{metric_card("Constellations", len(constellations))}
{metric_card("Curated Text References", total_text_refs)}
{metric_card("Norton Text Notes", len(curated_texts))}
{metric_card("Review Rows In Paths", total_reviews)}
</div>

## Focus Lanes

<div class="ah-note-grid">
{lane_cards(FOCUS_LANES, constellations_by_id, stats)}
</div>

## Start Here

These are compact entry points that make the project concrete before moving into larger constellations.

{starter_text_links([
    "gorgias-encomium-helen",
    "quintilian-institutio-oratoria",
    "schiller-aesthetic-education",
    "wollstonecraft-rights-woman",
    "gramsci-formation-intellectuals",
    "habermas-public-sphere",
], texts, classification_records)}

## All Constellations

| Path | Core Question | Texts | Assembled | Review Rows | Frequent Themes |
| --- | --- | ---: | ---: | ---: | --- |
{constellation_rows(constellations, stats)}

## How To Use This Page

1. Pick a focus lane that matches the current writing question.
2. Open one constellation and skim its text list before choosing a primary text note.
3. Use review rows as a caution signal, not as a reason to avoid the text.
4. Write passage notes only after checking the text note, page range, and restricted draft path.

## Provenance

{provenance_table([
    ("Source-derived metadata", "Focus lanes are scripted editorial routes; constellation IDs, questions, text IDs, and themes come from `data/source-register.yml`."),
    ("Extraction-derived metadata", "Assembled counts, page ranges, and review totals come from local extraction audit artifacts."),
    ("Generated scaffold", "Metrics, lanes, starter links, and constellation table are generated by `scripts/update_workspace_reading_paths.py`."),
    ("Copied source prose", "None. This page contains no copied Norton source prose."),
])}

## Backlinks

{backlink_list([
    link("Private Knowledge Base", "../"),
    link("Workspace Search", "../search/"),
    link("Norton Workspace Map", "../norton-map/"),
    link("Norton Text Notes", "../norton-texts/"),
])}

## Audit Trail

| Field | Value |
| --- | --- |
| Source ID | `{source["source_id"]}` |
| Source title | {html.escape(str(source.get("source_title", "")))} |
| Source rights status | `{html.escape(str(source.get("source_rights_status", "unknown")))}` |
| Source register | `data/source-register.yml` |
| Generated at | `{generated_at}` |
| Git commit | `{git_commit()}` |
| Script version | `{SCRIPT_VERSION}` |
| Output path | `{relative_to_root(output_path)}` |
"""
    return markdown, audit_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="data/extraction-sources.yml")
    parser.add_argument("--source-id", default="norton-theory-criticism")
    parser.add_argument("--source-register", default="data/source-register.yml")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = load_config(args.config, args.source_id)
    source_register = load_source_register(args.source_register)
    output_path = Path(args.output)
    markdown, audit_rows = build_reading_paths_page(source, source_register, output_path)

    if args.dry_run:
        print(markdown)
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    paths = resolve_source_paths(source)
    audit_path = paths["audit_dir"] / "workspace-reading-paths.csv"
    write_csv(
        audit_path,
        ["constellation_id", "text_count", "assembled_count", "review_total", "themes", "generated_at", "script_version", "git_commit"],
        audit_rows,
    )
    print(f"Wrote workspace reading paths to {relative_to_root(output_path)}")
    print(f"Wrote workspace reading path audit to {relative_to_root(audit_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
