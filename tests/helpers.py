"""Shared test helpers for checking the built Zola site in public/."""
from __future__ import annotations

import html
import json
import pathlib
import re
from html.parser import HTMLParser

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLIC = REPO_ROOT / "public"
FIXTURES = REPO_ROOT / "tests" / "fixtures"

# Elements with no closing tag; never pushed onto the open-tag stack.
_VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


def html_pages() -> list[pathlib.Path]:
    """Every built .html file under public/."""
    return sorted(PUBLIC.rglob("*.html"))


class _ClassScopedParser(HTMLParser):
    """Watches the element whose class attribute contains `target_class`,
    tracking open tags on a stack so a stray/unmatched closing tag
    (common in old hand-written HTML) doesn't end the capture early: an
    end tag only closes something if its name is actually on the stack,
    matching real browsers' error recovery instead of naive depth
    counting. Subclasses override `on_start`/`on_end`/`on_data`, called
    only while capturing is active."""

    def __init__(self, target_class: str) -> None:
        super().__init__()
        self.target_class = target_class
        self.capturing = False
        self._stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        classes = (attr_dict.get("class") or "").split()
        if not self.capturing and self.target_class in classes:
            self.capturing = True
            self._stack = [tag]
            return
        if self.capturing:
            self.on_start(tag)
            if tag not in _VOID_ELEMENTS:
                self._stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self.capturing or tag not in self._stack:
            return
        while self._stack and self._stack[-1] != tag:
            self._stack.pop()
        if self._stack:
            self._stack.pop()
        if not self._stack:
            self.capturing = False

    def handle_data(self, data: str) -> None:
        if self.capturing:
            self.on_data(data)

    def on_start(self, tag: str) -> None:
        pass

    def on_data(self, data: str) -> None:
        pass


class _TextCollector(_ClassScopedParser):
    def __init__(self, target_class: str) -> None:
        super().__init__(target_class)
        self.parts: list[str] = []

    def on_data(self, data: str) -> None:
        self.parts.append(data)


def article_text(page_html: str) -> str:
    """Visible text inside the element with class 'post-body', with
    whitespace collapsed to single spaces."""
    parser = _TextCollector("post-body")
    parser.feed(page_html)
    text = "".join(parser.parts)
    return re.sub(r"\s+", " ", text).strip()


class _TagCounter(_ClassScopedParser):
    def __init__(self, target_class: str, count_tag: str) -> None:
        super().__init__(target_class)
        self.count_tag = count_tag
        self.count = 0

    def on_start(self, tag: str) -> None:
        if tag == self.count_tag:
            self.count += 1


def count_pre_blocks(page_html: str) -> int:
    """Number of <pre> elements inside the element with class
    'post-body'."""
    parser = _TagCounter("post-body", "pre")
    parser.feed(page_html)
    return parser.count


def normalize(text: str) -> list[str]:
    """Lowercased word list with punctuation stripped and HTML entities
    decoded. Typographic (curly) quotes are folded to straight ones
    first, so e.g. "i’ve" and "i've" tokenize identically --
    kramdown and Zola differ on smart-quote rendering, but that's a
    punctuation-style difference, not a content difference."""
    decoded = html.unescape(text).lower()
    decoded = decoded.replace("’", "'").replace("‘", "'")
    return re.findall(r"[a-z0-9']+", decoded)


def load_fixture(name: str):
    """Loads a fixture from tests/fixtures/ by filename. JSON files are
    parsed; anything else is returned as text."""
    path = FIXTURES / name
    if path.suffix == ".json":
        return json.loads(path.read_text())
    return path.read_text()
