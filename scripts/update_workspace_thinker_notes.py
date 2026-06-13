#!/usr/bin/env python3
"""Generate private thinker notes for curated Norton workspace texts."""

from __future__ import annotations

import argparse
import html
from collections import Counter, defaultdict
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
    classification_records_for_text,
    constellations_for_text_ids,
    counter_summary,
    load_source_register,
    page_kinds_by_author,
    page_range_for_records,
    read_csv_rows,
    review_counts_by_author,
    review_counts_for_records,
    works_by_author,
)
from update_workspace_passage_notes import load_passage_notes
from update_workspace_text_notes import author_row_for_text, linked_constellation, registered_work_titles, text_constellations


SCRIPT_VERSION = "1"
DEFAULT_OUTPUT_DIR = "docs/workspace/thinkers"
DEFAULT_PASSAGE_NOTES = "data/passage-notes.yml"


def thinker_slug_for_text(text: dict[str, Any], author_row: dict[str, str] | None) -> str:
    if author_row and author_row.get("author_slug"):
        return author_row["author_slug"]
    return slugify(str(text.get("creator", ""))) or "unknown-thinker"


def text_note_link(text_id: str, label: str) -> str:
    return f"[{html.escape(label)}](../norton-texts/{text_id}.md)"


def thinker_constellation_links(text_ids: list[str], constellations: list[dict[str, Any]]) -> str:
    ids = constellations_for_text_ids(text_ids, constellations)
    if not ids:
        return "- No constellation links yet."
    return "\n".join(f"- {linked_constellation(value, relative_prefix='../')}" for value in ids)


def passage_notes_for_text_ids(text_ids: list[str], passage_notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requested = set(text_ids)
    return [note for note in passage_notes if str(note.get("text_id", "")) in requested]


def thinker_passage_note_links(text_ids: list[str], passage_notes: list[dict[str, Any]]) -> str:
    notes = passage_notes_for_text_ids(text_ids, passage_notes)
    if not notes:
        return "- No passage notes yet."
    return "\n".join(
        f"- [{html.escape(str(note.get('title', note.get('id', 'Untitled Passage'))))}](../passages/{html.escape(str(note.get('id', '')))}.md)"
        for note in notes
    )


def registered_work_titles_for_texts(texts: list[dict[str, Any]]) -> list[str]:
    titles: list[str] = []
    for text in texts:
        for title in registered_work_titles(text):
            if title not in titles:
                titles.append(title)
    return titles


def text_rows_for_thinker(
    texts: list[dict[str, Any]],
    author_rows: dict[str, dict[str, str] | None],
    classification_records: list[dict[str, Any]],
    review_counts: dict[str, Counter[str]],
    constellations: list[dict[str, Any]],
    passage_notes: list[dict[str, Any]],
) -> str:
    rows = []
    for text in texts:
        text_id = str(text["id"])
        author_row = author_rows.get(text_id)
        author_slug = author_row.get("author_slug", "") if author_row else ""
        text_records = classification_records_for_text(classification_records, text)
        text_review_counts = review_counts_for_records(text_records) or review_counts.get(author_slug, Counter())
        pages = page_range_for_records(text_records)
        constellation_links = "<br>".join(linked_constellation(str(item.get("id", "")), relative_prefix="../") for item in text_constellations(text_id, constellations))
        passage_count = len(passage_notes_for_text_ids([text_id], passage_notes))
        rows.append(
            "| "
            + " | ".join(
                [
                    text_note_link(text_id, str(text.get("title", text_id))),
                    html.escape(pages),
                    str(text_review_counts.get("total", 0)),
                    str(passage_count),
                    constellation_links or "",
                    f"`{html.escape(str(text.get('status', 'unknown')))}`",
                ]
            )
            + " |"
        )
    return "\n".join(rows) or "| No texts linked yet |  |  |  |  |  |"


def build_thinker_page(
    thinker_slug: str,
    thinker_name: str,
    texts: list[dict[str, Any]],
    source: dict[str, Any],
    author_rows: dict[str, dict[str, str] | None],
    classification_records: list[dict[str, Any]],
    works: dict[str, list[str]],
    page_kinds: dict[str, Counter[str]],
    review_counts: dict[str, Counter[str]],
    constellations: list[dict[str, Any]],
    passage_notes: list[dict[str, Any]],
    output_path: Path,
) -> str:
    generated_at = now_utc()
    text_ids = [str(text["id"]) for text in texts]
    first_author_row = next((author_rows.get(text_id) for text_id in text_ids if author_rows.get(text_id)), None)
    author_slug = first_author_row.get("author_slug", thinker_slug) if first_author_row else thinker_slug
    themes = sorted({str(theme) for text in texts for theme in text.get("themes", [])})
    work_titles = registered_work_titles_for_texts(texts) or works.get(author_slug, [])

    return f"""# {html.escape(thinker_name)}

{note_meta([
    ("Type", "thinker node"),
    ("Status", "generated private workspace note"),
    ("Source mode", "restricted metadata only"),
    ("Tags", ", ".join(themes) or "TBD"),
])}

{private_banner("Private thinker node", "This page is generated from curated metadata and extraction audits. It contains no copied Norton source prose.")}

## Working Use

Use this note as the thinker-level hub between Norton text nodes, constellations, review pressure, and future passage notes. It is not yet a public biography or interpretive essay.

## Texts In This Workspace

| Text | Norton Pages | Review Rows | Passage Notes | Constellations | Register Status |
| --- | --- | ---: | ---: | --- | --- |
{text_rows_for_thinker(texts, author_rows, classification_records, review_counts, constellations, passage_notes)}

## Works And Excerpt Blocks

{chr(10).join(f"- {html.escape(value)}" for value in work_titles) or "- No work titles detected yet."}

## Constellation Backlinks

{thinker_constellation_links(text_ids, constellations)}

## Review Pressure

| Signal | Value |
| --- | --- |
| Page kinds | {counter_summary(page_kinds.get(author_slug, Counter()), limit=5) or "not classified"} |
| Review rows | {review_counts.get(author_slug, Counter()).get("total", 0)} |
| Review reasons | {counter_summary(review_counts.get(author_slug, Counter()), skip={"total"}, limit=5) or "No review reasons recorded."} |

## Passage Queue

{passage_card("Anchor Candidates", "Choose Passages After Text Review", [
    ("Source location", "use linked text notes and restricted drafts."),
    ("Rights mode", "private until an edition or translation is selected and reviewed."),
    ("Use", "identify passages that explain why this thinker matters to one or more constellations."),
])}

## Passage Notes

{thinker_passage_note_links(text_ids, passage_notes)}

## Provenance

{provenance_table([
    ("Source-derived metadata", "Thinker name, text IDs, titles, themes, and source rights status come from tracked source metadata."),
    ("Extraction-derived metadata", "Page ranges, works, page kinds, and review rows come from local extraction audit artifacts."),
    ("Generated scaffold", "Working Use, Review Pressure, Passage Queue, and Open Questions are generated scaffolding."),
    ("Human commentary", "Not yet reviewed as interpretive commentary."),
    ("Copied source prose", "None."),
])}

## Backlinks

{backlink_list([
    link("Private Knowledge Base", "../../"),
    link("Norton Workspace Map", "../../norton-map/"),
    link("Norton Text Notes", "../../norton-texts/"),
    link("Passage Notes", "../../passages/"),
    *[link(str(note.get("title", note.get("id", "Untitled Passage"))), f"../../passages/{note.get('id', '')}/") for note in passage_notes_for_text_ids(text_ids, passage_notes)],
    link("Thinker Index", "../"),
])}

## Audit Trail

| Field | Value |
| --- | --- |
| Thinker slug | `{thinker_slug}` |
| Source ID | `{source["source_id"]}` |
| Source title | {html.escape(str(source.get("source_title", "")))} |
| Source rights status | `{html.escape(str(source.get("source_rights_status", "unknown")))}` |
| Generated at | `{generated_at}` |
| Git commit | `{git_commit()}` |
| Script version | `{SCRIPT_VERSION}` |
| Output path | `{relative_to_root(output_path)}` |

## Open Questions

- Which edition or translation should anchor public use of this thinker?
- Which text should be reviewed first?
- Which constellation makes this thinker most useful to the project?
"""


def build_index(source: dict[str, Any], grouped: dict[str, list[dict[str, Any]]], output_path: Path) -> str:
    rows = []
    for thinker_slug, texts in sorted(grouped.items()):
        thinker_name = str(texts[0].get("creator", thinker_slug.replace("-", " "))) if texts else thinker_slug
        rows.append(
            "| "
            + " | ".join(
                [
                    f"[{html.escape(thinker_name)}]({thinker_slug}.md)",
                    str(len(texts)),
                    ", ".join(html.escape(str(text.get("title", ""))) for text in texts),
                ]
            )
            + " |"
        )
    generated_at = now_utc()
    return f"""# Thinker Notes

This private index is generated from curated source metadata and local extraction audits. It gives the workspace a thinker layer between text notes and constellations.

{private_banner("Private thinker index", "These pages are navigational records and generated scaffolds. They do not publish copied Norton text.")}

| Thinker | Text Nodes | Current Texts |
| --- | ---: | --- |
{chr(10).join(rows)}

## Provenance

{provenance_table([
    ("Source-derived metadata", "Thinker names and text titles come from `data/source-register.yml`."),
    ("Generated scaffold", "This index is generated by `scripts/update_workspace_thinker_notes.py`."),
    ("Copied source prose", "None."),
])}

## Audit Trail

| Field | Value |
| --- | --- |
| Source ID | `{source["source_id"]}` |
| Source title | {html.escape(str(source.get("source_title", "")))} |
| Generated at | `{generated_at}` |
| Git commit | `{git_commit()}` |
| Script version | `{SCRIPT_VERSION}` |
| Output path | `{relative_to_root(output_path)}` |
"""


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
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = load_config(args.config, args.source_id)
    paths = resolve_source_paths(source)
    source_register = load_source_register(args.source_register)
    curated_texts = [text for text in source_register.get("curated_texts", []) if text.get("id") != source["source_id"]]
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

    author_rows = {
        str(text.get("id", "")): author_row_for_text(text, author_assembly)
        for text in curated_texts
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for text in curated_texts:
        grouped[thinker_slug_for_text(text, author_rows.get(str(text.get("id", ""))))].append(text)

    planned_outputs: list[tuple[Path, str, dict[str, str]]] = []
    index_path = output_dir / "index.md"
    planned_outputs.append((index_path, build_index(source, grouped, index_path), {"thinker_slug": "index", "status": "ok", "error": ""}))
    for thinker_slug, texts in sorted(grouped.items()):
        output_path = output_dir / f"{thinker_slug}.md"
        thinker_name = str(texts[0].get("creator", thinker_slug.replace("-", " "))) if texts else thinker_slug
        planned_outputs.append(
            (
                output_path,
                build_thinker_page(
                    thinker_slug=thinker_slug,
                    thinker_name=thinker_name,
                    texts=texts,
                    source=source,
                    author_rows=author_rows,
                    classification_records=classification_records,
                    works=works,
                    page_kinds=page_kinds,
                    review_counts=review_counts,
                    constellations=constellations,
                    passage_notes=passage_notes,
                    output_path=output_path,
                ),
                {"thinker_slug": thinker_slug, "status": "ok", "error": ""},
            )
        )

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
                "thinker_slug": audit["thinker_slug"],
                "output_file": relative_to_root(output_path),
                "output_sha256": sha256_file(output_path),
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
        paths["audit_dir"] / "workspace-thinker-notes.csv",
        [
            "thinker_slug",
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
    print(f"Wrote {len(planned_outputs)} workspace thinker note files to {relative_to_root(output_dir)}")
    print(f"Wrote workspace thinker note audit to {relative_to_root(paths['audit_dir'] / 'workspace-thinker-notes.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
