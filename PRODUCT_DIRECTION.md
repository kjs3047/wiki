# Product Direction

This note translates the Karpathy gist into a concrete product direction for this repository.

## Product thesis

The opportunity is not just note-taking.

It is a workflow product with five connected surfaces:

1. source ingest into a durable raw layer
2. LLM-managed compilation into a structured wiki
3. a frontend for browsing and visualizing the knowledge base
4. agent-callable tools for querying and maintaining the wiki
5. artifact outputs that can be filed back into the system

## Immediate build direction

This repository already has the seed of that model:

- `raw/` for source material
- `wiki/` for compiled markdown knowledge
- `KB_SCHEMA.md` for operating rules
- `ingest_url.py`, `ingest_pdf.py`, and `ingest_pipeline.py` for getting sources into the system
- `wiki_search.py` and `wiki_healthcheck.py` for working the knowledge base

## Why not jump straight to complex RAG

At moderate scale, maintained summaries and indexes can carry a surprising amount of the load.

A better order of operations is:

1. get the wiki maintenance loop correct
2. add simple search and lint tools
3. introduce heavier retrieval infrastructure only when scale actually demands it

## Design constraints

- raw sources must remain auditable and stable
- durable outputs should land back in the repository
- the agent should be the default maintainer
- the human should mostly curate, inspect, and ask better questions
