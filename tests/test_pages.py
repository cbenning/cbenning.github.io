import re
import unittest

from helpers import PUBLIC

# Confirmed 404 on the live site, so the new site not having them either
# is not a regression; each entry notes how it was checked.
KNOWN_BROKEN: set[str] = set()


def _read(path):
    return path.read_text()


class TestProjectsPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = _read(PUBLIC / "projects" / "index.html")

    def test_projects_page_cards(self):
        cards = re.findall(r'<article class="project-card" id="([^"]+)"', self.html)
        self.assertEqual(
            cards, ["davlog", "lanby", "fussel", "ticktick-to-todoist-migrator"]
        )
        for card_id in cards:
            with self.subTest(card_id=card_id):
                card_html = self._card_html(card_id)
                # the status LED always carries a readable text label,
                # so colour is never the only signal
                self.assertRegex(card_html, r'class="led led--\w+[^"]*"')
                self.assertRegex(card_html, r'class="led-label">\w+<')

    def _card_html(self, card_id):
        start = self.html.index(f'<article class="project-card" id="{card_id}"')
        rest = self.html[start:]
        end = rest.find("</article>")
        return rest[: end + len("</article>")]

    def test_project_links(self):
        davlog = self._card_html("davlog")
        self.assertIn("https://github.com/cbenning/davlog", davlog)
        self.assertIn("/posts/davlog/", davlog)
        fussel = self._card_html("fussel")
        self.assertIn("http://photos.benninger.ca", fussel)


class TestHomePage(unittest.TestCase):
    def test_home(self):
        html = _read(PUBLIC / "index.html")
        self.assertIn("Chris Benninger", html)
        self.assertIn("/art/hero-workbench.svg", html)
        self.assertIn("led--breathe", html)
        self.assertEqual(html.count('class="project-card"'), 4)
        # Scoped to the latest-posts list, not the whole page -- project
        # cards also link to their own /posts/<slug>/ write-up.
        list_start = html.index('class="post-list"')
        list_html = html[list_start : html.index("</ul>", list_start)]
        post_links = re.findall(r'href="(/posts/[^"]+/)"', list_html)
        self.assertEqual(len(post_links), 5)
        self.assertEqual(post_links[0], "/posts/davlog/")


class TestArchivePage(unittest.TestCase):
    def test_archive(self):
        html = _read(PUBLIC / "articles" / "index.html")
        post_links = re.findall(r'href="(/posts/[^"]+/)"', html)
        self.assertEqual(len(post_links), 40)
        self.assertIn("2026", html)
        self.assertIn("2010", html)
        self.assertLess(html.index("2026"), html.index("2010"))


class TestPostPage(unittest.TestCase):
    def test_post_page(self):
        html = _read(PUBLIC / "posts" / "davlog" / "index.html")
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
        self.assertIsNotNone(h1, "no <h1> found")
        self.assertIn("davlog", h1.group(1).lower())
        self.assertIn('<time datetime="2026-10-30', html)
        self.assertRegex(html, r'<a href="/tags/[^"]+/"')


class TestTagsPage(unittest.TestCase):
    def test_tags_page(self):
        html = _read(PUBLIC / "tags" / "index.html")
        self.assertIn('href="/tags/linux/"', html)


def _iter_html_pages():
    return sorted(PUBLIC.rglob("*.html"))


def _iter_links(html):
    for match in re.finditer(r'(?:href|src)="(/[^"]*)"', html):
        link = match.group(1)
        if link.startswith("//"):
            continue  # protocol-relative URL to an external host
        link = link.split("#", 1)[0].split("?", 1)[0]
        if link:
            yield link


class TestInternalLinks(unittest.TestCase):
    def test_internal_links_resolve(self):
        for page in _iter_html_pages():
            html = page.read_text()
            for link in _iter_links(html):
                if link in KNOWN_BROKEN:
                    continue
                with self.subTest(page=str(page.relative_to(PUBLIC)), link=link):
                    rel = link.lstrip("/")
                    candidate_file = PUBLIC / rel
                    candidate_index = PUBLIC / rel / "index.html"
                    self.assertTrue(
                        candidate_file.is_file() or candidate_index.is_file(),
                        f"broken link {link} on {page.relative_to(PUBLIC)}",
                    )


if __name__ == "__main__":
    unittest.main()
