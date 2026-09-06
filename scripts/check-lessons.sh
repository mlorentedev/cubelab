#!/usr/bin/env bash
# Guard: docs/lessons/ numbering and index integrity.
# 1. No two lesson files share a number (the collision that hit web#326, dotfiles#1519, kubelab).
# 2. Every lesson file is listed in its _index.md and every indexed file exists.
# Runs under bash and zsh; no globs (an unmatched glob aborts under zsh NOMATCH).
#
# kubelab adaptation of the fleet-wide canon: lessons here live one level down, in
# docs/lessons/<category>/lesson-NNN-<slug>.md, each category carrying its own
# _index.md (the top-level _index.md only links the categories). So the number
# check spans every category directory, and the index check runs per category
# against that category's _index.md. A lesson placed directly under docs/lessons/
# is still checked against the top-level _index.md, as in the canon.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LESSONS_DIR="$ROOT/docs/lessons"
[ -d "$LESSONS_DIR" ] || { echo "check-lessons: docs/lessons/ not present, nothing to check"; exit 0; }
rc=0
# Directories holding lessons: docs/lessons itself plus each immediate subdirectory.
# Emitted one per line and consumed through $(...): zsh splits a command
# substitution on whitespace, but not a plain $var (SH_WORD_SPLIT is off there).
lesson_dirs() { echo "$LESSONS_DIR"; find "$LESSONS_DIR" -mindepth 1 -maxdepth 1 -type d | sort; }
all_files() { for d in $(lesson_dirs); do ls "$d" | grep -E '^lesson-[0-9]+.*\.md$' || true; done; }
dupes="$(all_files | grep -oE '^lesson-[0-9]+' | sort | uniq -d || true)"
if [ -n "$dupes" ]; then
  echo "check-lessons: lesson numbers used more than once:"
  for n in $dupes; do
    for d in $(lesson_dirs); do ls "$d" | grep -E "^${n}-" | sed "s|^|  ${d#$ROOT/}/|" || true; done
  done
  rc=1
fi
for d in $(lesson_dirs); do
  INDEX="$d/_index.md"
  rel="${d#$ROOT/}"
  if [ -f "$INDEX" ]; then
    for f in $(ls "$d" | grep -E '^lesson-[0-9]+.*\.md$'); do
      grep -qF "$f" "$INDEX" || { echo "check-lessons: not in $rel/_index.md: $f"; rc=1; }
    done
    for f in $(grep -oE 'lesson-[0-9]+[A-Za-z0-9._-]*\.md' "$INDEX" | sort -u); do
      [ -f "$d/$f" ] || { echo "check-lessons: indexed in $rel/_index.md but missing: $f"; rc=1; }
    done
  elif [ -n "$(ls "$d" | grep -E '^lesson-[0-9]+' || true)" ]; then
    echo "check-lessons: $rel has lessons but no _index.md"; rc=1
  fi
done
[ "$rc" -eq 0 ] && echo "check-lessons: OK ($(all_files | grep -c .) lessons)"
exit $rc
