from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys


WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")


@dataclass(frozen=True)
class WikiPage:
    path: Path
    stem: str
    links: list[str]
    has_frontmatter: bool


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def wiki_dir() -> Path:
    return repo_root() / "wiki"


def iter_markdown_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def normalize_link_target(target: str) -> str:
    return target.strip().split("/")[-1].lower()


def extract_links(text: str) -> list[str]:
    return [normalize_link_target(match) for match in WIKI_LINK_RE.findall(text)]


def has_yaml_frontmatter(text: str) -> bool:
    return text.startswith("---\n")


def load_pages(root: Path) -> list[WikiPage]:
    pages: list[WikiPage] = []
    for path in iter_markdown_files(root):
        text = path.read_text(encoding="utf-8")
        pages.append(
            WikiPage(
                path=path,
                stem=path.stem.lower(),
                links=extract_links(text),
                has_frontmatter=has_yaml_frontmatter(text),
            )
        )
    return pages


def build_report(root: Path) -> dict[str, object]:
    pages = load_pages(root)
    by_stem: dict[str, list[Path]] = defaultdict(list)
    for page in pages:
        by_stem[page.stem].append(page.path)

    duplicate_stems = {
        stem: [str(path.relative_to(repo_root())) for path in paths]
        for stem, paths in sorted(by_stem.items())
        if len(paths) > 1
    }

    unique_targets = {
        stem: paths[0]
        for stem, paths in by_stem.items()
        if len(paths) == 1
    }

    incoming: dict[str, set[str]] = defaultdict(set)
    broken_links: list[dict[str, str]] = []

    for page in pages:
        for target in page.links:
            target_path = unique_targets.get(target)
            if target_path is None:
                broken_links.append(
                    {
                        "from": str(page.path.relative_to(repo_root())),
                        "target": target,
                    }
                )
                continue
            if target_path != page.path:
                incoming[target].add(page.stem)

    ignored_orphans = {"index", "log"}
    orphan_pages = [
        str(page.path.relative_to(repo_root()))
        for page in pages
        if page.stem not in ignored_orphans and not incoming.get(page.stem)
    ]

    ignored_no_outgoing = {"log"}
    low_link_pages = [
        {
            "path": str(page.path.relative_to(repo_root())),
            "outgoing_links": len(page.links),
        }
        for page in pages
        if len(page.links) == 0 and page.stem not in ignored_no_outgoing
    ]

    missing_frontmatter = [
        str(page.path.relative_to(repo_root()))
        for page in pages
        if not page.has_frontmatter
    ]

    return {
        "page_count": len(pages),
        "duplicate_stems": duplicate_stems,
        "broken_links": broken_links,
        "orphan_pages": orphan_pages,
        "pages_with_no_outgoing_links": low_link_pages,
        "missing_frontmatter": missing_frontmatter,
    }


def print_report(report: dict[str, object]) -> int:
    print(f"Pages checked: {report['page_count']}")

    has_findings = False

    duplicate_stems = report["duplicate_stems"]
    if duplicate_stems:
        has_findings = True
        print("\nDuplicate stems:")
        for stem, paths in duplicate_stems.items():
            print(f"  - {stem}")
            for path in paths:
                print(f"    {path}")

    broken_links = report["broken_links"]
    if broken_links:
        has_findings = True
        print("\nBroken links:")
        for finding in broken_links:
            print(f"  - {finding['from']} -> [[{finding['target']}]]")

    orphan_pages = report["orphan_pages"]
    if orphan_pages:
        has_findings = True
        print("\nOrphan pages:")
        for path in orphan_pages:
            print(f"  - {path}")

    no_outgoing = report["pages_with_no_outgoing_links"]
    if no_outgoing:
        has_findings = True
        print("\nPages with no outgoing links:")
        for item in no_outgoing:
            print(f"  - {item['path']}")

    missing_frontmatter = report["missing_frontmatter"]
    if missing_frontmatter:
        has_findings = True
        print("\nPages missing frontmatter:")
        for path in missing_frontmatter:
            print(f"  - {path}")

    if not has_findings:
        print("Wiki health check passed.")
        return 0

    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Structural health checks for the markdown wiki.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = wiki_dir()
    if not root.exists():
        print(f"wiki directory not found: {root}")
        return 1

    report = build_report(root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        has_findings = any(
            report[key]
            for key in (
                "duplicate_stems",
                "broken_links",
                "orphan_pages",
                "pages_with_no_outgoing_links",
                "missing_frontmatter",
            )
        )
        return 1 if has_findings else 0

    return print_report(report)


if __name__ == "__main__":
    sys.exit(main())
