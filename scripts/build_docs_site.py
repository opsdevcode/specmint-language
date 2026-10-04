#!/usr/bin/env python3
"""Build the public Mint docs site from markdown in this repository."""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from pathlib import Path

CANONICAL_DOCS_URL = "https://opsdevcode.github.io/specmint-language/"
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_FENCE = re.compile(r"^```(\w+)?\s*$")
_UL = re.compile(r"^[-*]\s+(.*)$")
_OL = re.compile(r"^(\d+)\.\s+(.*)$")
_TABLE_ROW = re.compile(r"^\|(.+)\|$")
_TABLE_SEP = re.compile(r"^\|[\s:|-]+\|$")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")


def _html_name(relative: Path) -> Path:
    if relative.name.lower() == "readme.md":
        return relative.with_name("index.html")
    if relative.suffix.lower() == ".md":
        return relative.with_suffix(".html")
    return relative


def _rewrite_href(target: str, *, source: Path) -> str:
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return target
    path, _, frag = target.partition("#")
    dest = (source.parent / path).as_posix()
    if dest.startswith("./"):
        dest = dest[2:]
    rewritten = Path(dest)
    if rewritten.suffix.lower() == ".md" or rewritten.name.lower() == "readme.md":
        rewritten = _html_name(rewritten)
    href = rewritten.as_posix()
    if frag:
        href = f"{href}#{frag}"
    return href


def _inline(text: str, *, source: Path) -> str:
    escaped = html.escape(text)

    def link(match: re.Match[str]) -> str:
        label = match.group(1)
        href = _rewrite_href(html.unescape(match.group(2)), source=source)
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


def markdown_to_html(markdown: str, *, source: Path) -> str:
    lines = markdown.splitlines()
    body: list[str] = []
    list_kind: str | None = None
    list_items: list[str] = []
    in_fence = False
    fence: list[str] = []
    para: list[str] = []
    table: list[list[str]] = []

    def flush_para() -> None:
        if para:
            body.append("<p>" + " ".join(_inline(part, source=source) for part in para) + "</p>")
            para.clear()

    def flush_table() -> None:
        if not table:
            return
        header, *rows = table
        body.append("<table><thead><tr>")
        body.extend(f"<th>{_inline(cell, source=source)}</th>" for cell in header)
        body.append("</tr></thead><tbody>")
        for row in rows:
            body.append("<tr>")
            body.extend(f"<td>{_inline(cell, source=source)}</td>" for cell in row)
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
            body.append(f"<h{level}>{_inline(heading.group(2), source=source)}</h{level}>")
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
            list_items.append(f"<li>{_inline(unordered.group(1), source=source)}</li>")
            continue
        ordered = _OL.match(line)
        if ordered:
            flush_para()
            if list_kind != "ol":
                _flush_list(list_kind, list_items, body)
                list_kind = "ol"
            list_items.append(f"<li>{_inline(ordered.group(2), source=source)}</li>")
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


def page_html(*, title: str, canonical: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="canonical" href="{html.escape(canonical, quote=True)}">
  <style>
    :root {{ color-scheme: light dark; }}
    body {{
      margin: 0 auto;
      max-width: 48rem;
      padding: 1.5rem 1.25rem 3rem;
      font-family: ui-sans-serif, system-ui, sans-serif;
      line-height: 1.5;
    }}
    a {{ color: #0b57d0; }}
    pre {{ overflow: auto; padding: 0.75rem; background: #f4f4f5; }}
    code {{ font-family: ui-monospace, SFMono-Regular, monospace; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d4d4d8; padding: 0.4rem 0.6rem; text-align: left; }}
    .banner {{ font-size: 0.95rem; color: #3f3f46; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


def _title_from_markdown(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _write_markdown_page(source: Path, output: Path, *, canonical: str) -> None:
    markdown = source.read_text(encoding="utf-8")
    title = _title_from_markdown(markdown, fallback=source.stem)
    body = markdown_to_html(markdown, source=source)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page_html(title=title, canonical=canonical, body=body), encoding="utf-8")


def build_docs_site(repo: Path, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / ".nojekyll").write_text("", encoding="utf-8")

    roots = (repo / "docs", repo / "specification")
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(repo)
            dest = out / _html_name(relative)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix.lower() == ".md":
                canonical = CANONICAL_DOCS_URL + _html_name(relative).as_posix()
                _write_markdown_page(path, dest, canonical=canonical)
            else:
                shutil.copy2(path, dest)

    for extra in (repo / "SECURITY.md", repo / "CONTRIBUTING.md"):
        dest = out / _html_name(Path(extra.name))
        canonical = CANONICAL_DOCS_URL + dest.name
        _write_markdown_page(extra, dest, canonical=canonical)

    index_source = repo / "docs" / "index.md"
    markdown = index_source.read_text(encoding="utf-8")
    rewritten = (
        markdown.replace("](../specification/", "](specification/")
        .replace("](../SECURITY.md)", "](SECURITY.html)")
        .replace("](../CONTRIBUTING.md)", "](CONTRIBUTING.html)")
        .replace("](quickstart.md)", "](docs/quickstart.html)")
        .replace("](why-not-terraform.md)", "](docs/why-not-terraform.html)")
        .replace("](compatibility.md)", "](docs/compatibility.html)")
        .replace("](roadmap.md)", "](docs/roadmap.html)")
        .replace("](adr/", "](docs/adr/")
    )
    fake_source = Path("index.md")
    body = markdown_to_html(rewritten, source=fake_source)
    title = _title_from_markdown(markdown, fallback="Mint language")
    (out / "index.html").write_text(
        page_html(title=title, canonical=CANONICAL_DOCS_URL, body=body),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("site"))
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    build_docs_site(args.repo.resolve(), args.out.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
