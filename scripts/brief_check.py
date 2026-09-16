#!/usr/bin/env python3
"""Structural check of a locale brief against TEMPLATE.md and its glossary.

usage: brief_check.py --root <skill-dir> --locale <tag> [--catalog <xcstrings>]
                     [--facts <harvest-dir>] [--out report.json]

Checks (B* brief, G* glossary, E* evidence, H* honesty):
  B1  the "## " headings and their order equal TEMPLATE.md
  B2  the Contents line lists those headings in order
  B3  no section is empty and no TEMPLATE instruction line survives verbatim
  G1  glossary parses, carries locale/snapshot/catalog_commit/terms/controls/open,
      and its locale equals the tag
  G2  every control in ro.json's control set has a preferred form and a roles object
  G3  each term carries preferred, forms, forbidden, decided_by, note; preferred is
      among forms; no forbidden form is also a form
  G4  each open item carries the fields term_audit.py reads, with recommended among options
  G5  the brief's Control forms table names each control's preferred form
  G6  the brief and the glossary list the same open ids
  E1  every dotted key cited in the brief exists in the catalog (needs --catalog)
  E2  Apple values, plural categories, the length trigger and the catalog tag match the
      harvest (needs --facts <dir>/per-locale/<tag>/)
  H1  no claim of native, owner or certified human approval
  H2  a locale with no shipped copy marks its glossary rows as seeds (decided_by
      skill-seed-<date>), so an owner can tell research from accepted copy

Exit 1 when any check fails. A finding is (check, severity, message); major blocks a
pilot batch, info is a note. The facts directory is the harvest described in
references/locale-decisions.md "## Platform terms"; omit --facts to skip E2.
"""
import argparse
import json
import os
import re
import sys

CONTROL_SET = ["Cancel", "Done", "Continue", "Save", "Edit", "Delete", "Skip", "Allow",
               "Don't allow", "Got it", "Retry", "Settings"]
TERM_FIELDS = ("preferred", "forms", "forbidden", "decided_by", "note")
OPEN_FIELDS = ("id", "options", "recommended", "recommended_reason", "decided_by", "status", "note")
KEY = re.compile(r"(?<![\w./-])([a-z][A-Za-z0-9]*(?:\.[a-zA-Z][A-Za-z0-9]*){1,4})(?![\w/-])")
NOT_KEYS = re.compile(r"\.(swift|md|json|py|sh|plist|png|xcstrings|strings|stringsdict|lproj|framework|app|bundle|txt|tsv)$")
HUMAN_CLAIM = re.compile(r"native[- ](?:speaker|reader)[- ](?:approved|reviewed|verified|certified)|"
                         r"reviewed by a native|certified (?:translation|translator)|owner[- ]approved|"
                         r"human[- ]approved", re.I)
SEED = re.compile(r"^skill-seed-\d{4}-\d{2}-\d{2}$")
DENIAL = re.compile(r"\b(no|not|never|without|neither|nobody|none|nothing|nor)\b|recommend|before the pilot|until a|claim")


def headings(text):
    return [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]


def sections(text):
    out, current = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            out[current] = []
        elif current:
            out[current].append(line)
    return out


def contents_line(text):
    for line in text.splitlines():
        if line.startswith("Contents:"):
            return [p.strip() for p in line[len("Contents:"):].split("·")]
    return None


def whole_word(text, form):
    return re.search(r"(?<!\w)" + re.escape(form) + r"(?!\w)", text, re.I) is not None


def check_brief(brief, template, findings):
    want, got = headings(template), headings(brief)
    if want != got:
        findings.append(("B1", "major", f"headings differ from TEMPLATE.md: missing {[h for h in want if h not in got]}, "
                                        f"extra {[h for h in got if h not in want]}, order {'differs' if set(want) == set(got) else 'n/a'}"))
    listed = contents_line(brief)
    if listed is None:
        findings.append(("B2", "major", "no Contents line"))
    elif listed != got:
        findings.append(("B2", "major", f"Contents line does not match the headings: {listed} vs {got}"))
    boilerplate = {l.strip() for l in template.splitlines() if len(l.strip()) > 60 and not l.startswith("#")}
    for name, lines in sections(brief).items():
        body = [l for l in lines if l.strip()]
        if not body:
            findings.append(("B3", "major", f"section '{name}' is empty"))
        for line in body:
            if line.strip() in boilerplate:
                findings.append(("B3", "major", f"section '{name}' still carries the TEMPLATE instruction line: {line.strip()[:80]}"))


def check_glossary(glossary, tag, brief, findings):
    for field in ("locale", "snapshot", "catalog_commit", "terms", "controls", "open"):
        if field not in glossary:
            findings.append(("G1", "major", f"glossary has no '{field}'"))
    if glossary.get("locale") != tag:
        findings.append(("G1", "major", f"glossary locale is {glossary.get('locale')!r}, not {tag!r}"))
    controls = glossary.get("controls", {})
    for label in CONTROL_SET:
        row = controls.get(label)
        if not isinstance(row, dict) or not row.get("preferred"):
            findings.append(("G2", "major", f"control {label!r} has no preferred form"))
            continue
        if not isinstance(row.get("roles", {}), dict):
            findings.append(("G2", "major", f"control {label!r} roles is not an object"))
        if not whole_word(brief, row["preferred"]):
            findings.append(("G5", "major", f"the brief never names {label!r}'s preferred form {row['preferred']!r}"))
    for tid, term in glossary.get("terms", {}).items():
        for field in TERM_FIELDS:
            if field not in term:
                findings.append(("G3", "major", f"term {tid!r} has no '{field}'"))
        forms = [f.casefold() for f in term.get("forms", [])]
        if term.get("preferred") and term["preferred"].casefold() not in forms:
            findings.append(("G3", "major", f"term {tid!r}: preferred {term['preferred']!r} is not in forms"))
        clash = [f for f in term.get("forbidden", []) if f.casefold() in forms]
        if clash:
            findings.append(("G3", "major", f"term {tid!r}: {clash} are both forbidden and a form"))
    ids = []
    for item in glossary.get("open", []):
        ids.append(item.get("id"))
        for field in OPEN_FIELDS:
            if field not in item:
                findings.append(("G4", "major", f"open item {item.get('id')!r} has no '{field}'"))
        if item.get("recommended") and item.get("recommended") not in item.get("options", []):
            findings.append(("G4", "major", f"open item {item.get('id')!r}: recommended is not one of options"))
    for oid in ids:
        if oid and not whole_word(brief, oid) and oid.replace("_", " ") not in brief:
            findings.append(("G6", "info", f"open id {oid!r} is in the glossary but not named in the brief"))


def check_evidence(brief, catalog_path, findings):
    with open(catalog_path, encoding="utf-8") as handle:
        keys = set(json.load(handle)["strings"])
    roots = {k.split(".")[0] for k in keys}
    stems = {k[:i] for k in keys for i, c in enumerate(k) if c == "."}
    unknown = set()
    for match in KEY.finditer(brief):
        token = match.group(1)
        # a bare stem ("main.tab" for main.tab.*) is a legitimate way to name a family
        after = brief[match.end():match.end() + 2]
        # "prefix.*"/"prefix*" name a key family and "x.y()" is Swift, not a key
        if after.startswith("*") or after.startswith(".*") or after.startswith("("):
            continue
        if NOT_KEYS.search(token) or token in keys or token in stems or token.split(".")[0] not in roots:
            continue
        unknown.add(token)
    for token in sorted(unknown):
        findings.append(("E1", "major", f"cited key {token!r} is not in the catalog"))


def check_facts(brief, glossary, tag, facts_dir, findings):
    here = os.path.join(facts_dir, "per-locale", tag)
    def load(name):
        path = os.path.join(here, name)
        return json.load(open(path, encoding="utf-8")) if os.path.isfile(path) else None
    terms, formats, coverage, length = load("platform-terms.json"), load("locale-formats.json"), load("apple-coverage.json"), load("length-stats.json")
    if terms:
        missing = []
        for term in terms.get("terms", []):
            cell = term.get("values", {}).get(tag, {})
            value = cell.get("value")
            if value and len(value) > 3 and term["id"].split(".")[0] in ("screen_time", "focus_mode", "home_screen", "settings", "photos", "health") \
                    and not whole_word(brief, value):
                missing.append(f"{term['id']}={value!r}")
        if missing:
            findings.append(("E2", "info", f"Apple values not quoted in the brief: {', '.join(missing[:8])}"))
    if formats and tag in formats:
        want = formats[tag]["plural"].get("recommended_required", [])
        named = [c for c in want if whole_word(brief, c)]
        if len(named) < len(want):
            findings.append(("E2", "major", f"plural categories {want} are required but the brief names only {named}"))
    if coverage:
        loc = coverage.get("locale") or {}
        want_tag = loc.get("recommended_catalog_tag")
        if want_tag and want_tag != tag:
            findings.append(("E2", "major", f"the harvest recommends catalog tag {want_tag!r}, this brief is {tag!r}"))
    if length:
        rec = ((length.get("locale") or {}).get("recommendation") or {})
        trigger = str(rec.get("trigger") or rec.get("recommended_trigger") or "")
        number = re.search(r"\d\.\d\d?", trigger)
        if number and number.group(0) not in brief:
            findings.append(("E2", "major", f"length trigger {number.group(0)} from the harvest is not in the brief"))


def check_honesty(brief, glossary, tag, findings):
    for match in HUMAN_CLAIM.finditer(brief):
        start = max(brief.rfind(". ", 0, match.start()), brief.rfind("\n", 0, match.start())) + 1
        end = brief.find(". ", match.end())
        sentence = brief[start:end if end > 0 else match.end() + 60].lower()
        if DENIAL.search(sentence):  # "no native reader has reviewed this" is the honest form
            continue
        findings.append(("H1", "major", f"claims human approval: {match.group(0)!r}"))
    if tag != "ro":
        unseeded = [tid for tid, term in glossary.get("terms", {}).items()
                    if not SEED.match(str(term.get("decided_by", "")))
                    and not str(term.get("decided_by", "")).startswith("apple-")]
        if unseeded:
            findings.append(("H2", "info", f"terms not marked as seeds: {', '.join(sorted(unseeded))}"))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser.add_argument("--locale", required=True)
    parser.add_argument("--catalog")
    parser.add_argument("--facts")
    parser.add_argument("--out", metavar="JSON")
    args = parser.parse_args()

    brief_path = os.path.join(args.root, "references", "locale-briefs", f"{args.locale}.md")
    glossary_path = os.path.join(args.root, "glossary", f"{args.locale}.json")
    findings = []
    if not os.path.isfile(brief_path):
        findings.append(("B1", "major", f"no brief at {brief_path}"))
    if not os.path.isfile(glossary_path):
        findings.append(("G1", "major", f"no glossary at {glossary_path}"))
    brief = open(brief_path, encoding="utf-8").read() if os.path.isfile(brief_path) else ""
    glossary = {}
    if os.path.isfile(glossary_path):
        try:
            glossary = json.load(open(glossary_path, encoding="utf-8"))
        except json.JSONDecodeError as error:
            findings.append(("G1", "major", f"glossary is not valid JSON: {error}"))
    if brief:
        check_brief(brief, open(os.path.join(args.root, "references", "locale-briefs", "TEMPLATE.md"), encoding="utf-8").read(), findings)
        check_honesty(brief, glossary, args.locale, findings)
        if glossary:
            check_glossary(glossary, args.locale, brief, findings)
        if args.catalog:
            check_evidence(brief, args.catalog, findings)
        if args.facts:
            check_facts(brief, glossary, args.locale, args.facts, findings)

    majors = [f for f in findings if f[1] == "major"]
    print(f"brief_check {args.locale}: {len(majors)} major, {len(findings) - len(majors)} info")
    for check, severity, message in findings:
        print(f"  {check} {severity}: {message}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump({"locale": args.locale, "findings": [{"check": c, "severity": s, "message": m} for c, s, m in findings]},
                      handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    sys.exit(1 if majors else 0)


if __name__ == "__main__":
    main()
