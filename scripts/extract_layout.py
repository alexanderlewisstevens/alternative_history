#!/usr/bin/env python3
"""Extract auditable PDF page layout metadata with column detection."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from lib.extraction_common import (
    git_commit,
    load_config,
    now_utc,
    read_sliced_manifest,
    relative_to_root,
    resolve_source_paths,
    select_page_rows,
    sha256_file,
    write_csv,
)


SCRIPT_VERSION = "1"


def strip_namespace(tag: str) -> str:
    return tag.split("}", 1)[-1]


def float_attr(element: ET.Element, name: str, default: float = 0.0) -> float:
    try:
        return float(element.attrib.get(name, default))
    except ValueError:
        return default


def parse_bbox_layout(page_pdf: Path) -> dict[str, Any]:
    if not shutil.which("pdftotext"):
        raise RuntimeError("pdftotext is required for layout extraction")

    result = subprocess.run(
        ["pdftotext", "-bbox-layout", str(page_pdf), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    root = ET.fromstring(result.stdout)

    page_element = None
    for element in root.iter():
        if strip_namespace(element.tag) == "page":
            page_element = element
            break
    if page_element is None:
        return {
            "page_width": None,
            "page_height": None,
            "block_count": 0,
            "line_count": 0,
            "word_count": 0,
            "column_count": 0,
            "reading_order": "no_text",
            "needs_layout_review": True,
            "line_boxes": [],
        }

    page_width = float_attr(page_element, "width")
    page_height = float_attr(page_element, "height")
    blocks = []
    lines = []
    word_count = 0

    for element in page_element.iter():
        tag = strip_namespace(element.tag)
        if tag == "block":
            blocks.append(
                {
                    "x_min": float_attr(element, "xMin"),
                    "x_max": float_attr(element, "xMax"),
                    "y_min": float_attr(element, "yMin"),
                    "y_max": float_attr(element, "yMax"),
                }
            )
        elif tag == "line":
            lines.append(
                {
                    "x_min": float_attr(element, "xMin"),
                    "x_max": float_attr(element, "xMax"),
                    "y_min": float_attr(element, "yMin"),
                    "y_max": float_attr(element, "yMax"),
                }
            )
        elif tag == "word":
            word_count += 1

    column_count, reading_order, needs_layout_review = detect_columns(
        page_width=page_width,
        page_height=page_height,
        lines=lines,
    )

    return {
        "page_width": page_width,
        "page_height": page_height,
        "block_count": len(blocks),
        "line_count": len(lines),
        "word_count": word_count,
        "column_count": column_count,
        "reading_order": reading_order,
        "needs_layout_review": needs_layout_review,
        "line_boxes": lines,
    }


def detect_columns(
    page_width: float,
    page_height: float,
    lines: list[dict[str, float]],
) -> tuple[int, str, bool]:
    if not lines or page_width <= 0 or page_height <= 0:
        return 0, "no_text", True

    top_cutoff = page_height * 0.08
    bottom_cutoff = page_height * 0.92
    body_lines = [
        line for line in lines
        if line["y_min"] >= top_cutoff and line["y_max"] <= bottom_cutoff
    ]
    if not body_lines:
        body_lines = lines

    candidate_lines = [
        line for line in body_lines
        if (line["x_max"] - line["x_min"]) <= page_width * 0.72
    ]
    if len(candidate_lines) < 8:
        return 1, "normalized:top-to-bottom", len(lines) < 3

    centers = sorted((line["x_min"] + line["x_max"]) / 2 for line in candidate_lines)
    left = [center for center in centers if center < page_width * 0.46]
    right = [center for center in centers if center > page_width * 0.54]

    if len(left) >= 4 and len(right) >= 4:
        gap = min(right) - max(left)
        if gap >= page_width * 0.08:
            imbalance = abs(len(left) - len(right)) / max(len(left), len(right))
            return 2, "normalized:left-column-then-right-column", imbalance > 0.65

    return 1, "normalized:top-to-bottom", False


def layout_output_paths(paths: dict[str, Path]) -> tuple[Path, Path]:
    layout_dir = paths["layout_dir"]
    return layout_dir / "layout.jsonl", layout_dir / "manifest.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="data/extraction-sources.yml")
    parser.add_argument("--source-id", default="norton-theory-criticism")
    parser.add_argument("--pages", help="Optional 1-based pages/ranges, such as 1,3-5.")
    parser.add_argument("--limit", type=int, help="Limit selected pages after filtering.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = load_config(args.config, args.source_id)
    paths = resolve_source_paths(source)
    page_rows = read_sliced_manifest(paths["sliced_pages_dir"])
    selected_rows = select_page_rows(page_rows, args.pages, args.limit)
    output_jsonl, output_manifest = layout_output_paths(paths)

    if args.dry_run:
        print(f"Would extract layout for {len(selected_rows)} page(s)")
        print(f"Would write {relative_to_root(output_jsonl)}")
        print(f"Would write {relative_to_root(output_manifest)}")
        return 0

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    audit_rows: list[dict[str, Any]] = []
    commit = git_commit()

    with output_jsonl.open("w", encoding="utf-8") as jsonl_file:
        for row in selected_rows:
            page_path = row["page_path"]
            timestamp = now_utc()
            status = "ok"
            error = ""
            try:
                layout = parse_bbox_layout(page_path)
                page_sha256 = sha256_file(page_path)
            except Exception as exc:
                layout = {
                    "page_width": None,
                    "page_height": None,
                    "block_count": 0,
                    "line_count": 0,
                    "word_count": 0,
                    "column_count": 0,
                    "reading_order": "error",
                    "needs_layout_review": True,
                    "line_boxes": [],
                }
                page_sha256 = ""
                status = "error"
                error = str(exc)

            record = {
                "source_id": source["source_id"],
                "source_title": source["source_title"],
                "source_pdf": source["source_pdf"],
                "page_number": row["page_number"],
                "page_file": row["page_file"],
                "total_pages": len(page_rows),
                "input_sha256": page_sha256,
                "generated_at": timestamp,
                "git_commit": commit,
                "script": "scripts/extract_layout.py",
                "script_version": SCRIPT_VERSION,
                "status": status,
                "error": error,
                "layout": layout,
            }
            jsonl_file.write(json.dumps(record, sort_keys=True) + "\n")

            audit_rows.append(
                {
                    "page_number": row["page_number"],
                    "page_file": row["page_file"],
                    "source_pdf": source["source_pdf"],
                    "input_sha256": page_sha256,
                    "column_count": layout["column_count"],
                    "reading_order": layout["reading_order"],
                    "needs_layout_review": layout["needs_layout_review"],
                    "block_count": layout["block_count"],
                    "line_count": layout["line_count"],
                    "word_count": layout["word_count"],
                    "status": status,
                    "error": error,
                    "generated_at": timestamp,
                    "git_commit": commit,
                }
            )

    write_csv(
        output_manifest,
        [
            "page_number",
            "page_file",
            "source_pdf",
            "input_sha256",
            "column_count",
            "reading_order",
            "needs_layout_review",
            "block_count",
            "line_count",
            "word_count",
            "status",
            "error",
            "generated_at",
            "git_commit",
        ],
        audit_rows,
    )
    print(f"Wrote {len(audit_rows)} layout record(s) to {relative_to_root(output_jsonl)}")
    print(f"Wrote layout manifest to {relative_to_root(output_manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

