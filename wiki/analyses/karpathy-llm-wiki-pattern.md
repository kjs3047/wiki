---
title: "Karpathy LLM Wiki Pattern"
type: "analysis"
status: "active"
source_date: "2026-04-05"
updated: "2026-04-05"
tags:
  - analysis
  - implementation
  - workflow
---

# Karpathy LLM Wiki Pattern

## Question Or Framing

How should Karpathy's `LLM Wiki` idea be translated into an immediately usable repository structure?

## Synthesis

The important part of the idea is not simply "store notes in markdown." It is to define a maintenance loop where the LLM continuously turns sources and questions into a better knowledge graph.

The repository therefore needs:

1. strict separation between raw inputs and maintained knowledge
2. a schema that tells the LLM how to ingest, answer, and lint
3. navigation files that stay current
4. enough tooling to catch obvious wiki drift
5. small CLIs that the LLM can call directly for ingest, search, and maintenance

## Evidence

[[2026-04-04-llm-wiki-gist]] emphasizes:

- raw sources as source of truth
- a wiki directory maintained by the LLM
- a schema document controlling agent behavior
- `index.md` and `log.md` as special files
- ingest, query, and lint as recurring operations

## Conclusions

The repository should be treated as a living compiled knowledge base, not as a notebook dump and not as a thin wrapper around search.

That means future work should prioritize:

- ingest discipline
- index and log maintenance
- creating concept pages before fragmentation grows
- turning valuable answers into durable analysis pages
- rendering outputs as files that can be reviewed in Obsidian instead of only returning terminal text

## Follow-up Questions

- Which Karpathy topics should become the next seeded concept pages?
- Should the repository eventually add richer output formats such as Marp slides or charts?
- What would a real product version look like beyond a collection of scripts?

## Sources

- [[2026-04-04-llm-wiki-gist]]
- [[llm-wiki]]
- [[andrej-karpathy]]
