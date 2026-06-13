#!/usr/bin/env python3
"""Smoke-check built MkDocs pages and local navigation targets."""

from __future__ import annotations

import argparse
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_PATHS = [
    "/",
    "/workspace/",
    "/workspace/norton-map/",
    "/workspace/norton-texts/",
    "/workspace/norton-texts/gorgias-encomium-helen/",
    "/workspace/passages/",
    "/workspace/passages/gorgias-speech-as-force/",
    "/workspace/poetry-and-judgment/",
]

EXPECTED_TEXT = {
    "/": "Alternative History",
    "/workspace/": "Private Knowledge Base",
    "/workspace/norton-map/": "Norton Workspace Map",
    "/workspace/norton-texts/": "Norton Text Notes",
    "/workspace/norton-texts/gorgias-encomium-helen/": "Encomium of Helen",
    "/workspace/passages/": "Passage Notes",
    "/workspace/passages/gorgias-speech-as-force/": "Speech As Force",
    "/workspace/poetry-and-judgment/": "Poetry And Judgment",
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for name, value in attrs:
            if name == "href" and value:
                self.links.append(value)


def normalize_path(value: str) -> str:
    if not value.startswith("/"):
        value = "/" + value
    return value


def html_path_for(site_dir: Path, path: str) -> Path:
    parsed = urllib.parse.urlparse(path)
    clean_path = parsed.path or "/"
    if clean_path.endswith("/"):
        return site_dir / clean_path.lstrip("/") / "index.html"
    if clean_path.endswith(".html"):
        return site_dir / clean_path.lstrip("/")
    return site_dir / clean_path.lstrip("/") / "index.html"


def read_from_site_dir(site_dir: Path, path: str) -> str:
    html_path = html_path_for(site_dir, path)
    if not html_path.exists():
        raise FileNotFoundError(f"missing built page for {path}: {html_path}")
    return html_path.read_text(encoding="utf-8")


def read_from_base_url(base_url: str, path: str) -> str:
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.read().decode("utf-8", errors="replace")


def internal_target_exists(site_dir: Path, target_path: str) -> bool:
    parsed = urllib.parse.urlparse(target_path)
    if parsed.scheme or parsed.netloc:
        return True
    if parsed.path.startswith("mailto:") or parsed.path.startswith("javascript:"):
        return True
    if not parsed.path:
        return True
    html_path = html_path_for(site_dir, parsed.path)
    asset_path = site_dir / parsed.path.lstrip("/")
    return html_path.exists() or asset_path.exists()


def check_page(
    *,
    path: str,
    site_dir: Path,
    base_url: str | None,
    check_links: bool,
) -> list[str]:
    errors: list[str] = []
    html = read_from_base_url(base_url, path) if base_url else read_from_site_dir(site_dir, path)
    expected = EXPECTED_TEXT.get(path)
    if expected and expected not in html:
        errors.append(f"{path}: expected text not found: {expected}")

    if check_links and not base_url:
        parser = LinkParser()
        parser.feed(html)
        for href in parser.links:
            if href.startswith("#"):
                continue
            absolute = urllib.parse.urljoin(path, href)
            if not internal_target_exists(site_dir, absolute):
                errors.append(f"{path}: broken internal link {href} -> {absolute}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, default=Path("site"), help="Built MkDocs site directory.")
    parser.add_argument("--base-url", help="Optional local server URL, for example http://127.0.0.1:8001")
    parser.add_argument("--path", action="append", help="Path to check. Repeat for multiple paths.")
    parser.add_argument("--skip-links", action="store_true", help="Skip internal link existence checks.")
    args = parser.parse_args()

    paths = [normalize_path(path) for path in (args.path or DEFAULT_PATHS)]
    if not args.base_url and not args.site_dir.exists():
        print(f"error: site directory does not exist: {args.site_dir}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in paths:
        try:
            errors.extend(
                check_page(
                    path=path,
                    site_dir=args.site_dir,
                    base_url=args.base_url,
                    check_links=not args.skip_links,
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path}: {exc}")

    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1

    mode = args.base_url or str(args.site_dir)
    print(f"OK smoke-checked {len(paths)} page(s) against {mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
