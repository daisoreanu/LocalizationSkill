#!/usr/bin/env python3
"""Slice a String Catalog into packet input JSON or a valid .xcstrings subset.

Default output is packet input: one entry per key with comment, extraction state,
source and target units (flat or plural), state, and the placeholders the source
carries, so a packet builder never re-parses the 600 KB catalog. --target-only
emits only the target strings under anonymous ids (s01, s02...) with the key map
written beside the output, which keeps a blind packet free of keys and English.
--emit-xcstrings writes a subset catalog in Xcode's own serialization, keeping
sourceLanguage and version, for eval fixtures. --shield adds the Swift shield
pairs as shield.<id>.title and shield.<id>.body (not emitted into .xcstrings).
Read-only on the catalog; never writes into the app checkout.
"""
import argparse
import copy
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalog_apply import dump_xcstrings  # noqa: E402
from catalog_check import SPEC, expand_shield_ids, read_keys_file, shield_entries  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--catalog", required=True, help="path to Localizable.xcstrings")
    sel = p.add_mutually_exclusive_group(required=True)
    sel.add_argument("--prefix", help="keys starting with this prefix (shield.<id>.* with --shield)")
    sel.add_argument("--keys", help="comma-separated keys")
    sel.add_argument("--keys-file", help="file with one key per line, a JSON list, or {\"keys\": [...]}")
    p.add_argument("--locale", required=True, help="target locale code, e.g. ro")
    p.add_argument("--target-only", action="store_true", help="only target strings under anonymous ids; key map written beside --out")
    p.add_argument("--shield", help="ShieldMessageCatalog.swift to include as shield.<id>.title/.body pairs")
    p.add_argument("--emit-xcstrings", action="store_true", help="write a valid .xcstrings subset instead of packet JSON")
    p.add_argument("--out", required=True, help="output file")
    return p.parse_args()


def select_keys(strings, args):
    if args.prefix:
        return [k for k in strings if k.startswith(args.prefix)]
    wanted = [k.strip() for k in args.keys.split(",") if k.strip()] if args.keys else read_keys_file(args.keys_file)
    wanted = expand_shield_ids(wanted, strings)
    missing = [k for k in wanted if k not in strings]
    if missing:
        sys.exit(f"keys not in the catalog: {', '.join(missing)}")
    return wanted


def unit_text(loc):
    """Flat value, or {category: value} for a plural unit; None when the language is absent."""
    if not loc:
        return None
    if "stringUnit" in loc:
        return loc["stringUnit"].get("value", "")
    plural = loc.get("variations", {}).get("plural", {})
    return {cat: unit.get("stringUnit", {}).get("value", "") for cat, unit in plural.items()}


def unit_state(loc):
    if not loc:
        return "missing"
    if "stringUnit" in loc:
        return loc["stringUnit"].get("state", "new")
    states = {u.get("stringUnit", {}).get("state", "new") for u in loc.get("variations", {}).get("plural", {}).values()}
    return states.pop() if len(states) == 1 else "mixed"


def packet_entry(key, entry, locale):
    locs = entry.get("localizations", {})
    en = unit_text(locs.get("en"))
    out = {"key": key, "comment": entry.get("comment", ""), "extractionState": entry.get("extractionState"),
           "kind": "plural" if isinstance(en, dict) else "flat", "en": en, "target": unit_text(locs.get(locale)),
           "state": None if entry.get("shield") else unit_state(locs.get(locale)),
           "placeholders": sorted({m.group(0) for m in SPEC.finditer(en if isinstance(en, str) else " ".join(en.values()))})}
    if entry.get("shield"):
        out.update({"source": "ShieldMessageCatalog.swift", "style": entry["style"]})
    return out


def packet(strings, keys, locale, args):
    return {"catalog": args.catalog, "sourceLanguage": "en", "locale": locale,
            "selection": {"prefix": args.prefix, "keys": None if args.prefix else keys}, "count": len(keys),
            "entries": [packet_entry(k, strings[k], locale) for k in keys]}


def target_only(strings, keys, locale):
    """Anonymous ids keep keys and English out of the blind packet; the id map goes to the coordinator."""
    items, id_map = [], {}
    for key in keys:
        text = unit_text(strings[key].get("localizations", {}).get(locale))
        if not text:
            continue
        sid = f"s{len(items) + 1:02d}"
        id_map[sid] = key
        items.append({"id": sid, "plural": text} if isinstance(text, dict) else {"id": sid, "text": text})
    return {"locale": locale, "count": len(items), "strings": items}, id_map


def subset_catalog(catalog, strings, keys, locale, only_target):
    out = {"sourceLanguage": catalog.get("sourceLanguage", "en"), "strings": {}, "version": catalog.get("version", "1.0")}
    for key in keys:
        entry = copy.deepcopy(strings[key])
        if only_target:
            locs = entry.get("localizations", {})
            entry["localizations"] = {lang: loc for lang, loc in locs.items() if lang in (out["sourceLanguage"], locale)}
        out["strings"][key] = entry
    return out


def write(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def main():
    args = parse_args()
    catalog = json.load(open(args.catalog, encoding="utf-8"))
    strings = dict(catalog["strings"])
    if args.shield:
        strings.update(shield_entries(args.shield))
    keys = select_keys(strings, args)
    if args.emit_xcstrings:
        shields = [k for k in keys if strings[k].get("shield")]
        if shields:
            print(f"skipping {len(shields)} shield pairs: shield copy lives in Swift, not the catalog", file=sys.stderr)
        keys = [k for k in keys if not strings[k].get("shield")]
        write(args.out, dump_xcstrings(subset_catalog(catalog, strings, keys, args.locale, args.target_only)))
    elif args.target_only:
        data, id_map = target_only(strings, keys, args.locale)
        write(args.out, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        map_path = re.sub(r"\.json$", "", args.out) + ".id_map.json"
        write(map_path, json.dumps(id_map, indent=2, ensure_ascii=False) + "\n")
        print(f"id map: {map_path} (coordinator only; never hand it to a blind agent)")
    else:
        write(args.out, json.dumps(packet(strings, keys, args.locale, args), indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {args.out}: {len(keys)} keys")


if __name__ == "__main__":
    main()
