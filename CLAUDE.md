# LLM Code Wiki — in-repo pointer

This is the **LLM Code Wiki** repo. The full schema and all workflows live in **`constitution.md`**
(the single source of truth) — this file only exists so that working *inside* this repo loads the
right context.

**Before doing any wiki operation here, read `constitution.md` and follow it.** Do not duplicate
its rules; always defer to it.

When working inside this repo, the wiki root is this directory, so paths resolve locally. From
*other* repos, the wiki is reached via the global `wiki` skill (installed by `/setup-wiki`), which
reads `constitution.md` and anchors paths to this repo's absolute location.
