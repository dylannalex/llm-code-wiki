# LLM Code Wiki — Template

A ready-to-use template for a **knowledge base over living code repositories**, maintained by an LLM
agent. You curate sources and ask questions; the agent reads your code, writes interlinked
markdown pages, keeps them cross-referenced, and flags pages that go stale when the code changes.

Works on **macOS, Linux, and Windows** with no dependencies (uses your shell's built-in hashing),
and it's **dead simple to set up** — run one command and you're up and running in a few minutes.

## The big picture

```mermaid
flowchart LR
    you(["You"])
    prompt["Your prompt (plain English)<br/>• 'scan the auth repo'<br/>• 'how does X work?'<br/>• 'save this'<br/>• 'check the wiki'"]
    code[("Your code<br/>repositories")]
    llm{{"LLM agent"}}
    wiki[["wiki/<br/>interlinked<br/>markdown pages"]]

    you -- "types" --> prompt
    prompt --> llm
    code -- "reads (never copies)" --> llm
    llm -- "writes & cross-links" --> wiki
    wiki -- "answers your questions" --> you
    code -. "code changes →<br/>pages flagged stale" .-> wiki
```

**In one sentence:** you point the agent at code and ask questions; it reads the code, writes a
cross-linked wiki of what it learned, and flags pages as stale when the underlying code changes.

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

1. Get the template — either clone the repo or download it as a zip:
   - Clone: `git clone https://github.com/dylannalex/llm-code-wiki.git`
   - Or download: [main.zip](https://github.com/dylannalex/llm-code-wiki/archive/refs/heads/main.zip) and unzip it.

   Then open the folder with your LLM agent (e.g. Claude Code).
2. Run **`/setup-wiki`** — it verifies hashing on your OS, then asks you a few things (what the
   wiki is about, your optional `scope:` tags, and which repos to track) and fills everything in.
   It also installs a global `wiki` skill so you can reach the wiki from any repo.

That's it.

## Daily use — just talk to your agent

There are **no special commands or exact wording** to memorize — ask in plain English and the
agent recognizes what you want. The phrasings below are just examples; say it however feels
natural.

| When you want to… | Say something like… | The agent… |
|---|---|---|
| Map out a repo | "scan / read / summarize `<repo>`" | reads it and writes `wiki/repositories/<repo>/overview.md` |
| Answer a question | "how does X work?" | answers from the wiki, offers to save the synthesis |
| Add another source | "add / import this article (or ticket)" | summarizes it and files it, cross-linked |
| Save what you figured out | "save this" / "file this" | writes it to `wiki/decisions/` or `wiki/concepts/` |
| Check the wiki is up to date | "check / audit the wiki" | flags out-of-date pages (via hashing), orphans, and gaps |
| See how much you've used it | "show wiki stats" | runs a local script: pages, sources, activity, orphans, size |

## How it works

Two zones: **machinery** at the repo root, **knowledge** in `wiki/`.

```mermaid
flowchart TB
    skill["wiki skill<br/>(reachable from any repo)"]

    subgraph root["repo root — machinery"]
        const["constitution.md<br/>the schema · single source of truth"]
        repos["repos.md<br/>repo name → on-disk path"]
        scripts["scripts/<br/>hashing · validate · metrics"]
    end

    subgraph vault["wiki/ — the knowledge (Obsidian vault)"]
        pages["interlinked markdown pages<br/>repositories · concepts · decisions · …"]
    end

    code[("your code<br/>repositories")]

    skill -- "reads on every call" --> const
    const -- "defines structure of" --> pages
    code -- "referenced + hashed,<br/>never copied" --> pages
    repos -. "resolves names in" .-> pages
    code -. "code changes →<br/>hash mismatch →<br/>page flagged stale" .-> scripts
    scripts -. "marks" .-> pages
```

- **`constitution.md`** holds the whole schema. The global **`wiki`** skill reads it on every call
  (so the wiki works from any repo); a short root **`CLAUDE.md`** redirects here when you work inside.
- Sources are **referenced + content-hashed, never copied** — so staleness is detectable, not silent.
- **`repos.md`** maps each repo name to wherever you cloned it.
- It's just git + markdown — version history and Obsidian's graph view come free.
- **Optional** (enable via `/setup-wiki`): a Python validator (pre-commit / CI) enforces schema and
  freshness; `scripts/metrics.py` reports local usage stats to a gitignored `metrics/` folder.

### What lives in `wiki/`

| Folder | Holds |
|---|---|
| `repositories/` | One subfolder per repo; `overview.md` maps its structure and is that repo's index. |
| `concepts/` | Cross-cutting mechanisms and cross-repo system synthesis. |
| `contracts/` | Service-to-service interfaces and boundaries (optional; multi-service domains). |
| `comparisons/` | Two implementations side by side — ours vs theirs, v1 vs v2, fork vs upstream. |
| `glossary/` | Short definitions of a term or technology. |
| `projects/` | Initiative status, decisions, and blockers — fed by your tracker + notes. |
| `decisions/` | ADR-style records: what was chosen, the alternatives, and why. |
| `sources/` | On-demand summaries of substantial `raw/` originals. |
| `raw/` | Immutable non-code originals — articles, notes, tracker snapshots, sessions. |

Plus `index.md` (root catalog) and `log.md` (append-only activity log). Every folder has its own
`index.md` except `repositories/`, where each repo's `overview.md` serves as the index.

See `docs/example-decision-page.md` for a worked example of the page format.
