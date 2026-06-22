# Log

Chronological, append-only. One entry per operation.
Format: `## [YYYY-MM-DD] <op> | <title>` where op ∈ {add, query, check, file}.

Quick peek at recent activity: `grep "^## \[" log.md | tail -5`