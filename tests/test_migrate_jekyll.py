import importlib.util
import pathlib
import sys
import tomllib
import unittest

try:
    import yaml  # noqa: F401

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))


@unittest.skipUnless(HAS_YAML, "PyYAML not installed")
class TestMigrateJekyll(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import migrate_jekyll

        cls.mod = migrate_jekyll

    def test_highlight_block(self):
        result = self.mod.convert_highlights(
            "a\n{% highlight bash %}\nls -l\n{% endhighlight %}\nb"
        )
        self.assertIn("\n```bash\nls -l\n```\n", result)
        self.assertNotIn("{%", result)

    def test_highlight_malformed_dollar(self):
        result = self.mod.convert_highlights("{% highlight scala $}x{% endhighlight %}")
        self.assertIn("```scala", result)
        self.assertIn("x", result)
        self.assertNotIn("{%", result)

    def test_highlight_one_line(self):
        result = self.mod.convert_highlights(
            "{% highlight sh %}$ faad -o - in.m4a | lame - out.mp3{% endhighlight %}"
        )
        self.assertIn("```sh", result)
        self.assertIn("$ faad -o - in.m4a | lame - out.mp3", result)
        self.assertNotIn("{%", result)

    def test_ial_removed(self):
        result = self.mod.strip_kramdown_ial("|a|\n{: .styled-table}\nx")
        self.assertEqual(result, "|a|\nx")

    def test_site_url(self):
        result = self.mod.replace_site_url('<img src="{{ site.url }}/assets/img/x.png">')
        self.assertEqual(result, '<img src="/assets/img/x.png">')

    def test_front_matter_draft(self):
        meta = {
            "title": "T",
            "published": False,
            "tags": ["a"],
            "categories": ["c"],
            "layout": "post",
        }
        result = self.mod.to_zola_front_matter(meta, "2013-06-05-what-is-sphinux-os-.html")
        self.assertIn("draft = true", result)
        self.assertIn("date = 2013-06-05", result)
        self.assertIn('tags = ["a"]', result)
        self.assertNotIn("layout", result)

    def test_front_matter_quotes(self):
        title = 'Scala: Declaring multiple vars as \'null\' while "enforcing" a type'
        meta = {"title": title, "published": True, "tags": [], "categories": []}
        result = self.mod.to_zola_front_matter(meta, "2012-10-24-x.html")
        parsed = tomllib.loads(result)
        self.assertEqual(parsed["title"], title)


if __name__ == "__main__":
    unittest.main()
