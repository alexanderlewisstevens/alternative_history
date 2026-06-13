#!/usr/bin/env python3
"""Assemble page records into one standardized author draft per author."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

from lib.extraction_common import (
    git_commit,
    load_config,
    now_utc,
    read_jsonl,
    read_markdown,
    relative_to_root,
    resolve_source_paths,
    select_page_rows,
    sha256_file,
    slugify,
    write_csv,
    yaml_frontmatter,
)
from validate_records import validate_file


SCRIPT_VERSION = "2"
CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}


def read_classifications(paths: dict[str, Path]) -> dict[int, dict[str, Any]]:
    classification_path = paths["classification_dir"] / "page-classifications.jsonl"
    return {
        int(row["page_number"]): row.get("classification", {})
        for row in read_jsonl(classification_path)
    }


def read_page_records(
    page_records_dir: Path,
    classifications: dict[int, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(page_records_dir.glob("page_*.md")):
        metadata, body = read_markdown(path)
        page_number = int(metadata["source"]["page_number"])
        records.append(
            {
                "path": path,
                "metadata": metadata,
                "body": body,
                "page_number": page_number,
                "page_file": metadata["source"]["page_file"],
                "classification": (classifications or {}).get(page_number, {}),
            }
        )
    return sorted(records, key=lambda item: item["page_number"])


def assembly_group(record: dict[str, Any]) -> tuple[str, str]:
    structure = record["metadata"].get("structure", {})
    classification = record.get("classification", {})
    author_name = (
        structure.get("author_name")
        or classification.get("visible_author_name")
        or classification.get("assembly_group_name")
        or "Unassigned Source Pages"
    )
    author_slug = (
        structure.get("author_slug")
        or classification.get("visible_author_slug")
        or classification.get("assembly_group_slug")
        or slugify(author_name)
    )
    return author_slug, author_name


def group_records(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        author_slug, _author_name = assembly_group(record)
        grouped[author_slug].append(record)
    return dict(grouped)


def markdown_table_row(values: list[Any]) -> str:
    return "| " + " | ".join("" if value is None else str(value) for value in values) + " |"


def lowest_confidence(records: list[dict[str, Any]]) -> str:
    values = [record.get("classification", {}).get("confidence", "low") for record in records]
    return min(values, key=lambda value: CONFIDENCE_RANK.get(value, 0), default="low")


def record_work_title(record: dict[str, Any]) -> str:
    return (
        record.get("classification", {}).get("work_title")
        or record["metadata"].get("structure", {}).get("work_title")
        or "Unknown work"
    )


def build_author_markdown(
    source: dict[str, Any],
    author_slug: str,
    records: list[dict[str, Any]],
    audit_log: Path,
) -> str:
    first = records[0]
    last = records[-1]
    _first_slug, author_name = assembly_group(first)
    generated_at = now_utc()
    page_paths = [relative_to_root(record["path"]) for record in records]
    classification_file = resolve_source_paths(source)["classification_dir"] / "page-classifications.jsonl"

    metadata = {
        "record_type": "author_file",
        "schema_version": 2,
        "title": author_name,
        "author": {
            "name": author_name,
            "slug": author_slug,
            "life_dates": None,
        },
        "source": {
            "source_id": source["source_id"],
            "source_title": source["source_title"],
            "source_pdf": source["source_pdf"],
            "first_page": first["page_number"],
            "last_page": last["page_number"],
        },
        "publication": {
            "access_level": source.get("default_access_level", "restricted"),
            "web_readable": True,
            "release_notes": source.get("notes", ""),
        },
        "rights": {
            "source_rights_status": source.get("source_rights_status", "unknown"),
            "public_release": bool(source.get("public_release", False)),
            "rights_evidence": source.get("rights_evidence", ""),
        },
        "assembly": {
            "generated_from_page_records": page_paths,
            "generated_from_classifications": [relative_to_root(classification_file)],
            "generated_at": generated_at,
            "confidence": lowest_confidence(records),
        },
        "audit": {
            "source_config": source.get("_config_path", ""),
            "audit_log": relative_to_root(audit_log),
        },
    }

    works = sorted(
        {
            record_work_title(record)
            for record in records
        }
    )
    work_rows = "\n".join(
        markdown_table_row(
            [work, f"{first['page_number']}-{last['page_number']}", "unknown", "Generated draft"]
        )
        for work in works
    )
    inventory_rows = "\n".join(
        markdown_table_row(
            [
                record["page_number"],
                record["metadata"]["source"].get("printed_page_label") or "",
                record_work_title(record),
                record["metadata"].get("structure", {}).get("page_role")
                or record.get("classification", {}).get("page_kind")
                or "unknown",
                (
                    f"{record['metadata'].get('layout', {}).get('column_count', 'unknown')} column(s)/"
                    f"{record['metadata'].get('layout', {}).get('reading_order', 'unknown')}"
                ),
                ";".join(record.get("classification", {}).get("review_reasons", []))
                or record["metadata"].get("layout", {}).get("layout_notes")
                or "",
            ]
        )
        for record in records
    )

    body = f"""# {author_name}

## Why This Author Matters

This generated restricted draft groups page records that have not yet been curated into a final public author page.

## Works In This Source

| Work | Page Range | Section Type | Notes |
| --- | --- | --- | --- |
{work_rows}

## Reader Summary

This draft was assembled from {len(records)} page record(s). Add original reader-facing analysis after author and work boundaries are reviewed.

## Selected Excerpts

### Excerpt Card

- Work: review required
- Source pages: {first["page_number"]}-{last["page_number"]}
- Rights mode: {source.get("default_output_mode", "summary_only")}
- Selection rationale: Generated placeholder for later curation.

No excerpt included by author assembler.

**Project commentary:** Add curated excerpt commentary after rights review.

## Source Notes

| Page | Marker | Note summary | Rights mode |
| --- | --- | --- | --- |
| TBD | TBD | TBD | {source.get("default_output_mode", "summary_only")} |

## Bibliography

| Page | Entry | Type | Notes |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

## Page Inventory

| Page | Printed Label | Work | Role | Layout | Notes |
| --- | --- | --- | --- | --- | --- |
{inventory_rows}

## Open Questions

- Confirm author/work boundaries.
- Curate source notes and bibliography items from page records.

## Further Reading

- 
"""
    return f"---\n{yaml_frontmatter(metadata)}\n---\n\n{body}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="data/extraction-sources.yml")
    parser.add_argument("--source-id", default="norton-theory-criticism")
    parser.add_argument("--pages", help="Optional 1-based pages/ranges, such as 1,3-5.")
    parser.add_argument("--limit", type=int, help="Limit selected page records after filtering.")
    parser.add_argument("--clean", action="store_true", help="Remove existing generated author drafts before writing.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = load_config(args.config, args.source_id)
    paths = resolve_source_paths(source)
    classifications = read_classifications(paths)
    records = read_page_records(paths["page_records_dir"], classifications)
    selected = select_page_rows(records, args.pages, args.limit)
    groups = group_records(selected)
    audit_log = paths["audit_dir"] / "author-assembly.csv"

    if args.dry_run:
        print(f"Would assemble {len(selected)} page record(s) into {len(groups)} author draft(s)")
        print(f"Would write drafts under {relative_to_root(paths['author_drafts_dir'])}")
        print(f"Would write audit log to {relative_to_root(audit_log)}")
        return 0

    paths["author_drafts_dir"].mkdir(parents=True, exist_ok=True)
    if args.clean:
        for old_file in paths["author_drafts_dir"].glob("*.md"):
            old_file.unlink()
    audit_log.parent.mkdir(parents=True, exist_ok=True)
    audit_rows: list[dict[str, Any]] = []
    commit = git_commit()

    for author_slug, group in sorted(groups.items()):
        output_file = paths["author_drafts_dir"] / f"{author_slug}.md"
        markdown = build_author_markdown(source, author_slug, group, audit_log)
        output_file.write_text(markdown, encoding="utf-8")
        validation = validate_file(output_file, expected_type="author_file")
        status = "ok" if not validation.errors else "validation_failed"
        audit_rows.append(
            {
                "author_slug": author_slug,
                "output_file": relative_to_root(output_file),
                "page_count": len(group),
                "first_page": group[0]["page_number"],
                "last_page": group[-1]["page_number"],
                "status": status,
                "error": "; ".join(validation.errors),
                "validation_result": "ok" if not validation.errors else "failed",
                "output_sha256": sha256_file(output_file),
                "generated_at": now_utc(),
                "git_commit": commit,
                "script_version": SCRIPT_VERSION,
            }
        )

    write_csv(
        audit_log,
        [
            "author_slug",
            "output_file",
            "page_count",
            "first_page",
            "last_page",
            "status",
            "error",
            "validation_result",
            "output_sha256",
            "generated_at",
            "git_commit",
            "script_version",
        ],
        audit_rows,
    )

    failed = [row for row in audit_rows if row["status"] != "ok"]
    print(f"Wrote {len(audit_rows)} author draft(s) to {relative_to_root(paths['author_drafts_dir'])}")
    print(f"Wrote author-assembly audit log to {relative_to_root(audit_log)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
