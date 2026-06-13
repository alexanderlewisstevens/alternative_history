#!/usr/bin/env python3
"""Classify sliced PDF pages for author-boundary assembly and review queues."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from lib.extraction_common import (
    git_commit,
    load_config,
    parse_page_spec,
    project_path,
    now_utc,
    read_jsonl,
    read_sliced_manifest,
    relative_to_root,
    resolve_source_paths,
    select_page_rows,
    sha256_file,
    slugify,
    write_csv,
    write_jsonl,
)


SCRIPT_VERSION = "1"
PAGE_KINDS = {
    "blank",
    "front_matter",
    "table_of_contents",
    "author_intro",
    "excerpt",
    "bibliography",
    "notes",
    "index_appendix",
    "mixed_excerpt_bibliography",
    "editorial_apparatus",
    "unknown",
}
OVERRIDE_FIELDS = {
    "page_kind",
    "confidence",
    "author_name",
    "author_slug",
    "work_title",
    "work_slug",
    "starts_new_author",
    "continues_previous_author",
    "contains_excerpt",
    "contains_source_notes",
    "contains_bibliography",
    "contains_editorial_apparatus",
    "include_in_author_assembly",
    "review_required",
    "review_reasons",
}
AUTHOR_HEADING_BLACKLIST = {
    "ACKNOWLEDGMENTS",
    "BIBLIOGRAPHY",
    "CONTENTS",
    "COPYRIGHT",
    "CREDITS",
    "INDEX",
    "INTRODUCTION",
    "NOTES",
    "PREFACE",
    "SELECTED BIBLIOGRAPHY",
}


def extract_text(page_pdf: Path) -> str:
    if not shutil.which("pdftotext"):
        raise RuntimeError("pdftotext is required for page classification")
    result = subprocess.run(
        ["pdftotext", "-layout", str(page_pdf), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.replace("\f", "")


def normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def visible_lines(text: str) -> list[str]:
    return [line for line in (normalize_line(raw) for raw in text.splitlines()) if line]


def is_upper_heading(line: str) -> bool:
    letters = re.sub(r"[^A-Za-z]", "", line)
    if len(letters) < 3:
        return False
    upper_count = sum(1 for char in letters if char.isupper())
    return upper_count / len(letters) >= 0.78


def titleize_heading(line: str) -> str:
    words = []
    for word in re.split(r"\s+", line.strip()):
        if word in {"B.C.E.", "C.E.", "B.C.", "A.D."}:
            words.append(word)
        elif len(word) <= 3 and word.lower() in {"of", "de", "du", "la", "le", "and"}:
            words.append(word.lower())
        else:
            words.append(word[:1].upper() + word[1:].lower())
    return " ".join(words)


def plausible_author_heading(line: str) -> bool:
    clean = normalize_line(line)
    if clean.upper() in AUTHOR_HEADING_BLACKLIST:
        return False
    if re.match(r"^\d+\s+(?:/|I|\|)\s+", clean):
        return False
    if re.search(r"\s(?:/|I|\|)\s*\d+\s*$", clean):
        return False
    if "/" in clean or "|" in clean or len(clean) > 64:
        return False
    if re.search(r"\b(FROM|OF HELEN|BOOK|CHAPTER|PART|VOLUME)\b", clean.upper()):
        return False
    return is_upper_heading(clean)


def detect_heading_author(lines: list[str]) -> tuple[str | None, bool]:
    first_lines = lines[:25]
    for index, line in enumerate(first_lines):
        if not plausible_author_heading(line):
            continue
        nearby = " ".join(first_lines[index + 1:index + 4])
        has_dates = bool(re.search(r"\b(ca\.|b\.|d\.|B\.C\.E\.|C\.E\.|[0-9]{3,4}\s*[-–]\s*[0-9]{2,4})", nearby))
        if has_dates or index <= 2:
            return titleize_heading(line), has_dates
    return None, False


def detect_running_author(lines: list[str]) -> str | None:
    for line in lines[:6]:
        match = re.match(r"^\d+\s+(?:/|I|\|)\s+([A-Z][A-Z .'\-]{2,})$", line)
        if match:
            candidate = normalize_line(match.group(1))
            if is_upper_heading(candidate) and candidate.upper() not in AUTHOR_HEADING_BLACKLIST:
                return titleize_heading(candidate)
        match = re.match(r"^([A-Z][A-Z .'\-]{2,}?)\s+(?:/|I|\|)\s+\d+", line)
        if match:
            candidate = normalize_line(match.group(1))
            if is_upper_heading(candidate) and candidate.upper() not in AUTHOR_HEADING_BLACKLIST:
                return titleize_heading(candidate)
    return None


def detect_work_title(lines: list[str]) -> str | None:
    for line in lines[:80]:
        match = re.match(r"^(?:From|FROM|F[Tt][Oo0~].{0,8})\s+['\"]?(.+?)['\"]?\s*$", line)
        if match:
            candidate = normalize_line(match.group(1)).strip(" .,:;\"'")
            if 3 <= len(candidate) <= 100:
                return candidate
    for line in lines[:8]:
        if "/" in line and not re.match(r"^\d+\s*/", line):
            candidate = normalize_line(line.split("/", 1)[0]).strip(" .,:;")
            if is_upper_heading(candidate) and candidate.upper() not in AUTHOR_HEADING_BLACKLIST:
                return titleize_heading(candidate)
    return None


def has_table_of_contents(lines: list[str]) -> bool:
    top = " ".join(lines[:30]).lower()
    dot_leaders = sum(1 for line in lines[:80] if re.search(r"\.{3,}\s*\d+\s*$", line))
    return "contents" in top and (dot_leaders >= 3 or "part " in top)


def has_source_notes(lines: list[str]) -> bool:
    if any(line.upper() in {"NOTES", "NOTES TO PAGES", "ENDNOTES"} for line in lines[:10]):
        return True
    bottom = lines[-18:]
    note_like = sum(1 for line in bottom if re.match(r"^\d+[\.,]\s+\S+", line))
    return note_like >= 2


def classify_page(
    row: dict[str, Any],
    layout_by_page: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    page_path = Path(row["page_path"])
    generated_at = now_utc()
    try:
        text = extract_text(page_path)
        status = "ok"
        error = ""
    except Exception as exc:
        text = ""
        status = "error"
        error = str(exc)

    lines = visible_lines(text)
    text_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    first_lines = lines[:8]
    joined_top = " ".join(lines[:30]).lower()
    top_heading = lines[0] if lines else ""
    layout_record = layout_by_page.get(row["page_number"], {})
    layout = layout_record.get("layout", {})

    heading_author, heading_has_dates = detect_heading_author(lines)
    running_author = detect_running_author(lines)
    visible_author = heading_author or running_author
    work_title = detect_work_title(lines)
    contains_bibliography = any(line.upper() in {"BIBLIOGRAPHY", "SELECTED BIBLIOGRAPHY", "WORKS CITED"} for line in lines)
    contains_notes = has_source_notes(lines)
    contains_editorial = any(term in joined_top for term in ["translator", "translated by", "edited by", "editor's note"])
    contains_excerpt = bool(
        re.search(r"^\[\d+\]", "\n".join(lines), re.MULTILINE)
        or re.search(r"^[A-Z][A-Z ]{2,}:", "\n".join(lines), re.MULTILINE)
        or work_title
    )

    starts_new_author = bool(heading_author and (heading_has_dates or row["page_number"] > 20))
    if not lines or len(" ".join(lines)) < 10:
        page_kind = "blank"
    elif has_table_of_contents(lines):
        page_kind = "table_of_contents"
    elif top_heading.upper().startswith(("INDEX", "APPENDIX")):
        page_kind = "index_appendix"
    elif top_heading.upper().startswith(("NOTES", "ENDNOTES")):
        page_kind = "notes"
    elif starts_new_author:
        page_kind = "author_intro"
    elif contains_bibliography and contains_excerpt:
        page_kind = "mixed_excerpt_bibliography"
    elif contains_bibliography:
        page_kind = "bibliography"
    elif contains_excerpt:
        page_kind = "excerpt"
    elif row["page_number"] <= 40 or any(term in joined_top for term in ["copyright", "preface", "acknowledgments"]):
        page_kind = "front_matter"
    elif contains_editorial:
        page_kind = "editorial_apparatus"
    else:
        page_kind = "unknown"

    review_reasons: list[str] = []
    confidence = "medium"
    if status != "ok":
        confidence = "low"
        review_reasons.append("classification_error")
    if page_kind == "unknown":
        confidence = "low"
        review_reasons.append("unknown_page_kind")
    if not visible_author and page_kind in {"author_intro", "excerpt", "mixed_excerpt_bibliography", "bibliography"}:
        confidence = "low"
        review_reasons.append("author_unknown")
    if starts_new_author and not heading_has_dates:
        confidence = "medium"
        review_reasons.append("author_boundary_without_life_dates")
    if contains_bibliography and contains_excerpt:
        review_reasons.append("mixed_excerpt_and_bibliography")
    if contains_notes:
        review_reasons.append("source_notes_detected")
    if layout.get("column_count", 0) and int(layout.get("column_count", 0)) > 1:
        review_reasons.append("multi_column_layout")
    if layout.get("needs_layout_review"):
        review_reasons.append("layout_review_required")
    if visible_author and page_kind in {"author_intro", "excerpt", "mixed_excerpt_bibliography"} and not review_reasons:
        confidence = "high"

    classification = {
        "page_kind": page_kind if page_kind in PAGE_KINDS else "unknown",
        "confidence": confidence,
        "primary_type": page_kind,
        "types": sorted(
            {
                page_kind,
                *("excerpt" for _ in [0] if contains_excerpt),
                *("bibliography" for _ in [0] if contains_bibliography),
                *("source_note" for _ in [0] if contains_notes),
                *("editorial_apparatus" for _ in [0] if contains_editorial),
            }
        ),
        "contains_excerpt": contains_excerpt,
        "contains_source_notes": contains_notes,
        "contains_bibliography": contains_bibliography,
        "contains_editorial_apparatus": contains_editorial,
        "visible_author_name": visible_author,
        "visible_author_slug": slugify(visible_author) if visible_author else None,
        "work_title": work_title,
        "work_slug": slugify(work_title) if work_title else None,
        "starts_new_author": starts_new_author,
        "continues_previous_author": False,
        "assembly_group_name": None,
        "assembly_group_slug": None,
        "include_in_author_assembly": page_kind not in {"blank", "front_matter", "table_of_contents", "index_appendix"},
        "review_required": bool(review_reasons),
        "review_reasons": sorted(set(review_reasons)),
        "override_applied": False,
        "override_id": "",
        "override_source": "",
        "signals": {
            "first_lines": first_lines,
            "top_heading": top_heading,
            "heading_author": heading_author,
            "running_author": running_author,
        },
    }

    return {
        "source_id": row.get("source_id", ""),
        "page_number": row["page_number"],
        "page_file": row["page_file"],
        "page_path": relative_to_root(page_path),
        "input_sha256": sha256_file(page_path) if page_path.exists() else "",
        "text_sha256": text_sha,
        "classification": classification,
        "layout": layout,
        "status": status,
        "error": error,
        "generated_at": generated_at,
        "git_commit": git_commit(),
        "script_version": SCRIPT_VERSION,
    }


def load_overrides(source: dict[str, Any]) -> tuple[Path | None, list[dict[str, Any]]]:
    override_path_value = source.get("classification_overrides")
    if not override_path_value:
        return None, []

    override_path = project_path(override_path_value)
    if not override_path.exists():
        raise FileNotFoundError(f"classification override file not found: {override_path}")

    with override_path.open("r", encoding="utf-8") as file_obj:
        data = yaml.safe_load(file_obj) or {}

    overrides = data.get("overrides", [])
    if not isinstance(overrides, list):
        raise ValueError(f"classification overrides must be a list: {override_path}")

    normalized: list[dict[str, Any]] = []
    for item in overrides:
        if not isinstance(item, dict):
            raise ValueError(f"classification override entries must be mappings: {override_path}")
        if "pages" not in item:
            raise ValueError(f"classification override missing pages: {override_path}")
        page_set = parse_page_spec(str(item["pages"]))
        if not page_set:
            raise ValueError(f"classification override has no pages: {item}")
        normalized.append({**item, "_page_set": page_set})
    return override_path, normalized


def rebuild_content_types(classification: dict[str, Any]) -> None:
    page_kind = classification.get("page_kind", "unknown")
    types = {page_kind}
    if classification.get("contains_excerpt"):
        types.add("excerpt")
    if classification.get("contains_bibliography"):
        types.add("bibliography")
    if classification.get("contains_source_notes"):
        types.add("source_note")
    if classification.get("contains_editorial_apparatus"):
        types.add("editorial_apparatus")
    classification["types"] = sorted(types)
    classification["primary_type"] = page_kind


def apply_classification_override(
    record: dict[str, Any],
    override: dict[str, Any],
    override_path: Path,
) -> None:
    classification = record["classification"]
    for field in OVERRIDE_FIELDS:
        if field not in override:
            continue
        if field == "author_name":
            classification["visible_author_name"] = override[field]
            classification["visible_author_slug"] = override.get("author_slug") or slugify(override[field])
        elif field == "author_slug":
            classification["visible_author_slug"] = override[field]
        elif field == "page_kind":
            page_kind = override[field]
            classification["page_kind"] = page_kind if page_kind in PAGE_KINDS else "unknown"
        else:
            classification[field] = override[field]

    if "work_title" in override and "work_slug" not in override:
        classification["work_slug"] = slugify(override["work_title"])
    if classification.get("visible_author_name") and not classification.get("visible_author_slug"):
        classification["visible_author_slug"] = slugify(classification["visible_author_name"])

    page_kind = classification.get("page_kind")
    if "contains_excerpt" not in override and page_kind in {"excerpt", "mixed_excerpt_bibliography"}:
        classification["contains_excerpt"] = True
    if "contains_bibliography" not in override and page_kind in {"bibliography", "mixed_excerpt_bibliography"}:
        classification["contains_bibliography"] = True
    if "contains_source_notes" not in override and page_kind == "notes":
        classification["contains_source_notes"] = True

    rebuild_content_types(classification)
    classification["assembly_group_name"] = classification.get("visible_author_name")
    classification["assembly_group_slug"] = classification.get("visible_author_slug")
    classification["override_applied"] = True
    classification["override_id"] = override.get("id", "")
    classification["override_source"] = relative_to_root(override_path)
    classification["review_reasons"] = [
        reason for reason in classification.get("review_reasons", [])
        if reason not in {"author_unknown", "unknown_page_kind", "running_head_differs_from_author_context"}
    ]
    if "review_required" not in override:
        classification["review_required"] = bool(classification["review_reasons"])


def apply_classification_overrides(
    records: list[dict[str, Any]],
    override_path: Path | None,
    overrides: list[dict[str, Any]],
) -> None:
    if not override_path or not overrides:
        return
    for record in records:
        page_number = record["page_number"]
        for override in overrides:
            if page_number in override["_page_set"]:
                apply_classification_override(record, override, override_path)


def apply_author_continuity(records: list[dict[str, Any]]) -> None:
    current_name: str | None = None
    current_slug: str | None = None
    for record in sorted(records, key=lambda item: item["page_number"]):
        classification = record["classification"]
        visible_name = classification.get("visible_author_name")
        visible_slug = classification.get("visible_author_slug")
        if classification.get("starts_new_author") and visible_name:
            current_name = visible_name
            current_slug = visible_slug
        elif visible_name and visible_slug and current_slug is None:
            current_name = visible_name
            current_slug = visible_slug
        elif visible_name and visible_slug and visible_slug == current_slug and not classification.get("starts_new_author"):
            classification["continues_previous_author"] = True
        elif visible_name and visible_slug and current_slug and visible_slug != current_slug:
            if not classification.get("work_title"):
                classification["work_title"] = visible_name
                classification["work_slug"] = visible_slug
            classification["visible_author_name"] = current_name
            classification["visible_author_slug"] = current_slug
            classification["continues_previous_author"] = True
            classification["review_required"] = True
            classification["review_reasons"].append("running_head_differs_from_author_context")
        elif not visible_name and current_name and classification["page_kind"] in {
            "excerpt",
            "mixed_excerpt_bibliography",
            "bibliography",
            "notes",
            "editorial_apparatus",
            "unknown",
        }:
            classification["visible_author_name"] = current_name
            classification["visible_author_slug"] = current_slug
            classification["continues_previous_author"] = True

        if classification["page_kind"] == "unknown" and classification.get("visible_author_name"):
            classification["page_kind"] = "author_intro"
            classification["primary_type"] = "author_intro"
            classification["types"] = [
                item for item in classification["types"]
                if item != "unknown"
            ] or ["author_intro"]
            if "author_intro" not in classification["types"]:
                classification["types"].append("author_intro")
            classification["confidence"] = "medium"

        if classification.get("visible_author_name"):
            classification["review_reasons"] = [
                reason for reason in classification["review_reasons"]
                if reason != "author_unknown"
            ]
            classification["assembly_group_name"] = classification["visible_author_name"]
            classification["assembly_group_slug"] = classification["visible_author_slug"]
        elif classification["page_kind"] in {"front_matter", "table_of_contents", "blank"}:
            classification["assembly_group_name"] = "Source Front Matter"
            classification["assembly_group_slug"] = "source-front-matter"
        elif classification["page_kind"] == "index_appendix":
            classification["assembly_group_name"] = "Source Back Matter"
            classification["assembly_group_slug"] = "source-back-matter"
        else:
            classification["assembly_group_name"] = "Unassigned Source Pages"
            classification["assembly_group_slug"] = "unassigned-source-pages"
            if "author_unknown" not in classification["review_reasons"]:
                classification["review_reasons"].append("author_unknown")
            classification["review_required"] = True
            classification["confidence"] = "low"

        classification["review_reasons"] = sorted(set(classification["review_reasons"]))


def csv_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        classification = record["classification"]
        rows.append(
            {
                "page_number": record["page_number"],
                "page_file": record["page_file"],
                "page_kind": classification["page_kind"],
                "confidence": classification["confidence"],
                "visible_author_name": classification.get("visible_author_name") or "",
                "visible_author_slug": classification.get("visible_author_slug") or "",
                "work_title": classification.get("work_title") or "",
                "starts_new_author": classification["starts_new_author"],
                "continues_previous_author": classification["continues_previous_author"],
                "assembly_group_slug": classification.get("assembly_group_slug") or "",
                "include_in_author_assembly": classification["include_in_author_assembly"],
                "review_required": classification["review_required"],
                "review_reasons": ";".join(classification["review_reasons"]),
                "override_applied": classification.get("override_applied", False),
                "override_id": classification.get("override_id", ""),
                "override_source": classification.get("override_source", ""),
                "input_sha256": record["input_sha256"],
                "text_sha256": record["text_sha256"],
                "status": record["status"],
                "error": record["error"],
                "generated_at": record["generated_at"],
                "git_commit": record["git_commit"],
                "script_version": record["script_version"],
            }
        )
    return rows


def review_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        classification = record["classification"]
        if not classification["review_required"]:
            continue
        rows.append(
            {
                "page_number": record["page_number"],
                "page_file": record["page_file"],
                "page_kind": classification["page_kind"],
                "confidence": classification["confidence"],
                "assembly_group_slug": classification.get("assembly_group_slug") or "",
                "visible_author_name": classification.get("visible_author_name") or "",
                "work_title": classification.get("work_title") or "",
                "review_reasons": ";".join(classification["review_reasons"]),
                "override_id": classification.get("override_id", ""),
                "first_lines": " / ".join(classification["signals"]["first_lines"][:3]),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="data/extraction-sources.yml")
    parser.add_argument("--source-id", default="norton-theory-criticism")
    parser.add_argument("--layout-jsonl", type=Path, help="Optional layout JSONL path.")
    parser.add_argument("--pages", help="Optional 1-based pages/ranges, such as 1,3-5.")
    parser.add_argument("--limit", type=int, help="Limit selected pages after filtering.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = load_config(args.config, args.source_id)
    paths = resolve_source_paths(source)
    override_path, overrides = load_overrides(source)
    layout_path = args.layout_jsonl or paths["layout_dir"] / "layout.jsonl"
    layout_by_page = {row["page_number"]: row for row in read_jsonl(layout_path)}
    rows = read_sliced_manifest(paths["sliced_pages_dir"])
    for row in rows:
        row["source_id"] = source["source_id"]
    selected = select_page_rows(rows, args.pages, args.limit)

    output_jsonl = paths["classification_dir"] / "page-classifications.jsonl"
    output_csv = paths["classification_dir"] / "manifest.csv"
    review_csv = paths["review_dir"] / "page-records-needing-review.csv"

    if args.dry_run:
        print(f"Would classify {len(selected)} page(s)")
        print(f"Would read layout from {relative_to_root(layout_path)}")
        if override_path:
            print(f"Would apply {len(overrides)} override rule(s) from {relative_to_root(override_path)}")
        print(f"Would write classifications to {relative_to_root(output_jsonl)}")
        print(f"Would write review queue to {relative_to_root(review_csv)}")
        return 0

    records = [classify_page(row, layout_by_page) for row in selected]
    apply_classification_overrides(records, override_path, overrides)
    apply_author_continuity(records)
    write_jsonl(output_jsonl, records)
    write_csv(
        output_csv,
        [
            "page_number",
            "page_file",
            "page_kind",
            "confidence",
            "visible_author_name",
            "visible_author_slug",
            "work_title",
            "starts_new_author",
            "continues_previous_author",
            "assembly_group_slug",
            "include_in_author_assembly",
            "review_required",
            "review_reasons",
            "override_applied",
            "override_id",
            "override_source",
            "input_sha256",
            "text_sha256",
            "status",
            "error",
            "generated_at",
            "git_commit",
            "script_version",
        ],
        csv_rows(records),
    )
    review = review_rows(records)
    write_csv(
        review_csv,
        [
            "page_number",
            "page_file",
            "page_kind",
            "confidence",
            "assembly_group_slug",
            "visible_author_name",
            "work_title",
            "review_reasons",
            "override_id",
            "first_lines",
        ],
        review,
    )

    failed = [record for record in records if record["status"] != "ok"]
    print(f"Wrote {len(records)} page classification(s) to {relative_to_root(output_jsonl)}")
    print(f"Wrote {len(review)} review queue row(s) to {relative_to_root(review_csv)}")
    if failed:
        print(f"error: {len(failed)} page classification(s) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
