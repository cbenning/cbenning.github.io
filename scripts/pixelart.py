#!/usr/bin/env python3
"""Renders text-grid pixel art (art/*.txt) to SVG (static/art/*.svg).

Art file format:
    <char> = #rrggbb[ glow]
    <char> = #rrggbb[ glow]
    ...
    <blank line>
    <grid row>
    <grid row>
    ...

One character per palette entry. '.' is always transparent. All grid
rows must be the same length.

Usage:
    python3 scripts/pixelart.py art static/art
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

_PALETTE_RE = re.compile(r"^(\S) = (#[0-9a-fA-F]{6})(?: (glow))?$")


@dataclass
class Color:
    hex: str
    glow: bool = False


@dataclass
class Art:
    palette: dict[str, Color]
    rows: list[str]


def parse_art(text: str) -> Art:
    lines = text.splitlines()

    palette: dict[str, Color] = {}
    i = 0
    while i < len(lines) and lines[i] != "":
        line = lines[i]
        match = _PALETTE_RE.match(line)
        if not match:
            raise ValueError(f"invalid palette line: {line!r}")
        char, hex_code, glow = match.groups()
        palette[char] = Color(hex=hex_code, glow=bool(glow))
        i += 1

    while i < len(lines) and lines[i] == "":
        i += 1

    rows = [line for line in lines[i:] if line != ""]
    if not rows:
        raise ValueError("no grid rows found")

    width = len(rows[0])
    for row_num, row in enumerate(rows, start=1):
        if len(row) != width:
            raise ValueError(
                f"ragged grid: row {row_num} has length {len(row)}, expected {width}"
            )
        for ch in row:
            if ch != "." and ch not in palette:
                raise ValueError(f"unknown character {ch!r} in row {row_num}")

    return Art(palette=palette, rows=rows)


def _runs(art: Art, include: "callable[[str], bool]") -> list[tuple[int, int, int, str]]:
    """Run-length encodes each row into (x, y, width, char) tuples,
    skipping '.' and any character include() rejects."""
    runs = []
    for y, row in enumerate(art.rows):
        x = 0
        while x < len(row):
            ch = row[x]
            if ch == "." or not include(ch):
                x += 1
                continue
            start = x
            while x < len(row) and row[x] == ch:
                x += 1
            runs.append((start, y, x - start, ch))
    return runs


def render_svg(art: Art, title: str) -> str:
    width = len(art.rows[0])
    height = len(art.rows)

    all_runs = _runs(art, lambda ch: True)
    glow_runs = _runs(art, lambda ch: art.palette[ch].glow)

    def rect(run: tuple[int, int, int, str]) -> str:
        x, y, w, ch = run
        return f'<rect x="{x}" y="{y}" width="{w}" height="1" fill="{art.palette[ch].hex}"/>'

    parts = [
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'shape-rendering="crispEdges" role="img">',
        f"<title>{title}</title>",
    ]
    if glow_runs:
        parts.append(
            '<defs><filter id="glow" x="-50%" y="-50%" width="200%" height="200%">'
            '<feGaussianBlur stdDeviation="1.2"/></filter></defs>'
        )
    parts.extend(rect(r) for r in all_runs)
    if glow_runs:
        parts.append('<g filter="url(#glow)">')
        parts.extend(rect(r) for r in glow_runs)
        parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: pixelart.py <art_dir> <output_dir>", file=sys.stderr)
        return 1
    art_dir, output_dir = Path(argv[0]), Path(argv[1])
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(art_dir.glob("*.txt")):
        art = parse_art(path.read_text())
        svg = render_svg(art, path.stem)
        (output_dir / f"{path.stem}.svg").write_text(svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
