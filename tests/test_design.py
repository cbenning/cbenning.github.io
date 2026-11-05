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


class TestSeoMeta(unittest.TestCase):
    """Found via code review: post/page templates never overrode the
    og:title block (every page showed "Chris Benninger" in social
    previews), `default()` doesn't fire on a front-matter field that's
    present but null (every post had an empty description), and there
    was no og:image at all."""

    def test_post_og_title_matches_page_title(self):
        html = (PUBLIC / "posts" / "davlog" / "index.html").read_text()
        self.assertIn('og:title" content="davlog', html)
        self.assertNotIn('og:title" content="Chris Benninger"', html)

    def test_no_empty_descriptions(self):
        for page in html_pages():
            text = page.read_text()
            if _is_redirect_page(text):
                continue
            with self.subTest(page=str(page.relative_to(PUBLIC))):
                self.assertNotIn('name="description" content="">', text)
                self.assertNotIn('og:description" content="">', text)

    def test_og_image_present(self):
        for page in html_pages():
            text = page.read_text()
            if _is_redirect_page(text):
                continue
            with self.subTest(page=str(page.relative_to(PUBLIC))):
                self.assertRegex(text, r'og:image" content="https://[^"]+"')

    def test_404_has_no_misleading_canonical(self):
        html = (PUBLIC / "404.html").read_text()
        self.assertNotIn('rel="canonical"', html)
        self.assertNotIn('og:url"', html)


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

    def test_long_text_wraps_instead_of_overflowing(self):
        """Found via a real 360px layout check: long unbroken URLs/paths
        in prose and un-wrapped tag-chip rows pushed several pages wider
        than the viewport, even though pre/table already scroll inside
        their own box (test_css_overflow_rules)."""
        body_rule = re.search(r"\.post-body\s*\{([^}]*)\}", self.css)
        self.assertIsNotNone(body_rule, "no rule found for .post-body")
        self.assertIn("overflow-wrap", body_rule.group(1))
        inline_code_rule = re.search(r':not\(pre\)>code\s*\{([^}]*)\}', re.sub(r"\s+", "", self.css))
        self.assertIsNotNone(inline_code_rule, "no rule found for :not(pre) > code")
        self.assertIn("overflow-wrap", inline_code_rule.group(1))
        post_list_li_rule = re.search(r"\.post-list li\s*\{([^}]*)\}", self.css)
        self.assertIsNotNone(post_list_li_rule, "no rule found for .post-list li")
        self.assertIn("flex-wrap", post_list_li_rule.group(1))

    def test_post_body_links_have_a_non_color_cue(self):
        """WCAG 1.4.1: colour alone can't be the only way to tell a link
        from body text. --led on --text is only 1.07:1, so a reader who
        can't distinguish the hue sees no link at all without this."""
        rule = re.search(r"\.post-body a\s*\{([^}]*)\}", self.css)
        self.assertIsNotNone(rule, "no rule found for .post-body a")
        self.assertIn("underline", rule.group(1))

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
