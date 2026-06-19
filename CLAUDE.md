# LLM Code Wiki — Schema

This repo is a **persistent, LLM-maintained knowledge base** (a Karpathy-style "LLM Wiki")
whose primary sources are **living code repositories** — repos that change over time —
supplemented by other sources (issue trackers, web, notes, AI sessions).

You (the LLM) own and maintain every page here. The human curates sources, asks questions, and
directs analysis — you do all the summarizing, cross-referencing, filing, and bookkeeping.

> **This file is the schema.** It tells you how the wiki is structured and what workflows to
> follow. Co-evolve it with the human as conventions improve.

> **Getting started?** See [[README]] for the quickstart. The first things to customize are the
> Purpose section below, the `scope:` axis values, and [[repos]] (the repo registry).

## Purpose & scope

<!-- CUSTOMIZE: one paragraph describing what THIS knowledge base is for and its center of
gravity — e.g. "Understanding our payments platform, using competitor repo X as a reference,"
or "Studying the Linux kernel networking stack." Keep it pointed; it guides every ingest. -->

A knowledge base centered on **<your primary system/codebase>**, with **<reference codebases>**
as a reference library, plus personal learnings (tech, vocabulary, concepts worth pinning down).

## Why "living code" changes the design

Unlike a generic notes wiki, the primary sources here *change*. Three consequences shape
everything below:
1. **Sources are referenced + content-hashed, never copied** — so staleness is detectable
   (`scripts/hash.sh`), not silent.
2. **A repo registry ([[repos]]) maps a repo NAME → on-disk path** — code lives wherever it's cloned.
3. **The taxonomy is code-shaped** — repositories, concepts spanning repos, contracts between
   services, comparisons of implementations.

## Structure

The **knowledge lives in `wiki/`** (the Obsidian vault — open Obsidian there) and the
**machinery lives at the repo root**. Pages are interlinked markdown using `[[wikilinks]]`.

```
repo root (machinery — keep out of the vault):
  README.md          human quickstart
  CLAUDE.md          this schema (must stay at root so Claude Code auto-loads it)
  repos.md           repo registry: maps repo NAME -> on-disk path + scope
  scripts/hash.sh    staleness checker (macOS/Linux)
  scripts/hash.ps1   staleness checker (Windows) — same CLI contract
  .claude/skills/    e.g. setup-wiki

wiki/ (the Obsidian vault — the knowledge):
  index.md           root catalog — lists the category folders (NOT individual pages)
  log.md             chronological, append-only activity log
  repositories/      one subfolder per repo; overview.md is the hub + that repo's index
  concepts/          cross-cutting mechanisms + cross-repo system synthesis
  contracts/         service-to-service interfaces / boundaries (optional; software-systems)
  comparisons/       compare two implementations / approaches / codebases
  glossary/          short definitional vocabulary pages
  projects/          initiatives, time-oriented (fed by your tracker + notes)
  decisions/         ADR-style decision records (incl. filed AI-session conclusions)
  sources/           on-demand summaries of substantial raw/ sources
  raw/               IMMUTABLE non-code originals (articles, notes, tracker snapshots, sessions)
```

### Path resolution (note: "repo root" ≠ "vault root")
- **`repository` source paths** resolve via [[repos]] (`repos.md`), whose paths are relative to
  the **repo root** (repos are typically siblings, e.g. `../some-repo/...`). Unchanged by nesting.
- **`file` source paths and `[[wikilinks]]`** are relative to the **vault** (`wiki/`), e.g.
  `raw/articles/x.md` means `wiki/raw/articles/x.md`.
- When the staleness scripts run from the repo root, prefix vault-relative `file` paths with
  `wiki/`. Repository paths need no prefix.

Pick the hash script by OS: `scripts/hash.sh` on macOS/Linux, `scripts/hash.ps1` on Windows
(`hash.ps1 -File <f> [-Recorded <hash>]`). Both print the same `<sha256>` / `FRESH|STALE|MISSING`
and emit lowercase hashes, so a hash recorded on one OS validates on another. No runtime deps.

Every category folder has its own `index.md` (one line per page) **except** `repositories/`,
where each repo's `overview.md` serves as that repo's index. (`repositories/index.md` is a
catalog *across* repos.)

### Page categories — when to use which
- **repositories/`<repo>`/** — what a specific codebase is and how it works. `overview.md` is
  the map (structure, entry points, stack, key modules). Split a section into its own sub-page
  only when it gets long *or* you keep querying it (lazy splitting — don't pre-split).
- **concepts/** — an *idea* or mechanism that may span codebases, or cross-repo system synthesis
  ("the platform end to end" stitching several repos).
- **contracts/** — how service A exposes data for service B to consume (schemas, boundaries).
  Optional — drop it if your domain isn't multi-service.
- **comparisons/** — two implementations side by side (ours vs theirs, v1 vs v2, fork vs upstream).
- **glossary/** — short definition of a term/tech. If it grows a thesis, graduate it to concepts/.
- **projects/** — initiative status/decisions/blockers, fed by your tracker + notes.
- **decisions/** — what was chosen, the alternatives, and why. Also where valuable
  **ai-agent-session** conclusions get filed.

`repositories/` = code artifacts. A *system* that spans repos lives in `concepts/` and links the
relevant repo pages.

## Frontmatter (every page)

```yaml
---
title: <human title>
scope: <value>               # OPTIONAL partition axis — see below. Omit if you don't need it.
type: <category>             # repository | concept | contract | comparison | glossary | project | decision
sources:
  - source_type: repository  # repository | file | web | tracker | ai-agent-session
    path: <locator>
    sha256: <hash>           # for hashable LOCAL files (repository, file)
    pulled: 2025-01-01       # for live/remote sources (web, tracker, ai-agent-session)
status: current              # current | stale | draft
updated: 2025-01-01
tags: [..]
---
```

### The `scope:` axis (optional, customize)
A single partition dimension for knowledge that lives in distinct "worlds." Pick values that fit
your domain and list them here, or drop `scope:` entirely if everything is one world. Examples:
- `ours` / `theirs` (your code vs a reference codebase)
- `v1` / `v2` (before/after a rewrite)
- `frontend` / `backend`
- `personal` (your own learnings, regardless of codebase)

The point of a single tag (rather than top-level folders per world) is that **comparison pages
and cross-cutting concepts stay single pages** — which is the high-value use case. The tag gives
you the "show me only X" view via Obsidian's filters when you want it.

### Source rules
- `path` is the **universal locator**, interpreted by `source_type`:
  - `repository` → `<repo-name>/<in-repo path>`. Resolve `<repo-name>` via [[repos]].
  - `file` → a path under `raw/`.
  - `web` → the URL.
  - `tracker` → the issue/ticket ID in your tracker (Jira, Linear, GitHub Issues, etc.).
  - `ai-agent-session` → optional `raw/ai-agent-sessions/<date>-<slug>.md` snapshot.
- Use **`sha256`** for hashable local files (repository, file) — precise staleness.
  Use **`pulled`** (date) for live/remote sources that can't be hashed.
- `source_type` is explicit (never parsed from `path`) so `lint` knows re-hash vs warn-stale.

## Workflows

### The interaction loop (applies to BOTH ingest and research/query)
1. **Understand.** Build genuine understanding first. Explore the relevant code/sources
   yourself; **ask the human only when there is genuine ambiguity the sources cannot resolve.**
   If the code already answers it, stay silent and go to step 2.
2. **Propose.** State that you'll update the wiki, and give an overview: which pages you'll
   create/update and the key points captured. Concise enough to eyeball.
3. **Confirm / deny.** Wait for the human's go. Write nothing before this gate.
   Escape hatch: if the human says "just file it," collapse step 1 for trivial sources.
4. **Write.** Apply the maintenance protocol below.

### Ingest scope (code repos)
- When a repo is **first added**: do one light **seed sweep** — structure, entry points, stack,
  top-level modules — to create `repositories/<repo>/overview.md` (breadth, not depth) + stamp
  sources. Add the repo to [[repos]] if missing.
- After that, ingests are **topic-slice driven**: deep-read only the slice relevant to the
  question/design, and write/update the pages it touches.

### Maintenance protocol (on every write)
1. Write/update the page(s).
2. Update the page's **folder `index.md`** entry (or the repo's `overview.md` for drill-downs).
3. Update root `index.md` **only** if a new folder/category or new repo appears.
4. Append a `log.md` entry: `## [YYYY-MM-DD] <op> | <title>` where op ∈ {ingest, query, lint, file}.
5. Maintain `[[wikilinks]]` to related pages in both directions where it makes sense.

### Filing insights from a session
Valuable conclusions from a working session shouldn't die in chat history. When the human says
"file this," run the write step: usually a `decisions/` page (design conclusions + rejected
alternatives) or `concepts/` (understanding reached). Use `source_type: ai-agent-session`, and
snapshot substantial sessions to `raw/ai-agent-sessions/`.

### Query
Navigate top-down: read root `index.md` → pick a folder → read its `index.md` →
drill into the 1-2 relevant pages. Answer with citations to wiki pages. If the answer is itself
valuable synthesis, offer to file it back as a new page.

### Lint (run when asked)
- **Staleness:** for each page, run the OS-appropriate hash script (`scripts/hash.sh` on
  macOS/Linux, `scripts/hash.ps1` on Windows) as `<script> <resolved-file> <recorded-sha256>` on
  every `repository`/`file` source. On `STALE`/`MISSING`, set `status: stale` and report. For
  `web`/`tracker`/`ai-agent-session`, flag entries with old `pulled` dates as "may be stale."
- Orphans (no inbound links), missing cross-references, concepts mentioned but lacking a page,
  contradictions between pages, data gaps fillable by web search.
- Suggest new questions to investigate and new sources to find.

## Optional integrations
- **Issue tracker (`source_type: tracker`).** If your tracker has an API/MCP server (Jira,
  Linear, GitHub Issues, ...), pull live and reference by ticket ID + `pulled` date;
  snapshot to `raw/tracker/` only for important/volatile items. Synthesis compounds in `projects/`.
- **A global "research cache" skill.** If your LLM setup has a separate research-cache mechanism
  that runs by default, disable it *in this repo* — this wiki replaces it (and absorbs its
  per-file hashing for staleness). The two would otherwise duplicate.

## Future improvements
- **qmd** (github.com/tobi/qmd) — local hybrid BM25/vector search + MCP server over the wiki
  markdown. Add when index-based navigation gets slow (~hundreds of pages). Indexes the same
  files; nothing to migrate.
