---
title: "Overview"
type: "overview"
status: "active"
source_date: "2026-04-05"
updated: "2026-04-05"
tags:
  - overview
  - thesis
---

# Overview

This repository tracks Karpathy's `LLM Wiki` idea as a maintained markdown knowledge base rather than a pile of disconnected notes.

## Current thesis

One of the most actionable ideas in Karpathy's recent knowledge-work writing is [[llm-wiki]]: use an LLM to maintain a persistent, interlinked markdown wiki that compounds knowledge over time.

For this repository, that means:

- `raw/` keeps inputs immutable
- `wiki/` holds the maintained synthesis
- `KB_SCHEMA.md` defines how the agent should ingest, answer, and lint
- durable analyses should be filed back into the wiki instead of disappearing into chat

## Current focal points

- [[andrej-karpathy]] as the central entity
- [[llm-wiki]] as the first major concept
- [[2026-04-04-llm-wiki-gist]] as the seed source
- [[karpathy-llm-wiki-pattern]] as the initial implementation analysis
