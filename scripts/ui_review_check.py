#!/usr/bin/env python3
"""Check flat ordinary UI translator or editor result structure, not language quality."""

import argparse
from collections import Counter
import json
from pathlib import Path


VERDICTS = {"pass", "finding", "not_checked", "not_applicable"}
REVIEW_VERDICTS = {"pass", "finding", "not_checked"}
SEVERITIES = {"critical", "major", "minor", "preference"}
REASONS_REQUIRED = {"not_checked", "not_applicable"}


def issue(errors, code, path, message):
    errors.append({"code": code, "path": path, "message": message})


def rows(value, path, errors):
    if not isinstance(value, list):
        issue(errors, "invalid", path, "expected an array")
        return []
    return value


def ids(items, path, errors):
    found = []
    for index, item in enumerate(items):
        location = f"{path}[{index}]"
        if not isinstance(item, dict):
            issue(errors, "invalid", location, "expected an object")
        elif not isinstance(item.get("id"), str) or not item["id"].strip():
            issue(errors, "invalid", f"{location}.id", "expected a nonempty string")
        else:
            found.append(item["id"])
    for identifier, count in Counter(found).items():
        if count > 1:
            issue(errors, "duplicate", path, f"ID {identifier!r} occurs {count} times")
    return set(found)


def coverage(expected, actual, path, errors):
    for identifier in sorted(expected - actual):
        issue(errors, "missing", path, f"missing ID {identifier!r}")
    for identifier in sorted(actual - expected):
        issue(errors, "extra", path, f"unexpected ID {identifier!r}")


def reason_list(row, field, path, errors):
    reasons = row.get(field)
    if not isinstance(reasons, list) or any(not isinstance(value, str) for value in reasons):
        issue(errors, "invalid", f"{path}.{field}", "expected an array of strings")
        return []
    return [value.strip() for value in reasons if value.strip()]


def verdicts(row, reason_field, path, errors):
    needs_reason = False
    for dimension in ("casing", "syntax", "register"):
        field = f"{dimension}_verdict"
        verdict = row.get(field)
        if not isinstance(verdict, str) or verdict not in VERDICTS:
            issue(errors, "invalid", f"{path}.{field}", f"expected one of {sorted(VERDICTS)}")
        if isinstance(verdict, str) and verdict in REASONS_REQUIRED:
            needs_reason = True
    reasons = reason_list(row, reason_field, path, errors)
    if needs_reason and not reasons:
        issue(errors, "unexplained", f"{path}.{reason_field}",
              "not_checked or not_applicable needs a nonempty uncertainty or scope reason")
    return reasons


def packet_ids(role, packet, errors):
    if role == "translator":
        entries = rows(packet.get("entries"), "packet.entries", errors)
        expected = ids(entries, "packet.entries", errors)
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            path = f"packet.entries[{index}]"
            if entry.get("hero") is not False:
                issue(errors, "unsupported", f"{path}.hero", "hero entries are unsupported")
            units = entry.get("source_units")
            if not isinstance(units, dict) or set(units) != {""} or not isinstance(units.get(""), str):
                issue(errors, "unsupported", f"{path}.source_units", "nested or plural source units are unsupported")
            if entry.get("variations") not in ({}, None):
                issue(errors, "unsupported", f"{path}.variations", "plural variations are unsupported")
            target_units = entry.get("target_units")
            if target_units not in (None, {}) and (not isinstance(target_units, dict)
                                                   or set(target_units) != {""}
                                                   or not isinstance(target_units.get(""), str)):
                issue(errors, "unsupported", f"{path}.target_units", "nested target units are unsupported")
        return expected

    if packet.get("hero") not in ([], None):
        issue(errors, "unsupported", "packet.hero", "hero packets are unsupported")
    strings = rows(packet.get("strings"), "packet.strings", errors)
    expected = ids(strings, "packet.strings", errors)
    for index, string in enumerate(strings):
        if not isinstance(string, dict):
            continue
        path = f"packet.strings[{index}]"
        if string.get("plural") is not None:
            issue(errors, "unsupported", f"{path}.plural", "plural strings are unsupported")
        if "units" in string or "variations" in string:
            issue(errors, "unsupported", path, "nested strings are unsupported")
        if not isinstance(string.get("text"), str):
            issue(errors, "invalid", f"{path}.text", "expected a string")
    return expected


def check_translator(packet, result, expected, errors):
    candidates = rows(result.get("candidates"), "result.candidates", errors)
    holds = rows(result.get("holds"), "result.holds", errors)
    source_entries = packet.get("entries") if isinstance(packet.get("entries"), list) else []
    empty_sources = {entry["id"] for entry in source_entries
                     if isinstance(entry, dict) and isinstance(entry.get("source_units"), dict)
                     and entry["source_units"].get("") == "" and isinstance(entry.get("id"), str)}
    candidate_ids = ids(candidates, "result.candidates", errors)
    hold_ids = ids(holds, "result.holds", errors)
    for identifier in sorted(candidate_ids & hold_ids):
        issue(errors, "overlap", "result", f"ID {identifier!r} is both candidate and hold")
    coverage(expected, candidate_ids | hold_ids, "result", errors)
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            continue
        path = f"result.candidates[{index}]"
        if isinstance(candidate.get("text"), (dict, list)) or "units" in candidate or "plural" in candidate:
            issue(errors, "unsupported", path, "nested or plural candidates are unsupported")
        elif not isinstance(candidate.get("text"), str):
            issue(errors, "invalid", f"{path}.text", "expected a string")
        elif not candidate["text"].strip() and candidate.get("id") not in empty_sources:
            issue(errors, "invalid", f"{path}.text", "empty candidate needs an empty source string")
        verdicts(candidate, "uncertainty", path, errors)
    for index, hold in enumerate(holds):
        if isinstance(hold, dict) and (not isinstance(hold.get("reason"), str) or not hold["reason"].strip()):
            issue(errors, "invalid", f"result.holds[{index}].reason", "expected a nonempty reason")


def check_editor(result, expected, errors):
    reviews = rows(result.get("reviews"), "result.reviews", errors)
    coverage(expected, ids(reviews, "result.reviews", errors), "result.reviews", errors)
    for index, review in enumerate(reviews):
        if not isinstance(review, dict):
            continue
        path = f"result.reviews[{index}]"
        verdict = review.get("verdict")
        if not isinstance(verdict, str) or verdict not in REVIEW_VERDICTS:
            issue(errors, "invalid", f"{path}.verdict", f"expected one of {sorted(REVIEW_VERDICTS)}")
        reasons = verdicts(review, "uncertainties", path, errors)
        findings = rows(review.get("findings"), f"{path}.findings", errors)
        if (verdict == "finding" or any(review.get(f"{name}_verdict") == "finding"
                                        for name in ("casing", "syntax", "register"))) and not findings:
            issue(errors, "invalid", f"{path}.findings", "finding verdict needs at least one finding")
        if verdict == "pass" and findings:
            issue(errors, "invalid", f"{path}.findings", "pass verdict cannot carry findings")
        if verdict == "not_checked" and not reasons:
            issue(errors, "unexplained", f"{path}.uncertainties", "not_checked needs a nonempty reason")
        for finding_index, finding in enumerate(findings):
            location = f"{path}.findings[{finding_index}]"
            if not isinstance(finding, dict):
                issue(errors, "invalid", location, "expected an object")
                continue
            if not isinstance(finding.get("severity"), str) or finding["severity"] not in SEVERITIES:
                issue(errors, "invalid", f"{location}.severity", f"expected one of {sorted(SEVERITIES)}")
            for field in ("category", "target_span", "reader_impact", "suggestion"):
                if not isinstance(finding.get(field), str) or not finding[field].strip():
                    issue(errors, "invalid", f"{location}.{field}", "expected a nonempty string")


def validate(role, packet, result):
    errors = []
    if not isinstance(packet, dict) or not isinstance(result, dict):
        issue(errors, "invalid", "root", "packet and result must be objects")
        return errors
    if not isinstance(packet.get("locale"), str) or not packet["locale"].strip():
        issue(errors, "invalid", "packet.locale", "expected a nonempty string")
    if result.get("locale") != packet.get("locale") or not isinstance(result.get("locale"), str):
        issue(errors, "mismatch", "result.locale", "locale differs from packet")
    if type(packet.get("rev")) is not int or packet["rev"] < 1:
        issue(errors, "invalid", "packet.rev", "expected a positive integer")
    if type(result.get("candidate_revision")) is not int or result["candidate_revision"] != packet.get("rev"):
        issue(errors, "mismatch", "result.candidate_revision", "revision differs from packet")
    expected = packet_ids(role, packet, errors)
    if role == "translator":
        check_translator(packet, result, expected, errors)
    else:
        check_editor(result, expected, errors)
    return errors


def main():
    parser = argparse.ArgumentParser(description="Structural check for flat ordinary UI A/C output only; no linguistic acceptance. Hero, plural, and nested packets are unsupported.")
    parser.add_argument("--role", required=True, choices=("translator", "editor"))
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args()
    try:
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
        result = json.loads(args.result.read_text(encoding="utf-8"))
        errors = validate(args.role, packet, result)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors = [{"code": "input", "path": "file", "message": str(exc)}]
    print(json.dumps({"ok": not errors, "scope": "flat ordinary UI structure only; no linguistic acceptance",
                      "role": args.role, "diagnostics": errors}, ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
