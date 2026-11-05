import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import pixelart  # noqa: E402

ART_DIR = REPO_ROOT / "art"
STATIC_ART_DIR = REPO_ROOT / "static" / "art"


class TestParseArt(unittest.TestCase):
    def test_ragged_rows(self):
        text = "A = #ff0000\n\nAA\nA\n"
        with self.assertRaises(ValueError) as ctx:
            pixelart.parse_art(text)
        self.assertIn("row 2", str(ctx.exception))

    def test_unknown_char(self):
        text = "A = #ff0000\n\nAZ\n"
        with self.assertRaises(ValueError) as ctx:
            pixelart.parse_art(text)
        self.assertIn("'Z'", str(ctx.exception))


class TestRenderSvg(unittest.TestCase):
    def test_run_merging(self):
        text = "A = #ff0000\nB = #00ff00\n\nAAB\n"
        art = pixelart.parse_art(text)
        svg = pixelart.render_svg(art, "test")
        self.assertEqual(svg.count("<rect"), 2)
        first_rect = svg.split("<rect", 2)[1]
        self.assertIn('width="2"', first_rect)

    def test_glow_only_when_used(self):
        no_glow = pixelart.render_svg(
            pixelart.parse_art("A = #ff0000\n\nA\n"), "no-glow"
        )
        self.assertNotIn("feGaussianBlur", no_glow)

        with_glow = pixelart.render_svg(
            pixelart.parse_art("A = #ff0000 glow\n\nA\n"), "with-glow"
        )
        self.assertIn("feGaussianBlur", with_glow)

    def test_transparent(self):
        svg = pixelart.render_svg(pixelart.parse_art("A = #ff0000\n\n.A\n"), "t")
        self.assertEqual(svg.count("<rect"), 1)

    def test_svg_has_viewbox_and_title(self):
        art = pixelart.parse_art("A = #ff0000\n\nAAA\nAAA\n")
        svg = pixelart.render_svg(art, "my-title")
        self.assertIn('viewBox="0 0 3 2"', svg)
        self.assertIn('shape-rendering="crispEdges"', svg)
        self.assertIn('role="img"', svg)
        self.assertIn("<title>my-title</title>", svg)


class TestGeneratedArt(unittest.TestCase):
    def test_generated_files_current(self):
        art_files = sorted(ART_DIR.glob("*.txt"))
        self.assertTrue(art_files, "no art source files found")
        for path in art_files:
            with self.subTest(file=path.name):
                art = pixelart.parse_art(path.read_text())
                expected = pixelart.render_svg(art, path.stem)
                actual_path = STATIC_ART_DIR / f"{path.stem}.svg"
                self.assertTrue(actual_path.is_file(), f"missing {actual_path}")
                self.assertEqual(actual_path.read_text(), expected)

    def test_art_sizes(self):
        sizes = {
            "hero-workbench": (224, 72),
            "davlog": (64, 40),
            "fussel": (64, 40),
            "ticktick-to-todoist-migrator": (64, 40),
        }
        for stem, (width, height) in sizes.items():
            with self.subTest(stem=stem):
                art = pixelart.parse_art((ART_DIR / f"{stem}.txt").read_text())
                self.assertEqual(len(art.rows[0]), width)
                self.assertEqual(len(art.rows), height)


if __name__ == "__main__":
    unittest.main()
