from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def run_root_script(script_name: str, args: list[str]) -> int:
    script_path = repo_root() / script_name
    cmd = [sys.executable, str(script_path), *args]
    return subprocess.run(cmd, check=False).returncode


def wiki_dir() -> Path:
    return repo_root() / "wiki"


def count_markdown_pages(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for _ in root.rglob("*.md"))


def stats_command() -> int:
    root = wiki_dir()
    page_count = count_markdown_pages(root)
    print(f"Wiki root: {root}")
    print(f"Total pages: {page_count}")
    print("Canonical CLIs:")
    print('  - python wiki_search.py --query "..."')
    print("  - python wiki_healthcheck.py")
    print('  - python ingest_pipeline.py "<source>"')
    return 0


def scaffold_source_command(args: argparse.Namespace) -> int:
    return run_root_script(
        "ingest_pipeline.py",
        [
            args.source,
            "--kind",
            args.kind,
            *([] if not args.title else ["--title", args.title]),
            *([] if not args.slug else ["--slug", args.slug]),
            *([] if not args.date else ["--date", args.date]),
        ],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Repository utility wrapper for knowledge-base operations.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lint_parser = subparsers.add_parser("lint", help="Run the canonical wiki health check.")
    lint_parser.set_defaults(func=lambda args: run_root_script("wiki_healthcheck.py", []))

    search_parser = subparsers.add_parser("search", help="Run the canonical wiki search.")
    search_parser.add_argument("--query", required=True, help="Search query.")
    search_parser.add_argument("--limit", type=int, default=10, help="Maximum number of results.")
    search_parser.add_argument("--include-raw", action="store_true", help="Also search raw captures.")
    search_parser.add_argument(
        "--section",
        choices=["root", "raw", "entities", "concepts", "sources", "analyses"],
        help="Optional section filter.",
    )
    search_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    search_parser.set_defaults(
        func=lambda args: run_root_script(
            "wiki_search.py",
            [
                "--query",
                args.query,
                "--limit",
                str(args.limit),
                *(["--include-raw"] if args.include_raw else []),
                *(["--section", args.section] if args.section else []),
                *(["--json"] if args.json else []),
            ],
        )
    )

    stats_parser = subparsers.add_parser("stats", help="Show basic wiki stats and canonical command entrypoints.")
    stats_parser.set_defaults(func=lambda args: stats_command())

    scaffold_parser = subparsers.add_parser("scaffold-source", help="Create a source via the canonical ingest pipeline.")
    scaffold_parser.add_argument("source", help="Source URL or local file path.")
    scaffold_parser.add_argument(
        "--kind",
        choices=["auto", "url", "pdf", "text"],
        default="auto",
        help="Source kind override.",
    )
    scaffold_parser.add_argument("--title", help="Optional title override.")
    scaffold_parser.add_argument("--slug", help="Optional slug override.")
    scaffold_parser.add_argument("--date", help="Optional source date in YYYY-MM-DD format.")
    scaffold_parser.set_defaults(func=scaffold_source_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
