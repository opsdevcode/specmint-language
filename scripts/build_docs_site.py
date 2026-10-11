#!/usr/bin/env python3
"""Build the public Mint language site from markdown in this repository."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import sys
import tomllib
from pathlib import Path

CANONICAL_SITE_URL = "https://mint.opsdevco.de/"
FALLBACK_SITE_URL = "https://opsdevcode.github.io/specmint-language/"
RELEASES_URL = "https://github.com/opsdevcode/specmint-language/releases"
PRODUCT_URL = "https://opsdevco.de/products/mint"

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_FENCE = re.compile(r"^```(\w+)?\s*$")
_UL = re.compile(r"^[-*]\s+(.*)$")
_OL = re.compile(r"^(\d+)\.\s+(.*)$")
_TABLE_ROW = re.compile(r"^\|(.+)\|$")
_TABLE_SEP = re.compile(r"^\|[\s:|-]+\|$")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")

NAV: tuple[tuple[str, str], ...] = (
    ("", "Mint"),
    ("docs", "Docs"),
    ("docs/quickstart", "Quickstart"),
    ("language", "Language"),
    ("integrations", "Integrations"),
    ("downloads", "Downloads"),
    ("community", "Community"),
    ("playground", "Playground"),
    ("platform", "Platform"),
)

PUBLIC_ROUTES: tuple[tuple[str, str], ...] = (
    ("", "docs/site/home.md"),
    ("docs", "docs/index.md"),
    ("docs/quickstart", "docs/quickstart.md"),
    ("language", "docs/site/language.md"),
    ("integrations", "docs/site/integrations.md"),
    ("integrations/build", "docs/build-an-integration.md"),
    ("downloads", "docs/site/downloads.md"),
    ("community", "docs/community.md"),
    ("playground", "docs/site/playground.md"),
    ("platform", "docs/site/platform.md"),
)

OBSOLETE_REDIRECTS: tuple[tuple[str, str], ...] = (
    ("docs/quickstart.html", "docs/quickstart"),
    ("docs/community.html", "community"),
    ("docs/build-an-integration.html", "integrations/build"),
    ("docs/releases.html", "downloads"),
    ("docs/site/home.html", ""),
    ("docs/site/language.html", "language"),
    ("docs/site/integrations.html", "integrations"),
    ("docs/site/downloads.html", "downloads"),
    ("docs/site/playground.html", "playground"),
    ("docs/site/platform.html", "platform"),
)


def _html_name(relative: Path) -> Path:
    if relative.name.lower() == "readme.md":
        return relative.with_name("index.html")
    if relative.suffix.lower() == ".md":
        return relative.with_suffix(".html")
    return relative


def _route_file(route: str) -> Path:
    return Path(route) / "index.html" if route else Path("index.html")


def _relpath(from_file: Path, to_file: Path) -> str:
    return Path(os.path.relpath(to_file, start=from_file.parent)).as_posix()


def _canonical(route: str) -> str:
    if not route:
        return CANONICAL_SITE_URL
    return CANONICAL_SITE_URL + route.strip("/") + "/"


def _md_to_route() -> dict[str, str]:
    return {source: route for route, source in PUBLIC_ROUTES}


def _rewrite_href(
    target: str,
    *,
    repo: Path,
    source: Path,
    output_file: Path,
) -> str:
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return target
    path, _, frag = target.partition("#")
    if not path:
        return target
    dest_md = (source.parent / path).resolve()
    try:
        rel_md = dest_md.relative_to(repo.resolve())
    except ValueError:
        rewritten = Path(path)
        if rewritten.suffix.lower() == ".md" or rewritten.name.lower() == "readme.md":
            rewritten = _html_name(rewritten)
        href = rewritten.as_posix()
        return f"{href}#{frag}" if frag else href
    posix = rel_md.as_posix()
    route = _md_to_route().get(posix)
    to_file = _route_file(route) if route is not None else _html_name(rel_md)
    href = _relpath(output_file, to_file)
    if frag:
        href = f"{href}#{frag}"
    return href


def _inline(
    text: str,
    *,
    repo: Path,
    source: Path,
    output_file: Path,
) -> str:
    escaped = html.escape(text)

    def link(match: re.Match[str]) -> str:
        label = match.group(1)
        href = _rewrite_href(
            html.unescape(match.group(2)),
            repo=repo,
            source=source,
            output_file=output_file,
        )
        return f'<a href="{html.escape(href, quote=True)}">{label}</a>'

    escaped = _LINK.sub(link, escaped)
    escaped = _BOLD.sub(r"<strong>\1</strong>", escaped)
    return _INLINE_CODE.sub(r"<code>\1</code>", escaped)


def _flush_list(kind: str | None, items: list[str], out: list[str]) -> None:
    if not kind or not items:
        items.clear()
        return
    tag = "ul" if kind == "ul" else "ol"
    out.append(f"<{tag}>")
    out.extend(items)
    out.append(f"</{tag}>")
    items.clear()


def markdown_to_html(
    markdown: str,
    *,
    repo: Path,
    source: Path,
    output_file: Path,
) -> str:
    lines = markdown.splitlines()
    body: list[str] = []
    list_kind: str | None = None
    list_items: list[str] = []
    in_fence = False
    fence: list[str] = []
    para: list[str] = []
    table: list[list[str]] = []

    def inline(text: str) -> str:
        return _inline(text, repo=repo, source=source, output_file=output_file)

    def flush_para() -> None:
        if para:
            body.append("<p>" + " ".join(inline(part) for part in para) + "</p>")
            para.clear()

    def flush_table() -> None:
        if not table:
            return
        header, *rows = table
        body.append("<table><thead><tr>")
        body.extend(f"<th>{inline(cell)}</th>" for cell in header)
        body.append("</tr></thead><tbody>")
        for row in rows:
            body.append("<tr>")
            body.extend(f"<td>{inline(cell)}</td>" for cell in row)
            body.append("</tr>")
        body.append("</tbody></table>")
        table.clear()

    def split_row(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    for raw in lines:
        line = raw.rstrip()
        if in_fence:
            if _FENCE.match(line):
                body.append("<pre><code>" + html.escape("\n".join(fence)) + "</code></pre>")
                fence.clear()
                in_fence = False
            else:
                fence.append(raw)
            continue
        if _FENCE.match(line):
            flush_para()
            _flush_list(list_kind, list_items, body)
            list_kind = None
            flush_table()
            in_fence = True
            continue
        if not line.strip():
            flush_para()
            _flush_list(list_kind, list_items, body)
            list_kind = None
            flush_table()
            continue
        heading = _HEADING.match(line)
        if heading:
            flush_para()
            _flush_list(list_kind, list_items, body)
            list_kind = None
            flush_table()
            level = len(heading.group(1))
            body.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            continue
        if _TABLE_ROW.match(line):
            flush_para()
            _flush_list(list_kind, list_items, body)
            list_kind = None
            if _TABLE_SEP.match(line):
                continue
            table.append(split_row(line))
            continue
        if table:
            flush_table()
        unordered = _UL.match(line)
        if unordered:
            flush_para()
            if list_kind != "ul":
                _flush_list(list_kind, list_items, body)
                list_kind = "ul"
            list_items.append(f"<li>{inline(unordered.group(1))}</li>")
            continue
        ordered = _OL.match(line)
        if ordered:
            flush_para()
            if list_kind != "ol":
                _flush_list(list_kind, list_items, body)
                list_kind = "ol"
            list_items.append(f"<li>{inline(ordered.group(2))}</li>")
            continue
        _flush_list(list_kind, list_items, body)
        list_kind = None
        para.append(line.strip())

    if in_fence:
        body.append("<pre><code>" + html.escape("\n".join(fence)) + "</code></pre>")
    flush_para()
    _flush_list(list_kind, list_items, body)
    flush_table()
    return "\n".join(body)


def _software_version(repo: Path) -> str:
    data = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _json_ld(repo: Path) -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "Mint",
        "alternateName": "specmint",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Linux, macOS, Windows",
        "softwareVersion": _software_version(repo),
        "softwareRequirements": "Python 3.12",
        "license": "https://www.apache.org/licenses/LICENSE-2.0",
        "url": CANONICAL_SITE_URL,
        "downloadUrl": RELEASES_URL,
        "isAccessibleForFree": True,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": (
            "Standalone specification language with an offline deterministic CLI, "
            "MintIR, and plan-first integrations. Public preview; not production-ready."
        ),
        "creator": {"@type": "Organization", "name": "OpsDevCode", "url": "https://opsdevco.de/"},
    }
    return (
        '<script type="application/ld+json">'
        + json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
        + "</script>"
    )


def _nav_html(output_file: Path) -> str:
    items: list[str] = []
    for route, label in NAV:
        href = _relpath(output_file, _route_file(route))
        items.append(f'<a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>')
    return '<nav class="nav">' + " ".join(items) + "</nav>"


def _first_paragraph(markdown: str) -> str:
    parts: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if not stripped:
            if parts:
                break
            continue
        parts.append(stripped)
    text = " ".join(parts)
    text = _LINK.sub(r"\1", text)
    text = text.replace("**", "").replace("`", "")
    return text[:240]


def page_html(
    *,
    title: str,
    canonical: str,
    description: str,
    body: str,
    output_file: Path,
    json_ld: str | None = None,
    redirect: str | None = None,
) -> str:
    og = html.escape(canonical, quote=True)
    extra = ""
    if redirect:
        extra += (
            f'  <meta http-equiv="refresh" content="0; url={html.escape(redirect, quote=True)}">\n'
        )
    if json_ld:
        extra += f"  {json_ld}\n"
    nav = _nav_html(output_file)
    fallback = html.escape(FALLBACK_SITE_URL, quote=True)
    product = html.escape(PRODUCT_URL, quote=True)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <link rel="canonical" href="{og}">
  <link rel="alternate" href="{fallback}">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(description, quote=True)}">
  <meta property="og:url" content="{og}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary">
{extra}  <style>
    :root {{ color-scheme: light dark; }}
    body {{
      margin: 0 auto;
      max-width: 48rem;
      padding: 1.5rem 1.25rem 3rem;
      font-family: ui-sans-serif, system-ui, sans-serif;
      line-height: 1.5;
    }}
    .nav {{ display: flex; flex-wrap: wrap; gap: 0.65rem 1rem; margin-bottom: 1.5rem; }}
    .banner {{ font-size: 0.95rem; color: #3f3f46; }}
    footer {{ margin-top: 2.5rem; font-size: 0.9rem; color: #3f3f46; }}
    a {{ color: #0b57d0; }}
    pre {{ overflow: auto; padding: 0.75rem; background: #f4f4f5; }}
    code {{ font-family: ui-monospace, SFMono-Regular, monospace; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d4d4d8; padding: 0.4rem 0.6rem; text-align: left; }}
  </style>
</head>
<body>
{nav}
{body}
<footer>
  <p>Apache-2.0. Public preview — not production-ready, not 1.0. No <code>mint apply</code>.</p>
  <p>Commercial funnel: <a href="{product}">opsdevco.de/products/mint</a>.
  Generated fallback: <a href="{fallback}">{FALLBACK_SITE_URL}</a>.</p>
</footer>
</body>
</html>
"""


def _title_from_markdown(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _write_markdown_page(
    source: Path,
    output: Path,
    *,
    repo: Path,
    canonical: str,
    json_ld: str | None = None,
) -> None:
    markdown = source.read_text(encoding="utf-8")
    title = _title_from_markdown(markdown, fallback=source.stem)
    description = _first_paragraph(markdown) or title
    body = markdown_to_html(markdown, repo=repo, source=source, output_file=output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        page_html(
            title=title,
            canonical=canonical,
            description=description,
            body=body,
            output_file=output,
            json_ld=json_ld,
        ),
        encoding="utf-8",
    )


def _write_redirect(output: Path, *, route: str) -> None:
    href = _relpath(output, _route_file(route))
    canonical = _canonical(route)
    title = "Moved"
    safe_href = html.escape(href, quote=True)
    body = f'<p>Moved to <a href="{safe_href}">{html.escape(canonical)}</a>.</p>'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        page_html(
            title=title,
            canonical=canonical,
            description="This path moved.",
            body=body,
            output_file=output,
            redirect=href,
        ),
        encoding="utf-8",
    )


def _write_robots(out: Path) -> None:
    (out / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {CANONICAL_SITE_URL}sitemap.xml\n"
        f"Host: mint.opsdevco.de\n",
        encoding="utf-8",
    )


def _write_sitemap(out: Path) -> None:
    urls = "\n".join(
        f"  <url><loc>{html.escape(_canonical(route))}</loc></url>" for route, _ in PUBLIC_ROUTES
    )
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>\n",
        encoding="utf-8",
    )


def _write_404(out: Path) -> None:
    output = out / "404.html"
    body = (
        "<h1>Not found</h1>"
        "<p>That path is not part of the Mint language site. "
        'Start at the <a href="index.html">home page</a> or the '
        '<a href="docs/quickstart/index.html">quickstart</a>.</p>'
    )
    output.write_text(
        page_html(
            title="Not found",
            canonical=CANONICAL_SITE_URL + "404.html",
            description="Mint language site — page not found.",
            body=body,
            output_file=output,
        ),
        encoding="utf-8",
    )


def build_docs_site(repo: Path, out: Path, *, emit_cname: bool = False) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / ".nojekyll").write_text("", encoding="utf-8")
    json_ld = _json_ld(repo)

    skip_prefixes = ("docs/site/",)

    roots = (repo / "docs", repo / "specification")
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(repo)
            posix = relative.as_posix()
            if posix.startswith(skip_prefixes) or posix == "docs/site/CNAME":
                continue
            dest = out / _html_name(relative)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix.lower() == ".md":
                canonical = CANONICAL_SITE_URL + _html_name(relative).as_posix()
                route = _md_to_route().get(posix)
                if route is not None:
                    canonical = _canonical(route)
                _write_markdown_page(path, dest, repo=repo, canonical=canonical)
            else:
                shutil.copy2(path, dest)

    for extra in (repo / "SECURITY.md", repo / "CONTRIBUTING.md"):
        dest = out / _html_name(Path(extra.name))
        canonical = CANONICAL_SITE_URL + dest.name
        _write_markdown_page(extra, dest, repo=repo, canonical=canonical)

    for route, source_rel in PUBLIC_ROUTES:
        source = repo / source_rel
        dest = out / _route_file(route)
        extra_ld = json_ld if route == "" else None
        _write_markdown_page(
            source,
            dest,
            repo=repo,
            canonical=_canonical(route),
            json_ld=extra_ld,
        )

    for obsolete, route in OBSOLETE_REDIRECTS:
        _write_redirect(out / obsolete, route=route)

    _write_robots(out)
    _write_sitemap(out)
    _write_404(out)

    if emit_cname:
        shutil.copy2(repo / "docs" / "site" / "CNAME", out / "CNAME")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("site"))
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--cname",
        action="store_true",
        help="Copy docs/site/CNAME into the artifact (only after mint.opsdevco.de returns 200)",
    )
    args = parser.parse_args(argv)
    build_docs_site(args.repo.resolve(), args.out.resolve(), emit_cname=args.cname)
    return 0


if __name__ == "__main__":
    sys.exit(main())
