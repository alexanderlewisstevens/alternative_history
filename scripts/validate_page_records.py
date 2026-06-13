#!/usr/bin/env python3
"""Compatibility wrapper for v2 page-record validation."""

from __future__ import annotations

import sys

from validate_records import main


if __name__ == "__main__":
    sys.argv.extend(["--type", "page_record"])
    raise SystemExit(main())
