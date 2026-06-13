#!/usr/bin/env python3
"""Generate a static workspace search index and filtered search page."""

from __future__ import annotations

import argparse
import json
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
from lib.workspace_components import private_banner, provenance_table
from update_workspace_map import (
    author_matches_text,
    constellations_for_text_ids,
    load_source_register,
    page_range,
    read_csv_rows,
    review_counts_by_author,
)
from update_workspace_passage_notes import load_passage_notes
from update_workspace_text_notes import author_row_for_text


SCRIPT_VERSION = "1"
DEFAULT_OUTPUT_PAGE = "docs/workspace/search.md"
DEFAULT_OUTPUT_JSON = "docs/assets/data/workspace-search.json"
DEFAULT_PASSAGE_NOTES = "data/passage-notes.yml"


def safe_list(values: Any) -> list[str]:
    if not values:
        return []
    if isinstance(values, list):
        return [str(value) for value in values if str(value)]
    return [str(values)]


def entry(
    *,
    entry_id: str,
    kind: str,
    title: str,
    url: str,
    summary: str,
    tags: list[str],
    thinker: str = "",
    text_id: str = "",
    constellation_ids: list[str] | None = None,
    status: str = "",
    review_pressure: int = 0,
) -> dict[str, Any]:
    normalized_tags = sorted({slugify(tag, fallback="tag") for tag in tags if tag})
    return {
        "id": entry_id,
        "kind": kind,
        "title": title,
        "url": url,
        "summary": summary,
        "tags": normalized_tags,
        "thinker": thinker,
        "text_id": text_id,
        "constellations": sorted(set(constellation_ids or [])),
        "status": status,
        "review_pressure": review_pressure,
        "search_text": " ".join(
            [
                title,
                summary,
                thinker,
                text_id,
                status,
                " ".join(normalized_tags),
                " ".join(sorted(set(constellation_ids or []))),
            ]
        ).lower(),
    }


def build_entries(
    *,
    source: dict[str, Any],
    source_register: dict[str, Any],
    passage_notes: list[dict[str, Any]],
    author_assembly: list[dict[str, str]],
    review_counts: dict[str, Counter[str]],
) -> list[dict[str, Any]]:
    curated_texts = [text for text in source_register.get("curated_texts", []) if text.get("id") != source["source_id"]]
    constellations = source_register.get("constellations", [])
    entries: list[dict[str, Any]] = []

    for text in curated_texts:
        text_id = str(text.get("id", ""))
        author_row = author_row_for_text(text, author_assembly)
        author_slug = author_row.get("author_slug", "") if author_row else slugify(str(text.get("creator", "")))
        pages = page_range(author_row.get("first_page", ""), author_row.get("last_page", "")) if author_row else ""
        constellation_ids = constellations_for_text_ids([text_id], constellations)
        review_pressure = review_counts.get(author_slug, Counter()).get("total", 0)
        summary = f"{text.get('creator', '')}; {text.get('role', '')}; pages {pages or 'not assembled'}; {review_pressure} review rows."
        entries.append(
            entry(
                entry_id=f"text:{text_id}",
                kind="text",
                title=str(text.get("title", text_id)),
                url=f"/workspace/norton-texts/{text_id}/",
                summary=summary,
                tags=safe_list(text.get("themes", [])) + constellation_ids,
                thinker=str(text.get("creator", "")),
                text_id=text_id,
                constellation_ids=constellation_ids,
                status=str(text.get("status", "")),
                review_pressure=review_pressure,
            )
        )

    thinker_seen: set[str] = set()
    for text in curated_texts:
        author_row = author_row_for_text(text, author_assembly)
        thinker_slug = author_row.get("author_slug", "") if author_row else slugify(str(text.get("creator", "")))
        if not thinker_slug or thinker_slug in thinker_seen:
            continue
        thinker_seen.add(thinker_slug)
        thinker_texts = [item for item in curated_texts if author_matches_text(thinker_slug, item)]
        text_ids = [str(item.get("id", "")) for item in thinker_texts]
        constellation_ids = constellations_for_text_ids(text_ids, constellations)
        themes = [theme for item in thinker_texts for theme in safe_list(item.get("themes", []))]
        review_pressure = review_counts.get(thinker_slug, Counter()).get("total", 0)
        entries.append(
            entry(
                entry_id=f"thinker:{thinker_slug}",
                kind="thinker",
                title=str(thinker_texts[0].get("creator", thinker_slug.replace("-", " "))) if thinker_texts else thinker_slug,
                url=f"/workspace/thinkers/{thinker_slug}/",
                summary=f"{len(thinker_texts)} text node(s); {', '.join(text_ids)}.",
                tags=themes + constellation_ids,
                thinker=str(thinker_texts[0].get("creator", "")) if thinker_texts else thinker_slug,
                constellation_ids=constellation_ids,
                status="generated private workspace note",
                review_pressure=review_pressure,
            )
        )

    for constellation in constellations:
        constellation_id = str(constellation.get("id", ""))
        text_ids = safe_list(constellation.get("texts", []))
        entries.append(
            entry(
                entry_id=f"constellation:{constellation_id}",
                kind="constellation",
                title=constellation_id.replace("-", " ").title(),
                url=f"/workspace/{constellation_id}/",
                summary=str(constellation.get("question", "")),
                tags=safe_list(constellation.get("relations", [])) + text_ids,
                constellation_ids=[constellation_id],
                status="private constellation draft",
            )
        )

    for note in passage_notes:
        note_id = str(note.get("id", ""))
        constellation_ids = safe_list(note.get("constellation_ids", []))
        entries.append(
            entry(
                entry_id=f"passage:{note_id}",
                kind="passage",
                title=str(note.get("title", note_id)),
                url=f"/workspace/passages/{note_id}/",
                summary=str(note.get("paraphrase", "")).strip(),
                tags=safe_list(note.get("tags", [])) + constellation_ids,
                thinker=str(note.get("thinker", "")),
                text_id=str(note.get("text_id", "")),
                constellation_ids=constellation_ids,
                status=str(note.get("rights_mode", note.get("status", ""))),
            )
        )

    chapter_entries = [
        ("chapters/00-start-here/", "Start Here", "Project orientation and reading protocol.", ["orientation", "method"]),
        ("chapters/01-methods/", "Methods", "Method notes for reading curated theory and criticism.", ["method", "theory"]),
        ("chapters/02-rupture-points/", "Rupture Points", "Historical breaks, force, and discontinuity.", ["history", "rupture"]),
        ("chapters/03-erased-archives/", "Erased Archives", "Silence, loss, archive, and recovery.", ["archive", "memory"]),
        ("chapters/04-counterfactual-method/", "Counterfactual Method", "Counterfactual reading and historical possibility.", ["counterfactual", "method"]),
        ("chapters/05-memory-and-myth/", "Memory And Myth", "Memory, myth, and narrative inheritance.", ["memory", "myth"]),
    ]
    for url, title, summary, tags in chapter_entries:
        entries.append(
            entry(
                entry_id=f"chapter:{url}",
                kind="chapter",
                title=title,
                url=f"/{url}",
                summary=summary,
                tags=tags,
                status="chapter draft",
            )
        )

    return sorted(entries, key=lambda item: (item["kind"], item["title"].lower()))


def build_filter_counts(entries: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = {
        "kinds": Counter(),
        "tags": Counter(),
        "constellations": Counter(),
        "thinkers": Counter(),
        "statuses": Counter(),
    }
    for item in entries:
        counts["kinds"][item["kind"]] += 1
        counts["statuses"][item.get("status") or "unknown"] += 1
        if item.get("thinker"):
            counts["thinkers"][item["thinker"]] += 1
        for tag in item.get("tags", []):
            counts["tags"][tag] += 1
        for constellation_id in item.get("constellations", []):
            counts["constellations"][constellation_id] += 1
    return {key: dict(counter.most_common()) for key, counter in counts.items()}


def build_page(source: dict[str, Any], entries: list[dict[str, Any]], output_page: Path, output_json: Path) -> str:
    generated_at = now_utc()
    counts = Counter(item["kind"] for item in entries)
    return f"""# Workspace Search

This generated page gives the private workspace a filtered index across texts, thinkers, passage notes, constellations, and chapter drafts.

{private_banner("Private search surface", "This page indexes curated metadata and paraphrase-first notes. It does not publish copied Norton source prose.")}

<div class="ah-search-app" data-index="../../assets/data/workspace-search.json">
  <div class="ah-search-controls">
    <label for="ah-workspace-query">Search</label>
    <input id="ah-workspace-query" type="search" placeholder="Search thinker, text, constellation, passage, concept..." autocomplete="off">
    <label for="ah-kind-filter">Type</label>
    <select id="ah-kind-filter">
      <option value="">All types</option>
    </select>
    <label for="ah-tag-filter">Tag</label>
    <select id="ah-tag-filter">
      <option value="">All tags</option>
    </select>
    <label for="ah-constellation-filter">Constellation</label>
    <select id="ah-constellation-filter">
      <option value="">All constellations</option>
    </select>
  </div>
  <div class="ah-search-summary" aria-live="polite">Loading workspace index...</div>
  <div class="ah-search-results"></div>
</div>

## Static Coverage

| Type | Count |
| --- | ---: |
| Texts | {counts.get("text", 0)} |
| Thinkers | {counts.get("thinker", 0)} |
| Passages | {counts.get("passage", 0)} |
| Constellations | {counts.get("constellation", 0)} |
| Chapters | {counts.get("chapter", 0)} |

## Provenance

{provenance_table([
    ("Source-derived metadata", "Text, thinker, constellation, and source status fields come from `data/source-register.yml`."),
    ("Passage metadata", "Passage records come from `data/passage-notes.yml`."),
    ("Extraction-derived metadata", "Review pressure comes from local audit artifacts when available."),
    ("Generated scaffold", "This page and JSON index are generated by `scripts/update_workspace_search.py`."),
    ("Copied source prose", "None."),
])}

## Audit Trail

| Field | Value |
| --- | --- |
| Source ID | `{source["source_id"]}` |
| Source title | {source.get("source_title", "")} |
| Entry count | {len(entries)} |
| JSON index | `{relative_to_root(output_json)}` |
| Generated at | `{generated_at}` |
| Git commit | `{git_commit()}` |
| Script version | `{SCRIPT_VERSION}` |
| Output path | `{relative_to_root(output_page)}` |
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="data/extraction-sources.yml")
    parser.add_argument("--source-id", default="norton-theory-criticism")
    parser.add_argument("--source-register", default="data/source-register.yml")
    parser.add_argument("--passage-notes", default=DEFAULT_PASSAGE_NOTES)
    parser.add_argument("--output-page", default=DEFAULT_OUTPUT_PAGE)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = load_config(args.config, args.source_id)
    paths = resolve_source_paths(source)
    source_register = load_source_register(args.source_register)
    passage_notes = load_passage_notes(args.passage_notes)
    review_rows = read_csv_rows(paths["review_dir"] / "page-records-needing-review.csv")
    author_assembly = read_csv_rows(paths["audit_dir"] / "author-assembly.csv")
    review_counts = review_counts_by_author(review_rows)

    entries = build_entries(
        source=source,
        source_register=source_register,
        passage_notes=passage_notes,
        author_assembly=author_assembly,
        review_counts=review_counts,
    )
    payload = {
        "generated_at": now_utc(),
        "git_commit": git_commit(),
        "script_version": SCRIPT_VERSION,
        "source_id": source["source_id"],
        "entry_count": len(entries),
        "filters": build_filter_counts(entries),
        "entries": entries,
    }
    output_page = Path(args.output_page)
    output_json = Path(args.output_json)
    page_markdown = build_page(source, entries, output_page, output_json)

    if args.dry_run:
        print(page_markdown)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    output_page.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_page.write_text(page_markdown, encoding="utf-8")
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    generated_at = now_utc()
    write_csv(
        paths["audit_dir"] / "workspace-search.csv",
        [
            "source_id",
            "entry_count",
            "output_page",
            "output_page_sha256",
            "output_json",
            "output_json_sha256",
            "source_config",
            "source_register",
            "passage_notes",
            "status",
            "error",
            "generated_at",
            "git_commit",
            "script_version",
        ],
        [
            {
                "source_id": source["source_id"],
                "entry_count": len(entries),
                "output_page": relative_to_root(output_page),
                "output_page_sha256": sha256_file(output_page),
                "output_json": relative_to_root(output_json),
                "output_json_sha256": sha256_file(output_json),
                "source_config": source.get("_config_path", args.config),
                "source_register": args.source_register,
                "passage_notes": args.passage_notes,
                "status": "ok",
                "error": "",
                "generated_at": generated_at,
                "git_commit": git_commit(),
                "script_version": SCRIPT_VERSION,
            }
        ],
    )
    print(f"Wrote workspace search page to {relative_to_root(output_page)}")
    print(f"Wrote workspace search index to {relative_to_root(output_json)}")
    print(f"Wrote workspace search audit to {relative_to_root(paths['audit_dir'] / 'workspace-search.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
