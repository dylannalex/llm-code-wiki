---
name: wiki
description: "Access the LLM Code Wiki — a persistent, LLM-maintained knowledge base over living code repositories. Use when the user wants to map/scan/read a repo into the wiki, ask a question answerable from accumulated knowledge, add/import a source (article, ticket, note), file/save a session insight into the wiki, or check/audit the wiki for staleness. Works from any repo; all operations target the wiki at the path below."
---

# Access the LLM Code Wiki

> TEMPLATE FILE. `/setup-wiki` installs a copy of this skill into `~/.claude/skills/wiki/` with
> `<WIKI_PATH>` replaced by this wiki's absolute path. Do not rely on the placeholder at runtime.

The wiki lives at: `<WIKI_PATH>`

On every invocation:

1. **Read `<WIKI_PATH>/constitution.md` first.** It is the single source of truth for how this
   wiki is structured and maintained — taxonomy, frontmatter schema, the interaction loop, the
   maintenance protocol, and path resolution. Follow it. Do not act on the wiki before reading it,
   and do not duplicate its rules here.
2. **Anchor every path to `<WIKI_PATH>`.** Index reads, page paths, `repos.md` resolution, and the
   hash-script staleness checks all resolve relative to `<WIKI_PATH>`, **not** the repo you were
   invoked from.
3. **Follow the interaction loop** from the constitution: understand → propose → confirm → write.
   Never write to the wiki without the user's confirmation.
4. The repo you are currently in may be a **source** for the wiki — register it in
   `<WIKI_PATH>/repos.md` — but the wiki itself is always at `<WIKI_PATH>`.
