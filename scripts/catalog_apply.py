#!/usr/bin/env python3
"""Write candidate translations into a String Catalog, touching only the listed keys.

The catalog is re-serialized exactly as Xcode writes it (indent 2, " : " separator,
raw UTF-8, insertion order kept, empty objects as '{' blank line '}'), so the diff
shows only the keys in the candidates file. Before writing, the script proves the
untouched catalog round-trips byte for byte and that every changed line belongs to a
listed key; otherwise it aborts and writes nothing. Every unit is written with the
--state (default needs_review) because 'translated' means owner-accepted: a unit that
is already 'translated' is refused unless --overwrite-translated names that scope.

Candidates shape:
  {"locale": "ro", "rev": 2, "entries": [
      {"key": "paywall.trialToggle", "value": "Probă gratuită de %lld zile"},
      {"key": "widgets.streak.dayStreakCount", "plural": {"one": "...", "few": "...", "other": "..."}}]}

Shield copy is not in the catalog: edit ShieldMessageCatalog.swift by hand and list the ids.
This is the one script allowed to write into the app checkout, and only on the --catalog path.
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile

# Read-only git calls must not refresh the checkout's index.
os.environ.setdefault("GIT_OPTIONAL_LOCKS", "0")

CATEGORIES = {"zero", "one", "two", "few", "many", "other"}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--catalog", required=True, help="path to Localizable.xcstrings (written in place)")
    p.add_argument("--candidates", required=True, help="candidates JSON, see shape above")
    p.add_argument("--locale", required=True, help="target locale; must match the candidates file")
    p.add_argument("--state", default="needs_review", choices=["needs_review", "new"],
                   help="state written on every unit; 'translated' is owner-accepted and is never written by this script")
    p.add_argument("--dry-run", action="store_true", help="report the changes and write nothing")
    p.add_argument("--overwrite-translated", action="store_true",
                   help="allow rewriting units already in state 'translated' (an explicitly named audit scope)")
    return p.parse_args()


def dump_xcstrings(data):
    """Xcode's serialization: indent 2, ' : ' separator, raw UTF-8, empty objects as '{' blank line '}'."""
    text = json.dumps(data, indent=2, ensure_ascii=False, separators=(",", " : "))
    lines = []
    for line in text.split("\n"):
        m = re.match(r"^( *)(.*)\{\}(,?)$", line)
        if m:
            lines.extend([m.group(1) + m.group(2) + "{", "", m.group(1) + "}" + m.group(3)])
        else:
            lines.append(line)
    return "\n".join(lines) + "\n"


def load_catalog(path):
    raw = open(path, encoding="utf-8").read()
    data = json.loads(raw)
    if dump_xcstrings(data) != raw:
        sys.exit("catalog is not in Xcode's serialization, so any write would touch every key; "
                 "open and save it in Xcode, then rerun")
    return raw, data


def load_candidates(path, locale):
    data = json.load(open(path, encoding="utf-8"))
    if data.get("locale") != locale:
        sys.exit(f"candidates are for locale {data.get('locale')!r}, not {locale!r}")
    entries = data.get("entries")
    if not isinstance(entries, list):
        sys.exit("candidates need an 'entries' list")
    for entry in entries:
        validate_entry(entry)
    return entries


def validate_entry(entry):
    key = entry.get("key")
    if not key or ("value" in entry) == ("plural" in entry):
        sys.exit(f"entry {entry!r} needs 'key' and exactly one of 'value' or 'plural'")
    if "value" in entry and not (isinstance(entry["value"], str) and entry["value"].strip()):
        sys.exit(f"{key}: value must be a non-empty string")
    if "plural" in entry:
        bad = [c for c, v in entry["plural"].items() if c not in CATEGORIES or not (isinstance(v, str) and v.strip())]
        if bad or not entry["plural"]:
            sys.exit(f"{key}: plural needs CLDR categories with non-empty strings; bad: {bad}")


def unit(value, state):
    return {"stringUnit": {"state": state, "value": value}}


def new_localization(entry, state):
    if "value" in entry:
        return unit(entry["value"], state)
    plural = {cat: unit(entry["plural"][cat], state) for cat in sorted(entry["plural"])}
    return {"variations": {"plural": plural}}


def current_states(loc):
    if not loc:
        return set()
    if "stringUnit" in loc:
        return {loc["stringUnit"].get("state")}
    return {u.get("stringUnit", {}).get("state") for u in loc.get("variations", {}).get("plural", {}).values()}


def set_localization(entry, locale, loc):
    """Insert a new locale at its alphabetical slot, the order Xcode keeps; replace in place otherwise."""
    locs = entry.setdefault("localizations", {})
    if locale in locs:
        locs[locale] = loc
        return
    items = sorted([*locs.items(), (locale, loc)], key=lambda kv: kv[0])
    locs.clear()
    locs.update(items)


def plan_changes(strings, entries, locale, state, overwrite):
    changes, locked, unknown, unchanged = [], [], [], []
    for entry in entries:
        key = entry["key"]
        if key not in strings:
            unknown.append(key)
            continue
        old = strings[key].get("localizations", {}).get(locale)
        new = new_localization(entry, state)
        if old == new:
            unchanged.append(key)
        elif "translated" in current_states(old) and not overwrite:
            locked.append(key)
        else:
            changes.append((key, old, new))
    if unknown:
        sys.exit("keys not in the catalog (add them from source first): " + ", ".join(unknown))
    if locked:
        sys.exit("refusing to rewrite owner-accepted 'translated' units; drop them or pass --overwrite-translated: "
                 + ", ".join(locked))
    return changes, unchanged


def key_by_line(text):
    """Map each line of a serialized catalog to the top-level key that owns it (None outside 'strings')."""
    owners, current, in_strings = [], None, False
    for line in text.split("\n"):
        if line == '  "strings" : {':
            in_strings = True
        elif in_strings and line in ("  },", "  }"):
            in_strings, current = False, None
        m = re.match(r'^    "((?:[^"\\]|\\.)*)" : \{,?$', line)
        if in_strings and m:
            current = json.loads('"' + m.group(1) + '"')
        owners.append(current if in_strings else None)
    return owners


def guard_diff(old_text, new_text, allowed):
    """Abort unless every differing line belongs to a listed key."""
    old_owner, new_owner = key_by_line(old_text), key_by_line(new_text)
    touched = set()
    matcher = difflib.SequenceMatcher(None, old_text.split("\n"), new_text.split("\n"), autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        touched.update(old_owner[i1:i2])
        touched.update(new_owner[j1:j2])
    stray = sorted(k if k is not None else "<outside strings>" for k in touched - set(allowed))
    if stray:
        sys.exit("diff would touch unlisted keys, nothing written: " + ", ".join(stray))
    return len(touched)


def describe(old, new):
    kind = "plural" if "variations" in new else "flat"
    before = "missing" if old is None else ("plural" if "variations" in old else "flat")
    return f"{before} -> {kind}"


def write_atomic(path, text):
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".catalog_apply.")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def git_stat(path):
    try:
        out = subprocess.run(["git", "diff", "--numstat", "--", os.path.basename(path)], cwd=os.path.dirname(os.path.abspath(path)),
                             capture_output=True, text=True, check=True).stdout.strip()
        return out or "git diff: no change"
    except (OSError, subprocess.CalledProcessError):
        return "git diff: not available"


def main():
    args = parse_args()
    raw, catalog = load_catalog(args.catalog)
    entries = load_candidates(args.candidates, args.locale)
    changes, unchanged = plan_changes(catalog["strings"], entries, args.locale, args.state, args.overwrite_translated)
    for key, old, new in changes:
        set_localization(catalog["strings"][key], args.locale, new)
        print(f"{'would write' if args.dry_run else 'write'} {key} ({describe(old, new)}, state {args.state})")
    new_text = dump_xcstrings(catalog)
    if not changes:
        print(f"nothing to write: {len(unchanged)} unchanged; catalog round-trips byte-identical")
        return
    touched = guard_diff(raw, new_text, [k for k, _, _ in changes])
    if args.dry_run:
        print(f"dry run: {len(changes)} keys would change, {len(unchanged)} unchanged, diff guard ok ({touched} keys)")
        return
    write_atomic(args.catalog, new_text)
    print(f"wrote {args.catalog}: {len(changes)} keys changed, {len(unchanged)} unchanged")
    print(git_stat(args.catalog))


if __name__ == "__main__":
    main()
