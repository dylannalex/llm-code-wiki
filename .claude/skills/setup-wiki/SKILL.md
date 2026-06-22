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

If `repos.md` already lists real repos and the Purpose in `constitution.md` is already filled, this
wiki is probably already set up — confirm with the user before changing anything.

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
kernel networking stack"). Then rewrite the `## Purpose & scope` section of `constitution.md`,
replacing the `<!-- CUSTOMIZE -->` placeholder with a pointed one-paragraph description.

## 3. Set the `scope:` tag

Ask whether their knowledge splits into distinct "worlds" worth tagging. Offer common shapes:
`ours`/`theirs`, `v1`/`v2`, `frontend`/`backend`, or **none** (single world). Update the
`### The scope: tag` section of `constitution.md` to list the chosen values (or note that `scope:`
is unused and may be omitted from frontmatter).

## 4. Fill the repo registry

Help the user populate `repos.md`. Offer to scan sibling directories for git repos to suggest rows:
```bash
for d in ../*/ ../*/*/; do [ -d "$d/.git" ] && echo "$(basename "$d") -> $d"; done
```
For each repo the user wants to track, add a row: `name | scope | path | notes`. Use **relative
paths from the repo root** (where `repos.md` lives), e.g. `../some-repo`. Remove the example rows.
Confirm the table with the user.

## 5. Install the global `wiki` skill

This wiki is meant to be reached from **any repo**, so install the user-level `wiki` skill. It's a
thin entry point: its body just reads `constitution.md` (the single source of truth) and anchors
all paths to this wiki. The repo ships a version-controlled template at `skills/wiki/SKILL.md`;
install a copy with this wiki's absolute path baked in:

```bash
WIKI_PATH="$(pwd)"                                   # no trailing slash
mkdir -p ~/.claude/skills/wiki
sed "s|<WIKI_PATH>|$WIKI_PATH|g" skills/wiki/SKILL.md > ~/.claude/skills/wiki/SKILL.md
```

Then:
1. Confirm the install path printed back the real absolute path (no leftover `<WIKI_PATH>`).
2. Tell the user to **restart Claude Code**, after which the `wiki` skill is available everywhere
   and auto-triggers when they talk about the wiki (mapping a repo into it, asking a question,
   filing an insight, checking staleness) — no command to memorize.
3. Remind them: when they want to track a new source repo, add it to `<WIKI_PATH>/repos.md`.

> Re-run this step (or just re-run the `sed` line) whenever the wiki moves to a new path, or when
> `skills/wiki/SKILL.md` itself changes. Day-to-day schema edits go in `constitution.md`, which the
> installed skill reads live by absolute path — so those need no reinstall.

**Working inside this repo** needs no install: the short `CLAUDE.md` here auto-loads and redirects
to `constitution.md`.

## 5b. Enable validation (optional — requires Python 3)

The repo ships an opt-in validator (`scripts/validate.py`) that enforces the frontmatter schema,
source freshness (re-hashing), and index presence. If the user doesn't want it, skip this step —
the validator files lie dormant and are safe to delete.

If they do want it:
1. Confirm Python 3 is available: `command -v python3`. If absent, tell the user to install
   Python 3 or skip this step.
2. Smoke-test it on the fresh vault and confirm it passes:
   ```bash
   python3 scripts/validate.py            # should exit 0 (ok)
   ```
3. Activate the local pre-commit hook so commits that fail validation are blocked:
   ```bash
   chmod +x scripts/hooks/pre-commit
   git config core.hooksPath scripts/hooks
   ```
4. A CI workflow ships at `.github/workflows/validate.yml` (runs
   `python3 scripts/validate.py --no-repo-hash`, since CI can't see sibling code repos). Keep it if
   using GitHub Actions; delete it otherwise.

## 6. Tidy up (offer, don't force)

Ask whether to:
- The vault ships empty; the decision-page format demo lives in `docs/example-decision-page.md`
  (keep it as a reference, or delete it once the user is comfortable with the format).
- Reset `wiki/log.md` to a fresh first entry dated today.
- Re-initialize git history (`rm -rf .git && git init`) so the wiki starts with its own history
  instead of the template's. **Confirm explicitly before running any `rm`.**
- If the user uses a global "research cache" skill that auto-triggers, remind them this wiki
  replaces it here (see the *Optional integrations* note in `constitution.md`).

## 7. Done

Summarize what changed, and reassure the user there are no commands to memorize — just ask in
plain English. Give examples: "scan / read `<repo>`" to map a repo, ask any question to research,
"save this" to keep a session insight, "check the wiki" to health-check for out-of-date pages.
Suggest opening the **`wiki/`** folder as the Obsidian vault. Remind them to restart Claude Code
so the global `wiki` skill loads.
