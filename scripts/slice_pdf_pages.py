#!/usr/bin/env python3
"""Slice a PDF into one single-page PDF per page."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from lib.extraction_common import git_commit, now_utc, relative_to_root, sha256_file


DEFAULT_INPUT = Path("epdf.pub_the-norton-anthology-of-theory-and-criticism-5ea806ce63784.pdf")
DEFAULT_OUTPUT = Path("Norton_Anthology_Sliced_Author")
SCRIPT_VERSION = "2"


def parse_pages(page_spec: str, total_pages: int) -> list[int]:
    """Parse a 1-based page spec like '1,3-5' into 0-based indexes."""
    pages: set[int] = set()

    for raw_part in page_spec.split(","):
        part = raw_part.strip()
        if not part:
            continue

        if "-" in part:
            raw_start, raw_end = part.split("-", 1)
            start = int(raw_start)
            end = int(raw_end)
            if start > end:
                raise ValueError(f"Invalid descending page range: {part}")
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))

    invalid = [page for page in pages if page < 1 or page > total_pages]
    if invalid:
        raise ValueError(
            f"Page(s) out of range for {total_pages}-page PDF: "
            + ", ".join(str(page) for page in sorted(invalid))
        )

    return [page - 1 for page in sorted(pages)]


def slice_pdf(
    input_pdf: Path,
    output_dir: Path,
    prefix: str,
    force: bool,
    page_spec: str | None,
    dry_run: bool,
) -> int:
    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")

    reader = PdfReader(str(input_pdf))
    if reader.is_encrypted:
        decrypt_result = reader.decrypt("")
        if decrypt_result == 0:
            raise RuntimeError("PDF is encrypted and could not be opened with an empty password.")

    total_pages = len(reader.pages)
    page_indexes = (
        parse_pages(page_spec, total_pages)
        if page_spec
        else list(range(total_pages))
    )

    if dry_run:
        return len(page_indexes)

    if output_dir.exists() and any(output_dir.iterdir()) and not force:
        raise FileExistsError(
            f"Output directory is not empty: {output_dir}. "
            "Use --force to overwrite files."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    width = len(str(total_pages))
    manifest_path = output_dir / "manifest.csv"
    source_sha256 = sha256_file(input_pdf)
    commit = git_commit()

    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        manifest = csv.DictWriter(
            manifest_file,
            fieldnames=[
                "page_number",
                "file_name",
                "output_path",
                "source_pdf",
                "source_sha256",
                "output_sha256",
                "generated_at",
                "git_commit",
                "script",
                "script_version",
            ],
        )
        manifest.writeheader()

        for page_index in page_indexes:
            page_number = page_index + 1
            output_file = output_dir / f"{prefix}_{page_number:0{width}d}.pdf"

            writer = PdfWriter()
            writer.add_page(reader.pages[page_index])

            with output_file.open("wb") as pdf_file:
                writer.write(pdf_file)

            manifest.writerow(
                {
                    "page_number": page_number,
                    "file_name": output_file.name,
                    "output_path": relative_to_root(output_file),
                    "source_pdf": input_pdf.name,
                    "source_sha256": source_sha256,
                    "output_sha256": sha256_file(output_file),
                    "generated_at": now_utc(),
                    "git_commit": commit,
                    "script": "scripts/slice_pdf_pages.py",
                    "script_version": SCRIPT_VERSION,
                }
            )

    return len(page_indexes)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slice a PDF into one single-page PDF per page."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input PDF path. Default: {DEFAULT_INPUT}",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output directory. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--prefix",
        default="page",
        help="Output filename prefix. Default: page",
    )
    parser.add_argument(
        "--pages",
        help="Optional 1-based pages/ranges to slice, such as '1,3-5'. Default: all pages.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output files when the output directory is not empty.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print the number of pages that would be written.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        count = slice_pdf(
            input_pdf=args.input,
            output_dir=args.output,
            prefix=args.prefix,
            force=args.force,
            page_spec=args.pages,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"Would write {count} single-page PDF(s) to {args.output}")
    else:
        print(f"Wrote {count} single-page PDF(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
