"""Shared helpers for the auditable extraction pipeline."""

from __future__ import annotations

import csv
import json
import hashlib
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def project_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return "unknown"
    return result.stdout.strip() or "unknown"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(config_path: str | Path, source_id: str) -> dict[str, Any]:
    config_file = project_path(config_path)
    with config_file.open("r", encoding="utf-8") as file_obj:
        config = yaml.safe_load(file_obj) or {}

    for source in config.get("sources", []):
        if source.get("source_id") == source_id:
            source = dict(source)
            source["_config_path"] = str(config_file.relative_to(PROJECT_ROOT))
            return source

    raise ValueError(f"source_id not found in {config_file}: {source_id}")


def resolve_source_paths(source: dict[str, Any]) -> dict[str, Path]:
    source_id = source["source_id"]
    return {
        "source_pdf": project_path(source["source_pdf"]),
        "sliced_pages_dir": project_path(source["sliced_pages_dir"]),
        "layout_dir": project_path(source.get("layout_dir", f"work/layout/{source_id}")),
        "classification_dir": project_path(source.get("classification_dir", f"work/classification/{source_id}")),
        "review_dir": project_path(source.get("review_dir", f"work/review/{source_id}")),
        "page_records_dir": project_path(source["page_records_dir"]),
        "author_drafts_dir": project_path(source["author_drafts_dir"]),
        "prompts_dir": project_path(source.get("prompts_dir", f"work/prompts/{source_id}")),
        "audit_dir": project_path(source.get("audit_dir", f"work/audit/{source_id}")),
    }


def parse_page_spec(page_spec: str | None) -> set[int] | None:
    if not page_spec:
        return None

    pages: set[int] = set()
    for raw_part in page_spec.split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if start > end:
                raise ValueError(f"descending page range is invalid: {part}")
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    return pages


def read_sliced_manifest(sliced_pages_dir: Path) -> list[dict[str, Any]]:
    manifest_path = sliced_pages_dir / "manifest.csv"
    rows: list[dict[str, Any]] = []

    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8", newline="") as file_obj:
            reader = csv.DictReader(file_obj)
            for row in reader:
                page_number = int(row["page_number"])
                rows.append(
                    {
                        "page_number": page_number,
                        "page_file": row["file_name"],
                        "page_path": sliced_pages_dir / row["file_name"],
                    }
                )
    else:
        for page_path in sorted(sliced_pages_dir.glob("page_*.pdf")):
            match = re.search(r"(\d+)", page_path.stem)
            if not match:
                continue
            rows.append(
                {
                    "page_number": int(match.group(1)),
                    "page_file": page_path.name,
                    "page_path": page_path,
                }
            )

    return sorted(rows, key=lambda item: item["page_number"])


def select_page_rows(
    rows: Iterable[dict[str, Any]],
    page_spec: str | None,
    limit: int | None,
) -> list[dict[str, Any]]:
    requested_pages = parse_page_spec(page_spec)
    selected = [
        row for row in rows
        if requested_pages is None or row["page_number"] in requested_pages
    ]
    if limit is not None:
        selected = selected[:limit]
    return selected


def slugify(value: str | None, fallback: str = "unknown") -> str:
    if not value:
        return fallback
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or fallback


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def yaml_frontmatter(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False).strip()


def split_frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", markdown, re.DOTALL)
    if not match:
        raise ValueError("missing YAML frontmatter delimited by ---")
    metadata = yaml.safe_load(match.group(1)) or {}
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return metadata, match.group(2)


def read_markdown(path: Path) -> tuple[dict[str, Any], str]:
    return split_frontmatter(path.read_text(encoding="utf-8"))


def relative_to_root(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file_obj:
        for row in rows:
            file_obj.write(json.dumps(row, ensure_ascii=True, sort_keys=True))
            file_obj.write("\n")
