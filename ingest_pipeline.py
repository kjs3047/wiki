from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ingest_lib import (
    append_log,
    capture_pdf_source,
    capture_text_source,
    capture_url_source,
    create_or_update_source_page,
    recommend_agent_followup,
    relative_to_repo,
    repo_root,
    summarize_text,
    update_index,
)


def detect_kind(source: str, explicit_kind: str) -> str:
    if explicit_kind != "auto":
        return explicit_kind
    lowered = source.lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        return "pdf" if lowered.endswith(".pdf") else "url"
    return "pdf" if Path(source).suffix.lower() == ".pdf" else "text"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="End-to-end ingest pipeline for URL, PDF, or local text sources.")
    parser.add_argument("source", help="Source URL, PDF path, or local text/markdown file.")
    parser.add_argument(
        "--kind",
        choices=["auto", "url", "pdf", "text"],
        default="auto",
        help="Force the ingest mode instead of inferring it.",
    )
    parser.add_argument("--title", help="Optional title override.")
    parser.add_argument("--slug", help="Optional slug override.")
    parser.add_argument("--date", help="Optional source date in YYYY-MM-DD format.")
    parser.add_argument("--timeout", type=int, default=20, help="Network timeout in seconds.")
    parser.add_argument("--download-images", action="store_true", help="Download linked images for URL captures.")
    parser.add_argument("--max-images", type=int, default=10, help="Maximum number of URL images to download.")
    parser.add_argument("--copy-original", action="store_true", help="Copy local PDFs into raw/assets/pdfs/.")
    parser.add_argument("--force", action="store_true", help="Overwrite raw/wiki artifacts if they already exist.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    kind = detect_kind(args.source, args.kind)

    if kind == "url":
        capture = capture_url_source(
            url=args.source,
            title=args.title,
            slug=args.slug,
            source_date=args.date,
            download_linked_images=args.download_images,
            max_images=args.max_images,
            timeout=args.timeout,
            force=args.force,
        )
    elif kind == "pdf":
        capture = capture_pdf_source(
            source=args.source,
            title=args.title,
            slug=args.slug,
            source_date=args.date,
            copy_original=args.copy_original,
            timeout=args.timeout,
            force=args.force,
        )
    else:
        capture = capture_text_source(
            source=args.source,
            title=args.title,
            slug=args.slug,
            source_date=args.date,
            force=args.force,
        )

    wiki_path = create_or_update_source_page(capture, force=args.force)
    root = repo_root()
    index_updated = update_index(root / "wiki" / "index.md", wiki_path.stem, summarize_text(capture.text_body, max_chars=180))
    log_updated = append_log(root / "wiki" / "log.md", capture, wiki_path)

    print(f"Raw capture: {relative_to_repo(capture.raw_path)}")
    print(f"Wiki source page: {relative_to_repo(wiki_path)}")
    print(f"Kind: {capture.kind}")
    print(f"Title: {capture.title}")
    print(f"Index updated: {'yes' if index_updated else 'no'}")
    print(f"Log updated: {'yes' if log_updated else 'no'}")
    if capture.asset_paths:
        print("Assets:")
        for path in capture.asset_paths:
            print(f"  - {relative_to_repo(path)}")
    if capture.notes:
        print("Notes:")
        for note in capture.notes:
            print(f"  - {note}")

    print()
    print(recommend_agent_followup(capture, wiki_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
