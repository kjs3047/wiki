from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from wiki_healthcheck import build_report


def page(title: str, body: str) -> str:
    return "\n".join(
        [
            "---",
            f'title: "{title}"',
            "---",
            "",
            f"# {title}",
            "",
            body,
            "",
        ]
    )


class WikiHealthcheckTests(unittest.TestCase):
    def test_build_report_detects_orphans_and_broken_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "wiki"
            (root / "concepts").mkdir(parents=True)
            (root / "index.md").write_text(page("Index", "[[linked-page]]"), encoding="utf-8")
            (root / "concepts" / "linked-page.md").write_text(page("Linked Page", "Body"), encoding="utf-8")
            (root / "concepts" / "orphan-page.md").write_text(page("Orphan Page", "No links"), encoding="utf-8")
            (root / "concepts" / "broken-page.md").write_text(page("Broken Page", "[[missing-page]]"), encoding="utf-8")

            report = build_report(root)

            self.assertTrue(any(item["target"] == "missing-page" for item in report["broken_links"]))
            self.assertTrue(any(path.endswith("orphan-page.md") for path in report["orphan_pages"]))

    def test_build_report_detects_missing_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "wiki"
            root.mkdir(parents=True)
            (root / "index.md").write_text("# Index\n", encoding="utf-8")

            report = build_report(root)
            self.assertTrue(any(path.endswith("index.md") for path in report["missing_frontmatter"]))


if __name__ == "__main__":
    unittest.main()
