#!/usr/bin/env python3
"""One-off: migrates Jekyll content (_posts/, about.md, projects/*) into
Zola's content/ directory, converting Liquid tags and front matter.

Run manually, once:
    python3 scripts/migrate_jekyll.py
"""
from __future__ import annotations

import datetime
import json
import pathlib
import re

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_HIGHLIGHT_RE = re.compile(
    r"\{%\s*highlight\s+(\S+?)(?:\s+\$)?\s*%?\}(.*?)\{%\s*endhighlight\s*%\}",
    re.DOTALL,
)
_IAL_RE = re.compile(r"^\{:[^\n]*\}\n?", re.MULTILINE)
_SITE_URL_RE = re.compile(r"\{\{\s*site\.url\s*\}\}")
_DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-")


def convert_highlights(body: str) -> str:
    """Replaces every {% highlight LANG %}...{% endhighlight %} block
    (including the malformed 'LANG $' form and single-line blocks) with
    a fenced code block."""

    def _replace(match: re.Match) -> str:
        lang = match.group(1)
        code = match.group(2).strip("\n")
        return f"\n```{lang}\n{code}\n```\n"

    return _HIGHLIGHT_RE.sub(_replace, body)


def strip_kramdown_ial(body: str) -> str:
    """Removes lines that consist only of a kramdown inline attribute
    list, e.g. '{: .styled-table}'."""
    return _IAL_RE.sub("", body)


def replace_site_url(body: str) -> str:
    """Replaces {{ site.url }} with an empty string, turning
    '{{ site.url }}/path' into the root-relative '/path'."""
    return _SITE_URL_RE.sub("", body)


def _date_str(meta: dict, filename: str) -> str | None:
    """Returns the post's date as 'YYYY-MM-DD', from front matter or the
    filename's date prefix. Returns None for pages that have neither
    (e.g. about.md, project pages), which Zola does not require a date
    for."""
    raw_date = meta.get("date")
    if raw_date:
        if isinstance(raw_date, (datetime.date, datetime.datetime)):
            return raw_date.strftime("%Y-%m-%d")
        return str(raw_date)[:10]
    match = _DATE_PREFIX_RE.match(filename)
    if match:
        return match.group(1)
    return None


def to_zola_front_matter(meta: dict, filename: str) -> str:
    """Builds a Zola TOML front-matter block (without the +++ fences)
    from Jekyll front matter, dropping fields Zola doesn't use."""
    lines = [f"title = {json.dumps(meta.get('title', ''))}"]
    date_str = _date_str(meta, filename)
    if date_str:
        lines.append(f"date = {date_str}")

    description = meta.get("description")
    if description:
        lines.append(f"description = {json.dumps(description)}")

    if meta.get("published") is False:
        lines.append("draft = true")

    tags = meta.get("tags") or []
    if tags:
        lines.append("[taxonomies]")
        lines.append(f"tags = {json.dumps(list(tags))}")

    categories = meta.get("categories") or []
    if categories:
        lines.append("[extra]")
        lines.append(f"categories = {json.dumps(list(categories))}")

    return "\n".join(lines) + "\n"


def _split_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return meta, body


def migrate_file(src: pathlib.Path, dest_dir: pathlib.Path) -> pathlib.Path:
    """Migrates one Jekyll content file into dest_dir, returning the
    path written."""
    meta, body = _split_front_matter(src.read_text())

    body = strip_kramdown_ial(body)
    body = convert_highlights(body)
    body = replace_site_url(body)

    front_matter = to_zola_front_matter(meta, src.name)

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{src.stem}.md"
    dest.write_text(f"+++\n{front_matter}+++\n\n{body}")
    return dest


def main() -> None:
    posts_dir = REPO_ROOT / "content" / "posts"
    for src in sorted((REPO_ROOT / "_posts").iterdir()):
        if src.is_file():
            migrate_file(src, posts_dir)

    migrate_file(REPO_ROOT / "about.md", REPO_ROOT / "content")

    projects_dir = REPO_ROOT / "content" / "projects"
    migrated = migrate_file(REPO_ROOT / "projects" / "workviz" / "index.html", projects_dir)
    migrated.rename(projects_dir / "workviz.md")
    migrated = migrate_file(
        REPO_ROOT / "projects" / "omega-editor-theme" / "index.html", projects_dir
    )
    migrated.rename(projects_dir / "omega-editor-theme.md")


if __name__ == "__main__":
    main()
