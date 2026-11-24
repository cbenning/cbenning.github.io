import re
import unittest
import xml.etree.ElementTree as ET

from helpers import PUBLIC, REPO_ROOT, live_posts, load_fixture

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
        self.assertEqual(len(atom_root.findall(f"{ATOM_NS}entry")), len(live_posts()))
        self.assertEqual(len(feed_root.findall(f"{ATOM_NS}entry")), min(20, len(live_posts())))

    def test_feed_ids_match_baseline(self):
        """atom.xml carries every post, newest first; feed.xml is its
        newest 20. Every id from the live Jekyll feeds is still present
        and spelled the same, so existing subscribers don't see old
        posts reappear as new. Posts written since the migration are
        allowed alongside them. Two posts share a date (2010-11-06),
        where Jekyll's tie-break was an unspecified filesystem detail
        not worth reproducing, so order is checked by date sequence."""
        baseline = load_fixture("legacy-feeds.json")
        atom_ids = _entry_ids((PUBLIC / "atom.xml").read_text())
        feed_ids = _entry_ids((PUBLIC / "feed.xml").read_text())
        dates = _post_dates()

        def date_sequence(ids):
            return [dates[_slug_from_id(i)] for i in ids]

        self.assertEqual({_slug_from_id(i) for i in atom_ids}, {s for s, _ in live_posts()})
        self.assertLessEqual(set(baseline["atom.xml"]), set(atom_ids))
        self.assertEqual(date_sequence(atom_ids), sorted(date_sequence(atom_ids), reverse=True))
        # the two feeds spell ids differently (atom.xml relative,
        # feed.xml absolute), as Jekyll did, so compare by slug
        self.assertEqual(
            [_slug_from_id(i) for i in feed_ids], [_slug_from_id(i) for i in atom_ids[:20]]
        )
        # feed.xml ids that were already live keep their exact spelling
        legacy_feed_ids = set(baseline["feed.xml"])
        for entry_id in feed_ids:
            if _slug_from_id(entry_id) in {_slug_from_id(i) for i in legacy_feed_ids}:
                with self.subTest(entry_id=entry_id):
                    self.assertIn(entry_id, legacy_feed_ids)

    def test_feed_updated_matches_baseline_timezone(self):
        """Found via code review: entries rendered <updated> in UTC
        (+00:00) while the live feeds used America/Vancouver, shifting
        every timestamp by 7-8 hours. A reader that tracks <updated>
        (not just <id>) could re-surface every entry, and Pacific-time
        readers would see each post's date a day early. Every entry the
        live feeds had must keep its exact timestamp, and every entry
        (including newer posts) must be in Pacific time."""
        baseline = load_fixture("legacy-feeds.json")
        baseline_atom = dict(zip(baseline["atom.xml"], baseline["atom.xml_updated"]))
        new_atom = _entry_updated_by_id((PUBLIC / "atom.xml").read_text())
        new_feed = _entry_updated_by_id((PUBLIC / "feed.xml").read_text())
        for entry_id, updated in baseline_atom.items():
            with self.subTest(entry_id=entry_id):
                self.assertEqual(new_atom.get(entry_id), updated)
        for entry_id, updated in {**new_atom, **new_feed}.items():
            with self.subTest(entry_id=entry_id):
                self.assertRegex(updated, r"T00:00:00-0[78]:00$")

    def test_llms_txt(self):
        text = (PUBLIC / "llms.txt").read_text()
        self.assertTrue(text.startswith("# Chris Benninger"))
        post_lines = re.findall(
            r"^- \[.+\]\(https://benninger\.ca/posts/[^)]+/\)", text, re.MULTILINE
        )
        self.assertEqual(len(post_lines), len(live_posts()))
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
        # the sitemap lists exactly the published posts and nothing else
        sitemap_posts = set(re.findall(r"https://benninger\.ca/posts/([a-z0-9][a-z0-9-]*)/", text))
        self.assertEqual(sitemap_posts, {s for s, _ in live_posts()})


if __name__ == "__main__":
    unittest.main()
