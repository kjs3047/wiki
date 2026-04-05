from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys


@dataclass(frozen=True)
class SearchResult:
    path: Path
    score: int
    snippet: str


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def iter_markdown_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def wiki_section(path: Path, root: Path) -> str:
    relative = path.relative_to(root)
    if len(relative.parts) == 1:
        return "root"
    if relative.parts[0] == "wiki":
        return relative.parts[1] if len(relative.parts) > 2 else "root"
    return relative.parts[0]


def find_snippet(text: str, terms: list[str]) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lowered_terms = [term.lower() for term in terms if term.strip()]

    for line in lines:
        lowered = line.lower()
        if any(term in lowered for term in lowered_terms):
            return line

    return lines[0] if lines else ""


def score_text(text: str, query: str, terms: list[str]) -> int:
    lowered = text.lower()
    score = lowered.count(query) * 5
    score += sum(lowered.count(term) for term in terms)
    return score


def search_markdown(
    root: Path,
    query: str,
    limit: int,
    include_raw: bool,
    section: str | None,
) -> list[SearchResult]:
    targets: list[Path] = []
    wiki_root = root / "wiki"
    if wiki_root.exists():
        targets.extend(iter_markdown_files(wiki_root))

    if include_raw:
        raw_root = root / "raw"
        if raw_root.exists():
            targets.extend(iter_markdown_files(raw_root))

    normalized_query = query.strip().lower()
    terms = [term for term in re.split(r"\s+", normalized_query) if term]

    results: list[SearchResult] = []
    for path in targets:
        if section and wiki_section(path, root) != section:
            continue
        text = path.read_text(encoding="utf-8")
        score = score_text(text, normalized_query, terms)
        if score <= 0:
            continue

        results.append(
            SearchResult(
                path=path,
                score=score,
                snippet=find_snippet(text, [normalized_query, *terms]),
            )
        )

    results.sort(key=lambda item: (-item.score, str(item.path)))
    return results[:limit]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Naive markdown search over the knowledge base.")
    parser.add_argument("--query", required=True, help="Search query.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of results.")
    parser.add_argument(
        "--include-raw",
        action="store_true",
        help="Also search raw source captures in addition to wiki pages.",
    )
    parser.add_argument(
        "--section",
        choices=["root", "raw", "entities", "concepts", "sources", "analyses"],
        help="Optional section filter.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON for easier agent consumption.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    query = args.query.strip()
    if not query:
        print("query must not be empty")
        return 1

    results = search_markdown(repo_root(), query, args.limit, args.include_raw, args.section)

    if not results:
        print("No results found.")
        return 0

    if args.json:
        payload = [
            {
                "path": str(result.path.relative_to(repo_root())),
                "section": wiki_section(result.path, repo_root()),
                "score": result.score,
                "snippet": result.snippet,
            }
            for result in results
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"Search query: {query}")
    if args.section:
        print(f"Section: {args.section}")
    print(f"Results: {len(results)}")
    print()

    for index, result in enumerate(results, start=1):
        section_name = wiki_section(result.path, repo_root())
        print(f"{index}. {result.path.relative_to(repo_root())} [{section_name}] (score={result.score})")
        if result.snippet:
            print(f"   {result.snippet}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
