# Log

Chronological, append-only. One entry per operation.
Format: `## [YYYY-MM-DD] <op> | <title>` where op ∈ {add, query, check, file}.

Quick peek at recent activity: `grep "^## \[" log.md | tail -5`

## [2025-01-01] file | Wiki initialized from template

Created from the LLM Code Wiki template. Next steps: customize the Purpose in `../constitution.md`, set
the `scope:` values, and fill in `../repos.md`. See [[decisions/example-decision]] for the page format.
