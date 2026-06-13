#!/usr/bin/env python3
"""Print auditable pipeline artifact counts and consistency checks."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from lib.extraction_common import (
    load_config,
    read_jsonl,
    read_sliced_manifest,
    relative_to_root,
    resolve_source_paths,
    sha256_file,
)


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as file_obj:
        return max(0, sum(1 for _ in csv.DictReader(file_obj)))


def count_files(path: Path, pattern: str) -> int:
    return len(list(path.glob(pattern))) if path.exists() else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="data/extraction-sources.yml")
    parser.add_argument("--source-id", default="norton-theory-criticism")
    parser.add_argument("--strict", action="store_true", help="Fail when expected artifacts are missing.")
    args = parser.parse_args()

    source = load_config(args.config, args.source_id)
    paths = resolve_source_paths(source)

    source_pdf = paths["source_pdf"]
    sliced_manifest_rows = read_sliced_manifest(paths["sliced_pages_dir"]) if paths["sliced_pages_dir"].exists() else []
    layout_jsonl = paths["layout_dir"] / "layout.jsonl"
    layout_manifest = paths["layout_dir"] / "manifest.csv"
    classification_jsonl = paths["classification_dir"] / "page-classifications.jsonl"
    classification_manifest = paths["classification_dir"] / "manifest.csv"
    review_queue = paths["review_dir"] / "page-records-needing-review.csv"
    page_generation_log = paths["audit_dir"] / "page-record-generation.csv"
    author_assembly_log = paths["audit_dir"] / "author-assembly.csv"

    source_sha = sha256_file(source_pdf) if source_pdf.exists() else ""
    layout_records = read_jsonl(layout_jsonl)
    classification_records = read_jsonl(classification_jsonl)
    page_record_count = count_files(paths["page_records_dir"], "page_*.md")
    author_draft_count = count_files(paths["author_drafts_dir"], "*.md")

    print(f"source_id: {source['source_id']}")
    print(f"source_pdf: {relative_to_root(source_pdf)}")
    print(f"source_pdf_exists: {source_pdf.exists()}")
    print(f"source_sha256: {source_sha}")
    print(f"sliced_pages_dir: {relative_to_root(paths['sliced_pages_dir'])}")
    print(f"sliced_pdf_count: {count_files(paths['sliced_pages_dir'], '*.pdf')}")
    print(f"sliced_manifest_rows: {len(sliced_manifest_rows)}")
    print(f"layout_jsonl: {relative_to_root(layout_jsonl)}")
    print(f"layout_record_count: {len(layout_records)}")
    print(f"layout_manifest_rows: {count_csv_rows(layout_manifest)}")
    print(f"classification_jsonl: {relative_to_root(classification_jsonl)}")
    print(f"classification_record_count: {len(classification_records)}")
    print(f"classification_manifest_rows: {count_csv_rows(classification_manifest)}")
    print(f"review_queue: {relative_to_root(review_queue)}")
    print(f"review_queue_rows: {count_csv_rows(review_queue)}")
    print(f"page_records_dir: {relative_to_root(paths['page_records_dir'])}")
    print(f"page_record_count: {page_record_count}")
    print(f"page_generation_audit_rows: {count_csv_rows(page_generation_log)}")
    print(f"author_drafts_dir: {relative_to_root(paths['author_drafts_dir'])}")
    print(f"author_draft_count: {author_draft_count}")
    print(f"author_assembly_audit_rows: {count_csv_rows(author_assembly_log)}")

    errors: list[str] = []
    if args.strict:
        if not source_pdf.exists():
            errors.append("source PDF is missing")
        if not paths["sliced_pages_dir"].exists():
            errors.append("sliced pages directory is missing")
        if layout_records and page_record_count > len(layout_records):
            errors.append("page record count exceeds layout record count")
        if classification_records and len(classification_records) != count_csv_rows(classification_manifest):
            errors.append("classification JSONL count does not match classification manifest row count")
        if page_record_count and len(classification_records) < page_record_count:
            errors.append("classification record count is lower than page record count")
        if page_record_count and count_csv_rows(page_generation_log) != page_record_count:
            errors.append("page-generation audit row count does not match page record count")
        if author_draft_count and count_csv_rows(author_assembly_log) != author_draft_count:
            errors.append("author-assembly audit row count does not match author draft count")

    for error in errors:
        print(f"error: {error}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
