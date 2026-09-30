#!/usr/bin/env python3
"""Inventory quote records without changing or discarding corpus content."""

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import defaultdict
from pathlib import Path


SHIPPABLE = {
    "sourced", "sourced_unverified", "supplied_unverified", "authored",
    "curated", "legacy_unsourced",
}
EXCLUDED = {"rejected", "not_relevant", "unverified"}
LOCALE_PATTERN = re.compile(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*")


def content_hash(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def issue(code, record_ids, detail, blocking=True):
    return {"code": code, "record_ids": sorted(record_ids), "detail": detail,
            "blocking": blocking}


def record_locale(record):
    if "language" not in record:
        return "en"
    language = record["language"]
    return language if isinstance(language, str) and LOCALE_PATTERN.fullmatch(language) else "<invalid>"


def verification_status(record):
    verification = record.get("verification")
    if isinstance(verification, dict):
        return verification.get("status")
    return verification


def is_user_content(record):
    return (record.get("userCreated") is True or record.get("isUserCreated") is True
            or record.get("origin") == "user" or record.get("contentType") == "user")


def build_inventory(corpus: dict, locales: list[str]) -> dict:
    if not isinstance(corpus, dict) or not isinstance(corpus.get("quotes"), list):
        raise ValueError("corpus must contain a quotes list")
    if not locales or any(not isinstance(locale, str) or not LOCALE_PATTERN.fullmatch(locale)
                          for locale in locales):
        raise ValueError("locales must be nonempty language codes")
    if len(locales) != len(set(locales)):
        raise ValueError("locales must be unique")

    records = {}
    for record in corpus["quotes"]:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not record["id"].strip():
            raise ValueError("every quote must have a nonempty string id")
        record_id = record["id"]
        if record_id in records:
            raise ValueError(f"duplicate quote id: {record_id}")
        records[record_id] = record

    parent = {record_id: record_id for record_id in records}
    record_issues = defaultdict(list)

    def root(record_id):
        while parent[record_id] != record_id:
            parent[record_id] = parent[parent[record_id]]
            record_id = parent[record_id]
        return record_id

    def connect(left, right):
        left_root, right_root = root(left), root(right)
        if left_root != right_root:
            parent[max(left_root, right_root)] = min(left_root, right_root)

    pair_keys = defaultdict(list)
    reference_keys = defaultdict(list)
    valid_parent = {}
    for record_id, record in records.items():
        category = record.get("category")
        if not isinstance(category, str) or not category.strip():
            record_issues[record_id].append(issue("invalid_category", [record_id], "Missing or malformed category"))
        if not isinstance(record.get("text"), str) or not record["text"].strip():
            record_issues[record_id].append(issue("invalid_text", [record_id], "Missing or empty text"))
        language = record_locale(record)
        if "language" not in record:
            record_issues[record_id].append(issue("assumed_english", [record_id],
                                                   "Missing language treated as en by the legacy emitter", False))
        elif language == "<invalid>":
            record_issues[record_id].append(issue("invalid_language", [record_id], "Malformed language"))

        status = verification_status(record)
        if isinstance(status, str) and status in EXCLUDED:
            record_issues[record_id].append(issue("excluded_status", [record_id], f"Verification status: {status}"))
        elif not isinstance(status, str) or status not in SHIPPABLE:
            record_issues[record_id].append(issue("unknown_verification", [record_id],
                                                   f"Unknown verification status: {status!r}"))
        if is_user_content(record):
            record_issues[record_id].append(issue("user_content", [record_id], "User content is outside corpus translation"))

        pair_id = record.get("pairId")
        if pair_id is not None:
            if isinstance(pair_id, str) and pair_id.strip() and isinstance(category, str):
                pair_keys[(category, pair_id)].append(record_id)
            else:
                record_issues[record_id].append(issue("invalid_pair_id", [record_id], "Malformed pairId"))
        source = record.get("source")
        reference = source.get("canonicalReference") if isinstance(source, dict) else None
        if reference is not None:
            if not isinstance(reference, str) or not reference.strip():
                record_issues[record_id].append(issue("invalid_canonical_reference", [record_id],
                                                       "Malformed canonicalReference"))
            elif category == "religion" and source.get("verifiedBy") == "canonical_corpus":
                reference_keys[(category, reference)].append(record_id)
            else:
                record_issues[record_id].append(issue("unverified_canonical_reference", [record_id],
                                                       "Canonical reference cannot establish a counterpart without scripture evidence"))

        target_id = record.get("translationOf")
        if target_id is None:
            continue
        if not isinstance(target_id, str) or not target_id.strip():
            record_issues[record_id].append(issue("invalid_translation_link", [record_id], "Malformed translationOf"))
        elif target_id not in records:
            record_issues[record_id].append(issue("missing_translation_target", [record_id],
                                                   f"translationOf target {target_id!r} is missing"))
        elif records[target_id].get("category") != category:
            link_issue = issue("cross_category_translation", [record_id, target_id],
                               "translationOf crosses categories")
            record_issues[record_id].append(link_issue)
            record_issues[target_id].append(link_issue)
        else:
            valid_parent[record_id] = target_id
            connect(record_id, target_id)

    for keys in (pair_keys, reference_keys):
        for keyed_records in keys.values():
            for record_id in keyed_records[1:]:
                connect(keyed_records[0], record_id)

    cycles = set()
    for start in valid_parent:
        path, position = [], {}
        current = start
        while current in valid_parent and current not in position:
            position[current] = len(path)
            path.append(current)
            current = valid_parent[current]
        if current in position:
            cycles.add(tuple(sorted(path[position[current]:])))
    for cycle in sorted(cycles):
        for record_id in cycle:
            record_issues[record_id].append(issue("translation_cycle", cycle, "translationOf contains a cycle"))

    components = defaultdict(list)
    for record_id in records:
        components[root(record_id)].append(record_id)

    groups = []
    translation_targets = set(valid_parent.values())
    for member_ids in components.values():
        member_ids.sort()
        members = defaultdict(list)
        group_issues = []
        categories, pair_ids, references = set(), set(), set()
        for record_id in member_ids:
            record = records[record_id]
            category = record.get("category")
            if isinstance(category, str):
                categories.add(category)
            if isinstance(record.get("pairId"), str) and record["pairId"].strip():
                pair_ids.add(record["pairId"])
            source = record.get("source")
            reference = source.get("canonicalReference") if isinstance(source, dict) else None
            if isinstance(reference, str) and reference.strip():
                references.add(reference)
            language = record_locale(record)
            members[language].append(record_id)
            group_issues.extend(record_issues[record_id])

        category = next(iter(categories)) if len(categories) == 1 else ""
        if len(pair_ids) > 1 or len(references) > 1:
            group_issues.append(issue("conflicting_metadata", member_ids,
                                      "Linked records have different pairId or canonicalReference values"))
        for language, ids in members.items():
            if len(ids) > 1:
                group_issues.append(issue("ambiguous_locale", ids,
                                          f"Multiple records are linked in locale {language}"))

        roots = [record_id for record_id in member_ids if record_id not in valid_parent]
        linked_roots = [record_id for record_id in roots if record_id in translation_targets]
        if len(linked_roots) > 1:
            source_id = member_ids[0]
            group_issues.append(issue("ambiguous_source", member_ids,
                                      "Multiple translationOf roots claim the group"))
        elif len(linked_roots) == 1:
            source_id = linked_roots[0]
        elif len(members.get("en", [])) == 1:
            source_id = members["en"][0]
            if len(member_ids) > 1 and not linked_roots:
                group_issues.append(issue("unknown_original_language", member_ids,
                                          "No translationOf chain establishes the original", False))
        elif len(member_ids) == 1:
            source_id = member_ids[0]
        elif len(roots) == 1:
            source_id = roots[0]
        else:
            source_id = member_ids[0]
            group_issues.append(issue("ambiguous_source", member_ids,
                                      "No unambiguous translation source"))

        source_record = records[source_id]
        source_pair = source_record.get("pairId")
        source_data = source_record.get("source")
        source_reference = source_data.get("canonicalReference") if isinstance(source_data, dict) else None
        if len(pair_ids) == 1 and (not linked_roots or source_pair in pair_ids):
            group_id = f"pair:{category}:{next(iter(pair_ids))}"
        elif (len(references) == 1 and category == "religion"
              and isinstance(source_data, dict) and source_data.get("verifiedBy") == "canonical_corpus"
              and source_reference in references):
            group_id = f"reference:{category}:{next(iter(references))}"
        else:
            group_id = f"record:{source_id}" if len(linked_roots) == 1 else f"record:{member_ids[0]}"
        missing = [locale for locale in locales if locale not in members]
        groups.append({"id": group_id, "category": category,
                       "members": {language: members[language] for language in sorted(members)},
                       "source_id": source_id, "missing_locales": missing,
                       "eligible": bool(missing) and not any(item["blocking"] for item in group_issues),
                       "issues": group_issues})

    groups.sort(key=lambda group: group["id"])
    all_issues = [item for group in groups for item in group["issues"]]
    counts = {"records": len(records), "groups": len(groups),
              "eligible_groups": sum(group["eligible"] for group in groups),
              "complete_groups": sum(not group["missing_locales"] for group in groups),
              "held_groups": sum(bool(group["missing_locales"]) and not group["eligible"] for group in groups),
              "missing_locale_slots": sum(len(group["missing_locales"]) for group in groups),
              "issues": len(all_issues)}
    return {"schema_version": 1, "corpus_hash": content_hash(corpus),
            "locales": locales[:], "records": records, "groups": groups,
            "issues": all_issues, "counts": counts}


def main():
    parser = argparse.ArgumentParser(description="Preservation-first quote corpus inventory")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--locales", required=True, help="Comma-separated target locales")
    parser.add_argument("--out", type=Path, help="Output JSON path; stdout when omitted")
    args = parser.parse_args()
    if args.out and args.out.resolve() == args.corpus.resolve():
        parser.error("output must not overwrite the corpus")
    with args.corpus.open(encoding="utf-8") as source:
        inventory = build_inventory(json.load(source), args.locales.split(","))
    encoded = json.dumps(inventory, ensure_ascii=False, indent=2) + "\n"
    if args.out is None:
        print(encoded, end="")
        return
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.out.parent,
                                         prefix=f".{args.out.name}.", delete=False) as temporary:
            temporary.write(encoded)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, args.out)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


if __name__ == "__main__":
    main()
