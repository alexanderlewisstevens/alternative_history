#!/usr/bin/env python3
"""Write a rights-safe MkDocs status page from extraction audit artifacts."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from lib.extraction_common import (
    git_commit,
    load_config,
    now_utc,
    read_jsonl,
    read_sliced_manifest,
    relative_to_root,
    resolve_source_paths,
)


SCRIPT_VERSION = "1"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as file_obj:
        return list(csv.DictReader(file_obj))


def count_files(path: Path, pattern: str) -> int:
    return len(list(path.glob(pattern))) if path.exists() else 0


def table_row(values: list[Any]) -> str:
    return "| " + " | ".join("" if value is None else str(value) for value in values) + " |"


def author_rows(author_assembly: list[dict[str, str]]) -> str:
    if not author_assembly:
        return "| No thinker drafts found |  |  |  |  |"
    return "\n".join(
        table_row(
            [
                row.get("author_slug", ""),
                row.get("page_count", ""),
                f"{row.get('first_page', '')}-{row.get('last_page', '')}",
                row.get("validation_result", ""),
                row.get("output_file", ""),
            ]
        )
        for row in author_assembly
    )


def review_reason_counts(review_rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in review_rows:
        reasons = row.get("review_reasons", "")
        for reason in reasons.split(";"):
            reason = reason.strip()
            if reason:
                counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def review_rows_markdown(review_rows: list[dict[str, str]]) -> str:
    counts = review_reason_counts(review_rows)
    if not counts:
        return "| No open review reasons | 0 |"
    return "\n".join(table_row([reason, count]) for reason, count in counts.items())


def page_range(classification_records: list[dict[str, Any]]) -> str:
    pages = sorted(int(row["page_number"]) for row in classification_records if row.get("page_number"))
    if not pages:
        return "No classified pages"
    return f"{pages[0]}-{pages[-1]}"


def metric_cards(metrics: list[tuple[str, Any]]) -> str:
    return "\n".join(
        f"""<div class=\"ah-metric-card\">
  <div class=\"ah-metric-label\">{label}</div>
  <div class=\"ah-metric-value\">{value}</div>
</div>"""
        for label, value in metrics
    )


def build_status_markdown(source: dict[str, Any], output_path: Path) -> str:
    paths = resolve_source_paths(source)
    layout_records = read_jsonl(paths["layout_dir"] / "layout.jsonl")
    classification_records = read_jsonl(paths["classification_dir"] / "page-classifications.jsonl")
    sliced_rows = read_sliced_manifest(paths["sliced_pages_dir"]) if paths["sliced_pages_dir"].exists() else []
    review_rows = read_csv_rows(paths["review_dir"] / "page-records-needing-review.csv")
    page_generation_rows = read_csv_rows(paths["audit_dir"] / "page-record-generation.csv")
    author_assembly = read_csv_rows(paths["audit_dir"] / "author-assembly.csv")
    generated_at = now_utc()
    page_record_count = count_files(paths["page_records_dir"], "page_*.md")
    author_draft_count = count_files(paths["author_drafts_dir"], "*.md")
    classified_pages = page_range(classification_records)

    return f"""# Extraction Status

This page is generated from audit artifacts. It intentionally contains metadata only, not Norton-derived source text.

<div class="ah-metric-grid">
{metric_cards([
    ("Classified Pages", classified_pages),
    ("Page Records", page_record_count),
    ("Thinker Drafts", author_draft_count),
    ("Review Rows", len(review_rows)),
])}
</div>

## Local Workflow

- Use [Review Dashboard](review-dashboard.md) to choose the next editorial checks.
- Use this page to confirm artifact counts after extraction and assembly.
- Keep restricted generated drafts out of public catalog pages until rights review is complete.

## Current Restricted Source

| Field | Value |
| --- | --- |
| Source ID | `{source["source_id"]}` |
| Source title | {source["source_title"]} |
| Rights status | `{source.get("source_rights_status", "unknown")}` |
| Public release | `{str(bool(source.get("public_release", False))).lower()}` |
| Default output mode | `{source.get("default_output_mode", "summary_only")}` |
| Access level | `{source.get("default_access_level", "restricted")}` |
| Source config | `{source.get("_config_path", "")}` |
| Classification overrides | `{source.get("classification_overrides", "none")}` |

## Artifact Counts

| Artifact | Count | Location |
| --- | ---: | --- |
| Sliced PDFs | {len(sliced_rows)} | `{relative_to_root(paths["sliced_pages_dir"])}` |
| Layout records | {len(layout_records)} | `{relative_to_root(paths["layout_dir"] / "layout.jsonl")}` |
| Classification records | {len(classification_records)} | `{relative_to_root(paths["classification_dir"] / "page-classifications.jsonl")}` |
| Review queue rows | {len(review_rows)} | `{relative_to_root(paths["review_dir"] / "page-records-needing-review.csv")}` |
| Page records | {page_record_count} | `{relative_to_root(paths["page_records_dir"])}` |
| Page-generation audit rows | {len(page_generation_rows)} | `{relative_to_root(paths["audit_dir"] / "page-record-generation.csv")}` |
| Thinker drafts | {author_draft_count} | `{relative_to_root(paths["author_drafts_dir"])}` |
| Thinker-assembly audit rows | {len(author_assembly)} | `{relative_to_root(paths["audit_dir"] / "author-assembly.csv")}` |

## Classified Range

| Field | Value |
| --- | --- |
| Classified source pages | `{classified_pages}` |
| Status page generated at | `{generated_at}` |
| Git commit | `{git_commit()}` |
| Script version | `{SCRIPT_VERSION}` |
| Output path | `{relative_to_root(output_path)}` |

## Thinker Draft Inventory

| Thinker slug | Pages | Source page range | Validation | Restricted draft |
| --- | ---: | --- | --- | --- |
{author_rows(author_assembly)}

## Review Queue Summary

| Review reason | Pages |
| --- | ---: |
{review_rows_markdown(review_rows)}

## Publication Boundary

The thinker drafts listed above are restricted working artifacts. They should not be copied into public catalog pages until rights review, excerpt selection, and original project commentary are complete.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="data/extraction-sources.yml")
    parser.add_argument("--source-id", default="norton-theory-criticism")
    parser.add_argument("--output", default="docs/_meta/extraction-status.md")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = load_config(args.config, args.source_id)
    output_path = Path(args.output)
    markdown = build_status_markdown(source, output_path)

    if args.dry_run:
        print(markdown)
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote extraction status page to {relative_to_root(output_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
