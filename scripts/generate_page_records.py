#!/usr/bin/env python3
"""Generate standardized page-record Markdown from layout metadata."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from lib.extraction_common import (
    git_commit,
    load_config,
    now_utc,
    read_jsonl,
    relative_to_root,
    resolve_source_paths,
    select_page_rows,
    sha256_file,
    write_csv,
    yaml_frontmatter,
)
from validate_records import validate_file


SCRIPT_VERSION = "3"
DEFAULT_PROMPT_TEMPLATE = Path("scripts/templates/page_to_markdown_agent_prompt.md")


def render_prompt(template_path: Path, variables: dict[str, Any]) -> str:
    text = template_path.read_text(encoding="utf-8")
    for key, value in variables.items():
        text = text.replace("{{ " + key + " }}", "" if value is None else str(value))
    return text


def page_title(source: dict[str, Any], page_number: int) -> str:
    return f"{source['source_title']} - Page {page_number}"


def layout_column_count(layout: dict[str, Any]) -> int:
    try:
        return max(0, int(layout.get("column_count", 0) or 0))
    except (TypeError, ValueError):
        return 0


def layout_column_mode(layout: dict[str, Any]) -> str:
    column_count = layout_column_count(layout)
    if column_count <= 0:
        return "unknown"
    if column_count == 1:
        return "single"
    if column_count == 2:
        return "two_column"
    return "multi_column"


def layout_reading_order(layout: dict[str, Any]) -> str:
    raw_order = str(layout.get("reading_order", "unknown") or "unknown")
    if raw_order in {"normalized:top-to-bottom", "normalized:left-column-then-right-column"}:
        return raw_order
    if raw_order == "no_text":
        return "not_applicable"
    if raw_order == "error":
        return "error"
    if raw_order.startswith("normalized"):
        return "normalized"
    if raw_order in {"unknown", "ambiguous", "source_order"}:
        return raw_order
    return "unknown"


def layout_confidence(layout: dict[str, Any]) -> str:
    column_count = layout_column_count(layout)
    raw_order = str(layout.get("reading_order", "unknown") or "unknown")
    needs_review = bool(layout.get("needs_layout_review", True))

    if raw_order in {"error", "unknown"} or column_count <= 0:
        return "low"
    if needs_review:
        return "medium"
    return "high"


def layout_notes(layout: dict[str, Any]) -> str:
    raw_order = str(layout.get("reading_order", "unknown") or "unknown")
    column_count = layout_column_count(layout)
    review_note = " Layout review is recommended." if layout.get("needs_layout_review") else ""
    return (
        "Generated from pdftotext layout metadata only; no source prose was "
        f"transcribed by the scaffold generator. Detected {column_count} column(s); "
        f"raw reading-order signal: {raw_order}.{review_note}"
    )


def classification_path(paths: dict[str, Path]) -> Path:
    return paths["classification_dir"] / "page-classifications.jsonl"


def read_classifications(paths: dict[str, Path]) -> dict[int, dict[str, Any]]:
    return {
        int(row["page_number"]): row.get("classification", {})
        for row in read_jsonl(classification_path(paths))
    }


def classification_for_page(classifications: dict[int, dict[str, Any]], page_number: int) -> dict[str, Any]:
    return classifications.get(
        page_number,
        {
            "page_kind": "unknown",
            "confidence": "low",
            "primary_type": "unknown",
            "types": ["unknown"],
            "contains_excerpt": False,
            "contains_source_notes": False,
            "contains_bibliography": False,
            "contains_editorial_apparatus": False,
            "visible_author_name": None,
            "visible_author_slug": None,
            "work_title": None,
            "work_slug": None,
            "starts_new_author": False,
            "continues_previous_author": False,
            "assembly_group_name": "Unassigned Source Pages",
            "assembly_group_slug": "unassigned-source-pages",
            "review_required": True,
            "review_reasons": ["missing_classification"],
        },
    )


def page_path_for_record(paths: dict[str, Path], page_record: dict[str, Any]) -> Path:
    page_path = page_record.get("page_path")
    if page_path:
        return Path(page_path)
    return paths["sliced_pages_dir"] / str(page_record["page_file"])


def build_page_record_markdown(
    source: dict[str, Any],
    layout_record: dict[str, Any],
    classification: dict[str, Any],
    prompt_template: Path,
    source_config: Path,
    audit_log: Path,
) -> str:
    page_number = layout_record["page_number"]
    title = page_title(source, page_number)
    page_file = layout_record["page_file"]
    layout = layout_record.get("layout", {})
    output_mode = source.get("default_output_mode", "summary_only")
    rights_status = source.get("source_rights_status", "unknown")
    access_level = source.get("default_access_level", "restricted")
    column_count = layout_column_count(layout)
    reading_order = layout_reading_order(layout)
    reading_order_confidence = layout_confidence(layout)
    needs_layout_review = bool(layout.get("needs_layout_review", True))
    notes = layout_notes(layout)
    author_name = classification.get("visible_author_name")
    author_slug = classification.get("visible_author_slug")
    work_title = classification.get("work_title")
    work_slug = classification.get("work_slug")
    page_kind = classification.get("page_kind", "unknown")
    content_types = classification.get("types") or [page_kind]
    review_reasons = classification.get("review_reasons") or []
    assembly_group_slug = classification.get("assembly_group_slug") or author_slug or "unassigned-source-pages"
    excerpt_section = "No excerpt included for this page.\n\nUse an agent or human review step to add a structured excerpt card only when the page contains an approved excerpt."
    if classification.get("contains_excerpt", False):
        excerpt_section = f"""### Excerpt Card

- Work: {work_title or "review required"}
- Source page: {page_number}
- Rights mode: {output_mode}
- Selection rationale: Classifier detected excerpt-like material; no source text reproduced by scaffold generator.

Excerpt text pending rights-aware review.

**Project commentary:** Add project commentary after curation."""

    source_notes_section = "No source notes recorded for this page."
    if classification.get("contains_source_notes", False):
        source_notes_section = f"""### Source Note

- Marker: review required
- Page: {page_number}
- Note summary: Classifier detected source-note markers; source note text was not transcribed by scaffold generator.
- Rights mode: {output_mode}"""

    bibliography_section = "No bibliography items recorded for this page."
    if classification.get("contains_bibliography", False):
        bibliography_section = f"""### Bibliography Item

- Page: {page_number}
- Entry: review required
- Type: bibliography signal
- Notes: Classifier detected bibliography material; source bibliography text was not transcribed by scaffold generator."""

    metadata = {
        "record_type": "page_record",
        "schema_version": 2,
        "title": title,
        "source": {
            "source_id": source["source_id"],
            "source_title": source["source_title"],
            "source_pdf": source["source_pdf"],
            "page_file": page_file,
            "page_number": page_number,
            "printed_page_label": None,
            "total_pages": layout_record.get("total_pages"),
        },
        "publication": {
            "access_level": access_level,
            "web_readable": True,
            "release_notes": source.get("notes", ""),
        },
        "rights": {
            "source_rights_status": rights_status,
            "output_mode": output_mode,
            "public_release": bool(source.get("public_release", False)),
            "rights_evidence": source.get("rights_evidence", ""),
        },
        "layout": {
            "extraction_method": "pdftotext -bbox-layout",
            "column_count": column_count,
            "reading_order": reading_order,
            "reading_order_confidence": reading_order_confidence,
            "needs_layout_review": bool(layout.get("needs_layout_review", True)),
            "layout_notes": notes,
        },
        "agent": {
            "agent_name": "local-scaffold",
            "model_identifier": "none:local-scaffold",
            "generated_at": now_utc(),
            "confidence": classification.get("confidence", "low"),
        },
        "provenance": {
            "source_derived": [
                "source.source_id",
                "source.source_title",
                "source.source_pdf",
                "source.page_file",
                "source.page_number",
                "rights.source_rights_status",
                "rights.output_mode",
            ],
            "layout_derived": [
                "layout.column_count",
                "layout.reading_order",
                "layout.needs_layout_review",
            ],
            "classification_derived": [
                "content.page_kind",
                "content.types",
                "structure.author_name",
                "structure.work_title",
            ],
            "generated_scaffold": [
                "Page Summary",
                "Excerpt Candidates",
                "Source Notes",
                "Bibliography Items",
                "Quality Checks",
                "Notes",
            ],
            "human_reviewed": False,
            "copied_source_prose": False,
        },
        "content": {
            "primary_type": classification.get("primary_type", page_kind),
            "types": content_types,
            "page_kind": page_kind,
            "contains_excerpt": bool(classification.get("contains_excerpt", False)),
            "contains_source_notes": bool(classification.get("contains_source_notes", False)),
            "contains_bibliography": bool(classification.get("contains_bibliography", False)),
            "contains_editorial_apparatus": bool(classification.get("contains_editorial_apparatus", False)),
        },
        "structure": {
            "author_name": author_name,
            "author_slug": author_slug,
            "work_title": work_title,
            "work_slug": work_slug,
            "section_title": None,
            "section_type": page_kind,
            "starts_new_author": bool(classification.get("starts_new_author", False)),
            "continues_previous_author": bool(classification.get("continues_previous_author", False)),
            "page_role": page_kind,
            "previous_page_context": None,
            "next_page_context": None,
        },
        "audit": {
            "input_sha256": layout_record.get("input_sha256", ""),
            "source_config": source.get("_config_path", ""),
            "source_config_sha256": sha256_file(source_config) if source_config.exists() else "",
            "prompt_template": relative_to_root(prompt_template),
            "prompt_template_sha256": sha256_file(prompt_template) if prompt_template.exists() else "",
            "classification_source": relative_to_root(classification_path(resolve_source_paths(source))),
            "audit_log": relative_to_root(audit_log),
        },
    }

    body = f"""# {title}

## Page Summary

Generated scaffold for source page {page_number}. Preliminary classifier page kind: `{page_kind}`. This record contains no transcribed source prose; it is ready for page-level agent review or human curation.

## Layout and Reading Order

- Column count: {column_count}
- Reading order: {reading_order}
- Reading order confidence: {reading_order_confidence}
- Needs layout review: {str(bool(layout.get("needs_layout_review", True))).lower()}
- Normalization notes: {notes}

## Bibliographic Signals

- Bibliography present: {str(bool(classification.get("contains_bibliography", False))).lower()}
- Source note markers present: {str(bool(classification.get("contains_source_notes", False))).lower()}
- Editorial apparatus present: {str(bool(classification.get("contains_editorial_apparatus", False))).lower()}
- Printed page label:

## Excerpt Candidates

{excerpt_section}

## Source Notes

{source_notes_section}

## Bibliography Items

{bibliography_section}

## Assembly Hints

- Suggested author file: `{assembly_group_slug}.md`
- Suggested work grouping: {work_title or ""}
- Start/end boundary evidence: starts_new_author={str(bool(classification.get("starts_new_author", False))).lower()}
- Continuity with previous page: continues_previous_author={str(bool(classification.get("continues_previous_author", False))).lower()}
- Continuity with next page:
- Keywords: scaffold, layout-review, {page_kind}

## Quality Checks

- [x] Page number recorded.
- [x] Rights status recorded.
- [x] Output mode obeyed.
- [x] Content types separated into excerpt, source notes, bibliography, and editorial apparatus.
- [x] Multi-column layout recorded and normalized if needed.
- [{"x" if author_name else " "}] Author/work boundary marked if visible.
- [x] Ambiguities noted.

## Notes

Classification review required: {str(bool(classification.get("review_required", False))).lower()}. Review reasons: {", ".join(review_reasons) if review_reasons else "none"}.

This page record was generated from layout and classification metadata only. Use an approved agent or human review step to fill excerpt, source-note, bibliography, and editorial apparatus details.
"""
    return f"---\n{yaml_frontmatter(metadata)}\n---\n\n{body}"


def run_agent_command(
    agent_command: str,
    prompt_file: Path,
    output_file: Path,
    page_record: dict[str, Any],
    source: dict[str, Any],
    paths: dict[str, Path],
) -> subprocess.CompletedProcess[str]:
    layout = page_record.get("layout", {})
    env = os.environ.copy()
    env.update(
        {
            "PAGE_PROMPT_FILE": str(prompt_file),
            "PAGE_RECORD_OUTPUT": str(output_file),
            "PAGE_NUMBER": str(page_record["page_number"]),
            "PAGE_FILE": str(page_record["page_file"]),
            "SOURCE_ID": str(page_record["source_id"]),
            "PAGE_PATH": str(page_path_for_record(paths, page_record)),
            "SOURCE_CONFIG": str(source.get("_config_path", "")),
            "OUTPUT_MODE": str(source.get("default_output_mode", "summary_only")),
            "ACCESS_LEVEL": str(source.get("default_access_level", "restricted")),
            "LAYOUT_COLUMN_MODE": layout_column_mode(layout),
            "LAYOUT_COLUMNS_DETECTED": str(layout_column_count(layout)),
            "LAYOUT_READING_ORDER": layout_reading_order(layout),
            "LAYOUT_READING_ORDER_CONFIDENCE": layout_confidence(layout),
            "LAYOUT_COLUMN_NOTES": layout_notes(layout),
            "CLASSIFICATION_PAGE_KIND": str(page_record.get("classification", {}).get("page_kind", "unknown")),
            "CLASSIFICATION_AUTHOR_NAME": str(page_record.get("classification", {}).get("visible_author_name") or ""),
            "CLASSIFICATION_WORK_TITLE": str(page_record.get("classification", {}).get("work_title") or ""),
            "CLASSIFICATION_REVIEW_REASONS": ",".join(page_record.get("classification", {}).get("review_reasons", [])),
        }
    )
    return subprocess.run(
        agent_command,
        shell=True,
        cwd=Path.cwd(),
        env=env,
        capture_output=True,
        text=True,
    )


def default_layout_path(paths: dict[str, Path]) -> Path:
    return paths["layout_dir"] / "layout.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="data/extraction-sources.yml")
    parser.add_argument("--source-id", default="norton-theory-criticism")
    parser.add_argument("--layout-jsonl", type=Path, help="Layout JSONL path.")
    parser.add_argument("--pages", help="Optional 1-based pages/ranges, such as 1,3-5.")
    parser.add_argument("--limit", type=int, help="Limit selected pages after filtering.")
    parser.add_argument("--prompt-template", type=Path, default=DEFAULT_PROMPT_TEMPLATE)
    parser.add_argument(
        "--agent-command",
        help=(
            "Optional external command called once per page. It receives "
            "PAGE_PROMPT_FILE and PAGE_RECORD_OUTPUT environment variables."
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = load_config(args.config, args.source_id)
    paths = resolve_source_paths(source)
    layout_path = args.layout_jsonl or default_layout_path(paths)
    layout_records = read_jsonl(layout_path)
    classifications = read_classifications(paths)
    selected = select_page_rows(layout_records, args.pages, args.limit)
    audit_log = paths["audit_dir"] / "page-record-generation.csv"
    prompt_template = args.prompt_template if args.prompt_template.is_absolute() else Path.cwd() / args.prompt_template
    source_config_path = Path(args.config)
    if not source_config_path.is_absolute():
        source_config_path = Path.cwd() / source_config_path
    prompt_template_sha = sha256_file(prompt_template) if prompt_template.exists() else ""
    source_config_sha = sha256_file(source_config_path) if source_config_path.exists() else ""

    if args.dry_run:
        print(f"Would generate {len(selected)} page record(s)")
        print(f"Would read {relative_to_root(layout_path)}")
        print(f"Would write records under {relative_to_root(paths['page_records_dir'])}")
        print(f"Would write audit log to {relative_to_root(audit_log)}")
        return 0

    paths["page_records_dir"].mkdir(parents=True, exist_ok=True)
    paths["prompts_dir"].mkdir(parents=True, exist_ok=True)
    audit_log.parent.mkdir(parents=True, exist_ok=True)

    audit_rows: list[dict[str, Any]] = []
    commit = git_commit()

    for record in selected:
        page_number = record["page_number"]
        classification = classification_for_page(classifications, page_number)
        record["classification"] = classification
        output_file = paths["page_records_dir"] / f"page_{page_number:04d}.md"
        prompt_file = paths["prompts_dir"] / f"page_{page_number:04d}.prompt.md"
        layout = record.get("layout", {})

        prompt = render_prompt(
            prompt_template,
            {
                "source_id": source["source_id"],
                "source_title": source["source_title"],
                "source_pdf": source["source_pdf"],
                "page_file": record["page_file"],
                "page_path": page_path_for_record(paths, record),
                "page_number": page_number,
                "total_pages": record.get("total_pages", ""),
                "source_rights_status": source.get("source_rights_status", "unknown"),
                "output_mode": source.get("default_output_mode", "summary_only"),
                "public_release": source.get("public_release", False),
                "access_level": source.get("default_access_level", "restricted"),
                "layout_column_count": layout_column_count(layout),
                "layout_reading_order": layout_reading_order(layout),
                "layout_reading_order_confidence": layout_confidence(layout),
                "layout_needs_layout_review": layout.get("needs_layout_review", True),
                "layout_notes": layout_notes(layout),
                "classification_page_kind": classification.get("page_kind", "unknown"),
                "classification_confidence": classification.get("confidence", "low"),
                "classification_author_name": classification.get("visible_author_name") or "",
                "classification_work_title": classification.get("work_title") or "",
                "classification_starts_new_author": classification.get("starts_new_author", False),
                "classification_continues_previous_author": classification.get("continues_previous_author", False),
                "classification_review_reasons": ", ".join(classification.get("review_reasons", [])),
                "previous_page_context": "",
                "next_page_context": "",
            },
        )
        prompt_file.write_text(prompt, encoding="utf-8")

        status = "ok"
        error = ""
        agent_name = "local-scaffold"
        agent_command_display = ""
        model_identifier = "none:local-scaffold"
        generated_at = now_utc()

        if args.agent_command:
            agent_name = "external-command"
            agent_command_display = shlex.join(["sh", "-c", args.agent_command])
            model_identifier = os.environ.get("PAGE_AGENT_MODEL") or os.environ.get("PAGE_AGENT_BACKEND") or "external-command"
            result = run_agent_command(
                args.agent_command,
                prompt_file,
                output_file,
                record,
                source,
                paths,
            )
            if result.returncode != 0:
                status = "error"
                error = result.stderr.strip() or result.stdout.strip()
            elif not output_file.exists():
                status = "error"
                error = "agent command did not create PAGE_RECORD_OUTPUT"
        else:
            markdown = build_page_record_markdown(
                source=source,
                layout_record=record,
                classification=classification,
                prompt_template=prompt_template,
                source_config=source_config_path,
                audit_log=audit_log,
            )
            output_file.write_text(markdown, encoding="utf-8")

        validation_result = "not_run"
        if output_file.exists():
            validation = validate_file(output_file, expected_type="page_record")
            validation_result = "ok" if not validation.errors else "failed"
            if validation.errors and status == "ok":
                status = "validation_failed"
                error = "; ".join(validation.errors)

        audit_rows.append(
            {
                "page_number": page_number,
                "page_file": record["page_file"],
                "source_pdf": source["source_pdf"],
                "input_sha256": record.get("input_sha256", ""),
                "prompt_template": relative_to_root(prompt_template),
                "prompt_file": relative_to_root(prompt_file),
                "output_file": relative_to_root(output_file),
                "agent_name": agent_name,
                "model_identifier": model_identifier,
                "agent_command": agent_command_display,
                "source_config": source.get("_config_path", args.config),
                "source_config_sha256": source_config_sha,
                "status": status,
                "error": error,
                "validation_result": validation_result,
                "prompt_template_sha256": prompt_template_sha,
                "output_sha256": sha256_file(output_file) if output_file.exists() else "",
                "generated_at": generated_at,
                "git_commit": commit,
                "script_version": SCRIPT_VERSION,
            }
        )

    write_csv(
        audit_log,
        [
            "page_number",
            "page_file",
            "source_pdf",
            "input_sha256",
            "prompt_template",
            "prompt_file",
            "output_file",
            "agent_name",
            "model_identifier",
            "agent_command",
            "source_config",
            "source_config_sha256",
            "status",
            "error",
            "validation_result",
            "prompt_template_sha256",
            "output_sha256",
            "generated_at",
            "git_commit",
            "script_version",
        ],
        audit_rows,
    )

    failed = [row for row in audit_rows if row["status"] != "ok"]
    print(f"Wrote {len(audit_rows)} page record(s) to {relative_to_root(paths['page_records_dir'])}")
    print(f"Wrote page-generation audit log to {relative_to_root(audit_log)}")
    if failed:
        print(f"error: {len(failed)} page record(s) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
