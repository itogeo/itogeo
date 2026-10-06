"""Build the portfolio sections of the site from data/portfolio.json.

Writes static HTML (no JavaScript needed, readable by search engines) between
marker comments in two pages:

    index.html            <!-- SPOTLIGHT:START --> ... <!-- SPOTLIGHT:END -->
                          <!-- FEATURED:START --> ... <!-- FEATURED:END -->
    projects/index.html   <!-- SPOTLIGHT:START --> ... <!-- SPOTLIGHT:END -->
                          <!-- PORTFOLIO:START --> ... <!-- PORTFOLIO:END -->

A project with a "spotlight" block gets a large section with its live site
embedded as an inset. The inset ignores scrolling until clicked, so it never
hijacks the page.

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
        sp = p.get("spotlight")
        if sp:
            if not str(sp.get("embed", "")).startswith("https://"):
                errors.append(f"{where}: spotlight.embed must start with https://")
            if not 0.4 <= float(sp.get("scale", 1)) <= 1:
                errors.append(f"{where}: spotlight.scale must be between 0.4 and 1")
            if not sp.get("points"):
                errors.append(f"{where}: spotlight needs a list of points")
        for key in ("live", "repo"):
            url = p.get(key)
            if url and not url.startswith("https://"):
                errors.append(f"{where}: {key} must start with https://")
    featured = [
        p for p in projects
        if p.get("featured") and not p.get("hidden") and not p.get("spotlight")
    ]
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


INSET_SCRIPT = """<script>
document.querySelectorAll('.sp-inset').forEach(function (inset) {
  var btn = inset.querySelector('.sp-activate');
  if (!btn) return;
  btn.addEventListener('click', function () { inset.classList.add('is-live'); });
  inset.addEventListener('mouseleave', function () { inset.classList.remove('is-live'); });
});
</script>"""


def spotlight(p: dict, index: int) -> str:
    sp = p["spotlight"]
    host = re.sub(r"^https://", "", p.get("live") or sp["embed"]).rstrip("/")
    points = "".join(f"<li>{escape(x)}</li>" for x in sp["points"])
    cta = sp.get("cta") or {"label": f"Open {p['name']}", "href": p.get("live")}
    buttons = [
        f'<a class="btn" href="{escape(cta["href"])}"'
        + ("" if cta["href"].startswith("mailto:") else ' target="_blank" rel="noopener"')
        + f'>{escape(cta["label"])}</a>'
    ]
    if p.get("live") and cta["href"] != p["live"]:
        buttons.append(
            f'<a class="btn btn-outline" href="{escape(p["live"])}" '
            f'target="_blank" rel="noopener">Open the map ↗</a>'
        )
    if p.get("repo"):
        buttons.append(
            f'<a class="btn btn-outline" href="{escape(p["repo"])}" '
            f'target="_blank" rel="noopener">Code on GitHub ↗</a>'
        )
    flip = " sp--flip" if index % 2 else ""
    scale = float(sp.get("scale", 1))
    frame_style = f' style="--sp-scale: {scale}"' if scale != 1 else ""
    status = f'<span class="pf-status">{escape(p["status"])}</span>' if p.get("status") else ""
    return f"""<section class="sp{flip}" id="spotlight-{escape(p['id'])}">
<div class="sp-text">
<div class="pf-meta"><span class="pf-kind pf-kind--{p['kind']}">{KIND_LABEL[p['kind']]}</span>{status}</div>
<h2 class="sp-name">{escape(p['name'])}</h2>
<p class="sp-headline">{escape(sp.get('headline') or p['tagline'])}</p>
<ul class="sp-points">{points}</ul>
<div class="sp-actions">{''.join(buttons)}</div>
</div>
<div class="sp-inset">
<div class="sp-bar"><span></span><span></span><span></span><a href="{escape(p.get('live') or sp['embed'])}" target="_blank" rel="noopener">{escape(host)}</a></div>
<div class="sp-frame"{frame_style}>
<iframe src="{escape(sp['embed'])}" title="{escape(p['name'])} live map" loading="lazy" allow="fullscreen"></iframe>
<button class="sp-activate" type="button">Click to explore the live map</button>
</div>
</div>
</section>"""


def spotlight_html(projects: list[dict]) -> str:
    items = [p for p in projects if p.get("spotlight")]
    if not items:
        return ""
    body = "\n".join(spotlight(p, i) for i, p in enumerate(items))
    return f'<div class="sp-wrap">\n{body}\n</div>\n{INSET_SCRIPT}'


def featured_html(projects: list[dict]) -> str:
    cards = "\n".join(
        card(p, full=False)
        for p in projects
        if p.get("featured") and not p.get("spotlight")
    )
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
    spot = spotlight_html(projects)
    inject(HOME, "SPOTLIGHT", spot)
    inject(PROJECTS, "SPOTLIGHT", spot)
    inject(HOME, "FEATURED", featured_html(projects))
    inject(PROJECTS, "PORTFOLIO", portfolio_html(projects))


if __name__ == "__main__":
    main()
