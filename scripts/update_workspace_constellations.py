#!/usr/bin/env python3
"""Generate private workspace constellation pages from curated source metadata."""

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
    sha256_file,
    write_csv,
)
from lib.workspace_components import backlink_list, link, note_meta, passage_card, private_banner, provenance_table
from update_workspace_map import (
    classification_records_for_text,
    counter_summary,
    load_source_register,
    page_kinds_by_author,
    page_kinds_for_records,
    page_range,
    page_range_for_records,
    read_csv_rows,
    review_counts_by_author,
    review_counts_for_records,
)
from update_workspace_text_notes import author_row_for_text


SCRIPT_VERSION = "2"
DEFAULT_OUTPUT_DIR = "docs/workspace"


def text_by_id(curated_texts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(text.get("id", "")): text for text in curated_texts if text.get("id")}


def text_note_path(text_id: str) -> str:
    return f"norton-texts/{text_id}.md"


def text_note_href(text_id: str) -> str:
    return f"../norton-texts/{text_id}/"


def text_role(text: dict[str, Any], index: int) -> str:
    themes = [str(value) for value in text.get("themes", [])]
    if themes:
        return ", ".join(themes[:3])
    return f"configured text {index + 1}"


def text_cards(
    constellation: dict[str, Any],
    texts: dict[str, dict[str, Any]],
    author_rows: dict[str, dict[str, str] | None],
    review_counts: dict[str, Counter[str]],
    classification_records: list[dict[str, Any]],
) -> str:
    cards = []
    for index, text_id in enumerate([str(value) for value in constellation.get("texts", [])]):
        text = texts.get(text_id, {})
        author_row = author_rows.get(text_id)
        author_slug = author_row.get("author_slug", "") if author_row else ""
        text_records = classification_records_for_text(classification_records, text)
        pages = page_range_for_records(text_records) or (page_range(author_row.get("first_page", ""), author_row.get("last_page", "")) if author_row else "not assembled")
        review_count = (review_counts_for_records(text_records) or review_counts.get(author_slug, Counter())).get("total", 0)
        label = f"{text.get('creator', 'Unknown')}, {text.get('title', text_id)}"
        cards.append(
            f"""  <a href="{text_note_href(text_id)}"><strong>{html.escape(str(label))}</strong><span>{html.escape(text_role(text, index))}; pages {html.escape(pages)}; {review_count} review rows</span></a>"""
        )
    return "\n".join(cards)


def relationship_rows(constellation: dict[str, Any], texts: dict[str, dict[str, Any]]) -> str:
    text_ids = [str(value) for value in constellation.get("texts", [])]
    relations = [str(value) for value in constellation.get("relations", [])]
    rows = []
    for index, relation in enumerate(relations):
        from_text = texts.get(text_ids[index % len(text_ids)], {}) if text_ids else {}
        to_text = texts.get(text_ids[(index + 1) % len(text_ids)], {}) if text_ids else {}
        from_label = str(from_text.get("creator", from_text.get("title", "TBD")))
        to_label = str(to_text.get("creator", to_text.get("title", "TBD")))
        rows.append(
            "| "
            + " | ".join(
                [
                    html.escape(relation.replace("-", " ").title()),
                    html.escape(from_label),
                    html.escape(to_label),
                    "Configured relation; needs close-reading evidence before promotion.",
                ]
            )
            + " |"
        )
    if not rows:
        return "| TBD | TBD | TBD | Relation not configured yet. |"
    return "\n".join(rows)


def reading_path(constellation: dict[str, Any], texts: dict[str, dict[str, Any]]) -> str:
    lines = []
    for index, text_id in enumerate([str(value) for value in constellation.get("texts", [])], start=1):
        text = texts.get(text_id, {})
        label = f"{text.get('creator', 'Unknown')}, {text.get('title', text_id)}"
        lines.append(f"{index}. [{html.escape(str(label))}]({text_note_path(text_id)})")
    return "\n".join(lines) or "1. Add texts to this constellation in `data/source-register.yml`."


def review_summary_rows(
    constellation: dict[str, Any],
    texts: dict[str, dict[str, Any]],
    author_rows: dict[str, dict[str, str] | None],
    page_kinds: dict[str, Counter[str]],
    review_counts: dict[str, Counter[str]],
    classification_records: list[dict[str, Any]],
) -> str:
    rows = []
    for text_id in [str(value) for value in constellation.get("texts", [])]:
        text = texts.get(text_id, {})
        author_row = author_rows.get(text_id)
        author_slug = author_row.get("author_slug", "") if author_row else ""
        text_records = classification_records_for_text(classification_records, text)
        text_pages = page_range_for_records(text_records) or (page_range(author_row.get("first_page", ""), author_row.get("last_page", "")) if author_row else "")
        text_reviews = review_counts_for_records(text_records) or review_counts.get(author_slug, Counter())
        text_kinds = page_kinds_for_records(text_records) or page_kinds.get(author_slug, Counter())
        rows.append(
            "| "
            + " | ".join(
                [
                    f"[{html.escape(str(text.get('title', text_id)))}]({text_note_path(text_id)})",
                    html.escape(text_pages),
                    str(text_reviews.get("total", 0)),
                    counter_summary(text_kinds, limit=3) or "",
                ]
            )
            + " |"
        )
    return "\n".join(rows) or "| No texts configured |  |  |  |"


def build_constellation_page(
    constellation: dict[str, Any],
    source: dict[str, Any],
    curated_texts: list[dict[str, Any]],
    author_rows: dict[str, dict[str, str] | None],
    page_kinds: dict[str, Counter[str]],
    review_counts: dict[str, Counter[str]],
    classification_records: list[dict[str, Any]],
    output_path: Path,
) -> str:
    constellation_id = str(constellation.get("id", "unknown"))
    texts = text_by_id(curated_texts)
    relations = [str(value) for value in constellation.get("relations", [])]
    generated_at = now_utc()
    title = constellation_id.replace("-", " ").title()

    return f"""# {html.escape(title)}

{note_meta([
    ("Type", "constellation note"),
    ("Status", "generated private workspace draft"),
    ("Source mode", "restricted metadata only"),
    ("Tags", ", ".join(relations) or "TBD"),
])}

{private_banner("Private constellation draft", "This page is generated from curated metadata and local extraction audits. It contains no copied Norton source prose.")}

## Core Question

{html.escape(str(constellation.get("question", "Question pending.")))}

## Working Claim

This is a scaffold for reading the configured texts together. It should become a stronger claim only after passage review, edition review, and close reading.

## Texts In Play

<div class="ah-graph-list">
{text_cards(constellation, texts, author_rows, review_counts, classification_records)}
</div>

## Relationship Map

| Relation | From | To | Current Status |
| --- | --- | --- | --- |
{relationship_rows(constellation, texts)}

## Reading Path

{reading_path(constellation, texts)}

## Review Pressure

| Text | Norton Pages | Review Rows | Page Kinds |
| --- | --- | ---: | --- |
{review_summary_rows(constellation, texts, author_rows, page_kinds, review_counts, classification_records)}

## Passage Queue

{passage_card("Anchor Candidates", "Choose Passages After Review", [
    ("Source location", "use the linked Norton text nodes and restricted drafts."),
    ("Rights mode", "restricted private notes until public-domain or otherwise usable reading copies are selected."),
    ("Use", "Identify two or three passages that make the constellation question concrete."),
])}

{passage_card("Editorial Boundary", "Not Yet A Public Essay", [
    ("Current state", "metadata scaffold."),
    ("Promotion rule", "do not turn this into public-facing interpretation until the selected passages and editions are reviewed."),
])}

## Provenance

{provenance_table([
    ("Source-derived metadata", "Constellation ID, question, text IDs, relations, source title, and rights status come from tracked source metadata."),
    ("Extraction-derived metadata", "Page ranges, review rows, and page-kind summaries come from local extraction audit artifacts."),
    ("Generated scaffold", "Working Claim, Relationship Map, Passage Queue, Review Pressure, and Open Questions are generated scaffolding."),
    ("Human commentary", "Not yet reviewed as interpretive commentary."),
    ("Copied source prose", "None. This generated page contains no copied Norton prose."),
])}

## Backlinks

{backlink_list([
    link("Private Knowledge Base", "../"),
    link("Norton Workspace Map", "../norton-map/"),
    link("Norton Text Notes", "../norton-texts/"),
    link("Constellation Catalog", "../../catalog/constellations/"),
])}

## Audit Trail

| Field | Value |
| --- | --- |
| Constellation ID | `{constellation_id}` |
| Source ID | `{source["source_id"]}` |
| Source title | {html.escape(str(source.get("source_title", "")))} |
| Source rights status | `{html.escape(str(source.get("source_rights_status", "unknown")))}` |
| Source register | `data/source-register.yml` |
| Generated at | `{generated_at}` |
| Git commit | `{git_commit()}` |
| Script version | `{SCRIPT_VERSION}` |
| Output path | `{relative_to_root(output_path)}` |

## Open Questions

- Which passage should become the first anchor for this constellation?
- Which public reading copy should be used for each text?
- Which relation labels need to be revised after close reading?
"""


def select_constellations(
    constellations: list[dict[str, Any]],
    constellation_ids: list[str] | None,
    limit: int | None,
) -> list[dict[str, Any]]:
    selected = constellations
    if constellation_ids:
        requested = set(constellation_ids)
        selected = [item for item in selected if str(item.get("id", "")) in requested]
    if limit is not None:
        selected = selected[:limit]
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="data/extraction-sources.yml")
    parser.add_argument("--source-id", default="norton-theory-criticism")
    parser.add_argument("--source-register", default="data/source-register.yml")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--constellation-id", action="append", help="Constellation ID to generate. Repeat for multiple IDs.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--force", action="store_true", help="Overwrite existing constellation pages.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = load_config(args.config, args.source_id)
    paths = resolve_source_paths(source)
    source_register = load_source_register(args.source_register)
    curated_texts = source_register.get("curated_texts", [])
    constellations = select_constellations(source_register.get("constellations", []), args.constellation_id, args.limit)
    classification_records = read_jsonl(paths["classification_dir"] / "page-classifications.jsonl")
    author_assembly = read_csv_rows(paths["audit_dir"] / "author-assembly.csv")
    review_rows = read_csv_rows(paths["review_dir"] / "page-records-needing-review.csv")
    page_kinds = page_kinds_by_author(classification_records)
    review_counts = review_counts_by_author(review_rows)
    output_dir = Path(args.output_dir)

    author_rows: dict[str, dict[str, str] | None] = {
        str(text.get("id", "")): author_row_for_text(text, author_assembly)
        for text in curated_texts
        if text.get("id") != source["source_id"]
    }

    planned_outputs: list[tuple[Path, str, dict[str, Any]]] = []
    for constellation in constellations:
        constellation_id = str(constellation.get("id", "unknown"))
        output_path = output_dir / f"{constellation_id}.md"
        exists = output_path.exists()
        if exists and not args.force:
            planned_outputs.append(
                (
                    output_path,
                    "",
                    {
                        "constellation_id": constellation_id,
                        "status": "skipped_existing",
                        "error": "",
                    },
                )
            )
            continue
        markdown = build_constellation_page(
            constellation=constellation,
            source=source,
            curated_texts=curated_texts,
            author_rows=author_rows,
            page_kinds=page_kinds,
            review_counts=review_counts,
            classification_records=classification_records,
            output_path=output_path,
        )
        planned_outputs.append(
            (
                output_path,
                markdown,
                {
                    "constellation_id": constellation_id,
                    "status": "ok",
                    "error": "",
                },
            )
        )

    if args.dry_run:
        for output_path, markdown, audit in planned_outputs:
            print(f"--- {relative_to_root(output_path)} [{audit['status']}] ---")
            if markdown:
                print(markdown)
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    audit_rows: list[dict[str, Any]] = []
    generated_at = now_utc()
    for output_path, markdown, audit in planned_outputs:
        if markdown:
            output_path.write_text(markdown, encoding="utf-8")
        audit_rows.append(
            {
                "constellation_id": audit["constellation_id"],
                "output_file": relative_to_root(output_path),
                "output_sha256": sha256_file(output_path) if output_path.exists() else "",
                "source_config": source.get("_config_path", args.config),
                "source_register": args.source_register,
                "status": audit["status"],
                "error": audit["error"],
                "generated_at": generated_at,
                "git_commit": git_commit(),
                "script_version": SCRIPT_VERSION,
            }
        )

    write_csv(
        paths["audit_dir"] / "workspace-constellations.csv",
        [
            "constellation_id",
            "output_file",
            "output_sha256",
            "source_config",
            "source_register",
            "status",
            "error",
            "generated_at",
            "git_commit",
            "script_version",
        ],
        audit_rows,
    )
    wrote_count = sum(1 for _path, markdown, _audit in planned_outputs if markdown)
    skipped_count = sum(1 for _path, markdown, _audit in planned_outputs if not markdown)
    print(f"Wrote {wrote_count} workspace constellation pages to {relative_to_root(output_dir)}")
    if skipped_count:
        print(f"Skipped {skipped_count} existing constellation pages; pass --force to overwrite")
    print(f"Wrote workspace constellation audit to {relative_to_root(paths['audit_dir'] / 'workspace-constellations.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
