#!/bin/sh
# Maintainer check: every checkout path the skill docs cite still exists.
set -eu

usage() {
  cat <<'TXT'
usage: scripts/check_paths.sh --app-root <checkout> [--skill-root <dir>]

Extracts backticked paths under Manifesting/, ManifestingTests/, Data/, Docs/ and scripts/
from SKILL.md and references/**/*.md. scripts/ paths resolve against the skill repo first
and the checkout second (the app has its own scripts/); everything else against --app-root.
{a,b} braces expand, * and ? glob (one match is enough), :line suffixes and trailing flags
drop, a trailing / requires a directory. Prints each missing path as file:line and exits 1
when any is missing.
TXT
}

APP_ROOT=""
SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
while [ $# -gt 0 ]; do
  case "$1" in
    --app-root) APP_ROOT="$2"; shift 2 ;;
    --skill-root) SKILL_ROOT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
[ -n "$APP_ROOT" ] && [ -d "$APP_ROOT" ] || { usage >&2; exit 2; }

exec python3 - "$SKILL_ROOT" "$APP_ROOT" <<'PY'
import glob
import os
import re
import sys

skill, app = sys.argv[1:3]
PREFIX = re.compile(r"^(Manifesting|ManifestingTests|Data|Docs|scripts)/")
docs = [os.path.join(skill, "SKILL.md")] + sorted(glob.glob(os.path.join(skill, "references", "**", "*.md"), recursive=True))


def expand(token):
    match = re.search(r"\{([^{}]*)\}", token)
    if not match:
        return [token]
    return [t for alt in match.group(1).split(",") for t in expand(token[:match.start()] + alt + token[match.end():])]


def exists(root, path):
    if any(ch in path for ch in "*?"):
        return bool(glob.glob(os.path.join(root, path)))
    full = os.path.join(root, path)
    return os.path.isdir(full) if path.endswith("/") else os.path.exists(full)


cited = missing = 0
for doc in docs:
    with open(doc, encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            for span in re.findall(r"`([^`]+)`", line):
                for raw in re.split(r"\s+|,(?![^{]*\})|;", span):
                    token = re.sub(r":\d+(-\d+)?$", "", raw.strip("()[]'\".:;,"))
                    if not PREFIX.match(token) or "<" in token:
                        continue
                    for path in expand(token):
                        cited += 1
                        roots = [skill, app] if path.startswith("scripts/") else [app]
                        if not any(exists(root, path) for root in roots):
                            missing += 1
                            print(f"{os.path.relpath(doc, skill)}:{lineno}: {path} (not under {' or '.join(roots)})")
print(f"check_paths: {cited} citations, {missing} missing")
sys.exit(1 if missing else 0)
PY
