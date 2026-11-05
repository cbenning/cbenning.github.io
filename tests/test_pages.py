import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest

from helpers import PUBLIC, REPO_ROOT

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

    def test_stars_without_repo_does_not_break_the_build(self):
        """A project can legitimately have `stars` without `repo` (e.g.
        a GitLab-only project with a mirror star count), and `stars`
        with no `repo` used to crash the *entire* site build, not just
        that card: the badge linked unconditionally to `{{ p.repo
        }}/stargazers`. Proven directly against zola build, not just
        template text, since that's where the real failure was."""
        data_path = REPO_ROOT / "data" / "projects.toml"
        original = data_path.read_text()
        # lanby has no `repo` in the real data; temporarily give it stars
        mutated = original.replace(
            'id = "lanby"\nname = "Lanby"', 'id = "lanby"\nname = "Lanby"\nstars = 1'
        )
        self.assertNotEqual(mutated, original, "fixture assumption broke: no lanby entry found")
        scratch = tempfile.mkdtemp()
        try:
            data_path.write_text(mutated)
            result = subprocess.run(
                [str(REPO_ROOT / ".bin" / "zola"), "build", "-o", scratch, "--force"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, f"zola build failed:\n{result.stderr}")
            html = (pathlib.Path(scratch) / "projects" / "index.html").read_text()
            self.assertRegex(html, r"&#9733;</span>\s*1\s*<")
            self.assertNotIn('href="/stargazers"', html)  # no repo -> no dangling link
        finally:
            data_path.write_text(original)
            shutil.rmtree(scratch, ignore_errors=True)


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

    def test_home_cards_follow_order_field_not_declaration_order(self):
        """Home used to iterate data.projects in raw TOML declaration
        order while /projects/ explicitly sorted by `order` -- today
        the two happen to coincide, so this is proven by swapping two
        `order` values, not by reading the current page."""
        data_path = REPO_ROOT / "data" / "projects.toml"
        original = data_path.read_text()
        # davlog is order=1, lanby is order=2; swap them
        mutated = original.replace("order = 1", "order = 9").replace("order = 2", "order = 1").replace(
            "order = 9", "order = 2"
        )
        self.assertNotEqual(mutated, original, "fixture assumption broke: order fields not found")
        scratch = tempfile.mkdtemp()
        try:
            data_path.write_text(mutated)
            result = subprocess.run(
                [str(REPO_ROOT / ".bin" / "zola"), "build", "-o", scratch, "--force"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, f"zola build failed:\n{result.stderr}")
            html = (pathlib.Path(scratch) / "index.html").read_text()
            cards = re.findall(r'<article class="project-card" id="([^"]+)"', html)
            self.assertEqual(cards[:2], ["lanby", "davlog"])
        finally:
            data_path.write_text(original)
            shutil.rmtree(scratch, ignore_errors=True)


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
