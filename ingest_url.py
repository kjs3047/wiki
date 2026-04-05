from __future__ import annotations

import argparse
import sys

from ingest_lib import capture_url_source, relative_to_repo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch a URL and store it as an immutable raw source markdown file.")
    parser.add_argument("url", help="Source URL to capture.")
    parser.add_argument("--title", help="Optional title override.")
    parser.add_argument("--slug", help="Optional slug override.")
    parser.add_argument("--date", help="Optional source date in YYYY-MM-DD format.")
    parser.add_argument("--timeout", type=int, default=20, help="Network timeout in seconds.")
    parser.add_argument(
        "--download-images",
        action="store_true",
        help="Download linked images into raw/assets/<date-slug>/.",
    )
    parser.add_argument("--max-images", type=int, default=10, help="Maximum number of images to download.")
    parser.add_argument("--force", action="store_true", help="Overwrite the target raw markdown file if it exists.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = capture_url_source(
        url=args.url,
        title=args.title,
        slug=args.slug,
        source_date=args.date,
        download_linked_images=args.download_images,
        max_images=args.max_images,
        timeout=args.timeout,
        force=args.force,
    )

    print(f"Created raw capture: {relative_to_repo(result.raw_path)}")
    print(f"Title: {result.title}")
    print(f"Kind: {result.kind}")
    print(f"Source ref: {result.source_ref}")
    if result.asset_paths:
        print("Downloaded assets:")
        for path in result.asset_paths:
            print(f"  - {relative_to_repo(path)}")
    if result.notes:
        print("Notes:")
        for note in result.notes:
            print(f"  - {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
