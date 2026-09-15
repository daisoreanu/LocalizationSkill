#!/usr/bin/env python3
"""Grep aid over target copy: preferred-term counts per prefix, forbidden forms, control forms, open decisions.

usage: term_audit.py --catalog <xcstrings> --glossary glossary/<locale>.json --locale ro
                     [--shield ShieldMessageCatalog.swift] [--keys k1,k2 | --keys-file f | --prefix P]
                     [--fail-on-forbidden] [--out report.json]

Glossary fields read: terms.<id>.{preferred, forms, forbidden, decided_by, note},
controls.<Label>.{preferred, roles}, open[].{id, options, recommended, recommended_reason, decided_by, status, note}.
Matching is whole-word and case-insensitive on real diacritics; cedilla ş/ţ fold to ș/ț so a
wrong glyph still hits (catalog_check C4 reports the glyph). Plural variations count as their
own units (key#category); shield literals count as shield.<id>.title and .body.
A control's keys are the catalog keys whose en value equals the label; targets outside the
preferred form and its named roles are listed as drift for the editor, never as forbidden.
Exit 1 only with --fail-on-forbidden and at least one forbidden hit: a grep aid, not a validator.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalog_check import SHIELD_TARGET_FIELD, shield_fields  # noqa: E402

CEDILLA = str.maketrans({"ş": "ș", "ţ": "ț", "Ş": "Ș", "Ţ": "Ț"})


def fold(text):
    return text.translate(CEDILLA)


def matcher(forms):
    forms = [fold(f) for f in forms if f]
    if not forms:
        return None
    return re.compile(r"(?<!\w)(?:" + "|".join(re.escape(f) for f in forms) + r")(?!\w)", re.I)


def catalog_units(strings, locale):
    """(unit id, target text, en text) per translatable unit of the locale."""
    for key, entry in strings.items():
        loc = entry.get("localizations", {})
        en = loc.get("en", {}).get("stringUnit", {}).get("value", "")
        target = loc.get(locale, {})
        if "stringUnit" in target:
            yield key, target["stringUnit"].get("value", ""), en
        for category, unit in target.get("variations", {}).get("plural", {}).items():
            yield f"{key}#{category}", unit.get("stringUnit", {}).get("value", ""), en


def shield_units(text, locale):
    field = SHIELD_TARGET_FIELD.get(locale)
    if not field:
        return
    for fields in shield_fields(text):
        if "id" in fields:
            for part in ("title", "body"):
                yield f"shield.{fields['id']}.{part}", fields.get(part + field, ""), fields.get(part + "English", "")


def selected(units, keys, prefix):
    for uid, target, en in units:
        base = uid.split("#")[0]
        ids = {base, base.rsplit(".", 1)[0]} if base.startswith("shield.") else {base}
        if (keys is None or ids & keys) and (prefix is None or base.startswith(prefix)):
            yield uid, fold(target), en


def prefix_of(uid):
    return uid.split(".")[0]


def audit_terms(terms, units):
    report = {}
    for tid, term in terms.items():
        preferred, forbidden = matcher(term.get("forms") or [term.get("preferred", "")]), matcher(term.get("forbidden", []))
        per_prefix, hits = Counter(), []
        for uid, target, _ in units:
            if preferred and preferred.search(target):
                per_prefix[prefix_of(uid)] += 1
            if forbidden:
                found = forbidden.search(target)
                if found:
                    hits.append({"id": uid, "text": target, "form": found.group(0)})
        report[tid] = {"preferred": term.get("preferred"), "forms": term.get("forms", []), "forbidden": term.get("forbidden", []),
                       "decided_by": term.get("decided_by"), "note": term.get("note", ""), "total": sum(per_prefix.values()),
                       "per_prefix": dict(sorted(per_prefix.items(), key=lambda kv: -kv[1])), "forbidden_hits": hits}
    return report


def audit_controls(controls, units):
    report = {}
    for label, control in controls.items():
        roles = control.get("roles", {})
        accepted = {fold(control.get("preferred", "")).casefold(): "preferred"}
        accepted.update({fold(v).casefold(): f"role:{k}" for k, v in roles.items()})
        rows = []
        for uid, target, en in units:
            if en.strip().rstrip("…").strip().casefold() != label.casefold():
                continue
            rows.append({"id": uid, "text": target, "match": accepted.get(target.strip().casefold(), "drift")})
        report[label] = {"preferred": control.get("preferred"), "roles": roles, "rows": rows,
                         "drift": [r for r in rows if r["match"] == "drift"]}
    return report


def audit_open(items, units):
    report = []
    for item in items:
        counts = {}
        for option in item.get("options", []):
            pattern = matcher([option])
            counts[option] = sum(1 for _, target, _ in units if pattern and pattern.search(target))
        report.append({**item, "counts": counts})
    return report


def print_report(report):
    print(f"term_audit: locale {report['locale']} · {report['units']} units audited")
    print("terms")
    for tid, term in report["terms"].items():
        spread = " · ".join(f"{p} {n}" for p, n in term["per_prefix"].items()) or "none"
        print(f"  {tid} -> \"{term['preferred']}\" [{', '.join(term['forms'])}]  total {term['total']}: {spread}")
        if term["forbidden"]:
            print(f"    forbidden [{', '.join(term['forbidden'])}]: {len(term['forbidden_hits'])}")
            for hit in term["forbidden_hits"]:
                print(f"      {hit['id']}: {hit['text']}")
    print("controls")
    for label, control in report["controls"].items():
        tally = Counter(row["match"] for row in control["rows"])
        roles = ", ".join(f"{k}={v}" for k, v in control["roles"].items())
        print(f"  {label} -> {control['preferred']}" + (f" (roles: {roles})" if roles else "")
              + "  " + (" · ".join(f"{m} {n}" for m, n in sorted(tally.items())) or "no keys with this en value"))
        for row in control["drift"]:
            print(f"    drift {row['id']}: {row['text']}")
    if report["open"]:
        print("open decisions")
        for item in report["open"]:
            counts = " · ".join(f"\"{o}\" {n}" for o, n in item["counts"].items())
            print(f"  {item.get('id')} ({item.get('status', 'open')}, decided_by {item.get('decided_by', '?')}): {counts}")
            if item.get("recommended"):
                print(f"    recommended: {item['recommended']} ({item.get('recommended_reason', 'no reason recorded')})")
            if item.get("note"):
                print(f"    {item['note']}")
    print(f"summary: forbidden hits {report['forbidden_total']} · control drift {report['drift_total']} · open {len(report['open'])}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--glossary", required=True)
    parser.add_argument("--locale", required=True)
    parser.add_argument("--shield", metavar="SWIFT")
    parser.add_argument("--keys", help="comma-separated key or shield ids to audit")
    parser.add_argument("--keys-file", help="one id per line")
    parser.add_argument("--prefix")
    parser.add_argument("--fail-on-forbidden", action="store_true")
    parser.add_argument("--out", metavar="JSON")
    args = parser.parse_args()

    with open(args.catalog, encoding="utf-8") as handle:
        strings = json.load(handle)["strings"]
    with open(args.glossary, encoding="utf-8") as handle:
        glossary = json.load(handle)
    if glossary.get("locale") not in (None, args.locale):
        print(f"term_audit: glossary is for {glossary.get('locale')}, not {args.locale}", file=sys.stderr)
        sys.exit(2)
    keys = set(args.keys.split(",")) if args.keys else None
    if args.keys_file:
        with open(args.keys_file, encoding="utf-8") as handle:
            keys = (keys or set()) | {line.strip() for line in handle if line.strip()}
    units = list(catalog_units(strings, args.locale))
    if args.shield:
        with open(args.shield, encoding="utf-8") as handle:
            units += list(shield_units(handle.read(), args.locale))
    units = list(selected(units, keys, args.prefix))

    report = {"locale": args.locale, "units": len(units),
              "terms": audit_terms(glossary.get("terms", {}), units),
              "controls": audit_controls(glossary.get("controls", {}), units),
              "open": audit_open(glossary.get("open", []), units)}
    report["forbidden_total"] = sum(len(t["forbidden_hits"]) for t in report["terms"].values())
    report["drift_total"] = sum(len(c["drift"]) for c in report["controls"].values())
    print_report(report)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    sys.exit(1 if args.fail_on_forbidden and report["forbidden_total"] else 0)


if __name__ == "__main__":
    main()
