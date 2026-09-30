"""Validate declared UI casing without rewriting text or guessing linguistic intent."""
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


POLICY = Path(__file__).resolve().parents[1] / "references/casing-policy.json"
ROLES = {"screen_title", "button", "tab", "section_heading", "compact_heading", "caption",
         "body", "placeholder", "value_label", "continuation", "unit", "system_label", "brand", "format"}
STYLES = {"sentence", "uppercase", "lowercase", "title", "preserve", "uncased"}
POSITIONS = {"standalone", "continuation", "template", "not_applicable"}
OWNERS = {"catalog", "view", "formatter", "system"}
EXCLUDED_KINDS = {"quote", "affirmation", "scripture", "attributed-quotation", "user-content", "attributed", "user"}
TOKEN = re.compile(r"%#@\w+@|%(?:\d+\$)?[-+0#]*\d*(?:\.\d+)?(?:hh|h|ll|l|q|z|t|L)?[@dDiuUxXoOfeEgGcCsSpaAF%]")
WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)


def load_policy(path=POLICY):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def locale_policy(policy, locale):
    row = policy.get("locales", {}).get(locale)
    if row is None:
        return None
    return {"protected_terms": policy.get("protected_terms", []),
            **policy.get("profiles", {}).get(row.get("profile"), {}), **row}


def policy_errors(policy, locale):
    row = locale_policy(policy, locale)
    if not row:
        return [f"no explicit casing policy for {locale}"]
    errors = []
    if not row.get("evidence"):
        errors.append("locale casing policy has no evidence")
    for role in sorted(ROLES):
        if row.get("roles", {}).get(role) not in STYLES:
            errors.append(f"missing or invalid casing style for {role}")
    return errors


def finding(key, variation, message, severity="needs_disposition"):
    return {"check": "C12", "severity": severity, "key": key, "variation": variation, "message": message}


def text_units(localization, path=""):
    if "stringUnit" in localization:
        yield path, localization["stringUnit"].get("value", "")
    for kind, forms in localization.get("variations", {}).items():
        for name, value in forms.items():
            yield from text_units(value, f"{path}/{kind}:{name}".lstrip("/"))
    for name, value in localization.get("substitutions", {}).items():
        yield from text_units(value, f"{path}/substitution:{name}".lstrip("/"))


def context_errors(context, rule):
    if context.get("status") != "confirmed":
        yield "casing context is not confirmed"
    for field, allowed in (("role", ROLES), ("style", STYLES), ("position", POSITIONS), ("owner", OWNERS)):
        if context.get(field) not in allowed:
            yield f"missing or unknown casing {field}"
    exceptions = context.get("exceptions", [])
    if not isinstance(exceptions, list) or any(not isinstance(x, dict) or not x.get("text") or
                                               not x.get("reason") for x in exceptions):
        yield "casing exceptions require exact text and a reason"
    if not isinstance(context.get("protected_terms"), list) or any(
            not isinstance(x, str) or not x for x in context.get("protected_terms", [])):
        yield "protected_terms must be an explicit list of exact spellings"
    expected = rule.get("roles", {}).get(context.get("role"))
    if expected and context.get("style") != expected and not exceptions:
        yield f"role requires {expected} casing; a different style needs an exact, justified exception"
    if context.get("role") == "continuation" and context.get("position") != "continuation":
        yield "continuation role must identify its sentence position"
    if not context.get("evidence"):
        yield "casing context lacks role and display-owner evidence"
    transform = context.get("transform", {}).get("operation", "none")
    if transform not in {"none", "uppercase", "lowercase", "capitalize"}:
        yield "unknown display case transformation"
    if transform != "none":
        site = context["transform"]
        if not isinstance(site.get("file"), str) or not site["file"] or \
                type(site.get("line")) is not int or site["line"] < 1:
            yield "display transform requires a verified source file and line"
        if context.get("owner") != "view":
            yield "case transform conflicts with declared display owner"
        elif not all(context["transform"].get(field) for field in ("render_locale", "render_evidence")) or \
                context["transform"].get("render_status") != "pass":
            yield "view-owned transformation requires locale-specific rendered casing review"
    elif context.get("owner") == "view":
        yield "view-owned casing has no recorded transformation"


def protected_matches(value, term):
    def same_word(neighbour, edge):
        if neighbour.isdigit() or neighbour == "_":
            return True
        return neighbour.isalpha() and unicodedata.name(neighbour, "").split()[0] == \
            unicodedata.name(edge, "").split()[0]

    for match in re.finditer(re.escape(term), value, re.IGNORECASE):
        if match.start() and same_word(value[match.start() - 1], term[0]):
            continue
        if match.end() < len(value) and same_word(value[match.end()], term[-1]):
            continue
        yield match


def spelling_findings(value, context, rule):
    value = unicodedata.normalize("NFC", value)
    protected = [unicodedata.normalize("NFC", term) for term in
                 context.get("protected_terms", []) + rule.get("protected_terms", [])]
    exceptions = context.get("exceptions", [])
    for term in protected:
        for match in protected_matches(value, term):
            if match.group() != term:
                yield "major", f"protected spelling must be {term!r}, found {match.group()!r}"
    if any(unicodedata.normalize("NFC", x["text"]) == value for x in exceptions):
        return
    expected = rule.get("roles", {}).get(context["role"])
    if context["style"] != expected:
        yield "needs_disposition", "value does not match the exact exception to its role's casing style"
    masked = value
    for term in sorted(protected, key=len, reverse=True):
        for match in reversed(list(protected_matches(masked, term))):
            if match.group() == term:
                masked = masked[:match.start()] + "¤" + masked[match.end():]
    masked = TOKEN.sub("¤", masked)
    style = context["style"]
    if style in {"preserve", "uncased"}:
        return
    letters = [c for c in masked if c.lower() != c.upper()]
    if style == "uppercase" and any(c.islower() for c in letters):
        yield "major", "uppercase role contains lowercase letters"
    if style == "lowercase":
        if rule.get("interior_capitals") == "lexical_review":
            start = re.search(r"[\w¤]", masked)
            if start and start.group().isupper():
                yield "needs_disposition", "continuation begins with a capital; confirm noun or proper name"
        elif any(c.isupper() for c in letters):
            yield "needs_disposition", "lowercase fragment contains a capital; confirm a name or exception"
    if style not in {"sentence", "title"}:
        return
    # A placeholder, protected name or number can be the sentence's first word.
    start = re.search(r"[\w¤]", masked)
    if start and start.group().islower():
        yield "major", "standalone sentence/title starts with a lowercase letter"
    if len(letters) > 1 and all(c.isupper() for c in letters):
        yield "major", "unintended all caps outside protected names and acronyms"
    if any(match.group(1).islower() for match in re.finditer(r"[.!?]\s+(\w)", masked)):
        yield "needs_disposition", "lowercase after possible sentence boundary; confirm abbreviation or continuation"
    if style == "title":
        yield "needs_disposition", "title case requires locale-specific editorial review of main words"
    elif rule.get("interior_capitals") == "review":
        for match in WORD.finditer(masked):
            before = masked[:match.start()].rstrip(" \t")
            if re.search(r"[\w¤]", before) and before[-1] not in ".!?\n:" and match.group()[0].isupper():
                yield "needs_disposition", f"interior capital {match.group()!r}: confirm proper name or sentence boundary"
                break


def displayed_value(value, context, locale):
    if context["owner"] != "view":
        return value
    transform = context.get("transform", {})
    if transform.get("render_locale") != locale or transform.get("catalog_value") != value or \
            not isinstance(transform.get("rendered_value"), str):
        return None
    return transform["rendered_value"]


def check_casing(strings, keys, locale, packets, policy):
    """Return findings and explicit coverage; an empty finding list alone is not a readiness claim."""
    contexts, duplicates = {}, set()
    for packet in packets:
        if packet.get("locale") != locale:
            raise ValueError("casing context locale does not match the checked catalog locale")
        for entry in packet.get("entries", []):
            key = entry["key"]
            if key in contexts and contexts[key] != entry:
                duplicates.add(key)
            contexts[key] = entry
    rule = locale_policy(policy, locale) or {}
    policy_issues = policy_errors(policy, locale)
    findings, groups = [], defaultdict(list)
    coverage = {"keys": len(keys), "units": 0, "confirmed_units": 0, "excluded_keys": 0,
                "display_occurrences": 0, "unresolved_keys": [], "complete": False}
    for key in keys:
        entry = contexts.get(key, {})
        context = entry.get("casing", {})
        if entry.get("kind") in EXCLUDED_KINDS:
            if context.get("status") == "not_applicable" and context.get("evidence"):
                coverage["excluded_keys"] += 1
                continue
            findings.append(finding(key, "", "excluded content needs an explicit justified not_applicable record"))
            continue
        errors = list(policy_issues)
        if key in duplicates:
            errors.append("conflicting casing contexts for the same key")
        if entry.get("en") is not None:
            current = dict(text_units(strings[key].get("localizations", {}).get("en", {})))
            source = current.get("", current.get("plural:other", next(iter(current.values()), "")))
            if source != entry["en"] or strings[key].get("comment", "") != entry.get("comment", ""):
                errors.append("source or comment changed; refresh casing context before review")
            if "source_units" in entry and current != entry["source_units"]:
                errors.append("source variation changed; refresh casing context before review")
        findings.extend(finding(key, "", error) for error in errors)
        values = list(text_units(strings[key].get("localizations", {}).get(locale, {})))
        if not values:
            findings.append(finding(key, "", "no target units to check"))
        for variation, value in values:
            coverage["units"] += 1
            override = context.get("units", {}).get(variation)
            unit_context = {**context, **override} if override is not None else context
            if "substitution:" in variation and unit_context is context:
                findings.append(finding(key, variation, "substitution fragment requires its own casing context"))
                continue
            displays = [unit_context] + [{**unit_context, **occurrence}
                                         for occurrence in unit_context.get("occurrences", [])]
            for index, display in enumerate(displays):
                coverage["display_occurrences"] += 1
                display_path = variation if index == 0 else f"{variation}@o{index:02}"
                display_errors = list(context_errors(display, rule))
                findings.extend(finding(key, display_path, error) for error in display_errors)
                if errors or display_errors:
                    continue
                if index == 0:
                    coverage["confirmed_units"] += 1
                rendered = displayed_value(value, display, locale)
                if rendered is None:
                    findings.append(finding(key, display_path, "rendered casing evidence is absent or stale for this locale/value"))
                    continue
                findings.extend(finding(key, display_path, message, severity)
                                for severity, message in spelling_findings(rendered, display, rule))
                group = display.get("equivalent_group")
                if group:
                    groups[(group, display["role"], display["position"])].append(
                        (key, display_path, rendered, display["style"]))
    for rows in groups.values():
        for key, variation, value, style in rows:
            if any(style != other_style or (value.casefold() == other.casefold() and value != other)
                   for _, _, other, other_style in rows):
                findings.append(finding(key, variation, "equivalent controls disagree on casing", "major"))
    coverage["unresolved_keys"] = sorted({x["key"] for x in findings})
    coverage["complete"] = not findings and bool(keys)
    return findings, coverage
