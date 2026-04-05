# Knowledge Base Schema

This document defines how the markdown knowledge base should be maintained by an LLM agent.

It complements the root `AGENTS.md`. `AGENTS.md` governs agent behavior broadly. This file governs the wiki itself.

Exact source reference for this schema:

- `KARPATHY_LLM_WIKI_GIST.md`
- `GIST_ALIGNMENT.md`

## Objective

Build a persistent markdown wiki that compounds over time.

The wiki should:

- accumulate knowledge instead of rediscovering it on every query
- preserve a clean separation between raw sources and compiled knowledge
- make contradictions and missing links visible
- turn useful answers into durable wiki pages

## Core architecture

There are three layers:

1. `raw/`
   - Immutable inputs.
   - Articles, papers, datasets, screenshots, PDFs, and source captures live here.
   - Do not rewrite raw material during normal maintenance.

2. `wiki/`
   - LLM-maintained markdown knowledge base.
   - Source pages, concepts, entities, analyses, overview, index, and log live here.

3. `KB_SCHEMA.md`
   - Operational rules for how the LLM maintains the wiki.

Supporting root-level utilities:

- `TEMPLATE_INDEX.md`
  - Index of canonical templates
- `ingest_url.py`
  - Fetches a URL into `raw/sources/`
  - Can optionally localize linked images
- `ingest_pdf.py`
  - Converts a local or remote PDF into a raw markdown capture
- `ingest_pipeline.py`
  - Runs source capture plus initial wiki updates (`wiki/sources/`, `wiki/index.md`, `wiki/log.md`)
- `wiki_search.py`
  - Naive CLI search over `wiki/` and optionally `raw/`
  - Supports JSON output for agent consumption
- `wiki_healthcheck.py`
  - Structural health check for the wiki

## Directory conventions

Use this structure:

- `raw/sources/`
- `raw/assets/`
- `wiki/entities/`
- `wiki/concepts/`
- `wiki/sources/`
- `wiki/analyses/`

Special files:

- `wiki/index.md`: content-oriented catalog
- `wiki/log.md`: append-only chronological log
- `wiki/overview.md`: current top-level synthesis

## Page types

### Entity page

Required sections:

- Summary
- Why it matters here
- Related concepts
- Open questions
- Sources

### Concept page

Required sections:

- Definition
- Why it matters
- Evidence and examples
- Tensions or disagreements
- Related pages
- Sources

### Source page

Required sections:

- Source summary
- Key claims or observations
- Repo implications
- Related pages
- Source metadata

### Analysis page

Required sections:

- Question or framing
- Synthesis
- Evidence
- Conclusions
- Follow-up questions
- Sources

## Metadata conventions

Prefer YAML frontmatter. Use at least:

```yaml
title:
type:
status:
source_date:
updated:
tags:
```

Page type values:

- `entity`
- `concept`
- `source`
- `analysis`
- `index`
- `overview`
- `log`

Status values:

- `seed`
- `active`
- `superseded`

## Link conventions

- Prefer Obsidian-style `[[wiki-links]]`.
- Every meaningful page should link to other pages when possible.
- Every new page should be added to `wiki/index.md`.
- Entity and concept pages should cross-link, not only point to source pages.

## Ingest workflow

When a new source arrives:

1. Preserve the raw material under `raw/`.
   - Prefer `ingest_url.py`, `ingest_pdf.py`, or `ingest_pipeline.py` when applicable.
2. Create or update a page in `wiki/sources/`.
3. Update `wiki/overview.md` if the top-level synthesis changed.
4. Update all relevant entity pages.
5. Update all relevant concept pages.
6. Create an analysis page if the source unlocks a useful synthesis.
7. Update `wiki/index.md`.
8. Append an entry to `wiki/log.md`.

When the source contains relevant images or assets, preserve them locally under `raw/assets/` when practical.

## Query workflow

When answering questions:

1. Read `wiki/index.md` first.
2. Read the most relevant existing pages before touching raw sources.
3. Answer from the wiki whenever possible.
4. If the answer creates durable value, file it back into `wiki/analyses/`.
5. Link the new analysis from related entity and concept pages when useful.

Prefer artifact outputs over chat-only answers when the result will be reused:

- markdown page
- slide deck
- chart or figure
- comparison matrix

## Lint workflow

Periodically check for:

- broken wiki links
- orphan pages
- duplicate stems
- stale or superseded claims
- concepts referenced often but lacking their own page
- places where a comparison page would be more useful than scattered notes

Canonical commands:

```bash
python wiki_search.py --query "llm wiki"
python wiki_healthcheck.py
python wiki_healthcheck.py --json
```

## Source handling rules

- Raw sources are the source of truth.
- Derived wiki pages should never pretend to be raw captures.
- When evidence conflicts, record the conflict instead of smoothing it over.

## Writing rules

- Prefer dense, factual writing over motivational prose.
- Keep page titles stable.
- Update existing pages before creating near-duplicates.
- Put durable synthesis into the wiki; leave ephemeral coordination in chat.
- Mark inference as inference.
- Use exact dates when timing matters.

## Logging rules

`wiki/log.md` is append-only.

Use headings in this format:

```md
## [YYYY-MM-DD] operation | title
```

Valid operation labels include:

- `bootstrap`
- `ingest`
- `analysis`
- `lint`
- `refactor`

## Definition of done

An ingest or analysis task is not complete until:

- relevant wiki pages are updated
- `wiki/index.md` is current
- `wiki/log.md` has a new entry
- contradictions or uncertainties are explicitly noted
