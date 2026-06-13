#!/usr/bin/env python3
"""Write a private workspace map from restricted extraction metadata."""

from __future__ import annotations

import argparse
import csv
import html
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import yaml

from lib.extraction_common import (
    git_commit,
    load_config,
    now_utc,
    read_jsonl,
    relative_to_root,
    resolve_source_paths,
    slugify,
)


SCRIPT_VERSION = "2"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as file_obj:
        return list(csv.DictReader(file_obj))


def load_source_register(path: str | Path) -> dict[str, Any]:
    register_path = Path(path)
    with register_path.open("r", encoding="utf-8") as file_obj:
        data = yaml.safe_load(file_obj) or {}
    if not isinstance(data, dict):
        raise ValueError(f"source register must be a mapping: {register_path}")
    return data


def table_row(values: list[Any]) -> str:
    return "| " + " | ".join("" if value is None else str(value) for value in values) + " |"


def page_range(first_page: str, last_page: str) -> str:
    if first_page and last_page:
        return f"{first_page}-{last_page}"
    return ""


def source_page_range(classification_records: list[dict[str, Any]]) -> str:
    pages = sorted(int(row["page_number"]) for row in classification_records if row.get("page_number"))
    if not pages:
        return "none"
    return f"{pages[0]}-{pages[-1]}"


def split_reasons(value: str) -> list[str]:
    return [reason.strip() for reason in value.split(";") if reason.strip()]


def author_display_names(classification_records: list[dict[str, Any]], review_rows: list[dict[str, str]]) -> dict[str, str]:
    names: dict[str, str] = {}
    for record in classification_records:
        classification = record.get("classification", {})
        slug = classification.get("assembly_group_slug") or classification.get("visible_author_slug")
        name = classification.get("assembly_group_name") or classification.get("visible_author_name")
        if slug and name:
            names.setdefault(slug, name)
    for row in review_rows:
        slug = row.get("assembly_group_slug")
        name = row.get("visible_author_name")
        if slug and name:
            names.setdefault(slug, name)
    return names


def normalize_work_title(value: str) -> str:
    title = re.sub(r"\s+", " ", html.unescape(str(value))).strip()
    if not re.search(r"\b(book|chapter)\s+\d+$", title, flags=re.IGNORECASE):
        title = re.sub(r"\s+\d+$", "", title)
    return title.rstrip("!.,;:")


def work_title_key(value: str) -> str:
    key = slugify(normalize_work_title(value))
    return re.sub(r"^the-", "", key)


def similar_title(left: str, right: str) -> bool:
    left_key = work_title_key(left)
    right_key = work_title_key(right)
    if not left_key or not right_key:
        return False
    if left_key == right_key:
        return True
    return SequenceMatcher(None, left_key, right_key).ratio() >= 0.92


def extraction_work_titles(text: dict[str, Any]) -> list[str]:
    configured = text.get("extraction_work_titles")
    if isinstance(configured, list):
        titles = [str(value) for value in configured if str(value).strip()]
        if titles:
            return titles
    title = str(text.get("title", "")).strip()
    return [title] if title else []


def classification_record_matches_text(record: dict[str, Any], text: dict[str, Any]) -> bool:
    classification = record.get("classification", {})
    author_slug = str(classification.get("assembly_group_slug", ""))
    if not author_matches_text(author_slug, text):
        return False
    work_title = str(classification.get("work_title") or "")
    titles = extraction_work_titles(text)
    if not titles:
        return True
    return bool(work_title) and any(similar_title(work_title, title) for title in titles)


def classification_records_for_text(
    classification_records: list[dict[str, Any]],
    text: dict[str, Any],
) -> list[dict[str, Any]]:
    matched = [record for record in classification_records if classification_record_matches_text(record, text)]
    if matched:
        return matched
    return [
        record
        for record in classification_records
        if author_matches_text(str(record.get("classification", {}).get("assembly_group_slug", "")), text)
    ]


def page_range_for_records(records: list[dict[str, Any]]) -> str:
    pages = sorted(
        int(record.get("page_number", 0))
        for record in records
        if str(record.get("page_number", "")).isdigit() or isinstance(record.get("page_number"), int)
    )
    if not pages:
        return ""
    return page_range(str(pages[0]), str(pages[-1]))


def page_kinds_for_records(records: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for record in records:
        page_kind = record.get("classification", {}).get("page_kind") or "unknown"
        counter[str(page_kind)] += 1
    return counter


def review_counts_for_records(records: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for record in records:
        classification = record.get("classification", {})
        if not classification.get("review_required"):
            continue
        counter["total"] += 1
        for reason in classification.get("review_reasons", []) or []:
            counter[str(reason)] += 1
    return counter


def texts_for_author(author_slug: str, curated_texts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        text
        for text in curated_texts
        if text.get("id") != "norton-theory-criticism" and author_matches_text(author_slug, text)
    ]


def curated_titles_for_author(author_slug: str, curated_texts: list[dict[str, Any]]) -> list[str]:
    return [str(text.get("title", "")) for text in texts_for_author(author_slug, curated_texts) if text.get("title")]


def works_by_author(
    classification_records: list[dict[str, Any]],
    curated_texts: list[dict[str, Any]],
    names: dict[str, str],
) -> dict[str, list[str]]:
    grouped: dict[str, set[str]] = defaultdict(set)
    for record in classification_records:
        classification = record.get("classification", {})
        author_slug = classification.get("assembly_group_slug")
        work_title = classification.get("work_title")
        if author_slug and work_title and work_title != "review required":
            grouped[author_slug].add(str(work_title))

    normalized: dict[str, list[str]] = {}
    for author_slug, raw_titles in grouped.items():
        author_name = names.get(author_slug, author_slug.replace("-", " "))
        curated_titles = curated_titles_for_author(author_slug, curated_texts)
        selected: list[str] = []
        seen_keys: set[str] = set()

        for title in curated_titles:
            key = work_title_key(title)
            if key and key not in seen_keys:
                selected.append(title)
                seen_keys.add(key)

        for raw_title in sorted(raw_titles):
            title = normalize_work_title(raw_title)
            if not title:
                continue
            if similar_title(title, author_name):
                continue
            if any(similar_title(title, curated_title) for curated_title in curated_titles):
                continue
            key = work_title_key(title)
            if key and key not in seen_keys:
                selected.append(title)
                seen_keys.add(key)

        normalized[author_slug] = selected

    return normalized


def page_kinds_by_author(classification_records: list[dict[str, Any]]) -> dict[str, Counter[str]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for record in classification_records:
        classification = record.get("classification", {})
        author_slug = classification.get("assembly_group_slug")
        page_kind = classification.get("page_kind") or "unknown"
        if author_slug:
            grouped[author_slug][str(page_kind)] += 1
    return grouped


def review_counts_by_author(review_rows: list[dict[str, str]]) -> dict[str, Counter[str]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in review_rows:
        author_slug = row.get("assembly_group_slug") or "unknown"
        grouped[author_slug]["total"] += 1
        for reason in split_reasons(row.get("review_reasons", "")):
            grouped[author_slug][reason] += 1
    return grouped


def text_creator_slug(text: dict[str, Any]) -> str:
    return slugify(str(text.get("creator", "")))


def author_matches_text(author_slug: str, text: dict[str, Any]) -> bool:
    creator_slug = text_creator_slug(text)
    if not creator_slug:
        return False
    return creator_slug in author_slug or author_slug in creator_slug


def text_ids_for_author(author_slug: str, curated_texts: list[dict[str, Any]]) -> list[str]:
    return [str(text["id"]) for text in texts_for_author(author_slug, curated_texts)]


def constellations_for_text_ids(text_ids: list[str], constellations: list[dict[str, Any]]) -> list[str]:
    text_id_set = set(text_ids)
    matched = []
    for constellation in constellations:
        if text_id_set.intersection(set(constellation.get("texts", []))):
            matched.append(str(constellation.get("id", "")))
    return sorted(value for value in matched if value)


def truncate_list(values: list[str], limit: int = 5) -> str:
    if not values:
        return ""
    selected = values[:limit]
    suffix = f"<br><span class=\"meta-muted\">+{len(values) - limit} more</span>" if len(values) > limit else ""
    return "<br>".join(html.escape(value) for value in selected) + suffix


def text_note_link(text_id: str, label: str) -> str:
    return f"[{label}](norton-texts/{text_id}.md)"


def constellation_link(constellation_id: str) -> str:
    path = Path("docs/workspace") / f"{constellation_id}.md"
    if path.exists():
        return f"[{constellation_id}]({constellation_id}.md)"
    return constellation_id


def truncate_linked_constellations(values: list[str], limit: int = 5) -> str:
    if not values:
        return ""
    selected = values[:limit]
    suffix = f"<br><span class=\"meta-muted\">+{len(values) - limit} more</span>" if len(values) > limit else ""
    return "<br>".join(constellation_link(value) for value in selected) + suffix


def counter_summary(counter: Counter[str], skip: set[str] | None = None, limit: int = 3) -> str:
    skip = skip or set()
    items = [(key, value) for key, value in counter.most_common() if key not in skip and value]
    if not items:
        return ""
    selected = items[:limit]
    return "<br>".join(f"{html.escape(key)}: {value}" for key, value in selected)


def metric_cards(metrics: list[tuple[str, Any]]) -> str:
    return "\n".join(
        f"""<div class=\"ah-metric-card\">
  <div class=\"ah-metric-label\">{html.escape(str(label))}</div>
  <div class=\"ah-metric-value\">{html.escape(str(value))}</div>
</div>"""
        for label, value in metrics
    )


def author_inventory_rows(
    author_assembly: list[dict[str, str]],
    names: dict[str, str],
    works: dict[str, list[str]],
    page_kinds: dict[str, Counter[str]],
    review_counts: dict[str, Counter[str]],
    curated_texts: list[dict[str, Any]],
    constellations: list[dict[str, Any]],
) -> str:
    if not author_assembly:
        return "| No thinker drafts found |  |  |  |  |  |  |"

    lines = []
    for row in sorted(author_assembly, key=lambda item: int(item.get("first_page") or 0)):
        author_slug = row.get("author_slug", "")
        author_texts = texts_for_author(author_slug, curated_texts)
        text_ids = [str(text["id"]) for text in author_texts]
        constellation_ids = constellations_for_text_ids(text_ids, constellations)
        reviews = review_counts.get(author_slug, Counter())
        kinds = page_kinds.get(author_slug, Counter())
        display_name = names.get(author_slug, author_slug.replace("-", " ").title())
        linked_name = display_name
        if author_texts:
            linked_name = text_note_link(str(author_texts[0]["id"]), display_name)
        lines.append(
            table_row(
                [
                    linked_name,
                    page_range(row.get("first_page", ""), row.get("last_page", "")),
                    row.get("page_count", ""),
                    truncate_list(works.get(author_slug, []), limit=4),
                    truncate_linked_constellations(constellation_ids, limit=4),
                    reviews.get("total", 0),
                    counter_summary(kinds, limit=3),
                    f"`{row.get('output_file', '')}`",
                ]
            )
        )
    return "\n".join(lines)


def authors_for_text_id(
    text_id: str,
    curated_texts: list[dict[str, Any]],
    author_assembly: list[dict[str, str]],
) -> list[dict[str, str]]:
    text = next((item for item in curated_texts if item.get("id") == text_id), None)
    if not text:
        return []
    return [row for row in author_assembly if author_matches_text(row.get("author_slug", ""), text)]


def constellation_rows(
    constellations: list[dict[str, Any]],
    curated_texts: list[dict[str, Any]],
    author_assembly: list[dict[str, str]],
    names: dict[str, str],
    review_counts: dict[str, Counter[str]],
) -> str:
    if not constellations:
        return "| No constellations configured |  |  |  |"

    lines = []
    for constellation in constellations:
        matched_authors: dict[str, dict[str, str]] = {}
        for text_id in constellation.get("texts", []):
            for author in authors_for_text_id(str(text_id), curated_texts, author_assembly):
                matched_authors[author["author_slug"]] = author
        author_labels = []
        review_total = 0
        for author_slug, author in sorted(matched_authors.items(), key=lambda item: int(item[1].get("first_page") or 0)):
            text = next(
                (
                    item for item in curated_texts
                    if str(item.get("id", "")) in set(str(text_id) for text_id in constellation.get("texts", []))
                    and author_matches_text(author_slug, item)
                ),
                None,
            )
            label = names.get(author_slug, author_slug.replace("-", " ").title())
            linked_label = text_note_link(str(text["id"]), label) if text else html.escape(label)
            author_labels.append(
                f"{linked_label} "
                f"<span class=\"meta-muted\">({page_range(author.get('first_page', ''), author.get('last_page', ''))})</span>"
            )
            review_total += review_counts.get(author_slug, Counter()).get("total", 0)
        lines.append(
            table_row(
                [
                    constellation.get("id", ""),
                    constellation.get("question", ""),
                    "<br>".join(author_labels) if author_labels else "No current Norton draft",
                    review_total,
                    ", ".join(str(relation) for relation in constellation.get("relations", [])),
                ]
            )
        )
    return "\n".join(lines)


def build_markdown(source: dict[str, Any], source_register: dict[str, Any], output_path: Path) -> str:
    paths = resolve_source_paths(source)
    classification_records = read_jsonl(paths["classification_dir"] / "page-classifications.jsonl")
    author_assembly = read_csv_rows(paths["audit_dir"] / "author-assembly.csv")
    review_rows = read_csv_rows(paths["review_dir"] / "page-records-needing-review.csv")
    curated_texts = source_register.get("curated_texts", [])
    constellations = source_register.get("constellations", [])
    names = author_display_names(classification_records, review_rows)
    works = works_by_author(classification_records, curated_texts, names)
    page_kinds = page_kinds_by_author(classification_records)
    review_counts = review_counts_by_author(review_rows)
    touched_constellations = {
        constellation_id
        for row in author_assembly
        for constellation_id in constellations_for_text_ids(
            text_ids_for_author(row.get("author_slug", ""), curated_texts),
            constellations,
        )
    }
    generated_at = now_utc()

    return f"""# Norton Workspace Map

This page is generated from local extraction metadata. It is a private map for seeing how the Norton chunks currently fit together. It intentionally contains no copied Norton source prose.

<div class="ah-private-banner">
  <strong>Restricted workspace map</strong>
  <span>Use this page to navigate page ranges, thinker drafts, review pressure, and constellation coverage. Do not treat restricted draft paths as public content.</span>
</div>

<div class="ah-metric-grid">
{metric_cards([
    ("Source Pages", source_page_range(classification_records)),
    ("Thinker Drafts", len(author_assembly)),
    ("Review Rows", len(review_rows)),
    ("Constellations Touched", len(touched_constellations)),
])}
</div>

## How To Use This Map

- Start with a constellation to see which thinker chunks already exist.
- Use the thinker inventory to find page ranges, work titles, and review pressure.
- Resolve boundary and layout reviews before treating any chunk as stable.
- Promote nothing from restricted drafts into public pages without a separate rights decision.

## Constellation Coverage

| Constellation | Core Question | Current Norton Chunks | Review Rows | Relations |
| --- | --- | --- | ---: | --- |
{constellation_rows(constellations, curated_texts, author_assembly, names, review_counts)}

## Thinker Chunk Inventory

| Thinker | Pages | Page Count | Curated / Detected Works | Constellations | Review Rows | Page Kinds | Restricted Draft |
| --- | --- | ---: | --- | --- | ---: | --- | --- |
{author_inventory_rows(author_assembly, names, works, page_kinds, review_counts, curated_texts, constellations)}

## Audit Trail

| Field | Value |
| --- | --- |
| Source ID | `{source["source_id"]}` |
| Source title | {source["source_title"]} |
| Source rights status | `{source.get("source_rights_status", "unknown")}` |
| Classification records | `{relative_to_root(paths["classification_dir"] / "page-classifications.jsonl")}` |
| Review queue | `{relative_to_root(paths["review_dir"] / "page-records-needing-review.csv")}` |
| Author assembly audit | `{relative_to_root(paths["audit_dir"] / "author-assembly.csv")}` |
| Source register | `data/source-register.yml` |
| Generated at | `{generated_at}` |
| Git commit | `{git_commit()}` |
| Script version | `{SCRIPT_VERSION}` |
| Output path | `{relative_to_root(output_path)}` |

## Next Assembly Moves

1. Stabilize the first constellation, [Rhetoric And Force](rhetoric-and-force.md), from the chunks already visible here.
2. Use the generated [Norton Text Notes](norton-texts/index.md) to move from thinker chunks into constellations.
3. Use review counts to choose which chunks need boundary, layout, notes, or bibliography cleanup before deeper reading.
4. Keep this map private-first until rights and excerpt policy are settled.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="data/extraction-sources.yml")
    parser.add_argument("--source-id", default="norton-theory-criticism")
    parser.add_argument("--source-register", default="data/source-register.yml")
    parser.add_argument("--output", default="docs/workspace/norton-map.md")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = load_config(args.config, args.source_id)
    source_register = load_source_register(args.source_register)
    output_path = Path(args.output)
    markdown = build_markdown(source, source_register, output_path)

    if args.dry_run:
        print(markdown)
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote workspace map to {relative_to_root(output_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
