from __future__ import annotations

import argparse
import sys

from ingest_lib import capture_pdf_source, relative_to_repo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert a PDF into an immutable raw source markdown file.")
    parser.add_argument("source", help="Local PDF path or remote PDF URL.")
    parser.add_argument("--title", help="Optional title override.")
    parser.add_argument("--slug", help="Optional slug override.")
    parser.add_argument("--date", help="Optional source date in YYYY-MM-DD format.")
    parser.add_argument("--timeout", type=int, default=20, help="Network timeout in seconds for remote PDFs.")
    parser.add_argument(
        "--copy-original",
        action="store_true",
        help="Copy a local PDF into raw/assets/pdfs/. Remote PDFs are always saved there.",
    )
    parser.add_argument(
        "--fail-on-extract-error",
        action="store_true",
        help="Exit with an error if text extraction fails instead of writing a stub capture.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite the target raw markdown file if it exists.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = capture_pdf_source(
        source=args.source,
        title=args.title,
        slug=args.slug,
        source_date=args.date,
        copy_original=args.copy_original,
        timeout=args.timeout,
        force=args.force,
        fail_on_extract_error=args.fail_on_extract_error,
    )

    print(f"Created raw capture: {relative_to_repo(result.raw_path)}")
    print(f"Title: {result.title}")
    print(f"Kind: {result.kind}")
    print(f"Source ref: {result.source_ref}")
    print(f"Extractor: {result.extractor or 'none'}")
    if result.original_path:
        print(f"Original PDF: {relative_to_repo(result.original_path)}")
    if result.notes:
        print("Notes:")
        for note in result.notes:
            print(f"  - {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
