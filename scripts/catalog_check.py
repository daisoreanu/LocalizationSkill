#!/usr/bin/env python3
"""Deterministic checks over a String Catalog before and after each candidate revision.

Necessary, not sufficient: xcodebuild stays the structural gate and the language
reviewers decide everything a script cannot. Checks (each finding carries its id):

  C1  placeholder multiset en vs target per unit (numbered tokens by position;
      an integer placeholder may be dropped only in the zero/one plural form)
  C2  plural categories: a missing CLDR category is major, an extra one is info
  C3  markup and typography parity: **bold**, newlines, links (major);
      ellipsis form, double spaces, edge whitespace, emoji (info)
  C4  cedilla diacritics U+015E/U+015F/U+0162/U+0163 in Romanian (major)
  C5  length above the brief's trigger on single-line, widget and button classes;
      a render-list entry, not a finding
  C6  glossary forbidden forms in the target (major, needs --glossary)
  C7  translatable key with a missing, new or needs_review target (major)
  C8  target equals the source outside the identical-by-design allowlist (info)
  C9  missing comment, or a stub comment whose tail is just the key's last segment (info)
  C10 same-source divergence: one English value, several targets (needs_disposition;
      major when a glossary control row exists and a key contradicts it)
  C11 origin and reachability of literal keys: debugOnly, previewOnly, shadow, format
      are excluded from translation; anything else reachable is a needs_disposition.
      Reads the Swift sources under --app-root (derived only when --catalog sits inside
      a checkout); a fixture outside one gets a needs_disposition per literal key instead

Exit 1 when a critical finding exists. Never writes into the app checkout.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

# Read-only git calls must not refresh the checkout's index.
os.environ.setdefault("GIT_OPTIONAL_LOCKS", "0")

SPEC = re.compile(r"%(\d+\$)?[-+0#]*\d*(?:\.\d+)?(?:hh|h|ll|l|q|z|t|L)?([@dDiuUxXoOfeEgGcCsSpaAF%])")
TYPE_CLASS = {"@": "@", "%": "%", "p": "p"}
TYPE_CLASS.update({c: "d" for c in "dDiuUxXoO"})
TYPE_CLASS.update({c: "f" for c in "feEgGaAF"})
TYPE_CLASS.update({c: "s" for c in "sScC"})
LINK = re.compile(r"\[[^\]]+\]\([^)]+\)")
EMOJI = re.compile("[\\U0001F300-\\U0001FAFF\\u2600-\\u27BF\\u2B50\\u2B06\\u2B07]")
CEDILLA = re.compile("[\\u015e\\u015f\\u0162\\u0163]")
LETTER = re.compile(r"[^\W\d_]")
NAMED_KEY = re.compile(r"^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)+$")
# CLDR cardinal categories; add a locale here before its first run (default one/other).
PLURAL_REQUIRED = {"ro": {"one", "few", "other"}, "en": {"one", "other"}}
RISK_PREFIXES = tuple(p + "." for p in ("paywall", "screenTime", "screenTimeReport", "streakFreeze", "notifications",
                                         "insights", "moneyfesting", "currency", "onboarding.hourlyWage", "onboarding.income"))
RISK_PATTERN = re.compile(r"^onboarding\.[^.]*Permission")
CLAIM_WORDS = re.compile(
    r"\b(price|pay|paid|pays|free|trial|subscri\w*|refund|charge\w*|bill\w*|cost\w*|currenc\w*|"
    r"discount|lifetime|restore|premium|unlock\w*|locked|upgrade|allow\w*|permission\w*|access|"
    r"authori\w*|screen time|delete\w*|remov\w*|erase\w*|reset|clear|discard|not|never|no|"
    r"without|only|cannot|always|every|all|forever|lowest|guaranteed)\b|n't\b|\d|%(?!@)",
    re.I)
SINGLE_LINE_TAIL = re.compile(
    r"(button|cta|action|title|label|tab|toggle|badge|chip|pill|header|heading|name|option|"
    r"placeholder|short|suffix|unit)$", re.I)
CONTROL_NOUN = re.compile(r"\b(button|line|tab|badge|chip|pill|toggle|widget|label|shield|caption|eyebrow|heading|header|title)$", re.I)
FIT_HINT = re.compile(r"single[- ]line|one line", re.I)
QUALIFIER = re.compile(r"\s+(?:used|shown|opening|above|below|under|for|on|in|by|of|with|to|into|from|across|that|which)\b.*$", re.I)
# running text that wraps; a control noun elsewhere in the comment ('Badge unlock criterion') does not make it single-line
BODY_TAIL = re.compile(r"(criterion|earned|message|body|description|explanation)$", re.I)
IDENTICAL_BY_DESIGN = {"moneyfesting", "ok", "warren buffett", "apple", "3d"}
UNIT_WORDS = {"h", "min", "s", "m", "sec", "kg", "km"}
SHIELD_INIT = re.compile(
    r'\.init\(\s*id:\s*"([^"]+)",\s*style:\s*\.(\w+),\s*titleEnglish:\s*"((?:[^"\\]|\\.)*)",'
    r'\s*titleRomanian:\s*"((?:[^"\\]|\\.)*)",\s*bodyEnglish:\s*"((?:[^"\\]|\\.)*)",'
    r'\s*bodyRomanian:\s*"((?:[^"\\]|\\.)*)"', re.S)
SHIELD_FIELD = re.compile(r'(\w+):\s*"((?:[^"\\]|\\.)*)"')
SHIELD_TARGET_FIELD = {"en": "English", "ro": "Romanian"}
SKIP_DIRS = {"ManifestingTests", "DerivedData", "build", "Pods"}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--catalog", required=True, help="path to Localizable.xcstrings")
    p.add_argument("--locale", required=True, help="target locale code, e.g. ro")
    sel = p.add_mutually_exclusive_group()
    sel.add_argument("--keys", help="comma-separated keys to check")
    sel.add_argument("--keys-file", help="file with one key per line, a JSON list, or {\"keys\": [...]}")
    sel.add_argument("--prefix", help="check keys starting with this prefix (shield.<id>.* with --shield)")
    p.add_argument("--glossary", help="glossary/<locale>.json for C6 forbidden forms and C10 control rows")
    p.add_argument("--shield", help="ShieldMessageCatalog.swift; pairs join as shield.<id>.title and .body")
    p.add_argument("--app-root", help="checkout root for the C11 source scan; derived only when --catalog sits inside a checkout")
    p.add_argument("--length-trigger", type=float, default=1.35, help="C5 ratio from the locale brief (default 1.35)")
    p.add_argument("--out", required=True, help="findings JSON path")
    return p.parse_args()


def read_keys_file(path):
    text = open(path, encoding="utf-8").read()
    try:
        data = json.loads(text)
        return list(data["keys"] if isinstance(data, dict) else data)
    except ValueError:
        return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]


def units(entry, lang):
    """Map variation name ('' for the flat unit, 'plural:one'...) to its stringUnit."""
    loc = entry.get("localizations", {}).get(lang)
    if not loc:
        return {}
    out = {}
    if "stringUnit" in loc:
        out[""] = loc["stringUnit"]
    for kind, forms in loc.get("variations", {}).items():
        for cat, unit in forms.items():
            out[f"{kind}:{cat}"] = unit.get("stringUnit", {})
    subs = loc.get("substitutions")
    if subs:
        # A %#@name@ substitution passes argument argNum with its formatSpecifier, so compare it as that token.
        def expand(m):
            sub = subs.get(m.group(1), {})
            return "%%%s$%s" % (sub["argNum"], sub.get("formatSpecifier", "@")) if "argNum" in sub else m.group(0)
        out = {k: {**u, "value": re.sub(r"%#@(\w+)@", expand, u.get("value", ""))} for k, u in out.items()}
    return out


def unescape_swift(s):
    return s.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def shield_entries(path):
    """Shield copy lives in Swift, not the catalog; expose each pair as two flat pseudo-keys."""
    text = open(path, encoding="utf-8").read()
    entries = {}
    for mid, style, t_en, t_ro, b_en, b_ro in SHIELD_INIT.findall(text):
        for part, en, ro in (("title", t_en, t_ro), ("body", b_en, b_ro)):
            entries[f"shield.{mid}.{part}"] = {
                "comment": f"Shield {style} {part} (ShieldMessageCatalog.swift, id {mid})",
                "extractionState": "manual", "shield": True, "style": style,
                "localizations": {"en": {"stringUnit": {"state": "translated", "value": unescape_swift(en)}},
                                  "ro": {"stringUnit": {"state": "translated", "value": unescape_swift(ro)}}}}
    return entries


def shield_fields(text):
    """Every string field of each .init( block with escapes dropped, the parse worklist.py and term_audit.py share."""
    for block in text.split(".init(")[1:]:
        yield {name: re.sub(r"\\(.)", r"\1", value) for name, value in SHIELD_FIELD.findall(block)}


def tokens(value):
    """Placeholder list as (position, type class); '%%' and a bare '%' both count as a literal percent."""
    out, n = [], 0
    for m in SPEC.finditer(value):
        if m.group(2) == "%":
            out.append(("%", "%"))
            continue
        n += 1
        out.append((int(m.group(1)[:-1]) if m.group(1) else n, TYPE_CLASS[m.group(2)]))
    stripped = SPEC.sub("", value)
    out.extend(("%", "%") for _ in stripped.split("%")[1:])
    return out


def source_unit(en_units, variation):
    return en_units.get(variation) or en_units.get("plural:other") or en_units.get("")


def check_placeholders(key, en_units, tg_units):
    for var, unit in tg_units.items():
        src = source_unit(en_units, var)
        if not src:
            continue
        yield from compare_tokens(key, var, tokens(src.get("value", "")), tokens(unit.get("value", "")))


def compare_tokens(key, var, src, tgt):
    """Compare type multisets first, then position bindings, so one swapped pair is one finding."""
    missing, extra = type_counts(src) - type_counts(tgt), type_counts(tgt) - type_counts(src)
    category = var.split(":")[-1]
    for typ in missing:
        accepted = typ == "d" and category in ("zero", "one")
        yield finding("C1", "info" if accepted else "critical", key, var,
                      f"placeholder {typ} from the source is absent in the target"
                      + (f"; accepted in the '{category}' form where the count is spelled out" if accepted
                         else "; the user loses the number, unit or name the sentence is about"))
    for typ in extra:
        yield finding("C1", "critical", key, var, f"target adds placeholder {typ} the source does not pass; it prints garbage or crashes")
    if missing or extra or src == tgt:
        return
    if Counter(src) != Counter(tgt):
        yield finding("C1", "critical", key, var, "placeholders bind to the wrong argument types; number them (%1$@, %2$lld) to reorder")
    else:
        yield finding("C1", "info", key, var, "placeholder order differs from the source; fine because the tokens are numbered")


def type_counts(tokens_list):
    return Counter(t for _, t in tokens_list)


def check_plurals(key, locale, en_units, tg_units):
    en_cats = {v.split(":")[1] for v in en_units if v.startswith("plural:")}
    tg_cats = {v.split(":")[1] for v in tg_units if v.startswith("plural:")}
    if en_cats and not tg_cats and tg_units:
        yield finding("C2", "major", key, "", "source is plural but the target is a flat string; add the locale's plural forms")
        return
    if not tg_cats:
        return
    required = PLURAL_REQUIRED.get(locale, {"one", "other"})
    for cat in sorted(required - tg_cats):
        yield finding("C2", "major", key, f"plural:{cat}", f"missing plural form '{cat}' required for {locale}")
    for cat in sorted(tg_cats - required):
        yield finding("C2", "info", key, f"plural:{cat}", f"extra plural form '{cat}' that {locale} never selects")


def markup_counts(text):
    return {"**bold** markers": text.count("**"), "newlines": text.count("\n"), "links": len(LINK.findall(text))}


def check_markup(key, en_units, tg_units):
    for var, unit in tg_units.items():
        src = source_unit(en_units, var)
        if not src:
            continue
        s, t = src.get("value", ""), unit.get("value", "")
        for (label, in_source), in_target in zip(markup_counts(s).items(), markup_counts(t).values()):
            if in_source != in_target:
                yield finding("C3", "major", key, var, f"{label}: source has {in_source}, target has {in_target}; layout and emphasis depend on them")
        if ("…" in s) != ("…" in t) or ("..." in s) != ("..." in t):
            yield finding("C3", "info", key, var, "ellipsis form differs from the source ('…' vs '...')")
        if "  " in t:
            yield finding("C3", "info", key, var, "double space in the target")
        if (s != s.strip()) != (t != t.strip()):
            yield finding("C3", "info", key, var, "leading or trailing whitespace differs from the source")
        if len(EMOJI.findall(s)) != len(EMOJI.findall(t)):
            yield finding("C3", "info", key, var, "emoji count differs from the source; the brief keeps emoji as shipped")


def check_cedilla(key, tg_units):
    for var, unit in tg_units.items():
        if CEDILLA.search(unit.get("value", "")):
            yield finding("C4", "major", key, var, "cedilla ş/ţ instead of comma-below ș/ț")


def names_control(phrase):
    """True when the head noun of the phrase's first clause is a control: 'Generic Close button used across the app'
    and 'button that restores a subscription' qualify, 'instruction for changing an app icon into a widget' does not."""
    head = QUALIFIER.sub("", re.split(r"[;.,]", phrase, maxsplit=1)[0]).strip()
    return CONTROL_NOUN.search(head) is not None or FIT_HINT.search(phrase) is not None


def single_line_class(key, entry):
    """Comments follow 'Screen > element: purpose'; either side may name the control ('Paywall: button that restores...')."""
    tail = key.rsplit(".", 1)[-1]
    if BODY_TAIL.search(tail):
        return False
    element, _, purpose = entry.get("comment", "").partition(":")
    return (key.startswith(("widgets.", "shield.")) or SINGLE_LINE_TAIL.search(tail) is not None
            or names_control(element) or names_control(purpose))


def length_ratio(en_units, tg_units):
    ratios = []
    for var, unit in tg_units.items():
        src = source_unit(en_units, var)
        if src and src.get("value"):
            ratios.append(len(unit.get("value", "")) / len(src["value"]))
    return max(ratios) if ratios else 0.0


def check_glossary(key, tg_units, glossary):
    for name, term in glossary.get("terms", {}).items():
        for form in term.get("forbidden", []):
            pattern = re.compile(r"(?<!\w)" + re.escape(form) + r"(?!\w)", re.I)
            for var, unit in tg_units.items():
                if pattern.search(unit.get("value", "")):
                    yield finding("C6", "major", key, var,
                                  f"forbidden form '{form}' for '{name}'; glossary prefers '{term.get('preferred', '')}'")


def check_target_state(key, tg_units):
    if not tg_units:
        yield finding("C7", "major", key, "", "no target unit; the user sees English")
        return
    for var, unit in tg_units.items():
        state = unit.get("state")
        if state != "translated":
            yield finding("C7", "major", key, var, f"target state '{state}'; awaiting owner acceptance or a value")


def identical_by_design(value):
    words = re.findall(r"[^\W\d_]+", SPEC.sub("", value).lower())
    stripped = value.strip().lower().lstrip("-– ")
    return not words or stripped in IDENTICAL_BY_DESIGN or all(w in UNIT_WORDS for w in words)


def check_identity(key, en_units, tg_units):
    for var, unit in tg_units.items():
        src = source_unit(en_units, var)
        if src and src.get("value") == unit.get("value") and not identical_by_design(unit.get("value", "")):
            yield finding("C8", "info", key, var, "target equals the English source; confirm it is a fixed name or a real cognate")


def is_stub_comment(key, comment):
    tail = comment.rsplit(":", 1)[-1].strip().lower().replace(" ", "")
    return tail == key.rsplit(".", 1)[-1].lower()


def check_comment(key, entry):
    comment = entry.get("comment", "")
    if not comment:
        yield finding("C9", "info", key, "", "no comment; translators lack the screen, element and purpose")
    elif is_stub_comment(key, comment):
        yield finding("C9", "info", key, "", f"stub comment '{comment}' restates the key; write 'Screen > element: purpose'")


def normalise(value):
    return re.sub(r"\s+", " ", value.strip()).lower()


def control_row(glossary, en_value):
    for name, row in glossary.get("controls", {}).items():
        if name.lower() == en_value.lower():
            return name, row
    return None, None


def check_divergence(strings, selected, locale, glossary):
    groups = defaultdict(dict)
    for key, entry in strings.items():
        en_units = units(entry, "en")
        en, tg = en_units.get(""), units(entry, locale).get("")
        if en and tg and tg.get("value") and "consistency: role-different" not in entry.get("comment", ""):
            groups[(normalise(en.get("value", "")), tuple(sorted(en_units)))][key] = tg["value"].strip()
    for (en_norm, _), members in sorted(groups.items()):
        if len({normalise(v) for v in members.values()}) < 2 or not selected & set(members):
            continue
        yield from divergence_findings(en_norm, members, glossary)


def divergence_findings(en_norm, members, glossary):
    name, row = control_row(glossary, en_norm)
    if row:
        allowed = {row["preferred"], *row.get("roles", {}).values()}
        for key, value in sorted(members.items()):
            if value not in allowed:
                yield finding("C10", "major", key, "", f"'{value}' contradicts the glossary control row for {name} ({', '.join(sorted(allowed))})")
    else:
        listing = "; ".join(f"{k} -> '{v}'" for k, v in sorted(members.items()))
        first = sorted(members)[0]
        yield finding("C10", "needs_disposition", first, "",
                      f"same English '{en_norm}' has {len(set(members.values()))} targets: {listing}. "
                      "Pick one form, or mark a key's comment 'consistency: role-different - <reason>'")


def tier_for(key, entry, en_units):
    if any(v.startswith("plural:") for v in en_units) or ".a11y." in key or "accessibility" in key.lower():
        return "A"
    if key.startswith(RISK_PREFIXES) or RISK_PATTERN.match(key):
        return "A"
    en = en_units.get("", {}).get("value", "") or " ".join(u.get("value", "") for u in en_units.values())
    if CLAIM_WORDS.search(en):
        return "A"
    return "C" if en.strip() and " " not in en.strip() else "B"


def prefix_of(key):
    return ".".join(key.split(".")[:2]) if NAMED_KEY.match(key) else "<literal>"


def finding(check, severity, key, variation, message):
    return {"check": check, "severity": severity, "key": key, "variation": variation, "message": message}


# --- C11: origin and reachability of literal keys -----------------------------

def is_checkout(path):
    return (os.path.isdir(os.path.join(path, "Manifesting.xcodeproj"))
            and os.path.isdir(os.path.join(path, "Manifesting", "Foundation", "Localization")))


def git_toplevel(path):
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=path, capture_output=True, text=True, check=True)
        return os.path.realpath(out.stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        return None


def find_app_root(catalog, explicit):
    """Climb from the catalog no further than its git toplevel and accept only a real checkout,
    so a fixture in another repo never triggers a source walk of some unrelated folder."""
    if explicit:
        return explicit
    here = os.path.realpath(os.path.dirname(os.path.abspath(catalog)))
    top = git_toplevel(here)
    while True:
        if is_checkout(here):
            return here
        parent = os.path.dirname(here)
        if here == top or parent == here:
            return None
        here = parent


def swift_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(".swift"):
                yield os.path.join(dirpath, name)


class SwiftSource:
    """Per-line context: inside #if DEBUG, inside #Preview, and the nearest enclosing type name."""

    def __init__(self, path, root):
        self.path, self.rel = path, os.path.relpath(path, root)
        self.text = open(path, encoding="utf-8", errors="replace").read()
        self.lines = self.text.split("\n")
        self.debug, self.preview, self.owner = [], [], []
        self._scan()

    def _scan(self):
        depth_if, preview_depth, owner = 0, None, ""
        for line in self.lines:
            s = line.strip()
            if s.startswith("#if"):
                # nested #if inside a DEBUG block must be counted so its #endif does not close the DEBUG one
                depth_if += 1 if "DEBUG" in s or depth_if else 0
            m = re.match(r"(?:private |fileprivate |public |internal |final )*(struct|class|enum|extension|actor)\s+(\w+)", s)
            if m:
                owner = m.group(2)
            if s.startswith("#Preview"):
                preview_depth = 0
            self.debug.append(depth_if > 0)
            self.preview.append(preview_depth is not None)
            self.owner.append(owner)
            if preview_depth is not None:
                preview_depth += line.count("{") - line.count("}")
                if preview_depth <= 0:
                    preview_depth = None
            if s.startswith("#endif") and depth_if:
                depth_if -= 1

    def site_class(self, lineno, line):
        if re.search(r"defaultValue:\s*\"", line) or "verbatim:" in line or line.strip().startswith("//"):
            return None
        m = re.search(r'text\("([^"]+)",', line)
        if m and self.path.endswith("PlanWidgetCopy.swift"):
            return "shadow:" + m.group(1)
        if "@Parameter(title:" in line:
            return "intent"
        name = os.path.basename(self.path)
        if self.debug[lineno] or "DebugGallery" in name or "DebugGallery" in self.owner[lineno]:
            return "debugOnly"
        if self.preview[lineno] or "/PreviewSupport/" in self.path or "Preview" in self.owner[lineno] or "Preview" in name:
            return "previewOnly"
        return "reachable"


def literal_pattern(key):
    """Match the literal as written, or as the Swift interpolation the extractor turned into %lld."""
    pieces, last = [], 0
    for m in SPEC.finditer(key):
        pieces.append(re.escape(key[last:m.start()]))
        pieces.append("%" if m.group(2) == "%" else r"\\\(.*?\)")
        last = m.end()
    pieces.append(re.escape(key[last:]))
    return re.compile(r'"' + "".join(pieces) + r'"|"' + re.escape(key) + r'"')


def classify_literal(key, sources):
    """Return (class or None, sites) for a literal key by reading every call site."""
    if not LETTER.search(SPEC.sub("", key)):
        return "format", []
    pattern, sites = literal_pattern(key), []
    for src in sources:
        if not pattern.search(src.text):
            continue
        for i, line in enumerate(src.lines):
            if pattern.search(line):
                cls = src.site_class(i, line)
                if cls:
                    sites.append((cls, f"{src.rel}:{i + 1}"))
    classes = {c for c, _ in sites}
    unreachable = {c for c in classes if c.startswith("shadow:") or c in ("debugOnly", "previewOnly")}
    if not sites or classes != unreachable:
        return None, sites
    if any(c.startswith("shadow:") for c in classes):
        return "shadow", sites
    return "debugOnly" if "debugOnly" in classes else "previewOnly", sites


def literal_disposition(key, sites):
    where = ", ".join(f"{c} at {loc}" for c, loc in sites)
    if not sites:
        return finding("C11", "needs_disposition", key, "", "literal key with no call site in the app sources; stale key or interpolated literal, decide whether it ships")
    if {c for c, _ in sites} <= {"intent"}:
        return finding("C11", "needs_disposition", key, "", f"App Intent parameter title, hidden while isDiscoverable is false ({where}); name it as a key or confirm it never shows")
    return finding("C11", "needs_disposition", key, "", f"literal key reachable in release code ({where}); name it under <feature>.<screen>.<element> before translating")


def classify_origins(strings, app_root):
    literal_keys = [k for k in strings if not NAMED_KEY.match(k)]
    sources = [SwiftSource(p, app_root) for p in swift_files(app_root)] if app_root else []
    exclusions, findings = {}, []
    for key in literal_keys:
        cls, sites = classify_literal(key, sources)
        if cls:
            exclusions[key] = cls
        elif not sources:
            findings.append(finding("C11", "needs_disposition", key, "", "literal key; pass --app-root to classify it from its call sites"))
        else:
            findings.append(literal_disposition(key, sites))
    return exclusions, findings


# --- driver -------------------------------------------------------------------

def expand_shield_ids(wanted, strings):
    """worklist.py names a shield pair by one id (shield.<id>) because the pair is reviewed together; check both halves."""
    out = []
    for key in wanted:
        if key not in strings and all(strings.get(key + part, {}).get("shield") for part in (".title", ".body")):
            out.extend((key + ".title", key + ".body"))
        else:
            out.append(key)
    return out


def select_keys(strings, args):
    if args.keys:
        return expand_shield_ids([k.strip() for k in args.keys.split(",") if k.strip()], strings)
    if args.keys_file:
        return expand_shield_ids(read_keys_file(args.keys_file), strings)
    if args.prefix:
        return [k for k in strings if k.startswith(args.prefix)]
    return list(strings)


def run_checks(key, entry, locale, glossary, trigger, render_list):
    en, tg = units(entry, "en"), units(entry, locale)
    findings = list(check_placeholders(key, en, tg)) + list(check_plurals(key, locale, en, tg))
    findings += list(check_markup(key, en, tg)) + list(check_identity(key, en, tg))
    if locale == "ro":
        findings += list(check_cedilla(key, tg))
    if glossary:
        findings += list(check_glossary(key, tg, glossary))
    findings += list(check_target_state(key, tg))
    if not entry.get("shield"):
        findings += list(check_comment(key, entry))
    if single_line_class(key, entry) and length_ratio(en, tg) > trigger:
        render_list.append(key)
    return findings


def main():
    args = parse_args()
    catalog = json.load(open(args.catalog, encoding="utf-8"))
    strings = dict(catalog["strings"])
    if args.shield:
        strings.update(shield_entries(args.shield))
    glossary = json.load(open(args.glossary, encoding="utf-8")) if args.glossary else {}
    wanted = select_keys(strings, args)
    selected = [k for k in wanted if k in strings]
    chosen, missing = set(selected), sorted(set(wanted) - set(strings))
    exclusions, findings = classify_origins(strings, find_app_root(args.catalog, args.app_root))
    exclusions = {k: v for k, v in exclusions.items() if k in chosen}
    findings = [f for f in findings if f["key"] in chosen]
    tiers, render_list = {}, []
    for key in selected:
        entry = strings[key]
        if key in exclusions or not NAMED_KEY.match(key):
            continue
        tiers[key] = tier_for(key, entry, units(entry, "en"))
        findings += run_checks(key, entry, args.locale, glossary, args.length_trigger, render_list)
    findings += list(check_divergence(strings, set(tiers), args.locale, glossary))
    findings += [finding("C7", "major", k, "", "key not in the catalog") for k in missing]
    write_output(args, findings, tiers, exclusions, render_list, selected)
    return 1 if any(f["severity"] == "critical" for f in findings) else 0


def write_output(args, findings, tiers, exclusions, render_list, selected):
    order = {"critical": 0, "major": 1, "needs_disposition": 2, "info": 3}
    findings.sort(key=lambda f: (order[f["severity"]], f["check"], f["key"], f["variation"]))
    severities = Counter(f["severity"] for f in findings)
    out = {"catalog": args.catalog, "locale": args.locale, "findings": findings, "tiers": tiers,
           "exclusions": exclusions, "render_list": sorted(render_list),
           "prefix_counts": dict(sorted(Counter(prefix_of(k) for k in selected).items())),
           "summary": {"keys": len(selected), "translatable": len(tiers), "excluded": len(exclusions),
                       "tiers": dict(Counter(tiers.values())), "severities": dict(severities),
                       "checks": dict(sorted(Counter(f["check"] for f in findings).items()))}}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"{args.locale}: {len(selected)} keys, {len(tiers)} translatable, {len(exclusions)} excluded, "
           f"tiers {dict(Counter(tiers.values()))}, render list {len(render_list)}")
    print("findings: " + ", ".join(f"{k} {severities.get(k, 0)}" for k in order))
    for f in findings:
        if f["severity"] == "critical":
            print(f"  critical {f['check']} {f['key']} {f['variation']}: {f['message']}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    sys.exit(main())
