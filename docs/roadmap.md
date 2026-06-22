# Roadmap & maintainer notes

> Notes for people **developing the template**, not for running a wiki. These are intentionally
> kept out of `constitution.md` so they don't add recurring token cost to every skill invocation
> (the skill reads `constitution.md` in full each time it fires, from any repo).

## Future improvements

- **qmd** (github.com/tobi/qmd) — local hybrid BM25/vector search + MCP server over the wiki
  markdown. Add when index-based navigation gets slow (~hundreds of pages). Indexes the same
  files; nothing to migrate.
