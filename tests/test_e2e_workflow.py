from __future__ import annotations

import base64
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest


REPO_ROOT = Path(__file__).resolve().parent.parent
ROOT_FILES = [
    "ingest_lib.py",
    "ingest_url.py",
    "ingest_pdf.py",
    "ingest_pipeline.py",
    "wiki_search.py",
    "wiki_healthcheck.py",
]
MINIMAL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Zb7sAAAAASUVORK5CYII="
)
MINIMAL_PDF = b"%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 72 120 Td (Hello PDF) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000063 00000 n \n0000000122 00000 n \n0000000208 00000 n \ntrailer\n<< /Root 1 0 R /Size 5 >>\nstartxref\n302\n%%EOF\n"


class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class TestHTTPServer:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.httpd: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.base_url = ""

    def __enter__(self) -> str:
        handler = partial(QuietHTTPRequestHandler, directory=str(self.directory))
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        host, port = self.httpd.server_address
        self.base_url = f"http://{host}:{port}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        time.sleep(0.1)
        return self.base_url

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd.server_close()
        if self.thread is not None:
            self.thread.join(timeout=5)


def copy_root_files(destination: Path) -> None:
    for name in ROOT_FILES:
        shutil.copy2(REPO_ROOT / name, destination / name)


def run_python(repo_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", *args],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
    )


def write_overview(repo_dir: Path, source_stem: str) -> None:
    overview = repo_dir / "wiki" / "overview.md"
    overview.parent.mkdir(parents=True, exist_ok=True)
    overview.write_text(
        "\n".join(
            [
                "---",
                'title: "Overview"',
                'type: "overview"',
                'status: "active"',
                'source_date: "2026-04-04"',
                'updated: "2026-04-04"',
                "tags:",
                "  - overview",
                "---",
                "",
                "# Overview",
                "",
                f"- [[{source_stem}]]",
                "- [[index]]",
                "",
            ]
        ),
        encoding="utf-8",
    )


class EndToEndWorkflowTests(unittest.TestCase):
    def test_text_ingest_search_and_healthcheck(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir)
            copy_root_files(repo_dir)

            source_path = repo_dir / "sample-source.md"
            source_path.write_text(
                "# Persistent Wiki\n\nA persistent wiki keeps knowledge current instead of rediscovering it on every query.\n",
                encoding="utf-8",
            )

            ingest = run_python(repo_dir, "ingest_pipeline.py", str(source_path), "--kind", "text", "--date", "2026-04-04")
            self.assertEqual(ingest.returncode, 0, msg=ingest.stderr or ingest.stdout)

            source_stem = "2026-04-04-persistent-wiki"
            raw_capture = repo_dir / "raw" / "sources" / f"{source_stem}.md"
            wiki_source = repo_dir / "wiki" / "sources" / f"{source_stem}.md"
            self.assertTrue(raw_capture.exists())
            self.assertTrue(wiki_source.exists())

            search = run_python(repo_dir, "wiki_search.py", "--query", "persistent wiki", "--json")
            self.assertEqual(search.returncode, 0, msg=search.stderr or search.stdout)
            payload = json.loads(search.stdout)
            self.assertTrue(any(item["path"] == f"wiki/sources/{source_stem}.md" for item in payload))

            write_overview(repo_dir, source_stem)
            healthcheck = run_python(repo_dir, "wiki_healthcheck.py", "--json")
            self.assertEqual(healthcheck.returncode, 0, msg=healthcheck.stderr or healthcheck.stdout)
            report = json.loads(healthcheck.stdout)
            self.assertEqual(report["broken_links"], [])
            self.assertEqual(report["orphan_pages"], [])
            self.assertEqual(report["pages_with_no_outgoing_links"], [])
            self.assertEqual(report["missing_frontmatter"], [])

    def test_url_ingest_downloads_assets_from_local_server(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "repo"
            server_dir = Path(tmp_dir) / "server"
            repo_dir.mkdir(parents=True, exist_ok=True)
            server_dir.mkdir(parents=True, exist_ok=True)
            copy_root_files(repo_dir)

            (server_dir / "image.png").write_bytes(MINIMAL_PNG)
            (server_dir / "article.html").write_text(
                """
                <html>
                  <head><title>Local Example</title></head>
                  <body>
                    <article>
                      <h1>Local Example</h1>
                      <p>The local article describes a persistent wiki workflow.</p>
                      <img src=\"/image.png\" />
                    </article>
                  </body>
                </html>
                """,
                encoding="utf-8",
            )

            with TestHTTPServer(server_dir) as base_url:
                result = run_python(
                    repo_dir,
                    "ingest_url.py",
                    f"{base_url}/article.html",
                    "--download-images",
                    "--date",
                    "2026-04-04",
                )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            raw_capture = repo_dir / "raw" / "sources" / "2026-04-04-local-example.md"
            asset_dir = repo_dir / "raw" / "assets" / "2026-04-04-local-example"
            self.assertTrue(raw_capture.exists())
            self.assertTrue(asset_dir.exists())
            self.assertTrue(any(path.suffix == ".png" for path in asset_dir.iterdir()))

    def test_pdf_ingest_creates_raw_capture_and_copies_original(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir)
            copy_root_files(repo_dir)

            pdf_path = repo_dir / "hello.pdf"
            pdf_path.write_bytes(MINIMAL_PDF)

            result = run_python(
                repo_dir,
                "ingest_pdf.py",
                str(pdf_path),
                "--date",
                "2026-04-04",
                "--copy-original",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            raw_capture = repo_dir / "raw" / "sources" / "2026-04-04-hello.md"
            copied_original = repo_dir / "raw" / "assets" / "pdfs" / "2026-04-04-hello.pdf"
            self.assertTrue(raw_capture.exists())
            self.assertTrue(copied_original.exists())


if __name__ == "__main__":
    unittest.main()
