from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ingest_lib import extract_title_from_text, slugify, summarize_text, update_index


class IngestLibTests(unittest.TestCase):
    def test_slugify_normalizes_text(self) -> None:
        self.assertEqual(slugify("LLM Knowledge Bases"), "llm-knowledge-bases")
        self.assertEqual(slugify("  A/B Test  "), "a-b-test")

    def test_extract_title_from_text_skips_frontmatter(self) -> None:
        markdown = """---
title: \"Ignored frontmatter title\"
type: \"source\"
---

# Actual Heading

Body text here.
"""
        self.assertEqual(extract_title_from_text(markdown, "fallback"), "Actual Heading")

    def test_summarize_text_uses_non_heading_content(self) -> None:
        text = """# Title

First useful paragraph. It should be used.

Second useful paragraph for the summary.
"""
        summary = summarize_text(text)
        self.assertIn("First useful paragraph", summary)

    def test_update_index_adds_entry_only_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            index_path = Path(tmp_dir) / "index.md"
            index_path.write_text(
                "\n".join(
                    [
                        "---",
                        'title: "Wiki Index"',
                        "---",
                        "",
                        "# Wiki Index",
                        "",
                        "## Sources",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            inserted = update_index(index_path, "sample-source", "Sample summary")
            inserted_again = update_index(index_path, "sample-source", "Sample summary")

            content = index_path.read_text(encoding="utf-8")
            self.assertTrue(inserted)
            self.assertFalse(inserted_again)
            self.assertEqual(content.count("[[sample-source]]"), 1)


if __name__ == "__main__":
    unittest.main()
