---
name: deep-research
description: "Run a deep, multi-agent research pass over one or more code repositories and file the findings into the LLM Code Wiki. Use when the user wants to map/inventory/survey some theme across repos (e.g. 'research all the X across these repos', 'map every Y', 'deep dive on Z and write it up'), especially when it warrants parallel sub-agents. Grills the user on scope before starting, reads with Sonnet sub-agents, and writes the wiki with an Opus 4.8[1m] sub-agent. Works from any repo; all writes target the wiki at the path below."
---

# Deep research → LLM Code Wiki

The wiki lives at: `<WIKI_PATH>`

This skill runs a repeatable, **topic-agnostic** research workflow that ends with new/updated wiki
pages. The *subject* (AI features, auth flows, data pipelines, a migration, whatever) comes from the
user — this skill only defines the **method**.

## Before anything: read the constitution

**Read `<WIKI_PATH>/constitution.md` first.** It is the single source of truth for the wiki —
taxonomy, frontmatter schema, the interaction loop, the maintenance protocol, path resolution, and
the propose→confirm→write gate. Anchor every wiki path to `<WIKI_PATH>`. Do not duplicate its rules
here; this skill only adds the multi-agent *research method* on top of it.

## Two hard rules

1. **Grill before you research.** Do not spawn a single research agent until you and the user reach
   a shared understanding of the plan (see Phase 0). This is the most important rule.
2. **Read with Sonnet, write with Opus.** All lookup/discovery/deep-dive sub-agents run on
   **Sonnet** (`model: sonnet`). The wiki is written by a **single Opus writer sub-agent**
   (`model: claude-opus-4-8[1m]`). The orchestrator (you) synthesizes between the two.

---

## Phase 0 — Grill session (interview before research)

Enter plan mode, then **interview the user relentlessly down the design tree**, resolving
dependencies one decision at a time. For **every** question, offer your **recommended answer first**
(label it "(Recommended)"). Use `AskUserQuestion`; batch related questions, but sequence so that a
decision is settled before the ones that depend on it. Keep going until the plan is unambiguous.

Walk at least these branches (adapt to the topic):

- **Subject definition / scope** — what *exactly* counts as an instance of the thing being
  researched? (Cast the net explicitly; tag findings by sub-type.)
- **Repos / surface area** — which repos are in scope? Check `<WIKI_PATH>/repos.md`: register any
  on-disk-but-unregistered repo *before* citing it (the validator rejects unregistered repos), and
  honor the **Ignored** list.
- **Depth** — first-pass breadth only, or breadth then deep-dive every instance now?
- **Output shape** — per-repo pages + a cross-cutting `concepts/` synthesis? A `contracts/` page for
  cross-repo boundaries? A `comparisons/` page? (Default: per-repo + one synthesis page.)
- **Extra lenses** — beyond the obvious, what should every finding capture? (e.g. cost/latency,
  failure modes, data/PII, data storage, cross-repo links, eval/quality, security.) Ask, since these
  shape the deep-dive prompts.
- **Source links** — do they want clickable links back to code? If GitHub, confirm the remote +
  default branch per repo (`git -C <path> remote get-url origin`,
  `git -C <path> rev-parse --abbrev-ref origin/HEAD`) and build links as
  `https://github.com/<org>/<repo>/blob/<branch>/<path>#L<n>` — **not** local paths.
- **Sub-agent fan-out** — discovery granularity (default: one Sonnet agent per repo) and deep-dive
  granularity (default: one Sonnet agent per confirmed cluster).
- **Write model & concurrency** — confirm the single serialized Opus 4.8[1m] writer (parallel
  writers corrupt the shared `index.md`/`log.md`; the constitution's concurrency rule mandates
  serialized writes / union merges).
- **Gates** — a checkpoint after discovery to prune the inventory, and the constitution's
  pre-write proposal gate. Plus whether to snapshot the session to `raw/ai-agent-sessions/`.

Finish the grill with `ExitPlanMode` presenting the agreed plan. Only proceed once approved.

---

## Phase A — Discovery (Sonnet, parallel, read-only)

Spawn one **Sonnet** sub-agent per in-scope repo (in a single message, in parallel). Each returns:

- a light **first-pass map** of the repo (purpose, stack, entry points, top-level layout) for an
  `overview.md`, and
- an **inventory** of every surface matching the agreed subject definition: name, sub-type tag,
  file path(s) + line numbers, where it's invoked, and a one-line description.

Agents **do not write**. They report structured findings back to you.

## Checkpoint 1 — Prune the inventory

Present the combined inventory grouped into deep-dive **clusters** (merge tightly-coupled surfaces
so you don't spawn one agent per file). The user confirms/prunes which clusters get deep-dived.

## Phase B — Deep-dive (Sonnet, parallel, read-only)

Spawn one **Sonnet** sub-agent per confirmed cluster (parallel). Each deep-reads its cluster and
returns a structured brief covering the agreed lenses, with **exact source citations** (and the
agreed GitHub links). No writes.

## Synthesis + pre-write proposal gate (you)

Collect all Phase A + B findings, dedupe, and decide the final page set + structure. Then run the
constitution's gate: **present a written proposal** (every page to create/update, key findings,
sources) and **wait for the user's go**. Write nothing before approval.

## Phase C — Write (single Opus 4.8[1m] writer, serialized)

Dispatch **one** `model: opus` writer sub-agent that writes all pages **sequentially**
(overviews → per-repo subject pages → synthesis → any contract/comparison → session snapshot →
indexes/log). Brief it fully (it shares none of your context): the page set, the synthesized
content per page, the agreed source links, and these obligations from the constitution:

- correct frontmatter; `sha256` for every cited `repository`/`file` source (via the OS hash script);
- the maintenance protocol (page → folder `index.md` → root `index.md` only for new categories →
  append `log.md` → bidirectional `[[wikilinks]]`);
- one writer only, sequential, to avoid `index.md`/`log.md` conflicts.

## Verify

After writes, run `python3 <WIKI_PATH>/scripts/validate.py` (schema, source freshness/re-hash,
index presence, ignore list). Fix anything it flags in the pages you wrote; re-run until clean.

---

## Model assignment, in one line

**Sonnet** = Phase A discovery + Phase B deep-dive (read/lookup). **Opus 4.8[1m]** = the single
serialized wiki writer. You (orchestrator) grill, synthesize, and gate.
