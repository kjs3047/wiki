from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from wiki_search import search_markdown, wiki_section


class WikiSearchTests(unittest.TestCase):
    def test_search_markdown_finds_wiki_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "wiki" / "concepts").mkdir(parents=True)
            (root / "wiki" / "concepts" / "llm-wiki.md").write_text(
                "# LLM Wiki\n\nPersistent wiki knowledge base.\n",
                encoding="utf-8",
            )

            results = search_markdown(root, "persistent wiki", limit=10, include_raw=False, section=None)
            self.assertEqual(len(results), 1)
            self.assertIn("Persistent wiki", results[0].snippet)

    def test_section_filter_limits_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "wiki" / "sources").mkdir(parents=True)
            (root / "wiki" / "analyses").mkdir(parents=True)
            (root / "wiki" / "sources" / "alpha.md").write_text("alpha persistent wiki\n", encoding="utf-8")
            (root / "wiki" / "analyses" / "beta.md").write_text("beta persistent wiki\n", encoding="utf-8")

            results = search_markdown(root, "persistent wiki", limit=10, include_raw=False, section="sources")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].path.name, "alpha.md")

    def test_wiki_section_classifies_root_and_nested_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            self.assertEqual(wiki_section(root / "wiki" / "index.md", root), "root")
            self.assertEqual(wiki_section(root / "wiki" / "sources" / "alpha.md", root), "sources")
            self.assertEqual(wiki_section(root / "raw" / "sources" / "alpha.md", root), "raw")


if __name__ == "__main__":
    unittest.main()
