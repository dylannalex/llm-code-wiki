#!/usr/bin/env bash
# hash.sh — deterministic, zero-token staleness check for a wiki page's sources.
# Borrowed from the research-memory skill.
#   hash.sh <file>                 -> prints the file's sha256
#   hash.sh <file> <recorded_hash> -> prints FRESH | STALE | MISSING
# Used by the `lint` workflow to detect when a page's cited source files changed.
set -euo pipefail

file="${1:-}"
recorded="${2:-}"

if [ -z "$file" ]; then
  echo "usage: hash.sh <file> [recorded_hash]" >&2
  exit 2
fi

compute_hash() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    echo "no sha256 tool found (need sha256sum or shasum)" >&2
    exit 3
  fi
}

if [ ! -f "$file" ]; then
  if [ -n "$recorded" ]; then echo "MISSING"; exit 0; fi
  echo "file not found: $file" >&2
  exit 4
fi

current="$(compute_hash "$file")"

if [ -z "$recorded" ]; then
  echo "$current"
else
  [ "$current" = "$recorded" ] && echo "FRESH" || echo "STALE"
fi
