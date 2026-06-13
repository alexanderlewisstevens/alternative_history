#!/usr/bin/env python3
"""Run validation checks for valid and intentionally invalid fixtures."""

from __future__ import annotations

import argparse
from pathlib import Path

from validate_records import validate_file


VALID_FIXTURES = (
    "author-file.md",
    "page-record-bibliography.md",
    "page-record-footnotes.md",
    "page-record-mixed.md",
    "page-record-single-column.md",
    "page-record-two-column.md",
)

INVALID_FIXTURES = (
    "page-record-bibliography-in-excerpt.md",
    "page-record-markdown-footnote.md",
)


def iter_fixture_files(path: Path, pattern: str) -> list[Path]:
    if path.is_dir():
        return sorted(path.rglob(pattern))
    return [path]


def canonical_fixture_files(path: Path, file_names: tuple[str, ...]) -> list[Path]:
    return [path / file_name for file_name in file_names if (path / file_name).exists()]


def check_valid(path: Path, pattern: str | None) -> int:
    failures = 0
    files = (
        canonical_fixture_files(path, VALID_FIXTURES)
        if pattern is None
        else iter_fixture_files(path, pattern)
    )
    if not files:
        print(f"FAIL no valid fixtures found in {path}")
        return 1
    for file_path in files:
        result = validate_file(file_path)
        if result.errors or result.warnings:
            failures += 1
            print(f"FAIL valid fixture {file_path}")
            for error in result.errors:
                print(f"  error: {error}")
            for warning in result.warnings:
                print(f"  warning: {warning}")
        else:
            print(f"OK   valid fixture {file_path}")
    return failures


def check_invalid(path: Path, pattern: str | None) -> int:
    failures = 0
    files = (
        canonical_fixture_files(path, INVALID_FIXTURES)
        if pattern is None
        else iter_fixture_files(path, pattern)
    )
    if not files:
        print(f"FAIL no invalid fixtures found in {path}")
        return 1
    for file_path in files:
        result = validate_file(file_path)
        if result.errors:
            print(f"OK   invalid fixture failed as expected {file_path}")
        else:
            failures += 1
            print(f"FAIL invalid fixture unexpectedly passed {file_path}")
            for warning in result.warnings:
                print(f"  warning: {warning}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--valid-dir", type=Path, default=Path("tests/fixtures/valid"))
    parser.add_argument("--invalid-dir", type=Path, default=Path("tests/fixtures/invalid"))
    parser.add_argument("--valid-pattern")
    parser.add_argument("--invalid-pattern")
    args = parser.parse_args()

    failures = 0
    failures += check_valid(args.valid_dir, args.valid_pattern)
    failures += check_invalid(args.invalid_dir, args.invalid_pattern)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
