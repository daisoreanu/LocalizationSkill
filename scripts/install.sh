#!/bin/sh
# Link this checkout into both hosts' skill dirs; never drop an unsynced copy.
set -eu

usage() {
  cat <<'TXT'
usage: scripts/install.sh [--help]

Symlinks this skill checkout as ~/.claude/skills/moneyfesting-localization and
~/.codex/skills/moneyfesting-localization so both hosts load one copy. Re-points an
existing symlink; replaces a directory copy only when it is byte-identical (git metadata
aside), otherwise lists the differences and stops so nothing unsynced is lost. Never links
into an app checkout's .claude/skills. Safe to re-run.
TXT
}

case "${1:-}" in
  -h|--help) usage; exit 0 ;;
  "") ;;
  *) usage >&2; exit 2 ;;
esac

SRC="$(cd "$(dirname "$0")/.." && pwd)"
[ -f "$SRC/SKILL.md" ] || { echo "not a skill: $SRC" >&2; exit 1; }

differs() {
  diff -rq --exclude=.git --exclude=.DS_Store --exclude=__pycache__ "$SRC" "$1"
}

for dst in "$HOME/.claude/skills/moneyfesting-localization" "$HOME/.codex/skills/moneyfesting-localization"; do
  mkdir -p "$(dirname "$dst")"
  if [ -L "$dst" ]; then
    ln -sfn "$SRC" "$dst"
    echo "relinked $dst"
    continue
  fi
  if [ -e "$dst" ]; then
    [ -d "$dst" ] || { echo "$dst is a file; move it aside first" >&2; exit 1; }
    if ! differs "$dst" >/dev/null; then
      echo "unsynced copy at $dst; merge or remove it by hand first:" >&2
      differs "$dst" >&2 || true
      exit 1
    fi
    rm -rf "$dst"
  fi
  ln -s "$SRC" "$dst"
  echo "linked $dst"
done
