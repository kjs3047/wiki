# Gist Alignment

This note maps the Karpathy gist to the current repository implementation.

Authoritative source text:

- `KARPATHY_LLM_WIKI_GIST.md`

## Core idea

Gist claim:

- avoid rediscovering knowledge from scratch at query time
- build a persistent, compounding wiki between the user and raw sources

Repository mapping:

- `raw/` for immutable sources
- `wiki/` for compiled markdown knowledge
- `KB_SCHEMA.md` for the workflow contract

## Architecture

Gist layers:

1. raw sources
2. the wiki
3. the schema

Repository mapping:

- raw layer: `raw/`
- wiki layer: `wiki/`
- schema layer: `AGENTS.md` plus `KB_SCHEMA.md`

## Operations

Gist operations:

- ingest
- query
- lint

Repository mapping:

- source capture: `ingest_url.py` and `ingest_pdf.py`
- end-to-end bootstrap ingest: `ingest_pipeline.py`
- query helper: `wiki_search.py`
- lint helper: `wiki_healthcheck.py`

## Indexing and logging

Repository mapping:

- `wiki/index.md`
- `wiki/log.md`

## Optional CLI tools

Repository mapping:

- `wiki_search.py` provides naive full-text search with optional JSON output
- `wiki_healthcheck.py` provides structural checks for wiki maintenance

## Immediate next steps

1. add richer ingest helpers for URLs, PDFs, repos, and image bundles
2. add file-based outputs such as slide decks and charts
3. deepen linting for stale claims and concept gaps
4. add a small local UI for browsing results and generated artifacts
