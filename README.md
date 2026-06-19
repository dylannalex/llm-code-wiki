# LLM Code Wiki — Template

A ready-to-use template for a **knowledge base over living code repositories**, maintained by an LLM
agent. You curate sources and ask questions; the agent reads your code, writes interlinked
markdown pages, keeps them cross-referenced, and flags pages that go stale when the code changes.

Works on **macOS, Linux, and Windows** with no dependencies (uses your shell's built-in hashing),
and it's **dead simple to set up** — run one command and you're up and running in a few minutes.

## Who is this for?

Anyone who accumulates knowledge across one or more codebases and is tired of re-deriving it every
time. For example:

- **Engineers onboarding to a large or unfamiliar codebase** — build a map that compounds instead
  of re-reading the same files.
- **Teams building a new system while learning from an existing one** — capture "how do they do X,
  how should we" as first-class `comparisons/` pages.
- **People studying reference / competitor / upstream repos** — keep a durable, cross-referenced
  understanding rather than scattered notes.
- **Anyone who wants design decisions, mental models, and vocabulary to persist** beyond chat
  history.

It's a good fit if your knowledge is rooted in **code that changes over time** (staleness is
handled). It's overkill if you just need a few static notes — and it's not a RAG index; it's a
synthesized, hand-curated (by the LLM) wiki.

## Setup (2 minutes)

1. Copy this template to a new folder and open it with your LLM agent (e.g. Claude Code).
2. Run **`/setup-wiki`** — it verifies hashing on your OS, then asks you a few things (what the
   wiki is about, your optional `scope:` tags, which repos to track, and whether to access it from
   any repo via a global `/wiki` command) and fills everything in.

That's it. (Prefer to do it by hand? Edit the Purpose + `scope:` in `CLAUDE.md` and fill `repos.md`.)

## Daily use — just talk to your agent

| You say | It does |
|---|---|
| "seed-sweep `<repo>`" | maps a repo into `wiki/repositories/<repo>/overview.md` |
| ask any question | answers from the wiki, offers to file the synthesis |
| "file this" | saves a session's conclusions to `wiki/decisions/` or `wiki/concepts/` |
| "lint the wiki" | flags stale pages (via hashing), orphans, and gaps |

## How it works

- The knowledge lives in **`wiki/`** (open Obsidian there); the machinery (`CLAUDE.md`,
  `repos.md`, `scripts/`) stays at the repo root, out of the vault.
- **`CLAUDE.md`** is the schema — structure, page format, and workflows. Your agent reads it every
  session, so the operating manual lives in the repo itself.
- Sources are **referenced + content-hashed, never copied**, so staleness is detectable.
- **`repos.md`** maps a repo name to wherever you cloned it.
- It's just a git repo of markdown — version history and Obsidian's graph view come free.

See `wiki/decisions/example-decision.md` for the page format (delete it once you're rolling).
