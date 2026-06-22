# Skills in this repo

There are two skills, deliberately kept in **different folders** because they activate in
opposite places.

| Skill | Location | Auto-loads in this repo? | Purpose |
|---|---|---|---|
| `setup-wiki` | `.claude/skills/setup-wiki/` | **Yes** | One-time `/setup-wiki` wizard, run from inside this repo |
| `wiki` | `skills/wiki/` (plain dir) | **No** | Version-controlled *template* for the global skill |

`.claude/skills/` is what Claude Code auto-discovers when you work inside this repo. `setup-wiki`
belongs there because you invoke it here. `wiki` is deliberately parked **outside** `.claude/` so
it does **not** auto-load in-repo: it's a template containing a `<WIKI_PATH>` placeholder that is
invalid until setup substitutes the real path. If it lived in `.claude/skills/`, it would
auto-register here and could fire with a broken path. Don't "tidy up" by moving them together.

## How `/setup-wiki` installs the global `wiki` skill

Setup does **not** symlink and does **not** touch this repo's `.claude/`. It installs a
substituted **copy** into your **user-global** skills dir:

```bash
WIKI_PATH="$(pwd)"                                   # this wiki's absolute path
mkdir -p ~/.claude/skills/wiki
sed "s|<WIKI_PATH>|$WIKI_PATH|g" skills/wiki/SKILL.md > ~/.claude/skills/wiki/SKILL.md
```

- **Creates a new file** at `~/.claude/skills/wiki/SKILL.md` — the *user-level* skills dir, not the
  repo's `.claude/`. User-level skills load in every repo, which is what makes the wiki reachable
  **globally** from any project.
- **Copy, not symlink.** The `sed` bakes this wiki's absolute path into the copy. A symlink would
  mirror the unsubstituted `<WIKI_PATH>` placeholder and break.
- **The schema is not copied.** Only the thin skill is. The installed copy holds the absolute path
  and reads `constitution.md` live from it — so day-to-day schema edits need no reinstall. Re-run
  the `sed` line only when the wiki moves, or when `skills/wiki/SKILL.md` itself changes.

Working **inside this repo** needs no install: the root `CLAUDE.md` auto-loads and redirects to
`constitution.md`.
