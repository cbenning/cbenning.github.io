import unittest

from helpers import PUBLIC


class TestBuild(unittest.TestCase):
    def test_home_exists(self):
        self.assertTrue((PUBLIC / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
