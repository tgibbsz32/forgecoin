"""Purely offline test of wiki link integrity checks."""
import tempfile
import unittest
from pathlib import Path

from tools.check_wiki_docs import local_link_errors, check_wiki


class WikiLinksTests(unittest.TestCase):
    def test_existing_relative_and_external_urls(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            wiki = root / "docs" / "wiki"
            wiki.mkdir(parents=True)
            (wiki / "Home.md").write_text("# home")
            text = "[Home](Home.md) [Anchor](#here) [Web](https://example.org/page)"
            self.assertEqual(local_link_errors(text, wiki / "Home.md", root), [])

    def test_detect_missing_and_outside_root(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            wiki = root / "docs" / "wiki"
            wiki.mkdir(parents=True)
            src = wiki / "Home.md"
            errors = local_link_errors("[missing](gone.md) [outside](../../../secret)", src, root)
            self.assertEqual(len(errors), 2)
            self.assertIn("missing file", errors[0])
            self.assertIn("escapes repository", errors[1])

    def test_ignore_fenced_code(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            wiki = root / "docs" / "wiki"
            wiki.mkdir(parents=True)
            content = "~~~md\n[not real](missing.md)\n~~~\n[real](Home.md)"
            (wiki / "Home.md").write_text(content, encoding="utf-8")
            self.assertEqual(check_wiki(root), [])

    def test_detect_nonportable_and_missing_home(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            wiki = root / "docs" / "wiki"
            wiki.mkdir(parents=True)
            self.assertEqual(check_wiki(root), ["Wiki Home.md is missing"])
            src = wiki / "Home.md"
            errors = local_link_errors("[bad](/absolute.md) [also](sub\\name.md)", src, root)
            self.assertEqual(len(errors), 2)
            self.assertTrue(all("nonportable" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
