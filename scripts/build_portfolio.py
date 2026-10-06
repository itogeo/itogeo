"""Build the portfolio sections of the site from data/portfolio.json.

Writes static HTML (no JavaScript needed, readable by search engines) between
marker comments in two pages:

    index.html            <!-- FEATURED:START --> ... <!-- FEATURED:END -->
    projects/index.html   <!-- PORTFOLIO:START --> ... <!-- PORTFOLIO:END -->

Usage:
    python scripts/build_portfolio.py           # rebuild both pages
    python scripts/build_portfolio.py --check   # validate the JSON only

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "portfolio.json"
HOME = ROOT / "index.html"
PROJECTS = ROOT / "projects" / "index.html"

KINDS = {
    "client": ("Client work", "Maps and analysis built with partners."),
    "product": ("Products", "Things I build and run myself."),
    "open": ("Open source & free tools", "Free to use, fork, and improve."),
}
KIND_LABEL = {"client": "Client", "product": "Product", "open": "Open source"}
REQUIRED = ("id", "name", "kind", "tagline")
MAX_FEATURED = 6


def load() -> list[dict]:
    projects = json.loads(DATA.read_text(encoding="utf-8"))["projects"]
    errors = []
    seen = set()
    for i, p in enumerate(projects):
        where = p.get("id") or f"entry {i}"
        for key in REQUIRED:
            if not p.get(key):
                errors.append(f"{where}: missing '{key}'")
        if p.get("kind") not in KINDS:
            errors.append(f"{where}: kind must be one of {', '.join(KINDS)}")
        if p.get("id") in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(p.get("id"))
        for key in ("live", "repo"):
            url = p.get(key)
            if url and not url.startswith("https://"):
                errors.append(f"{where}: {key} must start with https://")
    featured = [p for p in projects if p.get("featured") and not p.get("hidden")]
    if len(featured) > MAX_FEATURED:
        errors.append(f"{len(featured)} featured projects; keep it to {MAX_FEATURED}")
    if errors:
        sys.exit("portfolio.json problems:\n  " + "\n  ".join(errors))
    return [p for p in projects if not p.get("hidden")]


def links(p: dict) -> str:
    out = []
    if p.get("live"):
        out.append(
            f'<a class="pf-link pf-link--live" href="{escape(p["live"])}" '
            f'target="_blank" rel="noopener">Live site ↗</a>'
        )
    if p.get("repo"):
        out.append(
            f'<a class="pf-link" href="{escape(p["repo"])}" '
            f'target="_blank" rel="noopener">Code on GitHub ↗</a>'
        )
    if not out:
        return ""
    return f'<div class="pf-links">{"".join(out)}</div>'


def card(p: dict, full: bool) -> str:
    parts = [
        f'<article class="pf-card" id="{escape(p["id"])}">',
        '<div class="pf-meta">',
        f'<span class="pf-kind pf-kind--{p["kind"]}">{KIND_LABEL[p["kind"]]}</span>',
    ]
    if p.get("status") and p["status"].lower() != KIND_LABEL[p["kind"]].lower():
        parts.append(f'<span class="pf-status">{escape(p["status"])}</span>')
    parts.append("</div>")
    parts.append(f'<h3>{escape(p["name"])}</h3>')
    if p.get("partner"):
        parts.append(f'<p class="pf-partner">With {escape(p["partner"])}</p>')
    parts.append(f'<p class="pf-tagline">{escape(p["tagline"])}</p>')
    if full and p.get("description"):
        parts.append(f'<p class="pf-desc">{escape(p["description"])}</p>')
    if full and p.get("stack"):
        chips = "".join(f"<li>{escape(s)}</li>" for s in p["stack"])
        parts.append(f'<ul class="pf-stack">{chips}</ul>')
    parts.append(links(p))
    parts.append("</article>")
    return "\n".join(x for x in parts if x)


def featured_html(projects: list[dict]) -> str:
    cards = "\n".join(card(p, full=False) for p in projects if p.get("featured"))
    return (
        '<section class="why-ito-section pf-section">\n'
        '<div class="pf-heading"><h2>Selected work</h2>'
        '<a class="pf-all" href="/projects/">All projects →</a></div>\n'
        f'<div class="pf-grid">\n{cards}\n</div>\n</section>'
    )


def portfolio_html(projects: list[dict]) -> str:
    n_open = sum(1 for p in projects if p.get("repo"))
    n_live = sum(1 for p in projects if p.get("live"))
    jump = " · ".join(
        f'<a href="#{k}-work">{title}</a>' for k, (title, _) in KINDS.items()
    )
    out = [
        '<section class="why-ito-section pf-section">',
        f'<p class="pf-summary">{len(projects)} projects · {n_live} live · '
        f'{n_open} with public code &nbsp;|&nbsp; {jump}</p>',
    ]
    for kind, (title, blurb) in KINDS.items():
        group = [p for p in projects if p["kind"] == kind]
        if not group:
            continue
        cards = "\n".join(card(p, full=True) for p in group)
        out.append(
            f'<div class="pf-group" id="{kind}-work">'
            f'<div class="pf-heading"><h2>{title}</h2></div>'
            f'<p class="pf-blurb">{blurb}</p>'
            f'<div class="pf-grid">\n{cards}\n</div></div>'
        )
    out.append("</section>")
    return "\n".join(out)


def inject(path: Path, marker: str, html: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"(<!-- {marker}:START -->).*?(<!-- {marker}:END -->)", re.DOTALL
    )
    if not pattern.search(text):
        sys.exit(f"{path.relative_to(ROOT)}: missing <!-- {marker}:START/END --> markers")
    text = pattern.sub(lambda m: f"{m.group(1)}\n{html}\n{m.group(2)}", text)
    path.write_text(text, encoding="utf-8")
    print(f"updated {path.relative_to(ROOT)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="validate only")
    args = ap.parse_args()
    projects = load()
    if args.check:
        print(f"ok: {len(projects)} published projects")
        return
    inject(HOME, "FEATURED", featured_html(projects))
    inject(PROJECTS, "PORTFOLIO", portfolio_html(projects))


if __name__ == "__main__":
    main()
