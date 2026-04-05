---
title: "LLM Wiki"
type: "concept"
status: "seed"
source_date: "2026-04-04"
updated: "2026-04-05"
tags:
  - concept
  - knowledge-base
  - workflow
---

# LLM Wiki

## Definition

`LLM Wiki` is a pattern where the LLM maintains a persistent, interlinked markdown wiki that sits between the user and raw source documents.

The key move is not "retrieve better at query time." The key move is "compile knowledge into a maintained artifact ahead of time and keep it current."

## Why It Matters

Compared with standard RAG:

- knowledge is accumulated rather than rediscovered
- contradictions can be recorded once and surfaced later
- cross-links and summaries improve over time
- useful answers can be promoted into permanent pages

## Evidence And Examples

The concept is introduced in [[2026-04-04-llm-wiki-gist]] and instantiated in this repository through:

- `raw/` as immutable input storage
- `wiki/` as the maintained synthesis layer
- `KB_SCHEMA.md` as the operational schema
- `ingest_pipeline.py`, `wiki_search.py`, and `wiki_healthcheck.py` as the first practical tools

## Tensions Or Disagreements

- The quality of the wiki depends on disciplined maintenance and source curation.
- At small scale, the schema may matter more than tooling. At larger scale, search and lint tooling become more important.
- A wiki can drift if the agent writes plausible synthesis without grounding updates in actual source pages.

## Related Pages

- [[andrej-karpathy]]
- [[karpathy-llm-wiki-pattern]]
- [[overview]]

## Sources

- [[2026-04-04-llm-wiki-gist]]
