#!/usr/bin/env python3
"""Render both publication sections from the same verified public inventory."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- PUBLICATIONS:START -->"
END = "<!-- PUBLICATIONS:END -->"


def figure_control(item: dict, language: str) -> str:
    """Offer an explicit preview or a verified publisher figure link."""
    korean = language == "ko"
    figure = item.get("figure")
    external = item.get("figure_external_url")
    if not figure and not external:
        return ""
    if figure:
        href = ("../" if korean else "") + figure
        label = "그림 보기" if korean else "View figure"
        if item.get("figure_kind") == "supplement":
            label = "보충 그림" if korean else "Supplement figure"
        attributes = ' data-image-viewer aria-haspopup="dialog"'
    else:
        href = external
        label = "출판사 그림 ↗" if korean else "Publisher figure ↗"
        attributes = ' target="_blank" rel="noopener"'
    description = f"{label}: {item['title']}"
    control = (
        f'<a class="pub-figure-link" href="{html.escape(href, quote=True)}"'
        f' aria-label="{html.escape(description, quote=True)}"{attributes}>'
        f'{label}</a>'
    )
    source_url = item.get("figure_source_url")
    if figure and source_url:
        source_label = "출처" if korean else "Source"
        control += (
            f' <a class="pub-figure-source" href="{html.escape(source_url, quote=True)}"'
            f' target="_blank" rel="noopener">{source_label}</a>'
        )
    license_url = item.get("figure_license")
    if figure and license_url:
        parts = urlparse(license_url).path.strip("/").split("/")
        license_name = f"CC {parts[1].upper()} {parts[2]}"
        control += (
            f' <a class="pub-figure-license" href="{html.escape(license_url, quote=True)}"'
            f' target="_blank" rel="noopener">{html.escape(license_name)}</a>'
        )
    return f'<span class="pub-figure-actions">{control}</span>'


def validate_figures(items: list[dict]) -> None:
    """Require a recorded figure decision when adding a publication."""
    for item in items:
        status = item.get("figure_status")
        if status not in {"existing", "available", "publisher", "none", "unavailable"}:
            raise ValueError(f"Figure availability has not been reviewed: {item['doi']}")
        if status in {"none", "unavailable"}:
            if not item.get("figure_note") or item.get("figure") or item.get("figure_external_url"):
                raise ValueError(f"Invalid figure-availability decision: {item['doi']}")
            continue
        if item.get("figure"):
            path = ROOT / item["figure"]
            if not path.is_file() or not path.resolve().is_relative_to((ROOT / "figs").resolve()):
                raise ValueError(f"Missing or invalid figure asset: {item['doi']}")
            if item.get("figure_sha256") and hashlib.sha256(path.read_bytes()).hexdigest() != item["figure_sha256"]:
                raise ValueError(f"Figure asset changed without review: {item['doi']}")
        elif not item.get("figure_external_url", "").startswith("https://"):
            raise ValueError(f"Missing verified figure access: {item['doi']}")


def render_item(item: dict, language: str) -> str:
    """Keep publication roles independent of the author's byline position."""
    korean = language == "ko"
    first = item["first_author"] or item["co_first_author"]
    lead = first or item["corresponding_author"]
    types = ["lead" if lead else "coauthor"]
    if item["corresponding_author"]:
        types.append("corresponding")
    authors = []
    for author in item["authors"]:
        value = html.escape(author["display"])
        authors.append(f"<strong>{value}</strong>" if author["self"] else value)
    badges = []
    if first:
        label = ("공동 제1저자" if korean else "Co-first author") if item[
            "co_first_author"
        ] else ("제1저자" if korean else "First author")
        badges.append(f'<span class="pub-badge pub-badge--first">{label}</span>')
    if item["corresponding_author"]:
        label = "교신저자" if korean else "Corresponding author"
        badges.append(f'<span class="pub-badge pub-badge--first">{label}</span>')
    if item.get("online_status"):
        label = item["online_status"][language]
        badges.append(f'<span class="pub-badge pub-badge--status">{html.escape(label)}</span>')
    figure = ""
    if item.get("figure"):
        figure_path = ("../" if korean else "") + item["figure"]
        figure = f' data-fig="{html.escape(figure_path, quote=True)}"'
        caption = item["title"]
        if item.get("figure_label"):
            caption = f"{item['figure_label']} · {caption}"
        figure += f' data-fig-cap="{html.escape(caption, quote=True)}"'
    classes = "pub-item first-author" if first else "pub-item"
    citation = ", ".join(filter(None, [
        item["journal"],
        str(item.get("volume") or "") + (
            f'({item["issue"]})' if item.get("issue") else ""
        ),
        item.get("article_number") or item.get("pages") or "",
    ]))
    doi = html.escape(item["doi"], quote=True)
    return f'''                    <div class="{classes}" data-type="{' '.join(types)}" data-doi="{doi}"{figure}>
                        <div class="pub-title"><a href="https://doi.org/{doi}" target="_blank" rel="noopener">{html.escape(item['title'])}</a></div>
                        <div class="pub-authors">{', '.join(authors)} ({item['year']})</div>
                        <div class="pub-meta"><span class="pub-journal">{html.escape(citation)}</span> {' '.join(badges)} {figure_control(item, language)}</div>
                    </div>'''


def render_section(data: dict, language: str) -> str:
    items = data["publications"]
    korean = language == "ko"
    counts = {
        "all": len(items),
        "lead": sum(
            x["first_author"] or x["co_first_author"] or x["corresponding_author"]
            for x in items
        ),
        "corresponding": sum(x["corresponding_author"] for x in items),
    }
    counts["coauthor"] = counts["all"] - counts["lead"]
    labels = {
        "all": "전체" if korean else "All articles",
        "lead": "제1·공동제1·교신저자" if korean else "First, co-first & corresponding",
        "coauthor": "공저자" if korean else "Co-author",
        "corresponding": "교신저자" if korean else "Corresponding",
    }
    tabs = []
    for key, label in labels.items():
        count = f' <span class="count">{counts[key]}</span>' if key in counts else ""
        active = " active" if key == "all" else ""
        tabs.append(f'                <button class="pub-tab{active}" data-tab="{key}">{label}{count}</button>')
    subtitle = (
        f"출판·온라인 공개 논문 {counts['all']}편. 제1·공동제1·교신저자 {counts['lead']}편 포함."
        if korean else
        f"{counts['all']} published and online articles, including {counts['lead']} as first, co-first, or corresponding author."
    )
    updated = date.fromisoformat(data["updated"])
    checked = (
        f"{updated.year}년 {updated.month}월 {updated.day}일 갱신"
        if korean else f"Updated {updated.strftime('%B')} {updated.day}, {updated.year}"
    )
    note = (
        "정식 출판과 온라인 선공개를 구분해 표시했습니다."
        if korean else "Early online articles are labeled separately."
    )
    show = "전체 논문 보기" if korean else "Show All Publications"
    title = "논문 실적" if korean else "Publication Record"
    pubitems = "\n".join(render_item(x, language) for x in items)
    return f'''{START}
<section class="section section--alt" id="publications">
    <div class="section-inner">
        <div class="section-header reveal">
            <div class="section-label">{'논문 목록' if korean else 'Publications'}</div>
            <h2 class="section-title">{title}</h2>
            <p class="section-subtitle">{subtitle} {note} {checked}.</p>
        </div>
        <div class="reveal">
            <div class="pub-tabs" id="pubTabs" role="group" aria-label="{'저자 역할별 논문' if korean else 'Filter articles by authorship'}">
{chr(10).join(tabs)}
            </div>
            <div class="pub-panel active" id="panel-all">
                <div class="pub-list-items">
{pubitems}
                </div>
                <button class="pub-show-more" id="pubShowMore">{show} <span class="arrow">&#9660;</span></button>
            </div>
            <div class="pub-panel" id="panel-lead"></div>
            <div class="pub-panel" id="panel-coauthor"></div>
            <div class="pub-panel" id="panel-corresponding"></div>
        </div>
    </div>
</section>
{END}'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if either page needs regeneration")
    args = parser.parse_args()
    data = json.loads((ROOT / "data/publications.json").read_text())
    dois = [x["doi"].lower() for x in data["publications"]]
    if len(dois) != len(set(dois)):
        raise ValueError("Duplicate DOI in publication inventory")
    validate_figures(data["publications"])
    for language, filename in [("en", "index.html"), ("ko", "ko/index.html")]:
        path = ROOT / filename
        source = path.read_text()
        pattern = re.escape(START) + r".*?" + re.escape(END)
        rendered, count = re.subn(pattern, lambda _: render_section(data, language), source, flags=re.S)
        if count != 1:
            raise ValueError(f"Expected exactly one publication region in {filename}")
        if args.check and rendered != source:
            raise SystemExit(f"Publication section is stale: {filename}")
        if not args.check:
            path.write_text(rendered)
    print(f"PASS: both languages contain the same {len(dois)} unique DOI records")


if __name__ == "__main__":
    main()
