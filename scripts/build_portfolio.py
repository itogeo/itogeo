"""Build the portfolio sections of the site from data/portfolio.json.

The site is a single page. This writes static HTML (readable by search
engines) between marker comments in index.html:

    <!-- SPOTLIGHT:START --> ... <!-- SPOTLIGHT:END -->   big sections with live maps
    <!-- FEATURED:START -->  ... <!-- FEATURED:END -->    the "More work" cards

A project with a "spotlight" block gets a large section with its live site
embedded as an inset, rendered at desktop size (1280x800) and scaled down to fit. Set "home": false inside a spotlight to show
that project as a card instead. The inset ignores scrolling until clicked, so it never
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

KINDS = {
    "client": ("Client work", "Maps and analysis built with partners."),
    "product": ("Products", "Things I build and run myself."),
    "open": ("Open source & free tools", "Free to use, fork, and improve."),
}
KIND_LABEL = {"client": "Client work", "product": "Product", "open": "Open source"}
QUIET_STATUS = {"live", "open source"}  # already obvious from the buttons


def meta_line(p: dict, with_kind: bool = True) -> str:
    bits = [KIND_LABEL[p["kind"]]] if with_kind else []
    status = (p.get("status") or "").strip()
    if status and status.lower() not in QUIET_STATUS:
        bits.append(status)
    if not bits:
        return ""
    return f'<p class="pf-meta">{escape(" — ".join(bits))}</p>'
REQUIRED = ("id", "name", "kind", "tagline")
MAX_FEATURED = 6


def on_home(p: dict) -> bool:
    sp = p.get("spotlight")
    return bool(sp) and sp.get("home", True)


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
        for key in ("live", "repo"):
            url = p.get(key)
            if url and not url.startswith("https://"):
                errors.append(f"{where}: {key} must start with https://")
    featured = [
        p for p in projects
        if p.get("featured") and not p.get("hidden") and not on_home(p)
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
    ]
    parts.append(f'<h3>{escape(p["name"])}</h3>')
    parts.append(f'<p class="pf-tagline">{escape(p["tagline"])}</p>')
    if full and p.get("description"):
        parts.append(f'<p class="pf-desc">{escape(p["description"])}</p>')
    parts.append(links(p))
    parts.append("</article>")
    return "\n".join(x for x in parts if x)


INSET_SCRIPT = """<script>
(function () {
  // Each inset renders its site at desktop size (1280x800) and shrinks it to fit.
  var frames = document.querySelectorAll('.sp-frame');
  function fit() {
    frames.forEach(function (f) { f.style.setProperty('--sp-fit', f.clientWidth / 1280); });
  }
  fit();
  window.addEventListener('resize', fit);
  if (window.ResizeObserver) { var ro = new ResizeObserver(fit); frames.forEach(function (f) { ro.observe(f); }); }
})();
document.querySelectorAll('.sp-inset').forEach(function (inset) {
  var btn = inset.querySelector('.sp-activate');
  if (!btn) return;
  btn.addEventListener('click', function () {
    // Too small to use in place on a phone: open the real site instead.
    if (inset.clientWidth < 560) { var link = inset.querySelector('figcaption a'); if (link) window.open(link.href, '_blank', 'noopener'); return; }
    inset.classList.add('is-live');
  });
  inset.addEventListener('mouseleave', function () { inset.classList.remove('is-live'); });
});
</script>"""


def spotlight(p: dict, index: int) -> str:
    sp = p["spotlight"]
    host = re.sub(r"^https://", "", p.get("live") or sp["embed"]).split("/")[0]
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
    return f"""<section class="sp{flip}" id="spotlight-{escape(p['id'])}">
<div class="sp-text">
<h2 class="sp-name">{escape(p['name'])}</h2>
<p class="sp-headline">{escape(sp.get('headline') or p['tagline'])}</p>
<div class="sp-actions">{''.join(buttons)}</div>
</div>
<figure class="sp-inset">
<div class="sp-frame">
<iframe src="{escape(sp['embed'])}" title="{escape(p['name'])} live map" loading="lazy" allow="fullscreen"></iframe>
<button class="sp-activate" type="button" aria-label="Use the {escape(p['name'])} map"></button>
</div>
<figcaption><a href="{escape(p.get('live') or sp['embed'])}" target="_blank" rel="noopener">{escape(host)} ↗</a><span>Live — click the map to pan and zoom</span></figcaption>
</figure>
</section>"""


def spotlight_html(projects: list[dict], home: bool) -> str:
    items = [p for p in projects if (on_home(p) if home else p.get("spotlight"))]
    if not items:
        return ""
    body = "\n".join(spotlight(p, i) for i, p in enumerate(items))
    return f'<div class="sp-wrap">\n{body}\n</div>\n{INSET_SCRIPT}'


def featured_html(projects: list[dict]) -> str:
    cards = "\n".join(
        card(p, full=False)
        for p in projects
        if p.get("featured") and not on_home(p)
    )
    return (
        '<section class="why-ito-section pf-section">\n'
        '<div class="pf-heading"><h2>Work</h2></div>\n'
        f'<div class="pf-grid">\n{cards}\n</div>\n</section>'
    )


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
    inject(HOME, "SPOTLIGHT", spotlight_html(projects, home=True))
    inject(HOME, "FEATURED", featured_html(projects))


if __name__ == "__main__":
    main()
