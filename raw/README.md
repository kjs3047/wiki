# Raw Layer

`raw/` stores immutable inputs and reference captures.

Rules:

- do not rewrite or summarize raw files in place after ingest
- if a file is not the true original source, label it clearly
- store local assets under `raw/assets/`
- store source captures under `raw/sources/`

This layer exists so the wiki can be regenerated or audited later.
