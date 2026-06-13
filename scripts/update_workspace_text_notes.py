#!/usr/bin/env python3
"""Generate private Norton text notes from extraction metadata."""

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
    slugify,
    write_csv,
)
from lib.workspace_components import backlink_list, link, note_meta, passage_card, private_banner, provenance_table
from update_workspace_map import (
    author_display_names,
    author_matches_text,
    counter_summary,
    classification_records_for_text,
    load_source_register,
    metric_cards,
    page_kinds_by_author,
    page_kinds_for_records,
    page_range,
    page_range_for_records,
    read_csv_rows,
    review_counts_by_author,
    review_counts_for_records,
    works_by_author,
)
from update_workspace_passage_notes import load_passage_notes


SCRIPT_VERSION = "3"
DEFAULT_OUTPUT_DIR = "docs/workspace/norton-texts"
DEFAULT_PASSAGE_NOTES = "data/passage-notes.yml"


def markdown_list(values: list[str], empty: str = "None recorded yet.") -> str:
    if not values:
        return f"- {empty}"
    return "\n".join(f"- {value}" for value in values)


def linked_constellation(constellation_id: str, relative_prefix: str = "../") -> str:
    path = Path("docs/workspace") / f"{constellation_id}.md"
    if path.exists():
        return f"[{constellation_id}]({relative_prefix}{constellation_id}.md)"
    return f"`{constellation_id}`"


def thinker_slug_for_text(text: dict[str, Any], author_row: dict[str, str] | None) -> str:
    if author_row and author_row.get("author_slug"):
        return author_row["author_slug"]
    return slugify(str(text.get("creator", ""))) or "unknown-thinker"


def linked_thinker(text: dict[str, Any], author_row: dict[str, str] | None) -> str:
    thinker_slug = thinker_slug_for_text(text, author_row)
    path = Path("docs/workspace/thinkers") / f"{thinker_slug}.md"
    label = str(text.get("creator", thinker_slug.replace("-", " ")))
    if path.exists():
        return f"[{html.escape(label)}](../thinkers/{thinker_slug}.md)"
    return html.escape(label)


def thinker_backlink(text: dict[str, Any], author_row: dict[str, str] | None) -> str:
    thinker_slug = thinker_slug_for_text(text, author_row)
    label = str(text.get("creator", thinker_slug.replace("-", " ")))
    return link(label, f"../../thinkers/{thinker_slug}/")


def constellation_backlink(constellation_id: str) -> str:
    return link(constellation_id, f"../../{constellation_id}/")


def passage_notes_for_text(text_id: str, passage_notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [note for note in passage_notes if str(note.get("text_id", "")) == text_id]


def passage_note_links_for_text(text_id: str, passage_notes: list[dict[str, Any]]) -> str:
    notes = passage_notes_for_text(text_id, passage_notes)
    if not notes:
        return "- No passage notes yet."
    return "\n".join(
        f"- [{html.escape(str(note.get('title', note.get('id', 'Untitled Passage'))))}](../passages/{html.escape(str(note.get('id', '')))}.md)"
        for note in notes
    )


def text_constellations(text_id: str, constellations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        constellation
        for constellation in constellations
        if text_id in [str(value) for value in constellation.get("texts", [])]
    ]


def author_row_for_text(text: dict[str, Any], author_assembly: list[dict[str, str]]) -> dict[str, str] | None:
    for row in author_assembly:
        if author_matches_text(row.get("author_slug", ""), text):
            return row
    return None


def registered_work_titles(text: dict[str, Any]) -> list[str]:
    titles: list[str] = []
    title = str(text.get("title", "")).strip()
    if title:
        titles.append(title)
    for value in text.get("extraction_work_titles", []):
        clean = str(value).strip()
        if clean and clean not in titles:
            titles.append(clean)
    return titles


def review_reason_summary(counter: Counter[str]) -> str:
    if not counter or counter.get("total", 0) == 0:
        return "No review rows currently flagged."
    summary = counter_summary(counter, skip={"total"}, limit=5)
    return summary or "Review rows present; reason labels are not populated."


def page_status_card(author_row: dict[str, str] | None, reviews: Counter[str], kinds: Counter[str]) -> str:
    if not author_row:
        return passage_card(
            "Chunk Status",
            "No Assembled Norton Chunk Yet",
            [
                ("Source location", "not currently assembled."),
                ("Review pressure", "no review rows available."),
            ],
        )

    pages = page_range(author_row.get("first_page", ""), author_row.get("last_page", ""))
    return passage_card(
        "Chunk Status",
        f"Norton Pages {pages}",
        [
            ("Page count", html.escape(author_row.get("page_count", ""))),
            ("Restricted draft", f"<code>{html.escape(author_row.get('output_file', ''))}</code>"),
            ("Page kinds", counter_summary(kinds, limit=4) or "not classified"),
            ("Review pressure", f"{reviews.get('total', 0)} rows. {review_reason_summary(reviews)}"),
        ],
    )


def constellation_table_rows(text_id: str, constellations: list[dict[str, Any]]) -> str:
    rows = []
    for constellation in text_constellations(text_id, constellations):
        rows.append(
            "| "
            + " | ".join(
                [
                    linked_constellation(str(constellation.get("id", ""))),
                    str(constellation.get("question", "")),
                    ", ".join(str(value) for value in constellation.get("relations", [])),
                ]
            )
            + " |"
        )
    if not rows:
        return "| No constellation assigned |  |  |"
    return "\n".join(rows)


def build_text_note(
    text: dict[str, Any],
    source: dict[str, Any],
    author_row: dict[str, str] | None,
    text_records: list[dict[str, Any]],
    names: dict[str, str],
    works: dict[str, list[str]],
    page_kinds: dict[str, Counter[str]],
    review_counts: dict[str, Counter[str]],
    constellations: list[dict[str, Any]],
    passage_notes: list[dict[str, Any]],
    output_path: Path,
) -> str:
    text_id = str(text["id"])
    author_slug = author_row.get("author_slug", "") if author_row else ""
    author_name = names.get(author_slug, str(text.get("creator", "")))
    work_titles = registered_work_titles(text) or works.get(author_slug, [])
    kinds = page_kinds_for_records(text_records) or page_kinds.get(author_slug, Counter())
    reviews = review_counts_for_records(text_records) or review_counts.get(author_slug, Counter())
    constellation_ids = [str(item.get("id", "")) for item in text_constellations(text_id, constellations)]
    themes = [str(value) for value in text.get("themes", [])]
    generated_at = now_utc()
    text_page_range = page_range_for_records(text_records) or (page_range(author_row.get("first_page", ""), author_row.get("last_page", "")) if author_row else "not assembled")
    source_location = html.escape(text_page_range)
    constellation_label = html.escape(", ".join(constellation_ids) or "the workspace")

    return f"""# {html.escape(author_name)}, {html.escape(str(text.get("title", "")))}

{note_meta([
    ("Type", "Norton text node"),
    ("Status", "generated private workspace note"),
    ("Source mode", "restricted metadata only"),
    ("Tags", ", ".join(themes) or "TBD"),
])}

{private_banner("Private Norton node", "This page is generated from extraction metadata and curated source-register entries. It contains no copied Norton source prose.")}

## Working Use

This note turns the current Norton chunk for {html.escape(author_name)} into a navigable workspace node. Use it to move between the restricted draft, the curated text spine, the first constellations, and the review queue before writing public-facing commentary.

## Current Chunk

{page_status_card({
    **author_row,
    "first_page": text_page_range.split("-")[0] if "-" in text_page_range else text_page_range,
    "last_page": text_page_range.split("-")[-1] if "-" in text_page_range else text_page_range,
    "page_count": str(len(text_records) or author_row.get("page_count", "")),
} if author_row else None, reviews, kinds)}

## Works And Excerpt Blocks

{markdown_list([html.escape(value) for value in work_titles], "No work titles detected yet.")}

## Constellations

| Constellation | Core Question | Relations |
| --- | --- | --- |
{constellation_table_rows(text_id, constellations)}

## Passage Queue

{passage_card("Anchor Candidates", "Choose Passages After Review", [
    ("Source location", f"Norton page range {source_location}."),
    ("Rights mode", "restricted private notes until a public-domain or otherwise usable reading copy is selected."),
    ("Use", f"Find the passages that make this text active inside {constellation_label}."),
])}

{passage_card("Review Before Quoting", "Layout, Notes, And Bibliography", [
    ("Review signal", review_reason_summary(reviews)),
    ("Editorial rule", "source notes belong in source-note fields, bibliography belongs in bibliography fields, and excerpt text stays separate."),
])}

## Passage Notes

{passage_note_links_for_text(text_id, passage_notes)}

## Provenance

{provenance_table([
    ("Source-derived metadata", "Curated text ID, creator, title, themes, register status, and source rights status come from `data/source-register.yml` and `data/extraction-sources.yml`."),
    ("Extraction-derived metadata", "Page range, restricted draft path, page kinds, and review pressure come from local audit artifacts."),
    ("Generated scaffold", "Working Use, Passage Queue, Backlinks, and Open Questions are generated workspace scaffolding."),
    ("Human commentary", "Not yet reviewed as interpretive commentary."),
    ("Copied source prose", "None. This generated note contains no copied Norton prose."),
])}

## Source Trail

| Field | Value |
| --- | --- |
| Text ID | `{text_id}` |
| Curated title | {html.escape(str(text.get("title", "")))} |
| Creator | {html.escape(str(text.get("creator", "")))} |
| Thinker note | {linked_thinker(text, author_row)} |
| Register status | `{html.escape(str(text.get("status", "unknown")))}` |
| Source anthology | {html.escape(str(source.get("source_title", "")))} |
| Source rights status | `{html.escape(str(source.get("source_rights_status", "unknown")))}` |
| Restricted draft | `{html.escape(author_row.get("output_file", "") if author_row else "")}` |
| Workspace map | [Norton Workspace Map](../norton-map.md) |
| Generated at | `{generated_at}` |
| Git commit | `{git_commit()}` |
| Script version | `{SCRIPT_VERSION}` |
| Output path | `{relative_to_root(output_path)}` |

## Backlinks

{backlink_list([
    link("Norton Text Notes", "../"),
    link("Norton Workspace Map", "../../norton-map/"),
    link("Private Knowledge Base", "../../"),
    link("Text Catalog", "../../../catalog/sources/"),
    f"Thinker: {thinker_backlink(text, author_row)}",
    link("Passage Notes", "../../passages/"),
    *[link(str(note.get("title", note.get("id", "Untitled Passage"))), f"../../passages/{note.get('id', '')}/") for note in passage_notes_for_text(text_id, passage_notes)],
    *([constellation_backlink(value) for value in constellation_ids] or ["No constellation backlinks yet."]),
])}

## Open Questions

- Which edition or translation should become the public reading copy?
- Which two or three passages should anchor this text in the workspace?
- Which review rows need cleanup before the chunk can be treated as stable?
"""


def build_index(
    source: dict[str, Any],
    curated_texts: list[dict[str, Any]],
    author_assembly: list[dict[str, str]],
    classification_records: list[dict[str, Any]],
    names: dict[str, str],
    review_counts: dict[str, Counter[str]],
    constellations: list[dict[str, Any]],
    passage_notes: list[dict[str, Any]],
    output_path: Path,
) -> str:
    rows = []
    assembled_count = 0
    for text in curated_texts:
        if text.get("id") == source["source_id"]:
            continue
        text_id = str(text["id"])
        author_row = author_row_for_text(text, author_assembly)
        author_slug = author_row.get("author_slug", "") if author_row else ""
        author_name = names.get(author_slug, str(text.get("creator", "")))
        text_records = classification_records_for_text(classification_records, text)
        pages = page_range_for_records(text_records) or (page_range(author_row.get("first_page", ""), author_row.get("last_page", "")) if author_row else "")
        text_review_counts = review_counts_for_records(text_records) or review_counts.get(author_slug, Counter())
        if author_row:
            assembled_count += 1
        constellation_ids = [str(item.get("id", "")) for item in text_constellations(text_id, constellations)]
        passage_count = len(passage_notes_for_text(text_id, passage_notes))
        rows.append(
            "| "
            + " | ".join(
                [
                    f"[{html.escape(str(text.get('title', '')))}]({text_id}.md)",
                    html.escape(author_name),
                    pages,
                    "<br>".join(linked_constellation(value) for value in constellation_ids),
                    str(passage_count),
                    str(text_review_counts.get("total", 0)),
                    f"`{html.escape(str(text.get('status', 'unknown')))}`",
                ]
            )
            + " |"
        )

    generated_at = now_utc()
    return f"""# Norton Text Notes

This index is generated from curated source metadata and local extraction audit files. It is a private workspace view for seeing which texts already have Norton chunks and where they fit.

<div class="ah-private-banner">
  <strong>Restricted workspace index</strong>
  <span>These pages are navigational records. They do not publish copied Norton text.</span>
</div>

<div class="ah-metric-grid">
{metric_cards([
    ("Curated Text Nodes", len([text for text in curated_texts if text.get("id") != source["source_id"]])),
    ("Assembled Chunks", assembled_count),
    ("Constellations", len(constellations)),
])}
</div>

## Text Nodes

| Text | Thinker | Norton Pages | Constellations | Passage Notes | Review Rows | Register Status |
| --- | --- | --- | --- | ---: | ---: | --- |
{chr(10).join(rows)}

## How To Use This Index

1. Start with a text note, then follow its constellation links.
2. Use review-row counts to decide which chunks need cleanup before close reading.
3. Keep copied passages private until an edition and rights path are selected.

## Provenance

| Layer | Status |
| --- | --- |
| Source-derived metadata | Text IDs, creators, titles, themes, and register status come from `data/source-register.yml`. |
| Extraction-derived metadata | Page ranges, review counts, and assembled chunk status come from local audit artifacts. |
| Generated scaffold | This index is generated by `scripts/update_workspace_text_notes.py`. |
| Human commentary | None in this generated index. |
| Copied source prose | None. |

## Audit Trail

| Field | Value |
| --- | --- |
| Source ID | `{source["source_id"]}` |
| Source title | {html.escape(str(source.get("source_title", "")))} |
| Source rights status | `{html.escape(str(source.get("source_rights_status", "unknown")))}` |
| Source register | `data/source-register.yml` |
| Workspace map | [Norton Workspace Map](../norton-map.md) |
| Generated at | `{generated_at}` |
| Git commit | `{git_commit()}` |
| Script version | `{SCRIPT_VERSION}` |
| Output path | `{relative_to_root(output_path)}` |
"""


def select_texts(curated_texts: list[dict[str, Any]], source_id: str, text_ids: list[str] | None, limit: int | None) -> list[dict[str, Any]]:
    selected = [text for text in curated_texts if text.get("id") != source_id]
    if text_ids:
        requested = set(text_ids)
        selected = [text for text in selected if str(text.get("id", "")) in requested]
    if limit is not None:
        selected = selected[:limit]
    return selected


def clean_output_dir(output_dir: Path) -> None:
    if not output_dir.exists():
        return
    for path in output_dir.glob("*.md"):
        path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="data/extraction-sources.yml")
    parser.add_argument("--source-id", default="norton-theory-criticism")
    parser.add_argument("--source-register", default="data/source-register.yml")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--passage-notes", default=DEFAULT_PASSAGE_NOTES)
    parser.add_argument("--text-id", action="append", help="Curated text ID to generate. Repeat for multiple texts.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--clean", action="store_true", help="Remove existing generated Markdown files in the output directory before writing.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = load_config(args.config, args.source_id)
    paths = resolve_source_paths(source)
    source_register = load_source_register(args.source_register)
    curated_texts = source_register.get("curated_texts", [])
    constellations = source_register.get("constellations", [])
    passage_notes = load_passage_notes(args.passage_notes)
    classification_records = read_jsonl(paths["classification_dir"] / "page-classifications.jsonl")
    author_assembly = read_csv_rows(paths["audit_dir"] / "author-assembly.csv")
    review_rows = read_csv_rows(paths["review_dir"] / "page-records-needing-review.csv")
    names = author_display_names(classification_records, review_rows)
    works = works_by_author(classification_records, curated_texts, names)
    page_kinds = page_kinds_by_author(classification_records)
    review_counts = review_counts_by_author(review_rows)
    output_dir = Path(args.output_dir)
    selected_texts = select_texts(curated_texts, source["source_id"], args.text_id, args.limit)

    planned_outputs: list[tuple[Path, str, dict[str, str]]] = []
    for text in selected_texts:
        text_id = str(text["id"])
        output_path = output_dir / f"{text_id}.md"
        author_row = author_row_for_text(text, author_assembly)
        text_records = classification_records_for_text(classification_records, text)
        text_page_range = page_range_for_records(text_records)
        markdown = build_text_note(
            text=text,
            source=source,
            author_row=author_row,
            text_records=text_records,
            names=names,
            works=works,
            page_kinds=page_kinds,
            review_counts=review_counts,
            constellations=constellations,
            passage_notes=passage_notes,
            output_path=output_path,
        )
        planned_outputs.append(
            (
                output_path,
                markdown,
                {
                    "text_id": text_id,
                    "author_slug": author_row.get("author_slug", "") if author_row else "",
                    "page_range": text_page_range or (page_range(author_row.get("first_page", ""), author_row.get("last_page", "")) if author_row else ""),
                    "constellations": ",".join(str(item.get("id", "")) for item in text_constellations(text_id, constellations)),
                },
            )
        )

    index_path = output_dir / "index.md"
    index_markdown = build_index(source, selected_texts, author_assembly, classification_records, names, review_counts, constellations, passage_notes, index_path)
    planned_outputs.insert(0, (index_path, index_markdown, {"text_id": "index", "author_slug": "", "page_range": "", "constellations": ""}))

    if args.dry_run:
        for output_path, markdown, _audit in planned_outputs:
            print(f"--- {relative_to_root(output_path)} ---")
            print(markdown)
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    if args.clean:
        clean_output_dir(output_dir)

    audit_rows: list[dict[str, Any]] = []
    generated_at = now_utc()
    for output_path, markdown, audit in planned_outputs:
        output_path.write_text(markdown, encoding="utf-8")
        audit_rows.append(
            {
                "text_id": audit["text_id"],
                "author_slug": audit["author_slug"],
                "page_range": audit["page_range"],
                "constellations": audit["constellations"],
                "output_file": relative_to_root(output_path),
                "output_sha256": sha256_file(output_path),
                "source_config": source.get("_config_path", args.config),
                "source_register": args.source_register,
                "status": "ok",
                "error": "",
                "generated_at": generated_at,
                "git_commit": git_commit(),
                "script_version": SCRIPT_VERSION,
            }
        )

    write_csv(
        paths["audit_dir"] / "workspace-text-notes.csv",
        [
            "text_id",
            "author_slug",
            "page_range",
            "constellations",
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
    print(f"Wrote {len(planned_outputs)} workspace text note files to {relative_to_root(output_dir)}")
    print(f"Wrote workspace text note audit to {relative_to_root(paths['audit_dir'] / 'workspace-text-notes.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
