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


def html_pages() -> list[pathlib.Path]:
    """Every built .html file under public/."""
    return sorted(PUBLIC.rglob("*.html"))


class _ClassContentExtractor(HTMLParser):
    """Collects the inner HTML (as text events) of every element whose
    class attribute contains the target class name."""

    def __init__(self, target_class: str) -> None:
        super().__init__()
        self.target_class = target_class
        self.depth: int | None = None
        self.cursor = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        classes = (attr_dict.get("class") or "").split()
        if self.depth is not None:
            self.cursor += 1
        elif self.target_class in classes:
            self.depth = 0
            self.cursor = 1

    def handle_endtag(self, tag: str) -> None:
        if self.depth is not None:
            self.cursor -= 1
            if self.cursor == 0:
                self.depth = None

    def handle_data(self, data: str) -> None:
        if self.depth is not None:
            self.parts.append(data)


def article_text(page_html: str) -> str:
    """Visible text inside the element with class 'post-body', with
    whitespace collapsed to single spaces."""
    parser = _ClassContentExtractor("post-body")
    parser.feed(page_html)
    text = "".join(parser.parts)
    return re.sub(r"\s+", " ", text).strip()


def normalize(text: str) -> list[str]:
    """Lowercased word list with punctuation stripped and HTML entities
    decoded."""
    decoded = html.unescape(text).lower()
    return re.findall(r"[a-z0-9']+", decoded)


def load_fixture(name: str):
    """Loads a fixture from tests/fixtures/ by filename. JSON files are
    parsed; anything else is returned as text."""
    path = FIXTURES / name
    if path.suffix == ".json":
        return json.loads(path.read_text())
    return path.read_text()
