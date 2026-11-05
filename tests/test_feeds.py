import re
import unittest
import xml.etree.ElementTree as ET

from helpers import PUBLIC, REPO_ROOT, load_fixture

ATOM_NS = "{http://www.w3.org/2005/Atom}"


def _entry_ids(xml_text: str) -> list[str]:
    root = ET.fromstring(xml_text)
    return [entry.find(f"{ATOM_NS}id").text for entry in root.findall(f"{ATOM_NS}entry")]


def _entry_updated_by_id(xml_text: str) -> dict[str, str]:
    root = ET.fromstring(xml_text)
    return {
        entry.find(f"{ATOM_NS}id").text: entry.find(f"{ATOM_NS}updated").text
        for entry in root.findall(f"{ATOM_NS}entry")
    }


def _slug_from_id(entry_id: str) -> str:
    return entry_id.rstrip("/").rsplit("/", 1)[-1]


def _post_dates() -> dict[str, str]:
    """Maps each post's URL slug to its 'date = YYYY-MM-DD' front matter,
    for checking feed order tolerant of same-date ties (see
    test_feed_ids_match_baseline)."""
    dates = {}
    for path in (REPO_ROOT / "content" / "posts").glob("*.md"):
        if path.name == "_index.md":
            continue
        match = re.search(r"^date = (\d{4}-\d{2}-\d{2})", path.read_text(), re.MULTILINE)
        if match:
            slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
            dates[slug] = match.group(1)
    return dates


class TestFeeds(unittest.TestCase):
    def test_feeds_parse(self):
        atom_text = (PUBLIC / "atom.xml").read_text()
        feed_text = (PUBLIC / "feed.xml").read_text()
        atom_root = ET.fromstring(atom_text)
        feed_root = ET.fromstring(feed_text)
        self.assertEqual(len(atom_root.findall(f"{ATOM_NS}entry")), 40)
        self.assertEqual(len(feed_root.findall(f"{ATOM_NS}entry")), 20)

    def test_feed_ids_match_baseline(self):
        """Checks the same ids, in the same date order, as the live
        feeds -- except where two posts share a date (one pair,
        2010-11-06), where Jekyll's tie-break was an unspecified
        filesystem detail not worth reproducing; the date sequence
        still has to match position-for-position, which pins every
        non-tied post exactly since dates are otherwise unique."""
        baseline = load_fixture("legacy-feeds.json")
        atom_ids = _entry_ids((PUBLIC / "atom.xml").read_text())
        feed_ids = _entry_ids((PUBLIC / "feed.xml").read_text())
        dates = _post_dates()

        def date_sequence(ids):
            return [dates[_slug_from_id(i)] for i in ids]

        self.assertEqual(set(atom_ids), set(baseline["atom.xml"]))
        self.assertEqual(date_sequence(atom_ids), date_sequence(baseline["atom.xml"]))
        self.assertEqual(set(feed_ids), set(baseline["feed.xml"]))
        self.assertEqual(date_sequence(feed_ids), date_sequence(baseline["feed.xml"]))

    def test_feed_updated_matches_baseline_timezone(self):
        """Found via code review: entries rendered <updated> in UTC
        (+00:00) while the live feeds used America/Vancouver, shifting
        every timestamp by 7-8 hours. A reader that tracks <updated>
        (not just <id>) could re-surface every entry, and Pacific-time
        readers would see each post's date a day early."""
        baseline = load_fixture("legacy-feeds.json")
        baseline_atom = dict(zip(baseline["atom.xml"], baseline["atom.xml_updated"]))
        baseline_feed = dict(zip(baseline["feed.xml"], baseline["feed.xml_updated"]))
        new_atom = _entry_updated_by_id((PUBLIC / "atom.xml").read_text())
        new_feed = _entry_updated_by_id((PUBLIC / "feed.xml").read_text())
        self.assertEqual(new_atom, baseline_atom)
        self.assertEqual(new_feed, baseline_feed)

    def test_llms_txt(self):
        text = (PUBLIC / "llms.txt").read_text()
        self.assertTrue(text.startswith("# Chris Benninger"))
        post_lines = re.findall(
            r"^- \[.+\]\(https://benninger\.ca/posts/[^)]+/\)", text, re.MULTILINE
        )
        self.assertEqual(len(post_lines), 40)
        other_section = text.split("## Other", 1)[1]
        self.assertIn("https://benninger.ca/projects/", other_section)
        self.assertIn("https://benninger.ca/about/", other_section)

    def test_llms_full(self):
        text = (PUBLIC / "llms-full.txt").read_text()
        baseline = load_fixture("legacy-posts.json")
        for data in baseline.values():
            self.assertIn(data["title"], text)
        self.assertNotIn("<p>", text)
        self.assertNotIn("&amp;", text)

    def test_robots(self):
        text = (PUBLIC / "robots.txt").read_text()
        self.assertEqual(
            text, "User-agent: *\nAllow: /\n\nSitemap: https://benninger.ca/sitemap.xml\n"
        )

    def test_sitemap_has_posts(self):
        text = (PUBLIC / "sitemap.xml").read_text()
        baseline = load_fixture("legacy-posts.json")
        for slug in baseline:
            with self.subTest(slug=slug):
                self.assertIn(f"https://benninger.ca/posts/{slug}/", text)
        for slug in [
            "scala-declaring-multiple-vars-as-null-and-enforcing-a-type",
            "what-is-sphinux-os-",
            "jvm-more-than-just-java",
        ]:
            with self.subTest(slug=slug):
                self.assertNotIn(f"/posts/{slug}/", text)


if __name__ == "__main__":
    unittest.main()
