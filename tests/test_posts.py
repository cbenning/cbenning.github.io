import difflib
import pathlib
import unittest

from helpers import PUBLIC, REPO_ROOT, article_text, count_pre_blocks, load_fixture, normalize

class TestProjectPages(unittest.TestCase):
    def test_legacy_project_pages_build(self):
        for slug in ["workviz", "omega-editor-theme"]:
            with self.subTest(slug=slug):
                self.assertTrue(
                    (PUBLIC / "projects" / slug / "index.html").is_file(),
                    f"legacy project page not built: /projects/{slug}/",
                )


class TestStaticFiles(unittest.TestCase):
    def test_static_files(self):
        self.assertEqual((PUBLIC / "CNAME").read_text().strip(), "benninger.ca")
        for rel in [
            "keybase.txt",
            "favicon.ico",
            "images/posts/unison.png",
            "assets/img/html5-before.png",
            "assets/img/html5-after.png",
            "assets/template.tar.gz",
            "assets/omega_v0.1.tar.gz",
        ]:
            with self.subTest(rel=rel):
                self.assertTrue((PUBLIC / rel).is_file(), f"missing {rel}")


class TestPosts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = load_fixture("legacy-posts.json")

    def _new_html(self, slug: str) -> str:
        path = PUBLIC / "posts" / slug / "index.html"
        self.assertTrue(path.is_file(), f"post not built: {slug}")
        return path.read_text()

    def test_post_text_matches_baseline(self):
        for slug, data in self.baseline.items():
            with self.subTest(slug=slug):
                new_html = self._new_html(slug)
                new_words = normalize(article_text(new_html))
                ratio = difflib.SequenceMatcher(None, data["words"], new_words).ratio()
                self.assertGreaterEqual(
                    ratio, 0.97, f"{slug}: text ratio {ratio:.3f} below 0.97"
                )

    def test_post_code_block_counts(self):
        for slug, data in self.baseline.items():
            with self.subTest(slug=slug):
                new_html = self._new_html(slug)
                count = count_pre_blocks(new_html)
                self.assertEqual(
                    count,
                    data["code_blocks"],
                    f"{slug}: expected {data['code_blocks']} <pre> blocks, got {count}",
                )

    def test_only_live_posts_are_built(self):
        """public/posts/ holds exactly the 40 posts that were live on
        the Jekyll site -- no more (a draft leaking out) and no fewer
        (a post lost in migration)."""
        built = {p.name for p in (PUBLIC / "posts").iterdir() if p.is_dir()}
        self.assertEqual(built, set(self.baseline))

    def test_no_liquid_left(self):
        content_dir = REPO_ROOT / "content"
        for path in content_dir.rglob("*.md"):
            text = path.read_text()
            with self.subTest(path=str(path)):
                self.assertNotIn("{%", text)
                self.assertNotIn("{{ site", text)


if __name__ == "__main__":
    unittest.main()
