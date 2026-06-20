---
name: setup-wiki
description: "USER-INVOKED ONLY (via /setup-wiki). One-time setup for a fresh LLM Code Wiki created from the template: verifies the hash script on this OS, then customizes Purpose, the scope tag, and the repo registry. Do NOT run this automatically or as part of any other task — only when the user explicitly types /setup-wiki."
disable-model-invocation: true
---

# Set up this wiki (one-time)

Run **only** when the user invokes `/setup-wiki`. This walks a fresh clone of the LLM Code Wiki
template through first-time setup. Be friendly and brief; do the mechanical work yourself and ask
the user only what you genuinely cannot infer. Work through the steps in order.

## 0. Confirm this is a fresh template

If `repos.md` already lists real repos and the Purpose in `CLAUDE.md` is already filled, this wiki
is probably already set up — confirm with the user before changing anything.

## 1. Verify hashing on this OS

Detect the platform and smoke-test the matching script so staleness detection works here.

**macOS / Linux** (bash):
```bash
chmod +x scripts/hash.sh
echo "hello" > /tmp/_wiki_t.txt
H=$(scripts/hash.sh /tmp/_wiki_t.txt)            # prints a hash
scripts/hash.sh /tmp/_wiki_t.txt "$H"            # FRESH
echo "changed" > /tmp/_wiki_t.txt
scripts/hash.sh /tmp/_wiki_t.txt "$H"            # STALE
rm /tmp/_wiki_t.txt
scripts/hash.sh /tmp/_wiki_t.txt "$H"            # MISSING
```

**Windows** (PowerShell):
```powershell
"hello" | Out-File -Encoding utf8 $env:TEMP\_wiki_t.txt
$H = scripts\hash.ps1 -File $env:TEMP\_wiki_t.txt            # prints a hash
scripts\hash.ps1 -File $env:TEMP\_wiki_t.txt -Recorded $H    # FRESH
"changed" | Out-File -Encoding utf8 $env:TEMP\_wiki_t.txt
scripts\hash.ps1 -File $env:TEMP\_wiki_t.txt -Recorded $H    # STALE
Remove-Item $env:TEMP\_wiki_t.txt
scripts\hash.ps1 -File $env:TEMP\_wiki_t.txt -Recorded $H    # MISSING
```

Report the four verdicts (hash / FRESH / STALE / MISSING). If the tool is missing:
- Linux without `sha256sum`/`shasum` → tell the user to install coreutils.
- Windows → `Get-FileHash` ships with PowerShell 4+; if missing, update PowerShell.

## 2. Define the Purpose

Ask the user, in one or two questions: **What is this knowledge base about — its center of
gravity?** (e.g. "our payments platform, with competitor repo X as reference," or "the Linux
kernel networking stack"). Then rewrite the `## Purpose & scope` section of `CLAUDE.md`, replacing
the `<!-- CUSTOMIZE -->` placeholder with a pointed one-paragraph description.

## 3. Set the `scope:` tag

Ask whether their knowledge splits into distinct "worlds" worth tagging. Offer common shapes:
`ours`/`theirs`, `v1`/`v2`, `frontend`/`backend`, or **none** (single world). Update the
`### The scope: tag` section of `CLAUDE.md` to list the chosen values (or note that `scope:` is
unused and may be omitted from frontmatter).

## 4. Fill the repo registry

Help the user populate `repos.md`. Offer to scan sibling directories for git repos to suggest rows:
```bash
for d in ../*/ ../*/*/; do [ -d "$d/.git" ] && echo "$(basename "$d") -> $d"; done
```
For each repo the user wants to track, add a row: `name | scope | path | notes`. Use **relative
paths from the repo root** (where `repos.md` lives), e.g. `../some-repo`. Remove the example rows.
Confirm the table with the user.

## 5. Choose how you'll access the wiki

Ask the user: **"Do you want to reach this wiki from ANY repo, or only when you're working inside
this repo?"**

- **From any repo (global access).** Install a thin, user-level `/wiki` skill that points at this
  wiki's absolute path, so you can query or file into the wiki while coding elsewhere. Do this:
  1. Get this wiki's absolute path: `pwd` (call it `<WIKI_PATH>`).
  2. Create `~/.claude/skills/wiki/` and write `~/.claude/skills/wiki/SKILL.md` with the content
     below, substituting `<WIKI_PATH>` literally (no trailing slash):

     ```
     ---
     name: wiki
     description: "USER-INVOKED ONLY (via /wiki). Access the LLM Code Wiki at <WIKI_PATH> from any repo — query it or file insights into it. On invocation, read <WIKI_PATH>/CLAUDE.md and follow it, anchoring ALL paths to the wiki root. Do NOT auto-trigger; only run when the user types /wiki."
     ---

     # Access the LLM Code Wiki

     The wiki artifact lives at: `<WIKI_PATH>`

     When invoked from anywhere:
     1. Read `<WIKI_PATH>/CLAUDE.md` — it is the single source of truth for how this wiki works.
        Follow it. (Do not duplicate its rules here; always defer to it.)
     2. Anchor **every** wiki operation to `<WIKI_PATH>` as the base directory: index reads, page
        paths, `repos.md` path resolution, and the hash-script staleness checks all resolve
        relative to `<WIKI_PATH>`, NOT the repo you happen to be invoked from.
     3. Follow the wiki interaction loop: understand -> propose -> confirm/deny -> write. Never
        write without the user's confirmation.
     4. The repo you are currently in may be a SOURCE for the wiki (cite it via `repos.md`), but
        the wiki itself is always at `<WIKI_PATH>`.
     ```
  3. Tell the user to **restart Claude Code**, then `/wiki` is available everywhere.
  4. If this wiki repo isn't in `repos.md` of itself and the user codes in repos not yet
     registered, remind them new source repos must be added to `<WIKI_PATH>/repos.md`.

- **Only inside this repo (in-repo, default).** Do nothing — the repo's own `CLAUDE.md`
  auto-loads whenever an agent works in this folder, so the wiki is fully usable here with no
  global install. (They can re-run `/setup-wiki` later to switch to global access.)

## 6. Tidy up (offer, don't force)

Ask whether to:
- Delete `wiki/decisions/example-decision.md` and its `wiki/decisions/index.md` row (format demo).
- Reset `wiki/log.md` to a fresh first entry dated today.
- Re-initialize git history (`rm -rf .git && git init`) so the wiki starts with its own history
  instead of the template's. **Confirm explicitly before running any `rm`.**
- If the user uses a global "research cache" skill that auto-triggers, remind them this wiki
  replaces it here (see the *Optional integrations* note in `CLAUDE.md`).

## 7. Done

Summarize what changed, and reassure the user there are no commands to memorize — just ask in
plain English. Give examples: "scan / read `<repo>`" to map a repo, ask any question to research,
"save this" to keep a session insight, "check the wiki" to health-check for out-of-date pages.
Suggest opening the **`wiki/`** folder as the Obsidian vault. If a global `CLAUDE.md` nudge or
skill was added, remind them to restart Claude Code.
