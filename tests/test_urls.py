import unittest

from helpers import PUBLIC, load_fixture

INTENTIONALLY_REMOVED = {
    "/404/",
    "/projects/index2/",
    "/assets/css/main.css",
    "/assets/css/skins/dark.css",
    "/assets/css/skins/default.css",
    "/assets/css/skins/light.css",
    "/assets/js/search-data.js",
    "/js/highlight.js/",
    "/js/highlight.js/README.ru/",
}


class TestLegacyUrls(unittest.TestCase):
    def test_legacy_urls_exist(self):
        urls = load_fixture("legacy-urls.txt").splitlines()
        for path in urls:
            if not path or path in INTENTIONALLY_REMOVED:
                continue
            with self.subTest(path=path):
                rel = path.lstrip("/")
                candidate_file = PUBLIC / rel
                candidate_index = PUBLIC / rel / "index.html"
                self.assertTrue(
                    candidate_file.is_file() or candidate_index.is_file(),
                    f"missing: {path}",
                )


if __name__ == "__main__":
    unittest.main()
