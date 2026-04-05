# Knowledge Base Workflow

Use this skill when the user wants to build, maintain, query, or clean up a markdown knowledge base in this repository.

This skill is designed around the `LLM Wiki` pattern:

- `raw/` holds immutable sources
- `wiki/` holds compiled markdown knowledge
- the agent maintains the wiki
- useful answers should be filed back into the wiki

Default repo mode:

- Read `KB_MODE.md` at the repository root.
- If the user does not specify a mode, use the mode declared there.
- If the user explicitly asks for `personal`, `research`, or `team`, that prompt-level request overrides `KB_MODE.md` for the current task.
- Treat `KB_MODE.md` as the canonical mode definition; the summaries below are operational guidance.

Template guide:

- `TEMPLATE_INDEX.md`
- `TEMPLATE_COMMON_SOURCE.md`
- `TEMPLATE_COMMON_ENTITY.md`
- `TEMPLATE_COMMON_CONCEPT.md`
- `TEMPLATE_COMMON_ANALYSIS.md`
- `TEMPLATE_PERSONAL_REFLECTION.md`
- `TEMPLATE_PERSONAL_TIMELINE.md`
- `TEMPLATE_RESEARCH_SOURCE_COMPARISON.md`
- `TEMPLATE_RESEARCH_THESIS_UPDATE.md`
- `TEMPLATE_TEAM_DECISION_RECORD.md`
- `TEMPLATE_TEAM_PROJECT_STATUS.md`

## When to use

Trigger this skill when the user asks to:

- ingest a URL, PDF, or markdown source
- update the wiki from newly added sources
- ask questions against the wiki and save the result as a file
- run health checks or search over the wiki
- maintain `wiki/index.md`, `wiki/log.md`, or `wiki/overview.md`
- use the repository as an Obsidian-friendly knowledge base

## Modes

The architecture stays the same across modes: `raw/`, `wiki/`, and the schema remain the base structure.

What changes by mode:

- preferred page types
- preferred metadata and summaries
- what counts as a high-value output
- what health checks matter most

### Mode: personal

Use when the knowledge base is centered on self-tracking, journaling, personal learning, goals, habits, or reflection.

Emphasize:

- chronology
- recurring patterns
- reflection summaries
- behavior and theme tracking

Preferred templates:

- `TEMPLATE_PERSONAL_REFLECTION.md`
- `TEMPLATE_PERSONAL_TIMELINE.md`

### Mode: research

Use when the knowledge base is centered on papers, articles, experiments, technical ideas, concept maps, or evolving theses.

Emphasize:

- source quality
- claim extraction
- evidence and citation structure
- contradiction handling
- synthesis across multiple sources

Preferred templates:

- `TEMPLATE_COMMON_SOURCE.md`
- `TEMPLATE_COMMON_CONCEPT.md`
- `TEMPLATE_RESEARCH_SOURCE_COMPARISON.md`
- `TEMPLATE_RESEARCH_THESIS_UPDATE.md`

### Mode: team

Use when the knowledge base is centered on internal documentation, meetings, decisions, project state, customer calls, or operations.

Emphasize:

- current state clarity
- decision tracking
- ownership and action context
- onboarding value

Preferred templates:

- `TEMPLATE_TEAM_DECISION_RECORD.md`
- `TEMPLATE_TEAM_PROJECT_STATUS.md`

## Repository-specific tools

Prefer these scripts before inventing new ones:

- `python ingest_url.py "<url>" [--download-images]`
- `python ingest_pdf.py "<path-or-url-to-pdf>" [--copy-original]`
- `python ingest_pipeline.py "<source>" [--kind url|pdf|text]`
- `python wiki_search.py --query "<query>"`
- `python wiki_healthcheck.py`
- `python tools/wiki_tool.py lint`
- `python tools/wiki_tool.py stats`

## Working contract

1. Identify whether the task is `ingest`, `query`, `healthcheck`, or `output generation`.
   - Also identify which mode is active: `personal`, `research`, or `team`.
2. Read the most relevant existing wiki pages before creating new files.
3. Keep raw sources immutable.
4. Put durable outputs into `wiki/analyses/` or another suitable wiki location.
5. Update `wiki/index.md` when creating meaningful new wiki pages.
6. Append to `wiki/log.md` when ingesting sources or creating substantial analyses.
7. Prefer updating an existing page over creating a near-duplicate.

## Mode: ingest

### Default flow

1. Capture the source with `ingest_url.py`, `ingest_pdf.py`, or `ingest_pipeline.py`.
2. Review the resulting raw capture and the generated source page.
3. Update related concept pages.
4. Update related entity pages.
5. Update `wiki/overview.md` if the top-level synthesis changed.
6. Confirm `wiki/index.md` and `wiki/log.md` are current.

Mode-sensitive emphasis:

- `personal`: emphasize themes, timelines, and reflection patterns
- `research`: emphasize evidence, concepts, and contradictions
- `team`: emphasize projects, decisions, and operational summaries

## Mode: query

### Default flow

1. Search the wiki with `wiki_search.py` or by reading `wiki/index.md`.
2. Read the most relevant pages.
3. Synthesize the answer with citations to wiki pages or raw captures.
4. If the answer is reusable, file it back into `wiki/analyses/`.
5. Add links from related concept or entity pages if needed.

Mode-sensitive emphasis:

- `personal`: prefer reflection pages and longitudinal summaries
- `research`: prefer synthesis pages and comparison analyses
- `team`: prefer decision-ready memos and current-state documents

## Mode: healthcheck

### Default flow

1. Run `python wiki_healthcheck.py`.
2. Inspect orphan pages, broken links, and missing frontmatter.
3. Look for concept gaps, stale claims, and weak cross-references.
4. Propose concrete fixes, then apply the high-confidence ones.
5. Log meaningful maintenance work in `wiki/log.md`.

Mode-sensitive emphasis:

- `personal`: check continuity and recurring self-observation threads
- `research`: check claim conflicts, evidence gaps, and missing concept pages
- `team`: check stale status docs, weak onboarding pages, and missing decision records

## Mode: output generation

Good output targets:

- markdown analysis
- comparison table
- strategy memo
- onboarding note
- Marp slide deck
- chart or figure

## Goal

The purpose of this workflow is not to create a prettier notes folder.

The purpose is to build a persistent working memory where:

- sources remain auditable
- the LLM handles the bookkeeping
- good answers become durable artifacts
- the knowledge base compounds over time
