import re
import unittest

from helpers import PUBLIC, REPO_ROOT, html_pages

TOKENS_PATH = REPO_ROOT / "sass" / "_tokens.scss"
STYLE_CSS = PUBLIC / "style.css"


def _relative_luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = lin(r), lin(g), lin(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(hex_a: str, hex_b: str) -> float:
    la, lb = _relative_luminance(hex_a), _relative_luminance(hex_b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def _load_tokens() -> dict[str, str]:
    text = TOKENS_PATH.read_text()
    return dict(re.findall(r"--([a-z-]+):\s*(#[0-9a-fA-F]{6})", text))


class TestColorContrast(unittest.TestCase):
    def test_contrast(self):
        tokens = _load_tokens()
        for name in ["text", "muted", "heading", "led"]:
            for background in ["bg", "panel"]:
                with self.subTest(name=name, background=background):
                    ratio = _contrast_ratio(tokens[name], tokens[background])
                    self.assertGreaterEqual(
                        ratio,
                        4.5,
                        f"--{name} on --{background}: contrast {ratio:.2f} below 4.5",
                    )


class TestImagesSized(unittest.TestCase):
    def test_images_have_explicit_dimensions(self):
        """Every <img> needs width and height attributes, so the
        browser reserves its space before the image loads instead of
        shifting the layout (found via a real Lighthouse CLS of 0.20
        on /projects/ before this was fixed)."""
        for page in html_pages():
            text = page.read_text()
            for match in re.finditer(r"<img\b[^>]*>", text):
                tag = match.group(0)
                with self.subTest(page=str(page.relative_to(PUBLIC)), tag=tag):
                    self.assertRegex(tag, r'\bwidth="\d+"')
                    self.assertRegex(tag, r'\bheight="\d+"')


class TestNoThirdParty(unittest.TestCase):
    def test_no_third_party(self):
        forbidden = ["fonts.googleapis", "fonts.gstatic", "cloudflareinsights", "disqus", "778-288-9371"]
        texts = [p.read_text() for p in html_pages()]
        if STYLE_CSS.is_file():
            texts.append(STYLE_CSS.read_text())
        for needle in forbidden:
            with self.subTest(needle=needle):
                self.assertFalse(
                    any(needle in text for text in texts), f"found forbidden string: {needle}"
                )


def _is_redirect_page(html: str) -> bool:
    return "<title>Redirect</title>" in html


class TestGoatCounter(unittest.TestCase):
    def test_goatcounter_everywhere(self):
        for page in html_pages():
            text = page.read_text()
            if _is_redirect_page(text):
                continue
            with self.subTest(page=str(page)):
                self.assertIn('data-goatcounter="https://benninger.goatcounter.com/count"', text)
                scripts = re.findall(r"<script\b[^>]*>", text)
                self.assertEqual(len(scripts), 1, f"expected exactly one <script>, got {scripts}")
                self.assertIn("goatcounter", scripts[0])


class TestNav(unittest.TestCase):
    def test_nav(self):
        for page in html_pages():
            text = page.read_text()
            if _is_redirect_page(text):
                continue
            with self.subTest(page=str(page)):
                self.assertIn('href="/"', text)
                self.assertIn('href="/projects/"', text)
                self.assertIn('href="/articles/"', text)
                self.assertNotIn('href="/cv/"', text)


class TestCss(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = STYLE_CSS.read_text()

    def test_css_overflow_rules(self):
        normalized = re.sub(r"\s+", "", self.css)
        self.assertIn("overflow-x:auto", normalized)
        pre_rule = re.search(r"pre\s*\{([^}]*)\}", self.css)
        self.assertIsNotNone(pre_rule, "no rule found for pre")
        self.assertIn("overflow-x", pre_rule.group(1))
        table_rule = re.search(r"table\s*\{([^}]*)\}", self.css)
        self.assertIsNotNone(table_rule, "no rule found for table")
        self.assertIn("overflow-x", table_rule.group(1))
        img_rule = re.search(r"img\s*\{([^}]*)\}", self.css)
        self.assertIsNotNone(img_rule, "no rule found for img")
        self.assertIn("max-width", img_rule.group(1))

    def test_css_accessibility_rules(self):
        self.assertIn("prefers-reduced-motion: reduce", self.css)
        reduced_motion_block = re.search(
            r"prefers-reduced-motion:\s*reduce\s*\)\s*\{(.*?)\}\s*\}", self.css, re.DOTALL
        )
        self.assertIsNotNone(reduced_motion_block, "no reduced-motion block found")
        self.assertRegex(reduced_motion_block.group(1), r"animation\s*:\s*none")
        self.assertRegex(reduced_motion_block.group(1), r"transition\s*:\s*none")
        self.assertIn(":focus-visible", self.css)

    def test_no_rounded_corners(self):
        # CSS is minified: the last declaration in a rule has no
        # trailing ';', so a value ends at ';' or the rule's '}'.
        matches = re.findall(r"border-radius\s*:\s*([^;}]+)[;}]", self.css)
        self.assertTrue(matches, "no border-radius declarations found")
        for value in matches:
            with self.subTest(value=value):
                self.assertIn(value.strip(), ("0", "0px"))


if __name__ == "__main__":
    unittest.main()
