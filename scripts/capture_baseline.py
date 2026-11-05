#!/usr/bin/env python3
"""One-off: captures a snapshot of the live benninger.ca site into
tests/fixtures/, so the Zola rebuild can be checked against it.

Run manually, once, before migrating content:
    python3 scripts/capture_baseline.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import urllib.request
from html.parser import HTMLParser

BASE_URL = "https://benninger.ca"
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"

sys.path.insert(0, str(REPO_ROOT / "tests"))
from helpers import normalize  # noqa: E402 (needs sys.path set first)

# Static files Jekyll copies verbatim; enumerated locally rather than
# crawled, since they are binary and already in the repo.
# Searched in order; the first that exists is used. Jekyll served these
# from the repo root; after the Zola migration they live under static/,
# which Zola publishes at the same root-relative URLs.
LOCAL_STATIC_DIR_CANDIDATES = ["images", "static/images"]
EXTRA_STATIC_FILES = [
    "/llms.txt",
    "/llms-full.txt",
    "/keybase.txt",
    "/favicon.ico",
    "/assets/img/html5-before.png",
    "/assets/img/html5-after.png",
    "/assets/template.tar.gz",
    "/assets/omega_v0.1.tar.gz",
]


def fetch(path: str) -> str:
    url = path if path.startswith("http") else BASE_URL + path
    with urllib.request.urlopen(url) as resp:  # noqa: S310 (fixed https host)
        return resp.read().decode("utf-8")


def sitemap_post_paths() -> list[str]:
    xml = fetch("/sitemap.xml")
    locs = re.findall(r"<loc>([^<]+)</loc>", xml)
    paths = []
    for loc in locs:
        path = loc.removeprefix(BASE_URL)
        if path.startswith("/posts/") and path.endswith("/"):
            paths.append(path)
    return paths


_VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class EntryContentExtractor(HTMLParser):
    """Pulls plain text and <pre> count out of the first element whose
    class attribute contains 'entry-content'. Tracks open tags on a
    stack so a stray/unmatched closing tag (the live posts have a few)
    doesn't end the capture early, the way a real browser's error
    recovery would ignore it instead of naive depth counting."""

    def __init__(self) -> None:
        super().__init__()
        self.capturing = False
        self._stack: list[str] = []
        self.text_parts: list[str] = []
        self.code_blocks = 0
        self.title: str | None = None
        self._in_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        classes = (attr_dict.get("class") or "").split()
        if tag == "title":
            self._in_title = True
        if not self.capturing and "entry-content" in classes:
            self.capturing = True
            self._stack = [tag]
            return
        if self.capturing:
            if tag == "pre":
                self.code_blocks += 1
            if tag not in _VOID_ELEMENTS:
                self._stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if not self.capturing or tag not in self._stack:
            return
        while self._stack and self._stack[-1] != tag:
            self._stack.pop()
        if self._stack:
            self._stack.pop()
        if not self._stack:
            self.capturing = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)
        if self.capturing:
            self.text_parts.append(data)

    def get_title(self) -> str:
        return "".join(self._title_parts).strip()


def capture_post(path: str) -> tuple[str, dict]:
    html = fetch(path)
    parser = EntryContentExtractor()
    parser.feed(html)
    slug = path.strip("/").removeprefix("posts/")
    words = normalize("".join(parser.text_parts))
    return slug, {
        "title": parser.get_title(),
        "words": words,
        "code_blocks": parser.code_blocks,
    }


def capture_feed_ids(path: str) -> list[str]:
    """Returns the <id> of each <entry>, in document order (skips the
    feed-level <id> that precedes the entries)."""
    xml = fetch(path)
    entries = re.findall(r"<entry>.*?</entry>", xml, re.DOTALL)
    ids = []
    for entry in entries:
        match = re.search(r"<id>([^<]*)</id>", entry)
        if match:
            ids.append(match.group(1))
    return ids


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)

    post_paths = sitemap_post_paths()

    urls: list[str] = []
    sitemap_xml = fetch("/sitemap.xml")
    for loc in re.findall(r"<loc>([^<]+)</loc>", sitemap_xml):
        urls.append(loc.removeprefix(BASE_URL) or "/")
    urls.extend(EXTRA_STATIC_FILES)
    images_dir = next(
        (REPO_ROOT / d for d in LOCAL_STATIC_DIR_CANDIDATES if (REPO_ROOT / d).is_dir()),
        None,
    )
    if images_dir is None:
        raise FileNotFoundError(
            f"none of {LOCAL_STATIC_DIR_CANDIDATES} exist under {REPO_ROOT}"
        )
    url_root = images_dir.relative_to(REPO_ROOT).parts[-1]  # "images", regardless of parent
    for f in sorted(images_dir.rglob("*")):
        if f.is_file():
            urls.append("/" + url_root + "/" + str(f.relative_to(images_dir)))
    (FIXTURES / "legacy-urls.txt").write_text("\n".join(urls) + "\n")

    posts = {}
    for path in post_paths:
        slug, data = capture_post(path)
        posts[slug] = data
    (FIXTURES / "legacy-posts.json").write_text(json.dumps(posts, indent=2, sort_keys=True))

    feeds = {
        "atom.xml": capture_feed_ids("/atom.xml"),
        "feed.xml": capture_feed_ids("/feed.xml"),
    }
    (FIXTURES / "legacy-feeds.json").write_text(json.dumps(feeds, indent=2))

    print(f"posts captured: {len(posts)}")
    print(f"atom.xml ids: {len(feeds['atom.xml'])}")
    print(f"feed.xml ids: {len(feeds['feed.xml'])}")


if __name__ == "__main__":
    main()
