from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from html import unescape
from html.parser import HTMLParser
import io
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


USER_AGENT = "Mozilla/5.0 (compatible; LLM-KB-Ingest/1.0; +https://github.com/kjs3047/wiki)"
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
DATED_STEM_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")


@dataclass(frozen=True)
class RawCaptureResult:
    kind: str
    title: str
    slug: str
    source_date: str
    source_ref: str
    raw_path: Path
    text_body: str
    original_path: Path | None = None
    asset_paths: list[Path] = field(default_factory=list)
    extractor: str | None = None
    notes: list[str] = field(default_factory=list)


class MarkdownishHTMLParser(HTMLParser):
    BLOCK_TAGS = {
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
    IGNORED_TAGS = {"script", "style", "noscript", "svg"}

    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.in_title = False
        self.skip_depth = 0
        self.title_chunks: list[str] = []
        self.current_chunks: list[str] = []
        self.blocks: list[str] = []
        self.image_urls: list[str] = []
        self.meta_title = ""
        self.meta_description = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key.lower(): value for key, value in attrs if value is not None}
        lowered_tag = tag.lower()

        if lowered_tag in self.IGNORED_TAGS:
            self.skip_depth += 1
            return

        if self.skip_depth:
            return

        if lowered_tag == "title":
            self.in_title = True
            return

        if lowered_tag == "meta":
            meta_name = (attributes.get("name") or attributes.get("property") or "").lower()
            meta_content = normalize_whitespace(attributes.get("content", ""))
            if not meta_content:
                return
            if meta_name in {"og:title", "twitter:title"} and not self.meta_title:
                self.meta_title = meta_content
            if meta_name in {"description", "og:description", "twitter:description"} and not self.meta_description:
                self.meta_description = meta_content
            return

        if lowered_tag == "img":
            candidate = attributes.get("src") or attributes.get("data-src") or attributes.get("data-original")
            if candidate:
                resolved = urljoin(self.base_url, candidate)
                if resolved.startswith("http://") or resolved.startswith("https://"):
                    self.image_urls.append(resolved)
            return

        if lowered_tag in self.BLOCK_TAGS:
            self.flush()

    def handle_endtag(self, tag: str) -> None:
        lowered_tag = tag.lower()

        if lowered_tag in self.IGNORED_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return

        if self.skip_depth:
            return

        if lowered_tag == "title":
            self.in_title = False
            return

        if lowered_tag in self.BLOCK_TAGS:
            self.flush()

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return

        cleaned = normalize_whitespace(unescape(data))
        if not cleaned:
            return

        if self.in_title:
            self.title_chunks.append(cleaned)
            return

        self.current_chunks.append(cleaned)

    def flush(self) -> None:
        if not self.current_chunks:
            return

        block = normalize_whitespace(" ".join(self.current_chunks))
        self.current_chunks.clear()
        if block:
            self.blocks.append(block)

    @property
    def title(self) -> str:
        preferred = self.meta_title or normalize_whitespace(" ".join(self.title_chunks))
        return preferred

    @property
    def body(self) -> str:
        self.flush()
        deduped: list[str] = []
        previous = ""
        for block in self.blocks:
            if block != previous:
                deduped.append(block)
            previous = block
        return "\n\n".join(deduped)


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def raw_sources_dir(root: Path | None = None) -> Path:
    base = root or repo_root()
    return base / "raw" / "sources"


def raw_assets_dir(root: Path | None = None) -> Path:
    base = root or repo_root()
    return base / "raw" / "assets"


def wiki_sources_dir(root: Path | None = None) -> Path:
    base = root or repo_root()
    return base / "wiki" / "sources"


def today_iso() -> str:
    return date.today().isoformat()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_repo_dirs(root: Path | None = None) -> None:
    base = root or repo_root()
    for path in (
        base / "raw",
        raw_sources_dir(base),
        raw_assets_dir(base),
        raw_assets_dir(base) / "pdfs",
        base / "wiki",
        wiki_sources_dir(base),
        base / "wiki" / "analyses",
        base / "wiki" / "concepts",
        base / "wiki" / "entities",
    ):
        path.mkdir(parents=True, exist_ok=True)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower().strip())
    return slug.strip("-") or "source"


def normalize_whitespace(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def encode_yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def build_frontmatter(fields: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
            continue
        lines.append(f"{key}: {encode_yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def write_text(path: Path, content: str, force: bool = False) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_bytes(path: Path, content: bytes, force: bool = False) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def relative_to_repo(path: Path) -> str:
    try:
        return str(path.relative_to(repo_root()))
    except ValueError:
        return str(path)


def is_relative_to(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


def fetch_url_bytes(url: str, timeout: int = 20) -> tuple[bytes, Any]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers


def decode_response_bytes(data: bytes, headers: Any) -> str:
    charset = None
    if hasattr(headers, "get_content_charset"):
        charset = headers.get_content_charset()

    for candidate in (charset, "utf-8", "cp949", "latin-1"):
        if not candidate:
            continue
        try:
            return data.decode(candidate)
        except UnicodeDecodeError:
            continue

    return data.decode("utf-8", errors="replace")


def guess_extension(url: str, headers: Any, default: str = ".bin") -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix:
        return suffix

    content_type = ""
    if hasattr(headers, "get_content_type"):
        content_type = headers.get_content_type()
    elif hasattr(headers, "get"):
        content_type = headers.get("Content-Type", "")

    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/svg+xml": ".svg",
        "application/pdf": ".pdf",
        "text/html": ".html",
        "text/plain": ".txt",
    }
    return mapping.get(content_type, default)


def extract_title_from_text(text: str, fallback: str) -> str:
    candidate_text = text
    if candidate_text.startswith("---\n"):
        parts = candidate_text.split("\n---", 1)
        if len(parts) == 2:
            candidate_text = parts[1]

    lines = [line.strip() for line in candidate_text.splitlines() if line.strip()]
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()
    for line in lines:
        if not line.startswith("---") and not re.match(r"^[a-zA-Z0-9_-]+:\s", line):
            return line[:120]
    return fallback


def summarize_text(text: str, max_chars: int = 320) -> str:
    blocks = [
        line.strip()
        for line in re.split(r"\n\s*\n", text)
        if line.strip() and not line.strip().startswith("---") and not line.strip().startswith("#")
    ]
    if not blocks:
        return "Initial source capture created. A richer summary should be added by the agent."

    summary = " ".join(blocks[:2])
    summary = normalize_whitespace(summary)
    if len(summary) <= max_chars:
        return summary
    return summary[: max_chars - 3].rstrip() + "..."


def bulletize_text(text: str, max_bullets: int = 5, max_chars: int = 180) -> list[str]:
    summary = summarize_text(text, max_chars=700)
    sentences = [normalize_whitespace(part) for part in SENTENCE_RE.split(summary) if normalize_whitespace(part)]
    bullets = sentences[:max_bullets]
    trimmed: list[str] = []
    for bullet in bullets:
        if len(bullet) > max_chars:
            trimmed.append(bullet[: max_chars - 3].rstrip() + "...")
        else:
            trimmed.append(bullet)
    return trimmed or ["Initial ingest completed; detailed synthesis still needed."]


def download_images(
    image_urls: list[str],
    asset_dir: Path,
    max_images: int = 10,
    timeout: int = 20,
    force: bool = False,
) -> list[Path]:
    downloaded: list[Path] = []
    unique_urls = dedupe_preserve_order(image_urls)
    for index, image_url in enumerate(unique_urls[:max_images], start=1):
        data, headers = fetch_url_bytes(image_url, timeout=timeout)
        extension = guess_extension(image_url, headers, default=".img")
        destination = asset_dir / f"image-{index:02d}{extension}"
        write_bytes(destination, data, force=force)
        downloaded.append(destination)
    return downloaded


def extract_pdf_text(pdf_bytes: bytes) -> tuple[str, int | None, str | None, list[str]]:
    errors: list[str] = []

    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(part.strip() for part in pages if part and part.strip()).strip()
        if text:
            return text, len(reader.pages), "pypdf", errors
        errors.append("pypdf extracted no text")
    except Exception as exc:
        errors.append(f"pypdf unavailable or failed: {exc}")

    try:
        from PyPDF2 import PdfReader  # type: ignore

        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(part.strip() for part in pages if part and part.strip()).strip()
        if text:
            return text, len(reader.pages), "PyPDF2", errors
        errors.append("PyPDF2 extracted no text")
    except Exception as exc:
        errors.append(f"PyPDF2 unavailable or failed: {exc}")

    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temporary:
                temporary.write(pdf_bytes)
                temp_path = Path(temporary.name)
            result = subprocess.run(
                [pdftotext, str(temp_path), "-"],
                capture_output=True,
                text=True,
                check=False,
            )
            text = result.stdout.strip()
            if result.returncode == 0 and text:
                return text, None, "pdftotext", errors
            errors.append(f"pdftotext returned {result.returncode}: {result.stderr.strip()}")
        except Exception as exc:
            errors.append(f"pdftotext failed: {exc}")
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)
    else:
        errors.append("pdftotext not found on PATH")

    return "", None, None, errors


def capture_pdf_source(
    source: str,
    title: str | None = None,
    slug: str | None = None,
    source_date: str | None = None,
    copy_original: bool = False,
    timeout: int = 20,
    force: bool = False,
    fail_on_extract_error: bool = False,
) -> RawCaptureResult:
    root = repo_root()
    ensure_repo_dirs(root)

    source_date = source_date or today_iso()
    original_path: Path | None = None

    if source.startswith("http://") or source.startswith("https://"):
        pdf_bytes, _headers = fetch_url_bytes(source, timeout=timeout)
        inferred_title = title or Path(urlparse(source).path).stem or "document"
        title = inferred_title
        slug = slug or slugify(title)
        original_path = raw_assets_dir(root) / "pdfs" / f"{source_date}-{slug}.pdf"
        write_bytes(original_path, pdf_bytes, force=force)
        source_ref = source
    else:
        input_path = Path(source).expanduser().resolve()
        pdf_bytes = input_path.read_bytes()
        title = title or input_path.stem
        slug = slug or slugify(title)
        source_ref = str(input_path)
        if copy_original:
            original_path = raw_assets_dir(root) / "pdfs" / f"{source_date}-{slug}.pdf"
            write_bytes(original_path, pdf_bytes, force=force)

    extracted_text, page_count, extractor, errors = extract_pdf_text(pdf_bytes)
    if fail_on_extract_error and not extracted_text:
        raise RuntimeError("PDF text extraction failed: " + "; ".join(errors))

    raw_path = raw_sources_dir(root) / f"{source_date}-{slug}.md"
    original_line = f"- Original PDF: `{relative_to_repo(original_path)}`" if original_path else "- Original PDF: not copied"
    note_lines = [f"- {item}" for item in errors] or ["- none"]

    body = extracted_text.strip() or "Text extraction failed. Review the original PDF and extractor notes."
    content = "\n".join(
        [
            build_frontmatter(
                {
                    "title": title,
                    "type": "raw-pdf-source",
                    "captured": today_iso(),
                    "source_date": source_date,
                    "status": "immutable",
                    "source_ref": source_ref,
                    "page_count": page_count if page_count is not None else "unknown",
                    "extractor": extractor or "none",
                    "tags": ["source", "pdf", "ingested"],
                }
            ),
            "",
            f"# {title}",
            "",
            "## Source Metadata",
            "",
            f"- Source ref: `{source_ref}`" if not source.startswith("http") else f"- Source ref: <{source_ref}>",
            original_line,
            "",
            "## Extraction Notes",
            "",
            *note_lines,
            "",
            "## Extracted Text",
            "",
            body,
            "",
        ]
    )
    write_text(raw_path, content, force=force)

    notes = errors[:]
    if not extracted_text:
        notes.append("No PDF text extracted automatically; manual review may be required.")

    return RawCaptureResult(
        kind="pdf",
        title=title,
        slug=slug,
        source_date=source_date,
        source_ref=source_ref,
        raw_path=raw_path,
        text_body=body,
        original_path=original_path,
        extractor=extractor,
        notes=notes,
    )


def capture_url_source(
    url: str,
    title: str | None = None,
    slug: str | None = None,
    source_date: str | None = None,
    download_linked_images: bool = False,
    max_images: int = 10,
    timeout: int = 20,
    force: bool = False,
) -> RawCaptureResult:
    root = repo_root()
    ensure_repo_dirs(root)

    source_date = source_date or today_iso()
    data, headers = fetch_url_bytes(url, timeout=timeout)
    content_type = headers.get_content_type() if hasattr(headers, "get_content_type") else str(headers.get("Content-Type", ""))
    decoded = decode_response_bytes(data, headers)

    image_paths: list[Path] = []
    notes: list[str] = []

    if "pdf" in content_type or Path(urlparse(url).path).suffix.lower() == ".pdf":
        return capture_pdf_source(
            source=url,
            title=title,
            slug=slug,
            source_date=source_date,
            timeout=timeout,
            force=force,
        )

    if "html" in content_type or Path(urlparse(url).path).suffix.lower() in {"", ".html", ".htm"}:
        parser = MarkdownishHTMLParser(url)
        parser.feed(decoded)
        parser.close()
        title = title or parser.title or urlparse(url).netloc
        body_text = parser.body or parser.meta_description or decoded
        slug = slug or slugify(title)
        if download_linked_images and parser.image_urls:
            asset_dir = raw_assets_dir(root) / f"{source_date}-{slug}"
            image_paths = download_images(
                parser.image_urls,
                asset_dir,
                max_images=max_images,
                timeout=timeout,
                force=force,
            )
    else:
        title = title or Path(urlparse(url).path).stem or urlparse(url).netloc
        slug = slug or slugify(title)
        body_text = decoded
        notes.append(f"Captured non-HTML content type: {content_type}")

    raw_path = raw_sources_dir(root) / f"{source_date}-{slug}.md"
    image_lines = [f"- `{relative_to_repo(path)}`" for path in image_paths] or ["- none"]
    note_lines = [f"- {note}" for note in notes] or ["- none"]

    content = "\n".join(
        [
            build_frontmatter(
                {
                    "title": title,
                    "type": "raw-web-source",
                    "captured": today_iso(),
                    "source_date": source_date,
                    "status": "immutable",
                    "source_url": url,
                    "tags": ["source", "web", "ingested"],
                }
            ),
            "",
            f"# {title}",
            "",
            "## Source Metadata",
            "",
            f"- Source URL: <{url}>",
            f"- Captured at: {now_iso()}",
            f"- Content type: {content_type or 'unknown'}",
            "",
            "## Downloaded Images",
            "",
            *image_lines,
            "",
            "## Notes",
            "",
            *note_lines,
            "",
            "## Body",
            "",
            body_text.strip() or "No body text extracted.",
            "",
        ]
    )
    write_text(raw_path, content, force=force)

    return RawCaptureResult(
        kind="url",
        title=title,
        slug=slug,
        source_date=source_date,
        source_ref=url,
        raw_path=raw_path,
        text_body=body_text,
        asset_paths=image_paths,
        notes=notes,
    )


def capture_text_source(
    source: str,
    title: str | None = None,
    slug: str | None = None,
    source_date: str | None = None,
    force: bool = False,
) -> RawCaptureResult:
    root = repo_root()
    ensure_repo_dirs(root)

    input_path = Path(source).expanduser().resolve()
    text = input_path.read_text(encoding="utf-8", errors="replace")

    if is_relative_to(input_path, raw_sources_dir(root)):
        match = DATED_STEM_RE.match(input_path.stem)
        inferred_date = match.group(1) if match else today_iso()
        inferred_slug = match.group(2) if match else slugify(input_path.stem)
        source_date = source_date or inferred_date
        title = title or extract_title_from_text(text, input_path.stem)
        slug = slug or inferred_slug
        return RawCaptureResult(
            kind="text",
            title=title,
            slug=slug,
            source_date=source_date,
            source_ref=str(input_path),
            raw_path=input_path,
            text_body=text,
        )

    source_date = source_date or today_iso()
    title = title or extract_title_from_text(text, input_path.stem)
    slug = slug or slugify(title)
    raw_path = raw_sources_dir(root) / f"{source_date}-{slug}.md"

    content = "\n".join(
        [
            build_frontmatter(
                {
                    "title": title,
                    "type": "raw-text-source",
                    "captured": today_iso(),
                    "source_date": source_date,
                    "status": "immutable",
                    "source_ref": str(input_path),
                    "tags": ["source", "text", "ingested"],
                }
            ),
            "",
            f"# {title}",
            "",
            "## Source Metadata",
            "",
            f"- Original file: `{input_path}`",
            "",
            "## Body",
            "",
            text.strip(),
            "",
        ]
    )
    write_text(raw_path, content, force=force)

    return RawCaptureResult(
        kind="text",
        title=title,
        slug=slug,
        source_date=source_date,
        source_ref=str(input_path),
        raw_path=raw_path,
        text_body=text,
    )


def ensure_index_file(index_path: Path) -> None:
    if index_path.exists():
        return
    content = "\n".join(
        [
            build_frontmatter(
                {
                    "title": "Wiki Index",
                    "type": "index",
                    "status": "active",
                    "source_date": today_iso(),
                    "updated": today_iso(),
                    "tags": ["index", "navigation"],
                }
            ),
            "",
            "# Wiki Index",
            "",
            "## Sources",
            "",
        ]
    )
    index_path.write_text(content, encoding="utf-8")


def ensure_log_file(log_path: Path) -> None:
    if log_path.exists():
        return
    content = "\n".join(
        [
            build_frontmatter(
                {
                    "title": "Wiki Log",
                    "type": "log",
                    "status": "active",
                    "source_date": today_iso(),
                    "updated": today_iso(),
                    "tags": ["log", "timeline"],
                }
            ),
            "",
            "# Wiki Log",
            "",
        ]
    )
    log_path.write_text(content, encoding="utf-8")


def create_or_update_source_page(capture: RawCaptureResult, force: bool = False) -> Path:
    root = repo_root()
    ensure_repo_dirs(root)
    wiki_path = wiki_sources_dir(root) / f"{capture.source_date}-{capture.slug}.md"
    if wiki_path.exists() and not force:
        return wiki_path
    summary = summarize_text(capture.text_body)
    bullets = bulletize_text(capture.text_body)

    content = "\n".join(
        [
            build_frontmatter(
                {
                    "title": capture.title,
                    "type": "source",
                    "status": "active",
                    "source_date": capture.source_date,
                    "updated": today_iso(),
                    "tags": ["source", capture.kind, "auto-generated"],
                }
            ),
            "",
            f"# {capture.title}",
            "",
            "## Source Summary",
            "",
            summary,
            "",
            "## Key Claims Or Observations",
            "",
            *[f"- {bullet}" for bullet in bullets],
            "",
            "## Repo Implications",
            "",
            "- This page was created by the deterministic ingest pipeline.",
            "- A follow-up agent pass should update related concept and entity pages.",
            "",
            "## Related Pages",
            "",
            "- [[overview]]",
            "",
            "## Source Metadata",
            "",
            f"- Raw capture: `{relative_to_repo(capture.raw_path)}`",
            f"- Source ref: <{capture.source_ref}>" if capture.source_ref.startswith("http") else f"- Source ref: `{capture.source_ref}`",
            f"- Original asset: `{relative_to_repo(capture.original_path)}`" if capture.original_path else "- Original asset: none",
            "",
        ]
    )

    write_text(wiki_path, content, force=force)
    return wiki_path


def update_index(index_path: Path, page_stem: str, summary: str) -> bool:
    ensure_index_file(index_path)
    content = index_path.read_text(encoding="utf-8")
    marker = f"[[{page_stem}]]"
    if marker in content:
        return False

    lines = content.splitlines()
    bullet = f"- [[{page_stem}]]: {summary}"
    inserted = False

    for index, line in enumerate(lines):
        if line.strip() == "## Sources":
            insert_at = index + 1
            while insert_at < len(lines) and not lines[insert_at].startswith("## "):
                insert_at += 1
            lines.insert(insert_at, bullet)
            inserted = True
            break

    if not inserted:
        if lines and lines[-1] != "":
            lines.append("")
        lines.extend(["## Sources", "", bullet])

    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def append_log(log_path: Path, capture: RawCaptureResult, wiki_path: Path) -> bool:
    ensure_log_file(log_path)
    content = log_path.read_text(encoding="utf-8")
    identifier = relative_to_repo(wiki_path)
    if identifier in content:
        return False

    entry = "\n".join(
        [
            "",
            f"## [{today_iso()}] ingest | {capture.title}",
            "",
            f"- Source kind: `{capture.kind}`",
            f"- Raw capture: `{relative_to_repo(capture.raw_path)}`",
            f"- Wiki source page: `{relative_to_repo(wiki_path)}`",
            f"- Source ref: <{capture.source_ref}>" if capture.source_ref.startswith("http") else f"- Source ref: `{capture.source_ref}`",
            "- Follow-up recommended: update related concept and entity pages after reviewing the auto summary.",
        ]
    )
    log_path.write_text(content.rstrip() + entry + "\n", encoding="utf-8")
    return True


def recommend_agent_followup(capture: RawCaptureResult, wiki_path: Path) -> str:
    return "\n".join(
        [
            "Next recommended agent prompt:",
            "",
            f"`{relative_to_repo(capture.raw_path)}`를 읽고 `{relative_to_repo(wiki_path)}`를 검토해서",
            "관련 concept/entity page를 업데이트하고 `wiki/index.md`, `wiki/log.md`, `wiki/overview.md`까지 반영해줘.",
        ]
    )
