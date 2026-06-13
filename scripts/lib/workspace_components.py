"""Reusable HTML/Markdown components for generated workspace pages."""

from __future__ import annotations

import html
import re
from typing import Iterable


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def note_meta(items: list[tuple[str, object]]) -> str:
    rows = "\n".join(
        f"  <span><strong>{esc(label)}:</strong> {esc(value)}</span>"
        for label, value in items
    )
    return f"""<div class="ah-note-meta">
{rows}
</div>"""


def private_banner(title: str, body: str) -> str:
    return f"""<div class="ah-private-banner">
  <strong>{esc(title)}</strong>
  <span>{esc(body)}</span>
</div>"""


def link(label: str, href: str) -> str:
    return f'<a href="{esc(href)}">{esc(label)}</a>'


def render_inline_links(value: str) -> str:
    if "<a " in value:
        return value
    escaped = esc(value)
    return re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: link(html.unescape(match.group(1)), html.unescape(match.group(2))),
        escaped,
    )


def passage_card(kicker: str, title: str, fields: Iterable[tuple[str, str]]) -> str:
    rows = "\n".join(
        f"  <p><strong>{esc(label)}:</strong> {value}</p>"
        for label, value in fields
    )
    return f"""<section class="ah-passage-card">
  <span class="ah-action-kicker">{esc(kicker)}</span>
  <h3>{esc(title)}</h3>
{rows}
</section>"""


def provenance_table(rows: list[tuple[str, str]]) -> str:
    rendered_rows = "\n".join(
        f"    <tr><td>{esc(layer)}</td><td>{status}</td></tr>"
        for layer, status in rows
    )
    return f"""<div class="ah-provenance-table">
  <table>
    <thead>
      <tr><th>Layer</th><th>Status</th></tr>
    </thead>
    <tbody>
{rendered_rows}
    </tbody>
  </table>
</div>"""


def backlink_list(items: list[str]) -> str:
    rendered_items = "\n".join(f"<li>{render_inline_links(item)}</li>" for item in items)
    return f"""<ul class="ah-backlink-list">
{rendered_items}
</ul>"""


def generated_note(body: str) -> str:
    return f"""<div class="ah-generated-note">
{body}
</div>"""
