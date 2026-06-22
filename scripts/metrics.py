#!/usr/bin/env python3
"""LLM Code Wiki usage metrics.

Computes local usage statistics for a wiki and writes them to metrics/ as a
snapshot plus an append-only history. Standard library only; reuses the
frontmatter parser and vault walker from validate.py so nothing is duplicated.

Two metric families, both derived entirely from the repo (no LLM coupling):

  A. Knowledge-base health (snapshot of the wiki/ vault)
     page counts per category and status, repos tracked, sources by type,
     raw originals captured, wikilink graph (links, orphans), content size.

  B. Activity over time (parsed from wiki/log.md)
     operation counts by type (add/query/check/file) and recent-window /
     per-month timelines.

Run on demand:  python3 scripts/metrics.py
Output:         metrics/latest.json  (overwritten snapshot)
                metrics/history.jsonl (one snapshot per run, append-only)

See constitution.md for the wiki schema this reads.
"""

import argparse
import datetime
import json
import os
import re
import sys

# Reuse the validator's parsing machinery (same scripts/ dir).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate  # noqa: E402


CATEGORIES = [
    "repositories", "concepts", "contracts", "comparisons",
    "glossary", "projects", "decisions", "sources",
]

# log.md entry:  ## [YYYY-MM-DD] <op> | <title>
LOG_ENTRY_RE = re.compile(
    r"^##\s*\[(\d{4}-\d{2}-\d{2})\]\s*(\w+)\s*\|\s*(.*)$"
)
LOG_OPS = ["add", "query", "check", "file"]

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def wikilink_targets(text):
    """Return the set of [[wikilink]] target stems (lowercased) in text."""
    out = set()
    for target in WIKILINK_RE.findall(text):
        target = target.split("|", 1)[0]   # drop alias
        target = target.split("#", 1)[0]   # drop heading anchor
        target = target.strip().strip("/")
        if not target:
            continue
        base = os.path.basename(target)
        if base.endswith(".md"):
            base = base[:-3]
        if base:
            out.add(base.lower())
    return out


def page_category(rel_path):
    """Top-level vault folder for a page, or '' if at vault root."""
    parts = rel_path.split(os.sep)
    return parts[0] if len(parts) > 1 else ""


def count_raw_originals(vault_root):
    """Count immutable originals under wiki/raw/ (excluding scaffolding)."""
    raw_root = os.path.join(vault_root, "raw")
    if not os.path.isdir(raw_root):
        return 0
    count = 0
    for _dirpath, _dirnames, filenames in os.walk(raw_root):
        for fn in filenames:
            if fn in (".gitkeep", ".DS_Store"):
                continue
            count += 1
    return count


def collect_content_metrics(vault_root, repo_root):
    """Tier A: knowledge-base health derived from the vault."""
    by_category = {c: 0 for c in CATEGORIES}
    by_status = {s: 0 for s in validate.VALID_STATUSES}
    by_status["unknown"] = 0
    by_source_type = {s: 0 for s in validate.VALID_SOURCE_TYPES}
    by_scope = {}

    pages = []          # (stem_lower, rel_path)
    outbound = {}       # stem_lower -> set of target stems
    total_links = 0
    sources_total = 0
    total_words = 0
    total_bytes = 0
    pages_total = 0

    for abs_path, rel_path in validate.collect_pages(vault_root):
        pages_total += 1
        try:
            with open(abs_path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue

        total_bytes += len(text.encode("utf-8"))
        total_words += len(text.split())

        cat = page_category(rel_path)
        if cat in by_category:
            by_category[cat] += 1

        stem = os.path.basename(rel_path)
        stem = stem[:-3].lower() if stem.endswith(".md") else stem.lower()
        pages.append((stem, rel_path))
        links = wikilink_targets(text)
        outbound[stem] = links
        total_links += len(links)

        try:
            fm = validate.parse_frontmatter(text)
        except validate.FrontmatterError:
            by_status["unknown"] += 1
            continue

        status = fm.get("status")
        if status in by_status:
            by_status[status] += 1
        else:
            by_status["unknown"] += 1

        scope = fm.get("scope")
        if scope:
            by_scope[scope] = by_scope.get(scope, 0) + 1

        srcs = fm.get("sources")
        if isinstance(srcs, list):
            for src in srcs:
                if not isinstance(src, dict):
                    continue
                sources_total += 1
                st = src.get("source_type")
                if st in by_source_type:
                    by_source_type[st] += 1

    # Orphans: knowledge pages not targeted by any other page's wikilink
    # (index.md files are excluded by collect_pages, so a page being listed in
    # its index does not save it — this surfaces missing cross-references).
    inbound = set()
    for stem, targets in outbound.items():
        for t in targets:
            if t != stem:
                inbound.add(t)
    orphans = sorted(stem for stem, _ in pages if stem not in inbound)

    repos_map = validate.parse_repos(os.path.join(repo_root, "repos.md"))

    avg_links = round(total_links / pages_total, 2) if pages_total else 0.0

    return {
        "pages_total": pages_total,
        "pages_by_category": by_category,
        "pages_by_status": by_status,
        "pages_by_scope": by_scope,
        "repos_tracked": len(repos_map),
        "sources_total": sources_total,
        "sources_by_type": by_source_type,
        "raw_originals": count_raw_originals(vault_root),
        "wikilinks_total": total_links,
        "wikilinks_avg_per_page": avg_links,
        "orphan_pages_count": len(orphans),
        "orphan_pages": orphans,
        "content_words": total_words,
        "content_bytes": total_bytes,
    }


def collect_activity_metrics(repo_root, today):
    """Tier B: activity timeline parsed from wiki/log.md."""
    log_path = os.path.join(repo_root, "wiki", "log.md")
    by_op = {op: 0 for op in LOG_OPS}
    by_op["other"] = 0
    by_month = {}
    dates = []

    if os.path.isfile(log_path):
        with open(log_path, "r", encoding="utf-8") as fh:
            for line in fh:
                m = LOG_ENTRY_RE.match(line.strip())
                if not m:
                    continue
                date_str, op, _title = m.groups()
                d = validate.parse_date(date_str)
                if d is None:
                    continue
                dates.append(d)
                op = op.lower()
                if op in by_op:
                    by_op[op] += 1
                else:
                    by_op["other"] += 1
                month = date_str[:7]
                by_month[month] = by_month.get(month, 0) + 1

    ops_total = sum(by_op.values())
    last_7 = sum(1 for d in dates if (today - d).days < 7)
    last_30 = sum(1 for d in dates if (today - d).days < 30)

    return {
        "ops_total": ops_total,
        "ops_by_type": by_op,
        "ops_by_month": dict(sorted(by_month.items())),
        "ops_last_7_days": last_7,
        "ops_last_30_days": last_30,
        "active_days": len(set(dates)),
        "first_activity": min(dates).isoformat() if dates else None,
        "last_activity": max(dates).isoformat() if dates else None,
    }


def read_last_snapshot(history_path):
    """Return the most recent snapshot dict from history.jsonl, or None."""
    if not os.path.isfile(history_path):
        return None
    last = None
    with open(history_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                last = line
    if not last:
        return None
    try:
        return json.loads(last)
    except json.JSONDecodeError:
        return None


def compute_deltas(snapshot, previous):
    """Deltas for headline counters vs the previous snapshot."""
    if not previous:
        return {}
    fields = [
        ("content", "pages_total"),
        ("content", "sources_total"),
        ("content", "content_words"),
        ("activity", "ops_total"),
    ]
    deltas = {}
    for section, key in fields:
        cur = snapshot.get(section, {}).get(key)
        old = previous.get(section, {}).get(key)
        if isinstance(cur, int) and isinstance(old, int):
            deltas["%s.%s" % (section, key)] = cur - old
    return deltas


def build_snapshot(repo_root):
    vault_root = os.path.join(repo_root, "wiki")
    today = datetime.date.today()
    return {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "content": collect_content_metrics(vault_root, repo_root),
        "activity": collect_activity_metrics(repo_root, today),
    }


def print_summary(snapshot, deltas):
    c = snapshot["content"]
    a = snapshot["activity"]

    def d(key):
        v = deltas.get(key)
        if not v:
            return ""
        return " (%+d)" % v

    print("LLM Code Wiki — usage metrics  (%s)" % snapshot["generated_at"])
    print("=" * 52)
    print("Knowledge base")
    print("  pages total ............. %d%s"
          % (c["pages_total"], d("content.pages_total")))
    cats = ", ".join("%s %d" % (k, v)
                     for k, v in c["pages_by_category"].items() if v)
    print("  by category ............. %s" % (cats or "—"))
    stat = ", ".join("%s %d" % (k, v)
                     for k, v in c["pages_by_status"].items() if v)
    print("  by status ............... %s" % (stat or "—"))
    print("  repos tracked ........... %d" % c["repos_tracked"])
    print("  sources total ........... %d%s"
          % (c["sources_total"], d("content.sources_total")))
    print("  raw originals ........... %d" % c["raw_originals"])
    print("  wikilinks (avg/page) .... %d (%.2f)"
          % (c["wikilinks_total"], c["wikilinks_avg_per_page"]))
    print("  orphan pages ............ %d" % c["orphan_pages_count"])
    print("  content size ............ %d words / %d bytes%s"
          % (c["content_words"], c["content_bytes"], d("content.content_words")))
    print("Activity (from log.md)")
    print("  operations total ........ %d%s"
          % (a["ops_total"], d("activity.ops_total")))
    ops = ", ".join("%s %d" % (k, v)
                    for k, v in a["ops_by_type"].items() if v)
    print("  by type ................. %s" % (ops or "—"))
    print("  last 7 / 30 days ........ %d / %d"
          % (a["ops_last_7_days"], a["ops_last_30_days"]))
    print("  active days ............. %d" % a["active_days"])
    print("  last activity ........... %s" % (a["last_activity"] or "—"))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Compute local usage metrics for the LLM Code Wiki.")
    parser.add_argument("repo_root", nargs="?", default=None,
                        help="Wiki repo root (defaults to the parent of scripts/).")
    parser.add_argument("--json", action="store_true",
                        help="Print the snapshot as JSON instead of a summary.")
    parser.add_argument("--no-write", action="store_true",
                        help="Compute and print only; do not write metrics/ files.")
    args = parser.parse_args(argv)

    repo_root = os.path.abspath(args.repo_root) if args.repo_root \
        else validate.default_repo_root()

    snapshot = build_snapshot(repo_root)

    metrics_dir = os.path.join(repo_root, "metrics")
    history_path = os.path.join(metrics_dir, "history.jsonl")
    previous = read_last_snapshot(history_path)
    deltas = compute_deltas(snapshot, previous)
    if deltas:
        snapshot["deltas_since_last"] = deltas

    if not args.no_write:
        os.makedirs(metrics_dir, exist_ok=True)
        with open(os.path.join(metrics_dir, "latest.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(snapshot, fh, indent=2)
            fh.write("\n")
        with open(history_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(snapshot) + "\n")

    if args.json:
        print(json.dumps(snapshot, indent=2))
    else:
        print_summary(snapshot, deltas)
        if not args.no_write:
            print("\nWrote metrics/latest.json and appended metrics/history.jsonl")

    return 0


if __name__ == "__main__":
    sys.exit(main())
