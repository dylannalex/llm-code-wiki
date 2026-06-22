# Repo registry

Maps a repo **name** (used in page `sources[].path`) to its on-disk location and `scope`.
Paths are relative to this wiki repo's root, so they survive moving the whole tree.
Adding a repo is a one-line addition here — no need to move or re-clone anything.

How resolution works: a page cites `path: my-service/src/foo.ts` → look up `my-service` here →
`../path/to/my-service` → read/hash `../path/to/my-service/src/foo.ts`.

<!-- CUSTOMIZE: replace the example rows with your repos. The `scope` column is optional;
use it to tag which "world" a repo belongs to (see the scope axis in constitution.md). -->

| name        | scope  | path                       | notes              |
|-------------|--------|----------------------------|--------------------|
| my-service  | ours   | ../my-service              | example — replace  |
| their-tool  | theirs | ../reference/their-tool    | example — replace  |

## Planned (not yet cloned)

Repos you intend to study but haven't cloned. Move a row up once it's on disk.

| name | scope |
|------|-------|
| _none_ | |

## Ignored (do not track)

Repos the wiki should **never** scan, map, or register — even if encountered while working from
them. The agent checks this list before a first-pass map or registry add, and `scripts/validate.py`
**deterministically rejects** any page whose `repository` source points at a name listed here. Use
it for throwaway scratch repos, vendored mirrors, or repos out of scope for this wiki.

| name | reason |
|------|--------|
| _none_ | |
