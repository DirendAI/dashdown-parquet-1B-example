#!/usr/bin/env python3
"""Inject SEO metadata into a built Dashdown site.

Dashdown's page template emits only <title> and a favicon — no meta
description, no Open Graph / Twitter Card tags, no canonical URL, and the
build produces no sitemap.xml or robots.txt. Like inject_posthog.py, this
fills the gap as a post-build step: walk the static export, insert the tags
before each page's </head>, and drop sitemap.xml + robots.txt at the root.

Config comes from env vars (set by the workflow):
  SITE_URL  Absolute base URL of the deployed site, WITHOUT a trailing slash
            (e.g. https://direndai.github.io/dashdown-parquet-1B-example).

If SITE_URL is unset/empty the script is a no-op, so local `dashdown build`
runs never break.

Per-page title/description come from the source page's frontmatter
(`pages/<route>.md` — Dashdown renders each route to <route>/index.html).
If assets/social-card.png exists in the repo it's copied into the site root
and referenced as the og:image, which is what makes links unfurl with a
proper card on Slack / X / LinkedIn / HN.
"""

import html
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PAGES_DIR = REPO_ROOT / "pages"
SOCIAL_CARD = REPO_ROOT / "assets" / "social-card.png"

META_TEMPLATE = """<!-- SEO metadata (injected at build time) -->
{tags}
"""


def page_frontmatter(route: str) -> dict:
    """Frontmatter of the source page for a built route ('' = root)."""
    candidates = [
        PAGES_DIR / (route or "index") / "index.md",
        PAGES_DIR / f"{route or 'index'}.md",
    ]
    for md in candidates:
        if not md.is_file():
            continue
        text = md.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        if m:
            try:
                fm = yaml.safe_load(m.group(1))
                if isinstance(fm, dict):
                    return fm
            except yaml.YAMLError:
                pass
    return {}


def site_name() -> str:
    cfg = REPO_ROOT / "dashdown.yaml"
    if cfg.is_file():
        try:
            data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("title"):
                return str(data["title"])
        except yaml.YAMLError:
            pass
    return "Dashdown"


def meta_tags(*, title: str, description: str, url: str, name: str, image: str | None) -> str:
    e = html.escape
    lines = []
    if description:
        lines.append(f'<meta name="description" content="{e(description)}">')
    lines += [
        f'<link rel="canonical" href="{e(url)}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{e(name)}">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:url" content="{e(url)}">',
    ]
    if description:
        lines.append(f'<meta property="og:description" content="{e(description)}">')
    if image:
        lines += [
            f'<meta property="og:image" content="{e(image)}">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:image" content="{e(image)}">',
        ]
    else:
        lines.append('<meta name="twitter:card" content="summary">')
    lines.append(f'<meta name="twitter:title" content="{e(title)}">')
    if description:
        lines.append(f'<meta name="twitter:description" content="{e(description)}">')
    return "\n".join(lines) + "\n"


def json_ld(*, name: str, description: str, site_url: str) -> str:
    """WebSite + Dataset structured data for the root page (Google Dataset Search)."""
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "name": name,
                "url": f"{site_url}/",
                "description": description,
            },
            {
                "@type": "Dataset",
                "name": "NYC taxi & ride-hail trips (TLC Trip Record Data), 2020–present",
                "description": (
                    "Every NYC yellow-cab, green-cab, Uber and Lyft trip since "
                    "January 2020 — about 1.6 billion rows of NYC TLC trip record "
                    "data, aggregated by DuckDB from the raw Parquet files and "
                    "visualized as an interactive dashboard, rebuilt nightly."
                ),
                "url": f"{site_url}/",
                "creator": {
                    "@type": "Organization",
                    "name": "NYC Taxi & Limousine Commission",
                    "url": "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page",
                },
                "isBasedOn": "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page",
                "temporalCoverage": "2020-01/..",
                "spatialCoverage": "New York City",
            },
        ],
    }
    payload = json.dumps(graph, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{payload}\n</script>\n'


def main() -> int:
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    site_url = os.environ.get("SITE_URL", "").strip().rstrip("/")

    if not site_url:
        print("SITE_URL not set — skipping SEO injection.")
        return 0

    name = site_name()
    image_url = None
    if SOCIAL_CARD.is_file():
        shutil.copyfile(SOCIAL_CARD, dist / "social-card.png")
        image_url = f"{site_url}/social-card.png"

    pages = sorted(p for p in dist.rglob("index.html") if "_dashdown" not in p.parts)
    urls = []
    injected = 0
    for page in pages:
        route = page.parent.relative_to(dist).as_posix()
        route = "" if route == "." else route
        url = f"{site_url}/{route}/" if route else f"{site_url}/"
        urls.append(url)

        html_text = page.read_text(encoding="utf-8")
        if 'property="og:title"' in html_text:  # idempotent — don't double-inject
            continue
        if "</head>" not in html_text:
            continue

        fm = page_frontmatter(route)
        title = str(fm.get("title") or "") or name
        description = " ".join(str(fm.get("description") or "").split())

        block = meta_tags(title=title, description=description, url=url, name=name, image=image_url)
        if not route:  # structured data only on the home page
            block += json_ld(name=name, description=description, site_url=site_url)
        page.write_text(
            html_text.replace("</head>", META_TEMPLATE.format(tags=block) + "</head>", 1),
            encoding="utf-8",
        )
        injected += 1

    today = datetime.now(timezone.utc).date().isoformat()
    entries = "\n".join(
        f"  <url>\n    <loc>{html.escape(u)}</loc>\n    <lastmod>{today}</lastmod>\n  </url>"
        for u in urls
    )
    (dist / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n</urlset>\n",
        encoding="utf-8",
    )
    (dist / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {site_url}/sitemap.xml\n",
        encoding="utf-8",
    )

    print(
        f"Injected SEO meta into {injected}/{len(pages)} page(s); "
        f"wrote sitemap.xml ({len(urls)} URL(s)) + robots.txt"
        + (" + social-card.png" if image_url else "")
        + f" for {site_url}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
