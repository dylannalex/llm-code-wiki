#!/usr/bin/env python3
"""LLM Code Wiki integrity validator.

Enforces the maintenance protocol from constitution.md against the pages in
the wiki/ vault. Standard library only (no PyYAML, no pip dependencies).

For each markdown page under wiki/ (excluding wiki/raw/, any index.md, and
wiki/log.md) it checks:
  - frontmatter is present and parseable for this constrained schema
  - required fields and their allowed values
  - each source's locator resolves and (for hashable local files) matches its
    recorded sha256; live sources have a recent `pulled` date
  - no `repository` source points at a repo listed under '## Ignored' in repos.md
  - the page is referenced from the appropriate index / overview

See constitution.md for the authoritative schema.
"""

import argparse
import datetime
import hashlib
import os
import re
import sys


# ----------------------------------------------------------------------------
# Constants from the schema (constitution.md)
# ----------------------------------------------------------------------------

VALID_TYPES = {
    "repository", "concept", "contract", "comparison",
    "glossary", "project", "decision",
}
VALID_STATUSES = {"current", "stale", "draft"}
VALID_SOURCE_TYPES = {"repository", "file", "web", "tracker", "ai-agent-session"}
LIVE_SOURCE_TYPES = {"web", "tracker", "ai-agent-session"}
REQUIRED_FIELDS = ["title", "type", "status", "updated", "sources", "tags"]

# Folders whose pages must appear in that folder's own index.md.
INDEXED_FOLDERS = {
    "concepts", "contracts", "comparisons", "glossary",
    "projects", "decisions", "sources",
}

PULLED_WARN_DAYS = 180


# ----------------------------------------------------------------------------
# Minimal YAML frontmatter parser (for THIS constrained schema only)
# ----------------------------------------------------------------------------

class FrontmatterError(Exception):
    """Raised when a page's frontmatter block cannot be parsed."""


def _strip_inline_comment(value):
    """Remove a trailing `# comment` from a scalar value (outside quotes)."""
    in_single = in_double = False
    for i, ch in enumerate(value):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            # Treat as a comment only if preceded by whitespace or at start.
            if i == 0 or value[i - 1] in " \t":
                return value[:i]
    return value


def _unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _parse_scalar(raw):
    return _unquote(_strip_inline_comment(raw).strip())


def _parse_inline_list(raw):
    """Parse `[a, b, c]` into a list of strings."""
    inner = raw.strip()[1:-1].strip()
    if not inner:
        return []
    return [_unquote(item.strip()) for item in inner.split(",") if item.strip()]


def extract_frontmatter_lines(text):
    """Return the raw lines of the leading `---` ... `---` block.

    Raises FrontmatterError if there is no opening/closing fence.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("page does not begin with a '---' frontmatter block")
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return lines[1:idx]
    raise FrontmatterError("frontmatter block is not closed with '---'")


def parse_frontmatter(text):
    """Parse the constrained frontmatter into a dict.

    Supports: top-level scalars, `tags` (inline or block list), and `sources`
    (a list of mappings). Raises FrontmatterError on malformed structure.
    """
    body_lines = extract_frontmatter_lines(text)
    data = {}
    i = 0
    n = len(body_lines)

    while i < n:
        raw = body_lines[i]
        stripped = raw.strip()

        # Skip blank lines and full-line comments.
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # Top-level keys are unindented.
        indent = len(raw) - len(raw.lstrip())
        if indent != 0:
            raise FrontmatterError(
                "unexpected indentation at top level: %r" % raw
            )

        if ":" not in stripped:
            raise FrontmatterError("expected 'key: value' but got: %r" % raw)

        key, _, after = stripped.partition(":")
        key = key.strip()
        after = after.strip()

        if key == "sources":
            sources, i = _parse_sources_block(body_lines, i + 1, n)
            data["sources"] = sources
            continue

        if key == "tags":
            if after:
                if after.startswith("["):
                    data["tags"] = _parse_inline_list(after)
                    i += 1
                    continue
                # Single scalar tag on the same line.
                data["tags"] = [_parse_scalar(after)]
                i += 1
                continue
            # Block list of tags.
            items, i = _parse_block_string_list(body_lines, i + 1, n)
            data["tags"] = items
            continue

        # Plain scalar.
        data[key] = _parse_scalar(after)
        i += 1

    return data


def _parse_block_string_list(lines, start, n):
    """Parse a block-style `- item` list of scalars starting at `start`."""
    items = []
    i = start
    while i < n:
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if not stripped.startswith("- "):
            if stripped == "-":
                i += 1
                continue
            break  # back to top level
        items.append(_parse_scalar(stripped[2:]))
        i += 1
    return items, i


def _parse_sources_block(lines, start, n):
    """Parse the `sources:` block list of mappings starting at `start`."""
    sources = []
    current = None
    base_indent = None
    i = start

    while i < n:
        raw = lines[i]
        stripped = raw.strip()

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = len(raw) - len(raw.lstrip())
        if indent == 0:
            break  # next top-level key

        if base_indent is None:
            base_indent = indent

        if stripped.startswith("- "):
            # Start of a new source mapping; first key is on this line.
            current = {}
            sources.append(current)
            rest = stripped[2:].strip()
            if rest:
                if ":" not in rest:
                    raise FrontmatterError(
                        "malformed source entry: %r" % raw
                    )
                k, _, v = rest.partition(":")
                current[k.strip()] = _parse_scalar(v)
            i += 1
            continue

        # Continuation key of the current mapping.
        if current is None:
            raise FrontmatterError(
                "source key found before any '-' list item: %r" % raw
            )
        if ":" not in stripped:
            raise FrontmatterError("malformed source key: %r" % raw)
        k, _, v = stripped.partition(":")
        current[k.strip()] = _parse_scalar(v)
        i += 1

    return sources, i


# ----------------------------------------------------------------------------
# repos.md parsing
# ----------------------------------------------------------------------------

def parse_repos(repos_path):
    """Parse the first markdown table of repos.md into {name: path}.

    Only the table BEFORE the '## Planned' heading is read (columns:
    name | scope | path | notes). Returns {} if the file is absent.
    """
    mapping = {}
    if not os.path.isfile(repos_path):
        return mapping

    with open(repos_path, "r", encoding="utf-8") as fh:
        text = fh.read()

    # Cut off everything from the Planned heading onward.
    planned = re.search(r"^##\s+Planned", text, re.MULTILINE)
    if planned:
        text = text[: planned.start()]

    header_seen = False
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # Separator row, e.g. |---|---|.
        if all(set(c) <= set("-: ") and c for c in cells):
            header_seen = True
            continue
        if not header_seen:
            # This is the header row (name | scope | path | notes).
            continue
        if len(cells) < 3:
            continue
        name, path = cells[0], cells[2]
        if name and path and not name.startswith("_"):
            mapping[name] = path
    return mapping


def parse_ignored_repos(repos_path):
    """Parse the '## Ignored (do not track)' table of repos.md into a set of names.

    Reads only the section between the '## Ignored' heading and the next '##'
    heading (columns: name | reason). Returns an empty set if the file or the
    section is absent.
    """
    ignored = set()
    if not os.path.isfile(repos_path):
        return ignored

    with open(repos_path, "r", encoding="utf-8") as fh:
        text = fh.read()

    start = re.search(r"^##\s+Ignored\b", text, re.MULTILINE)
    if not start:
        return ignored
    text = text[start.end():]
    nxt = re.search(r"^##\s+", text, re.MULTILINE)
    if nxt:
        text = text[: nxt.start()]

    header_seen = False
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") and c for c in cells):
            header_seen = True
            continue
        if not header_seen:
            continue
        name = cells[0] if cells else ""
        if name and not name.startswith("_"):
            ignored.add(name)
    return ignored


# ----------------------------------------------------------------------------
# Hashing
# ----------------------------------------------------------------------------

def sha256_file(path):
    """Return the lowercase hex sha256 of a file (matches hash.sh)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------------------
# Index reference extraction
# ----------------------------------------------------------------------------

def index_references(index_text):
    """Return a set of referenced names (lowercased) from an index page.

    Collects [[wikilink]] targets and explicit `.md` filename mentions (e.g.
    a markdown link like `[label](foo.md)`). Bare prose words are NOT counted,
    so a page is only considered indexed when something actually links to it.
    """
    refs = set()
    if index_text is None:
        return refs

    for target in re.findall(r"\[\[([^\]]+)\]\]", index_text):
        target = target.split("|", 1)[0]      # drop alias
        target = target.split("#", 1)[0]       # drop heading anchor
        target = target.strip().strip("/")
        if not target:
            continue
        base = os.path.basename(target)
        if base.endswith(".md"):
            base = base[:-3]
        refs.add(base.lower())

    # Explicit filename mentions ending in `.md` (e.g. `foo.md` or
    # `path/to/foo.md` inside a markdown link). Bare prose words are ignored.
    for token in re.findall(r"[A-Za-z0-9._\-/]+\.md", index_text):
        name = os.path.basename(token)[:-3]
        if name:
            refs.add(name.lower())

    return refs


# ----------------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------------

class Reporter:
    """Collects per-page errors and warnings."""

    def __init__(self):
        self.errors = []     # list of (relpath, message)
        self.warnings = []   # list of (relpath, message)

    def error(self, relpath, message):
        self.errors.append((relpath, message))

    def warning(self, relpath, message):
        self.warnings.append((relpath, message))


def parse_date(value):
    """Parse a YYYY-MM-DD date; return a date or None."""
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(str(value).strip())
    except ValueError:
        return None


def is_knowledge_page(relpath):
    """True if the page must carry frontmatter (i.e. is a knowledge page)."""
    parts = relpath.split(os.sep)
    if parts and parts[0] == "raw":
        return False
    if os.path.basename(relpath) == "index.md":
        return False
    if relpath == "log.md":
        return False
    return True


def validate_sources(rep, relpath, sources, repo_root, vault_root,
                     repos_map, ignored_repos, today, no_repo_hash):
    """Validate the `sources` list of a single page."""
    for idx, src in enumerate(sources):
        if not isinstance(src, dict):
            rep.error(relpath, "source #%d is not a mapping" % (idx + 1))
            continue

        stype = src.get("source_type")
        label = "source #%d" % (idx + 1)

        if not stype:
            rep.error(relpath, "%s missing 'source_type'" % label)
            continue
        if stype not in VALID_SOURCE_TYPES:
            rep.error(relpath, "%s has invalid source_type '%s'" % (label, stype))
            continue

        path = src.get("path")
        sha = src.get("sha256")
        pulled = src.get("pulled")

        if stype == "repository":
            if not path:
                rep.error(relpath, "%s (repository) missing 'path'" % label)
                continue
            if not sha:
                rep.error(relpath, "%s (repository) missing 'sha256'" % label)
                continue
            repo_name, _, in_repo = path.partition("/")
            if repo_name in ignored_repos:
                rep.error(relpath,
                          "%s references ignored repo '%s' (listed under "
                          "'## Ignored' in repos.md — the wiki must not track it)"
                          % (label, repo_name))
                continue
            if no_repo_hash:
                continue  # only presence is checked in this mode
            if not in_repo:
                rep.error(relpath,
                          "%s path '%s' is not '<repo>/<in-repo-path>'"
                          % (label, path))
                continue
            if repo_name not in repos_map:
                rep.error(relpath,
                          "%s references unregistered repo '%s' (not in repos.md)"
                          % (label, repo_name))
                continue
            full = os.path.normpath(
                os.path.join(repo_root, repos_map[repo_name], in_repo)
            )
            _check_hash(rep, relpath, label, full, sha)

        elif stype == "file":
            if not path:
                rep.error(relpath, "%s (file) missing 'path'" % label)
                continue
            if not sha:
                rep.error(relpath, "%s (file) missing 'sha256'" % label)
                continue
            full = os.path.normpath(os.path.join(vault_root, path))
            _check_hash(rep, relpath, label, full, sha)

        else:  # web / tracker / ai-agent-session
            if not pulled:
                rep.error(relpath, "%s (%s) missing 'pulled' date"
                          % (label, stype))
                continue
            pulled_date = parse_date(pulled)
            if pulled_date is None:
                rep.error(relpath, "%s (%s) has invalid 'pulled' date '%s'"
                          % (label, stype, pulled))
                continue
            age = (today - pulled_date).days
            if age > PULLED_WARN_DAYS:
                rep.warning(relpath,
                            "%s (%s) 'pulled' is %d days old (> %d)"
                            % (label, stype, age, PULLED_WARN_DAYS))


def _check_hash(rep, relpath, label, full_path, recorded):
    if not os.path.isfile(full_path):
        rep.error(relpath, "%s MISSING source file: %s" % (label, full_path))
        return
    current = sha256_file(full_path)
    if current.lower() != str(recorded).strip().lower():
        rep.error(relpath, "%s STALE: %s (recorded sha256 no longer matches)"
                  % (label, full_path))


def validate_index_presence(rep, relpath, vault_root, index_cache):
    """Check that the page is referenced from its index / overview."""
    parts = relpath.split(os.sep)
    name = os.path.basename(relpath)
    stem = name[:-3] if name.endswith(".md") else name
    folder = parts[0] if parts else ""

    if folder == "repositories":
        # repositories/<repo>/<page>.md
        if len(parts) < 3:
            return  # malformed layout; nothing sensible to check
        repo = parts[1]
        if stem == "overview":
            # overview.md must be referenced from repositories/index.md
            refs = _load_index(index_cache, vault_root,
                               os.path.join("repositories", "index.md"))
            if not _referenced(refs, stem, repo):
                rep.error(relpath,
                          "repo overview not referenced from repositories/index.md")
        else:
            # other pages must be referenced from that repo's overview.md
            refs = _load_index(index_cache, vault_root,
                               os.path.join("repositories", repo, "overview.md"))
            if not _referenced(refs, stem):
                rep.error(relpath,
                          "page not referenced from repositories/%s/overview.md"
                          % repo)
        return

    if folder in INDEXED_FOLDERS:
        refs = _load_index(index_cache, vault_root,
                           os.path.join(folder, "index.md"))
        if not _referenced(refs, stem):
            rep.error(relpath, "page not referenced from %s/index.md" % folder)


def _referenced(refs, *candidates):
    return any(c and c.lower() in refs for c in candidates)


def _load_index(cache, vault_root, rel_index_path):
    if rel_index_path in cache:
        return cache[rel_index_path]
    full = os.path.join(vault_root, rel_index_path)
    text = None
    if os.path.isfile(full):
        with open(full, "r", encoding="utf-8") as fh:
            text = fh.read()
    refs = index_references(text)
    cache[rel_index_path] = refs
    return refs


def collect_pages(vault_root):
    """Yield (abs_path, rel_path) for every knowledge page under the vault."""
    for dirpath, dirnames, filenames in os.walk(vault_root):
        # Don't descend into raw/.
        rel_dir = os.path.relpath(dirpath, vault_root)
        if rel_dir == "raw" or rel_dir.startswith("raw" + os.sep):
            dirnames[:] = []
            continue
        if "raw" in dirnames:
            dirnames.remove("raw")
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            abs_path = os.path.join(dirpath, fn)
            rel_path = os.path.relpath(abs_path, vault_root)
            if is_knowledge_page(rel_path):
                yield abs_path, rel_path


def validate(repo_root, no_repo_hash):
    """Run all checks; return (Reporter, pages_checked)."""
    vault_root = os.path.join(repo_root, "wiki")
    repos_path = os.path.join(repo_root, "repos.md")
    repos_map = parse_repos(repos_path)
    ignored_repos = parse_ignored_repos(repos_path)
    today = datetime.date.today()
    rep = Reporter()
    index_cache = {}
    pages_checked = 0

    if not os.path.isdir(vault_root):
        return rep, pages_checked

    for abs_path, rel_path in sorted(collect_pages(vault_root),
                                     key=lambda p: p[1]):
        pages_checked += 1
        try:
            with open(abs_path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            rep.error(rel_path, "could not read file: %s" % exc)
            continue

        try:
            fm = parse_frontmatter(text)
        except FrontmatterError as exc:
            rep.error(rel_path, "frontmatter: %s" % exc)
            continue

        # Required fields.
        for field in REQUIRED_FIELDS:
            if field not in fm or fm[field] in (None, "", []):
                rep.error(rel_path, "missing required field '%s'" % field)

        ptype = fm.get("type")
        if ptype and ptype not in VALID_TYPES:
            rep.error(rel_path, "invalid type '%s'" % ptype)

        pstatus = fm.get("status")
        if pstatus and pstatus not in VALID_STATUSES:
            rep.error(rel_path, "invalid status '%s'" % pstatus)

        sources = fm.get("sources")
        if isinstance(sources, list) and sources:
            validate_sources(rep, rel_path, sources, repo_root, vault_root,
                             repos_map, ignored_repos, today, no_repo_hash)

        validate_index_presence(rep, rel_path, vault_root, index_cache)

    return rep, pages_checked


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def default_repo_root():
    """The wiki repo root: parent of the scripts/ dir that holds this file."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate the LLM Code Wiki vault against the schema in "
                    "constitution.md.")
    parser.add_argument("repo_root", nargs="?", default=None,
                        help="Wiki repo root (defaults to the parent of scripts/).")
    parser.add_argument("--strict", action="store_true",
                        help="Treat warnings as errors (affects exit code).")
    parser.add_argument("--quiet", action="store_true",
                        help="Print only the summary and errors.")
    parser.add_argument("--no-repo-hash", action="store_true",
                        help="Skip resolving/hashing 'repository' sources "
                             "(only checks sha256 presence). Used by CI.")
    args = parser.parse_args(argv)

    repo_root = os.path.abspath(args.repo_root) if args.repo_root \
        else default_repo_root()

    rep, pages_checked = validate(repo_root, args.no_repo_hash)

    # Group output by page for readable, actionable reporting.
    by_page = {}
    for relpath, msg in rep.errors:
        by_page.setdefault(relpath, []).append(("ERROR", msg))
    if not args.quiet:
        for relpath, msg in rep.warnings:
            by_page.setdefault(relpath, []).append(("WARNING", msg))

    for relpath in sorted(by_page):
        for level, msg in by_page[relpath]:
            print("%s: %s %s" % (relpath, level, msg))

    n_err = len(rep.errors)
    n_warn = len(rep.warnings)
    print("%d pages checked, %d errors, %d warnings"
          % (pages_checked, n_err, n_warn))

    if n_err > 0 or (args.strict and n_warn > 0):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
