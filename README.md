# LLM Knowledge Base Workspace

A practical implementation of Andrej Karpathy's `LLM Wiki` pattern.

This repository is for building and operating a markdown knowledge base where:

- `raw/` stores immutable sources
- `wiki/` stores the compiled markdown knowledge base
- the LLM maintains the wiki over time
- useful answers are filed back into the wiki as durable artifacts

## Core idea

Most document workflows with LLMs behave like one-shot RAG: upload files, retrieve chunks, answer a question, repeat.

This repository takes a different approach. Instead of rediscovering knowledge from scratch on every query, the LLM incrementally builds and maintains a persistent wiki between you and the raw sources.

The result is a compounding artifact:

- sources stay auditable
- summaries and links improve over time
- contradictions can be recorded once and reused later
- questions can become new analysis pages instead of disappearing into chat history

## Repository layout

- `raw/`: immutable sources and downloaded assets
- `wiki/`: source pages, concept pages, entity pages, analyses, index, and log
- `tests/`: unit and end-to-end tests
- `.agents/skills/knowledge-base-workflow/`: repo-local skill for operating the knowledge base

## Canonical files

- exact Karpathy gist text: `KARPATHY_LLM_WIKI_GIST.md`
- schema: `KB_SCHEMA.md`
- default mode: `KB_MODE.md`
- skill: `.agents/skills/knowledge-base-workflow/SKILL.md`
- template index: `TEMPLATE_INDEX.md`

## Canonical CLIs

- `python ingest_url.py "<url>"`
- `python ingest_pdf.py "<path-or-url-to-pdf>"`
- `python ingest_pipeline.py "<source>"`
- `python wiki_search.py --query "<query>"`
- `python wiki_healthcheck.py`

## Repo-local skill

This repository includes a repo-local skill:

- `.agents/skills/knowledge-base-workflow/SKILL.md`

Suggested invocation phrases:

- `knowledge-base-workflow 스킬로 진행해줘`
- `knowledge-base-workflow 스킬로 research 모드로 ingest해줘`
- `knowledge-base-workflow 스킬로 team 모드로 health check 해줘`

The skill handles the default workflow:

1. capture the source into `raw/`
2. create or update the wiki source page
3. update relevant concept and entity pages
4. keep `wiki/index.md` and `wiki/log.md` current
5. save durable answers back into the wiki

## Modes

The repository default mode is defined in `KB_MODE.md`.

Current default:

- `research`

Prompt-level mode overrides:

- `personal`
- `research`
- `team`

The mode does not change the raw/wiki/schema architecture.
It changes operating priorities.

- `personal`: journals, goals, habits, reflections, recurring patterns
- `research`: papers, articles, claims, concepts, evidence, thesis-building
- `team`: meetings, project docs, decisions, onboarding, operational state

## Split templates

Canonical templates are split into root-level files:

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

See `TEMPLATE_INDEX.md` for the full mapping.

## Quick start

```bash
python ingest_pipeline.py "https://example.com/article" --download-images
python wiki_search.py --query "persistent wiki"
python wiki_healthcheck.py
```

After the pipeline run, ask the agent to do the semantic pass:

```text
방금 ingest한 source를 읽고 관련 concept page와 entity page를 업데이트해줘.
기존 wiki와 충돌하는 주장도 있으면 표시해줘.
```

## Practical walkthroughs

### Example 1: ingest a web article

```bash
python ingest_pipeline.py "https://example.com/article" --download-images
```

Then:

```text
knowledge-base-workflow 스킬로 이 source를 기존 wiki와 연결해줘.
```

### Example 2: ingest a PDF

```bash
python ingest_pipeline.py "C:\research\paper.pdf" --kind pdf --copy-original
```

Then:

```text
knowledge-base-workflow 스킬로 이 논문을 기존 source들과 비교 분석해서 analysis page로 저장해줘.
```

### Example 3: ingest existing markdown notes

```bash
python ingest_pipeline.py "C:\notes\ai\agent-memory.md" --kind text
```

Then:

```text
knowledge-base-workflow 스킬로 이 메모를 concept page까지 연결해줘.
```

### Smallest demo

```bash
python ingest_pipeline.py "KARPATHY_LLM_WIKI_GIST.md" --kind text --date 2026-04-04
python wiki_search.py --query "persistent wiki"
python wiki_healthcheck.py
```

## How to use the knowledge base after it grows

Use it for more than recall.

1. Fast recall
   - recover what you already know without starting from scratch
2. Multi-source synthesis
   - compare and merge claims across many sources
3. Decision support
   - generate options, risks, and strategic summaries
4. Artifact generation
   - save analyses, tables, briefs, and slides back into the repo
5. Gap detection
   - find contradictions, orphan pages, and missing concepts

The operating loop is:

1. ingest new sources
2. let the LLM update the wiki
3. ask questions against the wiki
4. save the best answers back into the wiki
5. run search and health checks
6. identify gaps and collect the next sources

## Validation

The repository includes CI in `.github/workflows/python-ci.yml`.

It runs:

- `python -m py_compile`
- `python -m unittest discover -s tests -v`

The test suite includes end-to-end coverage for:

- text ingest via `ingest_pipeline.py`
- local HTTP URL ingest via `ingest_url.py`
- PDF ingest via `ingest_pdf.py`
- downstream `wiki_search.py`
- downstream `wiki_healthcheck.py`
