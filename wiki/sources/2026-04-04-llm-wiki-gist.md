---
title: "2026-04-04 LLM Wiki gist"
type: "source"
status: "active"
source_date: "2026-04-04"
updated: "2026-04-05"
tags:
  - source
  - karpathy
  - knowledge-base
---

# 2026-04-04 LLM Wiki gist

## Source Summary

Karpathy describes a pattern for personal or team knowledge bases where an LLM incrementally maintains a structured markdown wiki instead of relying primarily on raw-document retrieval at question time.

He frames the wiki as a persistent artifact that compounds:

- sources stay immutable
- summaries and entity pages are updated over time
- questions can create durable analysis pages
- a schema document teaches the LLM how to behave as the wiki maintainer

## Key Claims Or Observations

- Standard RAG often rediscovers knowledge from scratch on each query.
- A maintained wiki preserves synthesis, contradictions, and cross-references between sessions.
- The LLM should own the bookkeeping work humans usually abandon.
- `index.md` and `log.md` are especially important because they help both humans and agents navigate the growing wiki.
- Search tooling can stay simple at moderate scale if summaries and indexes are maintained well.
- Outputs should be file-based artifacts such as markdown, Marp slides, or images, not only chat responses.

## Repo Implications

This repository adopts the source as an architectural seed:

- [[llm-wiki]] becomes the first concept page
- [[overview]] becomes the current synthesis page
- `KB_SCHEMA.md` becomes the maintenance contract
- `wiki/index.md` and `wiki/log.md` become required maintenance surfaces
- `ingest_*`, `wiki_search.py`, and `wiki_healthcheck.py` become the first practical CLIs

## Related Pages

- [[llm-wiki]]
- [[andrej-karpathy]]
- [[karpathy-llm-wiki-pattern]]

## Source Metadata

- Gist text: `KARPATHY_LLM_WIKI_GIST.md`
- Original URL: <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
