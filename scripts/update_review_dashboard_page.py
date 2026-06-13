#!/usr/bin/env python3
"""Write a rights-safe review dashboard from extraction review artifacts."""

from __future__ import annotations

import argparse
import csv
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
)


SCRIPT_VERSION = "1"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as file_obj:
        return list(csv.DictReader(file_obj))


def table_row(values: list[Any]) -> str:
    return "| " + " | ".join("" if value is None else str(value) for value in values) + " |"


def split_reasons(value: str) -> list[str]:
    return [reason.strip() for reason in value.split(";") if reason.strip()]


def priority_for_row(row: dict[str, str]) -> str:
    reasons = set(split_reasons(row.get("review_reasons", "")))
    if any(reason.startswith("transition_") or reason == "author_boundary_without_life_dates" for reason in reasons):
        return "boundary"
    if "mixed_excerpt_and_bibliography" in reasons:
        return "separation"
    if "layout_review_required" in reasons or "multi_column_layout" in reasons:
        return "layout"
    if "source_notes_detected" in reasons:
        return "notes"
    return "general"


def priority_label(priority: str) -> str:
    labels = {
        "boundary": "Boundary Review",
        "separation": "Content Separation",
        "layout": "Layout Review",
        "notes": "Source Notes",
        "general": "General Review",
    }
    return labels.get(priority, priority.title())


def priority_goal(priority: str) -> str:
    goals = {
        "boundary": "Confirm thinker and work boundaries before assembling public-facing drafts.",
        "separation": "Keep excerpt text, source notes, and bibliography material in separate template sections.",
        "layout": "Confirm multi-column reading order before any summary or excerpt curation.",
        "notes": "Move source footnotes into Source Notes without converting them into Markdown footnotes.",
        "general": "Resolve remaining template or classification questions.",
    }
    return goals.get(priority, "Resolve the queued review items.")


def priority_css_class(priority: str) -> str:
    classes = {
        "boundary": "warn",
        "separation": "warn",
        "layout": "neutral",
        "notes": "neutral",
        "general": "neutral",
    }
    return classes.get(priority, "neutral")


def priority_counts(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter(priority_for_row(row) for row in rows)


def reason_counts(rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(split_reasons(row.get("review_reasons", "")))
    return counts


def author_counts(rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts[row.get("visible_author_name") or "Unassigned"] += 1
    return counts


def priority_summary_cards(rows: list[dict[str, str]]) -> str:
    counts = priority_counts(rows)
    order = ["boundary", "separation", "layout", "notes", "general"]
    cards = []
    for priority in order:
        count = counts.get(priority, 0)
        cards.append(
            f"""<div class=\"ah-metric-card\">
  <div class=\"ah-metric-label\">{priority_label(priority)}</div>
  <div class=\"ah-metric-value\">{count}</div>
</div>"""
        )
    return "\n".join(cards)


def page_number(row: dict[str, str]) -> int:
    value = row.get("page_number", "")
    if value.isdigit():
        return int(value)
    return 0


def page_list(rows: list[dict[str, str]], limit: int = 12) -> str:
    pages = [row.get("page_number", "") for row in sorted(rows, key=page_number) if row.get("page_number")]
    if not pages:
        return "none"
    selected = pages[:limit]
    suffix = f" +{len(pages) - limit} more" if len(pages) > limit else ""
    return ", ".join(f"<code>{html.escape(page)}</code>" for page in selected) + suffix


def review_workbench(rows: list[dict[str, str]]) -> str:
    order = ["boundary", "separation", "layout", "notes", "general"]
    cards = []
    for priority in order:
        selected = [row for row in rows if priority_for_row(row) == priority]
        if not selected:
            continue
        cards.append(
            f"""<section class=\"ah-review-card {priority_css_class(priority)}\">
  <div class=\"ah-review-card-kicker\">{len(selected)} pages</div>
  <h3>{html.escape(priority_label(priority))}</h3>
  <p>{html.escape(priority_goal(priority))}</p>
  <p><strong>Start:</strong> {page_list(selected)}</p>
</section>"""
        )
    if not cards:
        return "<p>No open review rows are currently queued for this source.</p>"
    return "<div class=\"ah-review-grid\">\n" + "\n".join(cards) + "\n</div>"


def next_actions(rows: list[dict[str, str]]) -> str:
    counts = priority_counts(rows)
    actions = []
    if counts.get("boundary"):
        actions.append("Review boundary pages first; they can affect thinker grouping and page inventory.")
    if counts.get("separation"):
        actions.append("Check content-separation pages before excerpt curation so bibliography and notes stay out of excerpt cards.")
    if counts.get("layout"):
        actions.append("Review multi-column reading order before asking an agent to summarize or quote from those pages.")
    if counts.get("notes"):
        actions.append("Normalize source-note pages into `Source Notes`; do not convert source notes into Markdown footnotes.")
    if not actions:
        actions.append("No review rows are currently open for this source.")
    return "\n".join(f"- {action}" for action in actions)


def reason_table(rows: list[dict[str, str]]) -> str:
    counts = reason_counts(rows)
    if not counts:
        return "| No open review reasons | 0 |"
    return "\n".join(table_row([reason, count]) for reason, count in counts.most_common())


def author_table(rows: list[dict[str, str]]) -> str:
    counts = author_counts(rows)
    if not counts:
        return "| No thinkers need review | 0 |"
    return "\n".join(table_row([author, count]) for author, count in counts.most_common())


def priority_section(priority: str, rows: list[dict[str, str]]) -> str:
    selected = [row for row in rows if priority_for_row(row) == priority]
    if not selected:
        return ""
    lines = [
        f"## {priority_label(priority)}",
        "",
        "| Page | Thinker | Work | Reasons | Restricted page record |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for row in selected:
        page = row.get("page_number", "")
        source_id = row.get("source_id", "")
        page_record = f"work/page-records/{source_id}/page_{int(page):04d}.md" if source_id and page.isdigit() else ""
        if not page_record and page.isdigit():
            page_record = f"work/page-records/norton-theory-criticism/page_{int(page):04d}.md"
        lines.append(
            table_row(
                [
                    page,
                    row.get("visible_author_name", ""),
                    row.get("work_title", ""),
                    row.get("review_reasons", ""),
                    page_record,
                ]
            )
        )
    return "\n".join(lines)


def add_source_id(rows: list[dict[str, str]], source_id: str) -> list[dict[str, str]]:
    return [{**row, "source_id": source_id} for row in rows]


def classified_range(classification_records: list[dict[str, Any]]) -> str:
    pages = sorted(int(row["page_number"]) for row in classification_records if row.get("page_number"))
    if not pages:
        return "none"
    return f"{pages[0]}-{pages[-1]}"


def build_dashboard_markdown(source: dict[str, Any], output_path: Path) -> str:
    paths = resolve_source_paths(source)
    rows = add_source_id(read_csv_rows(paths["review_dir"] / "page-records-needing-review.csv"), source["source_id"])
    classification_records = read_jsonl(paths["classification_dir"] / "page-classifications.jsonl")
    generated_at = now_utc()
    priority_sections = "\n\n".join(
        section
        for section in (
            priority_section("boundary", rows),
            priority_section("separation", rows),
            priority_section("layout", rows),
            priority_section("notes", rows),
            priority_section("general", rows),
        )
        if section
    )

    return f"""# Review Dashboard

This is the editorial queue for restricted extraction work. It is generated from review metadata only and intentionally omits OCR/source-text snippets.

<div class=\"ah-metric-grid\">
{priority_summary_cards(rows)}
</div>

## Review Workbench

{review_workbench(rows)}

## How To Use This Page

{next_actions(rows)}

## Source Scope

| Field | Value |
| --- | --- |
| Source ID | `{source["source_id"]}` |
| Classified source pages | `{classified_range(classification_records)}` |
| Review queue rows | `{len(rows)}` |
| Review queue file | `{relative_to_root(paths["review_dir"] / "page-records-needing-review.csv")}` |
| Generated at | `{generated_at}` |
| Git commit | `{git_commit()}` |
| Script version | `{SCRIPT_VERSION}` |
| Output path | `{relative_to_root(output_path)}` |

## Review Reasons

| Reason | Pages |
| --- | ---: |
{reason_table(rows)}

## Thinkers Needing Review

| Thinker | Pages |
| --- | ---: |
{author_table(rows)}

{priority_sections}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="data/extraction-sources.yml")
    parser.add_argument("--source-id", default="norton-theory-criticism")
    parser.add_argument("--output", default="docs/_meta/review-dashboard.md")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = load_config(args.config, args.source_id)
    output_path = Path(args.output)
    markdown = build_dashboard_markdown(source, output_path)
    if args.dry_run:
        print(markdown)
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote review dashboard to {relative_to_root(output_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
