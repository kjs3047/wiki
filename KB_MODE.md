# Knowledge Base Mode

This file defines the default operating mode for the repo-local `knowledge-base-workflow` skill.

This is the canonical definition for mode selection in this repository.

## Default mode

`research`

## Meaning

The current repository should behave as a research-oriented knowledge base unless the user explicitly overrides the mode in the prompt.

This means the default emphasis is on:

- source ingest quality
- concept extraction
- evidence tracking
- contradiction handling
- synthesis across multiple sources
- durable analysis pages

## Allowed overrides

The user can temporarily override the default mode in a prompt, for example:

- `knowledge-base-workflow 스킬로 personal 모드로 진행해줘`
- `knowledge-base-workflow 스킬로 research 모드로 ingest해줘`
- `knowledge-base-workflow 스킬로 team 모드로 health check 해줘`

## Mode summary

`personal`

- goals
- journals
- habits
- reflection
- personal pattern tracking

`research`

- papers
- articles
- claims
- concepts
- thesis building

`team`

- meetings
- project docs
- decision logs
- onboarding
- operational state
