#!/usr/bin/env python3
"""Run real-browser smoke checks against the built MkDocs site."""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import socket
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


DEFAULT_CHECKS = [
    {
        "path": "/",
        "title": "Alternative History",
        "text": "Alternative History",
    },
    {
        "path": "/workspace/",
        "title": "Private Knowledge Base",
        "text": "Private Knowledge Base",
    },
    {
        "path": "/workspace/search/",
        "title": "Workspace Search",
        "text": "Workspace Search",
    },
    {
        "path": "/workspace/norton-texts/",
        "title": "",
        "text": "Norton Text Notes",
    },
    {
        "path": "/workspace/norton-texts/gorgias-encomium-helen/",
        "title": "Encomium of Helen",
        "text": "Source Trail",
    },
    {
        "path": "/workspace/passages/",
        "title": "",
        "text": "Current Passage Notes",
    },
    {
        "path": "/workspace/passages/gorgias-speech-as-force/",
        "title": "Speech As Force",
        "text": "Project Commentary",
    },
    {
        "path": "/workspace/poetry-and-judgment/",
        "title": "Poetry And Judgment",
        "text": "Poetry And Judgment",
    },
]


@dataclass
class SiteServer:
    base_url: str
    server: http.server.ThreadingHTTPServer
    thread: threading.Thread


class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextlib.contextmanager
def serve_site(site_dir: Path) -> Iterator[SiteServer]:
    handler = functools.partial(
        QuietHTTPRequestHandler,
        directory=str(site_dir),
    )
    port = free_port()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield SiteServer(
            base_url=f"http://127.0.0.1:{port}",
            server=server,
            thread=thread,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def load_checks(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return DEFAULT_CHECKS
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"browser smoke config must be a list: {path}")
    checks: list[dict[str, str]] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"check #{index} must be an object")
        page_path = item.get("path")
        expected_text = item.get("text")
        if not page_path or not expected_text:
            raise ValueError(f"check #{index} must include path and text")
        checks.append(
            {
                "path": str(page_path),
                "title": str(item.get("title", "")),
                "text": str(expected_text),
            }
        )
    return checks


def run_browser_checks(
    *,
    site_dir: Path,
    checks: list[dict[str, str]],
    browser_name: str,
    headless: bool,
) -> list[str]:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["playwright is not installed; run `make setup` first"]

    errors: list[str] = []
    console_errors: list[str] = []

    with serve_site(site_dir) as local_site:
        try:
            with sync_playwright() as playwright:
                browser_factory = getattr(playwright, browser_name)
                browser = browser_factory.launch(headless=headless)
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.on(
                    "console",
                    lambda message: console_errors.append(message.text)
                    if message.type == "error"
                    else None,
                )
                page.on(
                    "pageerror",
                    lambda exc: console_errors.append(str(exc)),
                )

                for check in checks:
                    url = local_site.base_url + check["path"]
                    page.goto(url, wait_until="networkidle")
                    body_text = page.locator("body").inner_text(timeout=5000)
                    expected_title = check.get("title")
                    if expected_title and expected_title not in page.title():
                        errors.append(
                            f"{check['path']}: expected title containing {expected_title!r}, got {page.title()!r}"
                        )
                    if check["text"] not in body_text:
                        errors.append(f"{check['path']}: expected visible text not found: {check['text']}")

                browser.close()
        except PlaywrightError as exc:
            if "Executable doesn't exist" in str(exc):
                errors.append("browser executable is missing; run `make install-browser`")
            else:
                errors.append(str(exc))

    errors.extend(f"console error: {message}" for message in console_errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, default=Path("site"), help="Built MkDocs site directory.")
    parser.add_argument("--config", type=Path, help="Optional JSON list of page checks.")
    parser.add_argument("--browser", default="chromium", choices=["chromium", "firefox", "webkit"])
    parser.add_argument("--headed", action="store_true", help="Run with a visible browser window.")
    args = parser.parse_args()

    if not args.site_dir.exists():
        print(f"error: site directory does not exist: {args.site_dir}", file=sys.stderr)
        return 1

    try:
        checks = load_checks(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    errors = run_browser_checks(
        site_dir=args.site_dir,
        checks=checks,
        browser_name=args.browser,
        headless=not args.headed,
    )
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1

    print(f"OK browser-smoke-checked {len(checks)} page(s) against {args.site_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
