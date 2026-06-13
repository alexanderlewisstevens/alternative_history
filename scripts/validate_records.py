#!/usr/bin/env python3
"""Validate schema-v2 page-record and author-file Markdown templates."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lib.extraction_common import read_markdown


SCHEMA_VERSION = 2

ALLOWED_ACCESS_LEVELS = {"public", "restricted", "private"}
ALLOWED_RIGHTS_STATUSES = {
    "unknown",
    "public_domain",
    "open_license",
    "copyrighted",
    "permission_granted",
    "government_public_domain",
    "fair_use_limited",
}
FULL_TEXT_ALLOWED_STATUSES = {
    "public_domain",
    "open_license",
    "permission_granted",
    "government_public_domain",
}
ALLOWED_OUTPUT_MODES = {
    "metadata_only",
    "summary_only",
    "limited_quote",
    "transcription",
}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}
ALLOWED_COLUMN_MODES = {
    "unknown",
    "single",
    "two_column",
    "multi_column",
    "mixed",
    "ambiguous",
}
ALLOWED_READING_ORDERS = {
    "unknown",
    "normalized",
    "normalized:top-to-bottom",
    "normalized:left-column-then-right-column",
    "source_order",
    "ambiguous",
    "not_applicable",
    "no_text",
    "error",
}
ALLOWED_CONTENT_TYPES = {
    "unknown",
    "excerpt",
    "bibliography",
    "source_note",
    "editorial_apparatus",
    "author_intro",
    "front_matter",
    "table_of_contents",
    "index_appendix",
    "mixed_excerpt_bibliography",
    "notes",
    "index",
    "image",
    "blank",
    "mixed",
}

PAGE_REQUIRED_FRONTMATTER = (
    "record_type",
    "schema_version",
    "title",
    "source.source_id",
    "source.source_title",
    "source.source_pdf",
    "source.page_file",
    "source.page_number",
    "source.total_pages",
    "publication.access_level",
    "publication.web_readable",
    "rights.source_rights_status",
    "rights.output_mode",
    "rights.public_release",
    "rights.rights_evidence",
    "layout.extraction_method",
    "layout.column_count",
    "layout.reading_order",
    "layout.reading_order_confidence",
    "layout.needs_layout_review",
    "content.primary_type",
    "content.types",
    "content.page_kind",
    "content.contains_excerpt",
    "content.contains_source_notes",
    "content.contains_bibliography",
    "content.contains_editorial_apparatus",
    "structure.section_type",
    "structure.starts_new_author",
    "structure.continues_previous_author",
    "structure.page_role",
)

AUTHOR_REQUIRED_FRONTMATTER = (
    "record_type",
    "schema_version",
    "title",
    "author.name",
    "author.slug",
    "source.source_id",
    "source.source_title",
    "source.source_pdf",
    "source.first_page",
    "source.last_page",
    "publication.access_level",
    "publication.web_readable",
    "rights.source_rights_status",
    "rights.public_release",
    "rights.rights_evidence",
    "assembly.generated_from_page_records",
    "assembly.generated_at",
    "assembly.confidence",
)

PAGE_SECTIONS = (
    "Page Summary",
    "Layout and Reading Order",
    "Bibliographic Signals",
    "Excerpt Candidates",
    "Source Notes",
    "Bibliography Items",
    "Assembly Hints",
    "Quality Checks",
    "Notes",
)

AUTHOR_SECTIONS = (
    "Why This Author Matters",
    "Works In This Source",
    "Reader Summary",
    "Selected Excerpts",
    "Source Notes",
    "Bibliography",
    "Page Inventory",
    "Open Questions",
    "Further Reading",
)


@dataclass
class ValidationResult:
    path: Path
    record_type: str
    errors: list[str]
    warnings: list[str]


def nested_get(data: dict[str, Any], dotted_path: str) -> Any:
    value: Any = data
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def normalize_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def heading_sequence(body: str) -> list[str]:
    return re.findall(r"^## (.+?)\s*$", body, re.MULTILINE)


def section_content(body: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", body, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^## .+$", body[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(body)
    return body[start:end].strip()


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def blockquote_word_count(text: str) -> int:
    quoted = "\n".join(
        line[1:].strip()
        for line in text.splitlines()
        if line.strip().startswith(">")
    )
    return word_count(quoted)


def validate_set(errors: list[str], value: Any, allowed: set[str], path: str) -> None:
    if value not in allowed:
        errors.append(f"{path} must be one of: {', '.join(sorted(allowed))}")


def check_required_paths(
    metadata: dict[str, Any],
    required_paths: tuple[str, ...],
    errors: list[str],
) -> None:
    for dotted_path in required_paths:
        if is_blank(nested_get(metadata, dotted_path)):
            errors.append(f"missing required frontmatter value: {dotted_path}")


def check_section_order(body: str, sections: tuple[str, ...], errors: list[str]) -> None:
    headings = heading_sequence(body)
    unexpected = [heading for heading in headings if heading not in sections]
    if unexpected:
        errors.append("unexpected sections present: " + ", ".join(unexpected))

    actual = [heading for heading in headings if heading in sections]
    if actual != list(sections):
        errors.append(
            "required sections must appear exactly in this order: "
            + " > ".join(sections)
        )

    for section in sections:
        if not re.search(rf"^## {re.escape(section)}\s*$", body, re.MULTILINE):
            errors.append(f"missing required section: {section}")


def check_publication_and_rights(
    metadata: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    *,
    requires_output_mode: bool,
) -> None:
    access_level = nested_get(metadata, "publication.access_level")
    web_readable = nested_get(metadata, "publication.web_readable")
    rights_status = nested_get(metadata, "rights.source_rights_status")
    public_release = nested_get(metadata, "rights.public_release")

    validate_set(errors, access_level, ALLOWED_ACCESS_LEVELS, "publication.access_level")
    validate_set(errors, rights_status, ALLOWED_RIGHTS_STATUSES, "rights.source_rights_status")

    if not isinstance(web_readable, bool):
        errors.append("publication.web_readable must be a boolean")
    if not isinstance(public_release, bool):
        errors.append("rights.public_release must be a boolean")

    if requires_output_mode:
        output_mode = nested_get(metadata, "rights.output_mode")
        validate_set(errors, output_mode, ALLOWED_OUTPUT_MODES, "rights.output_mode")
        if output_mode == "transcription":
            full_text_allowed = rights_status in FULL_TEXT_ALLOWED_STATUSES
            restricted_or_private = (
                access_level in {"restricted", "private"} and public_release is False
            )
            if not full_text_allowed and not restricted_or_private:
                errors.append(
                    "transcription mode requires full-text-allowed rights status, "
                    "or restricted/private access with public_release false"
                )

    if public_release is True and rights_status in {"copyrighted", "unknown"}:
        errors.append("public_release cannot be true for copyrighted or unknown source rights")
    if access_level == "public" and public_release is False:
        warnings.append("access_level is public but rights.public_release is false")


def validate_page_record(path: Path, metadata: dict[str, Any], body: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if metadata.get("record_type") != "page_record":
        errors.append("record_type must be page_record")
    if metadata.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    check_required_paths(metadata, PAGE_REQUIRED_FRONTMATTER, errors)
    check_publication_and_rights(metadata, errors, warnings, requires_output_mode=True)
    check_section_order(body, PAGE_SECTIONS, errors)

    confidence = nested_get(metadata, "agent.confidence")
    if confidence is not None:
        validate_set(errors, confidence, ALLOWED_CONFIDENCE, "agent.confidence")

    extraction_method = nested_get(metadata, "layout.extraction_method")
    column_count = nested_get(metadata, "layout.column_count")
    reading_order = nested_get(metadata, "layout.reading_order")
    reading_order_confidence = nested_get(metadata, "layout.reading_order_confidence")
    needs_layout_review = normalize_bool(nested_get(metadata, "layout.needs_layout_review"))
    layout_notes = nested_get(metadata, "layout.layout_notes")
    primary_type = nested_get(metadata, "content.primary_type")
    content_types = nested_get(metadata, "content.types")
    page_kind = nested_get(metadata, "content.page_kind")
    output_mode = nested_get(metadata, "rights.output_mode")
    contains_excerpt = normalize_bool(nested_get(metadata, "content.contains_excerpt"))
    contains_source_notes = normalize_bool(nested_get(metadata, "content.contains_source_notes"))
    contains_bibliography = normalize_bool(nested_get(metadata, "content.contains_bibliography"))
    contains_editorial_apparatus = normalize_bool(
        nested_get(metadata, "content.contains_editorial_apparatus")
    )

    if is_blank(extraction_method):
        errors.append("layout.extraction_method must describe the extraction method")
    if not isinstance(column_count, int) or column_count < 0:
        errors.append("layout.column_count must be a non-negative integer")
        column_count = 0

    validate_set(errors, reading_order, ALLOWED_READING_ORDERS, "layout.reading_order")
    validate_set(
        errors,
        reading_order_confidence,
        ALLOWED_CONFIDENCE,
        "layout.reading_order_confidence",
    )
    validate_set(errors, primary_type, ALLOWED_CONTENT_TYPES, "content.primary_type")
    validate_set(errors, page_kind, ALLOWED_CONTENT_TYPES, "content.page_kind")

    for path_name, value in (
        ("layout.needs_layout_review", needs_layout_review),
        ("content.contains_excerpt", contains_excerpt),
        ("content.contains_source_notes", contains_source_notes),
        ("content.contains_bibliography", contains_bibliography),
        ("content.contains_editorial_apparatus", contains_editorial_apparatus),
    ):
        if value is None:
            errors.append(f"{path_name} must be a boolean")

    if not isinstance(content_types, list) or not content_types:
        errors.append("content.types must be a non-empty list")
        content_types = []
    else:
        invalid_types = [item for item in content_types if item not in ALLOWED_CONTENT_TYPES]
        if invalid_types:
            errors.append(
                "content.types contains invalid values: "
                + ", ".join(str(item) for item in invalid_types)
            )
        if primary_type not in content_types and primary_type != "unknown":
            errors.append("content.primary_type must also appear in content.types")

    if column_count > 1:
        allowed_multi_order = {
            "normalized",
            "normalized:left-column-then-right-column",
            "ambiguous",
        }
        if reading_order not in allowed_multi_order:
            errors.append("multi-column pages must use normalized or ambiguous reading_order")
        if is_blank(layout_notes):
            errors.append("multi-column pages must include layout.layout_notes")

    if len(re.findall(r"^# .+$", body, re.MULTILINE)) != 1:
        errors.append("body must contain exactly one H1 page title")

    if re.search(r"\[\^[^\]]+\](?::)?", body):
        errors.append("page records must not use Markdown footnote syntax for source notes")

    excerpt_section = section_content(body, "Excerpt Candidates")
    source_notes_section = section_content(body, "Source Notes")
    bibliography_section = section_content(body, "Bibliography Items")
    notes_section = section_content(body, "Notes")

    if '<div class="excerpt-card"' in body:
        errors.append("page records must use Markdown Excerpt Card sections, not HTML cards")

    if contains_excerpt is True and "### Excerpt Card" not in excerpt_section:
        errors.append("content.contains_excerpt true requires an Excerpt Card")
    if contains_excerpt is False and "### Excerpt Card" in excerpt_section:
        errors.append("content.contains_excerpt false but Excerpt Card is present")

    if output_mode in {"metadata_only", "summary_only"} and blockquote_word_count(excerpt_section) > 40:
        errors.append("metadata_only/summary_only records must not include long blockquotes")

    if contains_source_notes is True and "### Source Note" not in source_notes_section:
        errors.append("content.contains_source_notes true requires at least one Source Note")
    if contains_source_notes is False and "### Source Note" in source_notes_section:
        errors.append("content.contains_source_notes false but Source Note is present")

    if contains_bibliography is True and "### Bibliography Item" not in bibliography_section:
        errors.append("content.contains_bibliography true requires at least one Bibliography Item")
    if contains_bibliography is False and "### Bibliography Item" in bibliography_section:
        errors.append("content.contains_bibliography false but Bibliography Item is present")

    if contains_editorial_apparatus is True and "editorial apparatus" not in notes_section.lower():
        errors.append(
            "content.contains_editorial_apparatus true requires editorial apparatus details in Notes"
        )

    if primary_type == "bibliography" and contains_bibliography is not True:
        errors.append("bibliography primary_type requires content.contains_bibliography true")
    if primary_type == "source_note" and contains_source_notes is not True:
        errors.append("source_note primary_type requires content.contains_source_notes true")
    if primary_type == "excerpt" and contains_excerpt is not True:
        errors.append("excerpt primary_type requires content.contains_excerpt true")

    if "### Bibliography Item" in excerpt_section:
        errors.append("bibliography items must not appear inside Excerpt Candidates")
    if "### Source Note" in excerpt_section:
        errors.append("source notes must not appear inside Excerpt Candidates")
    if "### Excerpt Card" in bibliography_section:
        errors.append("excerpt cards must not appear inside Bibliography Items")

    return ValidationResult(path=path, record_type="page_record", errors=errors, warnings=warnings)


def validate_author_file(path: Path, metadata: dict[str, Any], body: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if metadata.get("record_type") != "author_file":
        errors.append("record_type must be author_file")
    if metadata.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    check_required_paths(metadata, AUTHOR_REQUIRED_FRONTMATTER, errors)
    check_publication_and_rights(metadata, errors, warnings, requires_output_mode=False)
    check_section_order(body, AUTHOR_SECTIONS, errors)

    confidence = nested_get(metadata, "assembly.confidence")
    validate_set(errors, confidence, ALLOWED_CONFIDENCE, "assembly.confidence")

    generated_from = nested_get(metadata, "assembly.generated_from_page_records")
    if not isinstance(generated_from, list):
        errors.append("assembly.generated_from_page_records must be a list")

    if len(re.findall(r"^# .+$", body, re.MULTILINE)) != 1:
        errors.append("body must contain exactly one H1 author title")

    if re.search(r"\[\^[^\]]+\](?::)?", body):
        errors.append("author files must not use Markdown footnote syntax for source notes")

    if '<div class="excerpt-card"' in body:
        errors.append("author files must use Markdown Excerpt Card sections, not HTML cards")

    excerpt_section = section_content(body, "Selected Excerpts")
    if "### Excerpt Card" not in excerpt_section:
        errors.append("Selected Excerpts must include at least one Excerpt Card")
    if "### Bibliography Item" in excerpt_section:
        errors.append("bibliography items must not appear inside Selected Excerpts")
    if "### Source Note" in excerpt_section:
        errors.append("source notes must not appear inside Selected Excerpts")

    return ValidationResult(path=path, record_type="author_file", errors=errors, warnings=warnings)


def validate_file(path: Path, expected_type: str | None = None) -> ValidationResult:
    try:
        metadata, body = read_markdown(path)
    except Exception as exc:
        return ValidationResult(path=path, record_type="unknown", errors=[str(exc)], warnings=[])

    record_type = metadata.get("record_type", "unknown")
    if expected_type and record_type != expected_type:
        return ValidationResult(
            path=path,
            record_type=record_type,
            errors=[f"expected record_type {expected_type}, found {record_type}"],
            warnings=[],
        )

    if record_type == "page_record":
        return validate_page_record(path, metadata, body)
    if record_type == "author_file":
        return validate_author_file(path, metadata, body)

    return ValidationResult(
        path=path,
        record_type=record_type,
        errors=[f"unsupported record_type: {record_type}"],
        warnings=[],
    )


def iter_markdown_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
        else:
            files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Markdown file(s) or directories.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument(
        "--type",
        choices=["page_record", "author_file"],
        help="Require a specific record type.",
    )
    args = parser.parse_args()

    files = iter_markdown_files(args.paths)
    if not files:
        print("error: no Markdown files found", file=sys.stderr)
        return 1

    failed = False
    for file_path in files:
        result = validate_file(file_path, expected_type=args.type)
        if result.errors or (args.strict and result.warnings):
            failed = True

        if result.errors:
            print(f"FAIL {result.path}")
            for error in result.errors:
                print(f"  error: {error}")
        elif result.warnings:
            print(f"WARN {result.path}")
        else:
            print(f"OK   {result.path}")

        for warning in result.warnings:
            print(f"  warning: {warning}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
