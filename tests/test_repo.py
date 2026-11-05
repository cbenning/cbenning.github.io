import unittest

from helpers import REPO_ROOT

JEKYLL_PATHS = ["_config.yml", "Gemfile", "_layouts", "_includes", "_posts"]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "deploy.yml"


class TestNoJekyllFiles(unittest.TestCase):
    def test_no_jekyll_files(self):
        for rel in JEKYLL_PATHS:
            with self.subTest(path=rel):
                self.assertFalse((REPO_ROOT / rel).exists(), f"{rel} still exists")


class TestWorkflow(unittest.TestCase):
    def test_workflow_pins_zola(self):
        self.assertTrue(WORKFLOW_PATH.is_file(), "deploy.yml missing")
        text = WORKFLOW_PATH.read_text()
        self.assertIn("scripts/test.sh", text)
        self.assertIn("actions/upload-pages-artifact", text)
        self.assertIn("actions/deploy-pages", text)


if __name__ == "__main__":
    unittest.main()
