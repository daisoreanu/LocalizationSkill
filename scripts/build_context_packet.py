#!/usr/bin/env python3
"""Build the coordinator packet and the blind packet for one batch, then run the leak check that guards them.

The coordinator packet (coordinator/source.json) carries everything the forward translator and the
coordinator need: English, comment, screen and state, control, tier, invariants, neighbours, same-source
siblings and layout constraints. The blind packet (blind/target.rev<N>.json) carries only what a
target-language editor or back-translator may see: opaque ids, target text, neutral roles, token samples,
target-only neighbours and siblings, the target-side term list, markers and the rating scale. Keys and
English never enter it; the leak check proves that per run and exits 1 when it fails, which blocks
dispatch of roles B and C. Order follows the selection: worklist batch order, else --keys order, else
catalog order; the flow is the unit of review, not the line. Shield pairs from ShieldMessageCatalog.swift
join as shield.<id>.title and shield.<id>.body, the names worklist.py, catalog_check.py and
scan_layout_constraints.py use, so a shield batch and the pilot batch build like any other. Tiers,
shield parsing and the keys-file format come from catalog_check.py so one rule set serves both scripts.
"""

import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalog_check import RISK_PATTERN, read_keys_file, shield_entries, tier_for as check_tier, units as check_units  # noqa: E402

# Read-only git calls must not refresh the checkout's index.
os.environ.setdefault("GIT_OPTIONAL_LOCKS", "0")

PLACEHOLDER_RE = re.compile(r"%(\d+\$)?(%|@|l{0,2}[dui]|\.?\d*f|s)")
NEGATION_RE = re.compile(r"\b(not|never|no|nothing|none|without|cannot|can't|won't|don't|doesn't|isn't|aren't|"
                         r"didn't)\b", re.I)
MONEY_RE = re.compile(r"\b(price|priced|billed|billing|trial|subscription|subscribe|purchase|refund|charge|charged|"
                      r"free|earn|earned|earnings|money|paid|pay|restore|per (week|month|year))\b|[$€£]", re.I)
PERMISSION_RE = re.compile(r"\b(allow|permission|access|delete|deleted|remove|erase|reset|privacy|private|"
                           r"on your (phone|device))\b", re.I)
UNIT_RE = re.compile(r"\b(minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?|seconds?|mo|wk|yr)\b|%", re.I)
STRENGTH_RE = re.compile(r"\b(always|never|guaranteed|guarantee|every|all|forever|lowest|only|best|most|least|"
                         r"more|less|cheaper|faster|instantly|unlimited|100%)\b", re.I)
CONDITION_RE = re.compile(r"\b(if|when|whenever|until|unless|after|before|once|while|as soon as)\b", re.I)
BRANDS = ("Moneyfesting", "Apple", "iOS", "iPhone", "Screen Time", "Face ID", "Touch ID", "Apple Health", "Health",
          "Wellbeing", "Siri", "Shortcuts", "StandBy", "HealthKit", "Safari", "App Store", "Family Sharing",
          "Focus", "Dynamic Type", "VoiceOver")
PACKET_VOCABULARY = ("hero headline", "button", "title", "subtitle", "caption", "badge", "body", "label", "footer", "description",
                     "placeholder", "toggle", "tab", "alert title", "alert body", "menu item", "widget name",
                     "widget description", "voiceover label", "text", "hint", "value", "pass", "revise", "block",
                     "identical by design", "fixed name", "uppercase by design", "attributed", "user content", "plural",
                     "no target yet", "unverified", "constraints", "rendered")
TEXT_FIELD_RE = re.compile(r"\.text$|\.plural\.|sibling_text$|term_list[.\[]")
AVOID_FIELD_RE = re.compile(r"term_list\.avoid\b")
SCREEN_ROLES = [
    ("widgets.", "home widget, small and medium sizes"), ("paywall.", "subscription offer"),
    ("onboarding.", "first-run setup flow"), ("screenTimeReport.", "usage report"), ("screenTime.", "app limits"),
    ("focusTask.", "tasks and focus timer"), ("insights.", "statistics"), ("achievements.", "progress and rewards"),
    ("streakFreeze.", "progress and rewards"), ("profile.", "settings and profile"), ("quotes.", "daily quotes"),
    ("quote.", "daily quotes"), ("share.", "share card"), ("plan.", "daily plan"), ("moneyfesting.", "timed session"),
    ("notifications.", "notifications"), ("theme", "appearance"), ("currency.", "currency picker"),
    ("shield.", "app shield"), ("companion.", "app shield"), ("common.", "shared controls"), ("component.", "shared controls"),
    ("main.", "main navigation"), ("user.", "account"),
]
# Formatting samples per locale, rendered on 2026-09-16 with the app's own AppCurrency.format
# and Foundation styles; the '*' row fills whatever a locale row leaves out (see references/
# research-provenance.md '## Locale research'). Language words come from the glossary at runtime.
SAMPLES = {
    "ro": {"money": ["120 RON", "1.250,5 RON"], "percent": ["40 %", "100 %"], "date": ["12 mai", "31 decembrie 2026"], "time": ["9:41", "23:59"], "duration": ["25 min.", "1 oră, 45 min."]},
    "da": {"money": ["120 DKK", "1.250,5 DKK"], "percent": ["40 %", "100 %"], "date": ["12. maj", "31. december 2026"], "time": ["9.41", "23.59"], "duration": ["25 min.", "1 t. og 45 min."]},
    "sv": {"money": ["120 SEK", "1 250,5 SEK"], "percent": ["40 %", "100 %"], "date": ["12 maj", "31 december 2026"], "time": ["9:41", "23:59"], "duration": ["25 min", "1 tim, 45 min"]},
    "nb": {"money": ["120 NOK", "1 250,5 NOK"], "percent": ["40 %", "100 %"], "date": ["12. mai", "31. desember 2026"], "time": ["9:41", "23:59"], "duration": ["25 min", "1 t, 45 min"]},
    "fi": {"money": ["120 €", "1 250,5 €"], "percent": ["40 %", "100 %"], "date": ["12. toukokuuta", "31. joulukuuta 2026"], "time": ["9.41", "23.59"], "duration": ["25 min", "1 t 45 min"]},
    "is": {"money": ["120 ISK", "1.250 ISK"], "percent": ["40%", "100%"], "date": ["12. maí", "31. desember 2026"], "time": ["9:41", "23:59"], "duration": ["25 mín.", "1 klst. og 45 mín."]},
    "pl": {"money": ["120 PLN", "1250,5 PLN"], "percent": ["40%", "100%"], "date": ["12 maja", "31 grudnia 2026"], "time": ["9:41", "23:59"], "duration": ["25 min", "1 godz. i 45 min"]},
    "hu": {"money": ["120 HUF", "1250,5 HUF"], "percent": ["40%", "100%"], "date": ["május 12.", "2026. december 31."], "time": ["9:41", "23:59"], "duration": ["25 p", "1 ó és 45 p"]},
    "he": {"money": ["‏120 ‏ILS", "‏1,250.5 ‏ILS"], "percent": ["40%", "100%"], "date": ["12 במאי", "31 בדצמבר 2026"], "time": ["9:41", "23:59"], "duration": ["25 דק׳", "1 שעה ו45 דק׳"]},
    "tr": {"money": ["TRY 120", "TRY 1.250,5"], "percent": ["%40", "%100"], "date": ["12 Mayıs", "31 Aralık 2026"], "time": ["9:41", "23:59"], "duration": ["25 dk.", "1 sa. 45 dk."]},
    "el": {"money": ["120 €", "1.250,5 €"], "percent": ["40%", "100%"], "date": ["12 Μαΐου", "31 Δεκεμβρίου 2026"], "time": ["9:41 πμ", "11:59 μμ"], "duration": ["25 λ.", "1 ώ., 45 λ."]},
    "cs": {"money": ["120 CZK", "1 250,5 CZK"], "percent": ["40 %", "100 %"], "date": ["12. května", "31. prosince 2026"], "time": ["9:41", "23:59"], "duration": ["25 min", "1 h, 45 min"]},
    "nl": {"money": ["€ 120", "€ 1.250,5"], "percent": ["40%", "100%"], "date": ["12 mei", "31 december 2026"], "time": ["9:41", "23:59"], "duration": ["25 min", "1 uur, 45 min"]},
    "sk": {"money": ["120 €", "1 250,5 €"], "percent": ["40 %", "100 %"], "date": ["12. mája", "31. decembra 2026"], "time": ["9:41", "23:59"], "duration": ["25 min", "1 h 45 min"]},
    "bg": {"money": ["120 €", "1250,5 €"], "percent": ["40%", "100%"], "date": ["12 май", "31 декември 2026 г."], "time": ["9:41", "23:59"], "duration": ["25 мин", "1 ч и 45 мин"]},
    "pt-BR": {"money": ["BRL 120", "BRL 1.250,5"], "percent": ["40%", "100%"], "date": ["12 de maio", "31 de dezembro de 2026"], "time": ["9:41", "23:59"], "duration": ["25 min", "1 h e 45 min"]},
    "pt-PT": {"money": ["120 €", "1250,5 €"], "percent": ["40%", "100%"], "date": ["12 de maio", "31 de dezembro de 2026"], "time": ["9:41", "23:59"], "duration": ["25 min", "1 h e 45 min"]},
    "es-ES": {"money": ["120 €", "1250,5 €"], "percent": ["40 %", "100 %"], "date": ["12 de mayo", "31 de diciembre de 2026"], "time": ["9:41", "23:59"], "duration": ["25 min", "1 h y 45 min"]},
    "es-MX": {"money": ["MXN 120", "MXN 1,250.5"], "percent": ["40%", "100%"], "date": ["12 de mayo", "31 de diciembre de 2026"], "time": ["9:41 a.m.", "11:59 p.m."], "duration": ["25 min", "1 h y 45 min"]},
    "de": {"money": ["120 €", "1.250,5 €"], "percent": ["40 %", "100 %"], "date": ["12. Mai", "31. Dezember 2026"], "time": ["9:41", "23:59"], "duration": ["25 Min.", "1 Std., 45 Min."]},
    "it": {"money": ["120 €", "1250,5 €"], "percent": ["40%", "100%"], "date": ["12 maggio", "31 dicembre 2026"], "time": ["9:41", "23:59"], "duration": ["25 min", "1 h e 45 min"]},
    "fr": {"money": ["120 €", "1 250,5 €"], "percent": ["40 %", "100 %"], "date": ["12 mai", "31 décembre 2026"], "time": ["9:41", "23:59"], "duration": ["25 min", "1 h et 45 min"]},
    "ja": {"money": ["￥120", "￥1,250"], "percent": ["40%", "100%"], "date": ["5月12日", "2026年12月31日"], "time": ["9:41", "23:59"], "duration": ["25分", "1時間 45分"]},
    "ko": {"money": ["KRW 120", "KRW 1,250"], "percent": ["40%", "100%"], "date": ["5월 12일", "2026년 12월 31일"], "time": ["오전 9:41", "오후 11:59"], "duration": ["25분", "1시간 45분"]},
    "en": {"money": ["$120", "$1,250.5"], "percent": ["40%", "100%"], "date": ["May 12", "December 31, 2026"], "time": ["9:41 AM", "11:59 PM"], "duration": ["25 min", "1 hr, 45 min"]},
    "*": {"noun": ["sample"], "name": ["Ana", "Alexandra-Maria"], "money": ["120", "1,250.50"], "percent": ["40%", "100%"],
          "date": ["12/05", "31/12/2026"], "time": ["9:41", "23:59"], "duration": ["25 min", "1 h 45 min"],
          "app": ["Safari", "Instagram"], "number": ["3", "21"], "text": ["sample", "a somewhat longer sample"]},
}
COUNT_SAMPLES = {"minutes": [1, 25, 90], "hours": [1, 2, 21], "days": [1, 3, 21], "weeks": [1, 2, 21],
                 "months": [1, 3, 12], "years": [1, 2, 21], "seconds": [1, 30, 45], "percent": [5, 40, 100],
                 "count": [1, 3, 21]}
PER_DAY_SAMPLES = {"ro": ["3h pe zi", "12h pe zi"], "en": ["3h a day", "12h a day"]}
UNIT_KINDS = (("minutes", r"min"), ("hours", r"h(ou)?rs?\b|\bh\b"), ("days", r"day"), ("weeks", r"w(ee)?k"),
              ("months", r"mo(nth)?"), ("years", r"y(ea)?r"), ("seconds", r"sec"), ("percent", r"%|percent"))
AT_KINDS = (("money", ("amount", "price", "currency", "money", "wage", "cost", "earn", "value")),
            ("percent", ("percent", "percentage", "%")), ("date", ("date", "weekday", "day of")),
            ("time", ("time of day", "clock", "o'clock", "e.g. 9")),
            ("duration", ("duration", "elapsed", "minutes", "hours")),
            ("app", ("app name", "app's name", "website", "domain", "application")),
            ("name", ("user's name", "first name", "user name", "their name", "the name")),
            ("number", ("number", "count", "streak", "figure", "total")))
SCALE = {
    "naturalness": {"1": "reads as translated", "2": "understandable, foreign sentence shape",
                    "3": "acceptable, a local team would still rephrase", "4": "natural", "5": "reads as written locally"},
    "verdict": ["pass", "revise", "block"],
    "hero_rank": "rank the ids listed under hero from strongest to weakest for a local reader",
}
CONTEXT_LIMIT = 24


def die(msg):
    sys.exit("build_context_packet: " + msg)


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def git(args, cwd):
    try:
        return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def repo_root(path):
    d = os.path.dirname(os.path.abspath(path))
    while d and d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        d = os.path.dirname(d)
    return None


def guard_out_dir(out_dir, catalog):
    """Only the gitignored run-state root may be written inside the app checkout."""
    root = repo_root(catalog) if catalog else None
    out = os.path.abspath(out_dir)
    if root and out.startswith(root + os.sep) and not out.startswith(os.path.join(root, ".codex-tmp") + os.sep):
        die("refusing to write inside the app checkout outside .codex-tmp/: " + out)


def unit(entry, locale):
    """(text, plural dict, state) of one localization; state is the weakest state across plural forms."""
    loc = entry.get("localizations", {}).get(locale)
    if not loc:
        return None, None, None
    su = loc.get("stringUnit")
    if su:
        return su.get("value"), None, su.get("state")
    plural = loc.get("variations", {}).get("plural")
    if plural:
        forms = {cat: v["stringUnit"]["value"] for cat, v in plural.items()}
        states = [v["stringUnit"].get("state") for v in plural.values()]
        state = "needs_review" if "needs_review" in states else ("new" if "new" in states else states[0])
        return None, forms, state
    return None, None, None


def en_text(key, entry):
    text, plural, _ = unit(entry, "en")
    if plural:
        return plural.get("other") or next(iter(plural.values()))
    return text if text is not None else key


def count_kind(en, token, comment):
    """Unit right after the token in the English wins over comment words: `%lld days`, `%lld%%`, `/%lld MIN`."""
    after = en[en.find(token) + len(token):][:12].lower()
    for kind, rx in UNIT_KINDS:
        if re.match(r"\s*(" + rx + ")", after):
            return kind
    for kind, rx in UNIT_KINDS:
        if re.search(rx, comment):
            return kind
    return "count"


def placeholders(en, comment, locale, glossary=None):
    # A blind packet carries target text only, so fall back key by key and take the
    # language's own words from its glossary rather than the English placeholders.
    table = {**SAMPLES["*"], **SAMPLES.get(locale, {})}
    terms = [t.get("preferred") for t in (glossary or {}).get("terms", {}).values() if t.get("preferred")]
    if terms:
        table["noun"] = terms[:1]
        table["text"] = terms[:2]
    # Tokens in the comment ("%@ is ...") must not read as the percent keyword.
    cm = PLACEHOLDER_RE.sub(" ", (comment or "").lower())
    out, seen = [], set()
    for m in PLACEHOLDER_RE.finditer(en):
        token, spec = m.group(0), m.group(2)
        if token in seen:
            continue
        seen.add(token)
        if spec == "%":
            kind, samples = "literal-percent", ["%"]
        elif spec.endswith("f"):
            kind, samples = "decimal", [2.5, 12.75]
        else:
            kind = next((k for k, words in AT_KINDS if any(w in cm for w in words)), "noun")
            counted = kind in ("noun", "number") and re.search(r"\bnumber of\b|\bcount of\b", cm)
            if spec.endswith(("d", "u", "i")) or counted:
                kind = count_kind(en, token, cm)
                samples = COUNT_SAMPLES[kind]
            elif kind == "duration" and re.search(r"\ba day\b|\bper day\b|\bdaily\b", cm):
                kind, samples = "duration-per-day", PER_DAY_SAMPLES.get(locale, table["duration"])
            else:
                samples = table.get(kind, table["noun"])
        out.append({"token": token, "type": kind, "samples": samples})
    return out


def blind_tokens(ph):
    """One neutral sample per token; a second numeric token gets a different typical value so `%1 of %2` reads."""
    out, numeric = [], 0
    for p in ph:
        s = p["samples"]
        if isinstance(s[0], (int, float)) and len(s) > 1:
            numeric += 1
            out.append({"token": p["token"], "sample": s[min(numeric, len(s) - 1)]})
        else:
            out.append({"token": p["token"], "sample": s[0]})
    return out


def control_for(key, comment):
    tail = key.split(".")[-1].lower()
    cm = (comment or "").lower()
    head = re.split(r"[.;]\s", cm)[0]
    if ".a11y." in key or "voiceover" in cm or "accessibility" in cm:
        return "voiceover label"
    if tail == "displayname":
        return "widget name"
    if key.startswith("widgets.") and tail == "description":
        return "widget description"
    if ".alert." in key or "alert" in cm:
        return "alert body" if re.search(r"message|body", tail) else "alert title"
    if re.search(r"button|cta|action|confirm|cancel|done|skip|retry|continue|save|edit|delete|dismiss|close|allow|"
                 r"restore|subscribe|start|stop|primary|secondary", tail) or "button" in cm:
        return "button"
    if "badge" in tail or "badge" in cm:
        return "badge"
    if "toggle" in tail or "toggle" in cm:
        return "toggle"
    if re.search(r"\bhero\b", head):
        return "hero headline"
    if "placeholder" in tail or "placeholder" in head:
        return "placeholder"
    if "subtitle" in tail:
        return "subtitle"
    if re.search(r"title|heading|headline|hero", tail) or "title" in head:
        return "title"
    if re.search(r"caption|footer|hint|detail", tail) or "caption" in cm:
        return "caption"
    if re.search(r"body|message|description|explanation|summary|text|line", tail):
        return "body"
    if tail.startswith("tab") or "tab item" in cm:
        return "tab"
    return "label"


def kind_for(key, en, comment, control):
    cm = (comment or "").lower()
    if re.search(r"quotation|attributed|quote author|\.author$", cm + " " + key):
        return "attributed"
    if re.search(r"user-written|user content|user's own text|typed by the user", cm):
        return "user"
    if re.search(r"not money earned|not (actual|real) (money|earnings)|disclaimer", en + " " + cm, re.I):
        return "disclaimer"
    if re.search(r"legal|terms|privacy|eula|policy", key + " " + cm, re.I):
        return "legal"
    if re.search(r"ios's own|system label|apple's own|mirrors the system|quotes ios", cm):
        return "system-label"
    if "affirmation" in cm or "authored" in cm:
        return "authored"
    if re.search(r"hero|benefit|motivation|celebration|winback|lastchance|beforeafter|encourag", key, re.I) \
            or en.endswith("!"):
        return "promotional"
    if control in ("button", "toggle", "tab", "badge", "placeholder", "widget name") or len(en.split()) <= 4:
        return "functional"
    return "explanatory"


def hero_for(key, comment):
    tail = key.split(".")[-1]
    if re.search(r"hero|headline", tail, re.I) or "hero" in (comment or "").lower():
        return True
    if tail != "title":
        return False
    if RISK_PATTERN.match(key):
        return True
    return key.startswith(("paywall.", "screenTime.", "streakFreeze.")) \
        and not key.startswith(("paywall.plan.", "paywall.billed.", "paywall.price."))


def clause_at(text, pos):
    start = max((text.rfind(c, 0, pos) + 1 for c in ".!?;\n"), default=0)
    end = min([i for i in (text.find(c, pos) for c in ".!?;\n") if i >= 0] + [len(text)])
    return text[start:end].strip()


def invariants(en, control):
    out = []
    for m in NEGATION_RE.finditer(en):
        out.append("negation: " + clause_at(en, m.start()))
    for m in re.finditer(r"(%(?:\d+\$)?(?:%|@|l{0,2}[dui]|\.?\d*f|s)|\b\d[\d.,]*)(\s*(?:%%|%|[A-Za-z]+))?", en):
        token, tail = m.group(1), (m.group(2) or "").strip()
        numeric = not token.startswith("%") or token.endswith(("d", "u", "i", "f"))
        if numeric and (tail == "" or UNIT_RE.search(tail) or tail.startswith("%")):
            out.append("amount: " + (token + " " + tail).strip())
    for m in STRENGTH_RE.finditer(en):
        out.append("strengthening: " + m.group(0))
    for label, rx in (("condition", CONDITION_RE), ("money", MONEY_RE), ("permission", PERMISSION_RE)):
        for m in rx.finditer(en):
            out.append("%s: %s" % (label, clause_at(en, m.start())))
    for b in BRANDS:
        if re.search(r"\b%s\b" % re.escape(b), en):
            out.append("fixed name: " + b)
    if control == "button" and en:
        out.append("action: " + en)
    return list(dict.fromkeys(out))


def screen_role(keys):
    roles = []
    for k in keys:
        role = next((r for p, r in SCREEN_ROLES if k.startswith(p)), "app screen")
        if role not in roles:
            roles.append(role)
    return " / ".join(roles)


def screen_and_state(comment):
    if not comment:
        return "", ""
    head, sep, rest = comment.partition(":")
    return (head.strip(), rest.strip()) if sep else ("", comment.strip())


def norm(s):
    s = PLACEHOLDER_RE.sub(" ", s).lower().replace("’", "'").replace("‘", "'")
    s = re.sub(r"[^\w\s']", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def contains_whole(hay, needle):
    return " " + needle + " " in " " + hay + " "


def walk_strings(obj, path=""):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, "%s.%s" % (path, k) if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, "%s[%d]" % (path, i))


def fit_from_sites(sites):
    """Tightest numeric constraints across resolved sites; expressions stay unknown rather than guessed."""
    lines, scale, upper = None, None, False
    for s in sites:
        for mods in (s.get("modifiers", {}), s.get("inherited", {})):
            v = mods.get("lineLimit")
            if isinstance(v, str) and v.isdigit():
                lines = min(lines, int(v)) if lines else int(v)
            v = mods.get("minimumScaleFactor")
            if isinstance(v, str) and re.fullmatch(r"[\d.]+", v):
                scale = min(scale, float(v)) if scale else float(v)
            if ".uppercase" in str(mods.get("textCase", "")):
                upper = True
    fit = {"status": "constraints" if (lines or scale or upper) else "unverified", "sites": len(sites)}
    if lines:
        fit["lines"] = lines
    if scale:
        fit["min_scale"] = scale
    if upper:
        fit["uppercase"] = True
    return fit


def shield_path(explicit, catalog):
    """--shield, else the Swift file beside the catalog (Foundation/Localization -> Foundation/ShieldSupport)."""
    if explicit:
        if not os.path.exists(explicit):
            die("shield file not found: " + explicit)
        return os.path.abspath(explicit)
    guess = os.path.join(os.path.dirname(os.path.abspath(catalog)), "..", "ShieldSupport", "ShieldMessageCatalog.swift")
    return os.path.normpath(guess) if os.path.exists(guess) else None


class Packet:
    def __init__(self, args):
        self.args = args
        self.shield = shield_path(args.shield, args.catalog)
        self.strings = self.with_shields(load_json(args.catalog)["strings"])
        self.locale = args.locale
        self.glossary = load_json(args.glossary) if args.glossary else {}
        self.findings = load_json(args.findings) if args.findings else {}
        self.constraints = load_json(args.constraints) if args.constraints else {}
        self.candidates, self.rev = self.load_candidates()
        self.keys, self.batch, self.neighbour_batches = self.select()
        self.sites = {}
        for s in self.constraints.get("sites", []):
            if s.get("view") != "passthrough":
                self.sites.setdefault(s["key"], []).append(s)

    @classmethod
    def from_run(cls, args):
        """Reload an existing run for --update; nothing is rebuilt, so ids and neighbours stay stable."""
        coord = os.path.join(args.out_dir, "coordinator")
        self = cls.__new__(cls)
        self.args = args
        self.source_doc = load_json(os.path.join(coord, "source.json"))
        if self.source_doc["locale"] != args.locale:
            die("run locale %s does not match --locale %s" % (self.source_doc["locale"], args.locale))
        self.locale, self.batch = args.locale, self.source_doc.get("batch")
        self.rev = args.rev or self.source_doc.get("rev", 1)
        self.args.catalog = self.source_doc["catalog"]
        self.shield = self.source_doc.get("shield")
        self.strings = self.with_shields(load_json(self.args.catalog)["strings"])
        self.glossary = load_json(self.source_doc["glossary"]) if self.source_doc.get("glossary") else {}
        self.constraints = load_json(self.source_doc["constraints"]) if self.source_doc.get("constraints") else {}
        self.blind_doc = load_json(os.path.join(args.out_dir, "blind", "target.rev%d.json" % self.rev))
        self.id_map = load_json(os.path.join(coord, "id_map.json"))
        entries = self.source_doc["entries"]
        self.involved = [s["key"] for s in entries] + list(self.source_doc.get("context_keys", {}).values()) \
            + [x["key"] for s in entries for x in s["same_source"]]
        return self

    def with_shields(self, strings):
        strings = dict(strings)
        if self.shield:
            strings.update(shield_entries(self.shield))
        return strings

    def expand_shields(self, keys):
        """worklist.py lists a shield pair as shield.<id>; the packet reviews its title and body as two strings."""
        out = []
        for k in keys:
            pair = [k + ".title", k + ".body"]
            out += pair if k not in self.strings and pair[0] in self.strings else [k]
        return out

    def load_candidates(self):
        if not self.args.candidates:
            return {}, self.args.rev or 1
        c = load_json(self.args.candidates)
        if c.get("locale") not in (None, self.locale):
            die("candidates locale %s does not match --locale %s" % (c.get("locale"), self.locale))
        cands = {e["key"]: (e.get("value"), e.get("plural")) for e in c.get("entries", [])}
        return cands, self.args.rev or c.get("rev") or 1

    def select(self):
        a = self.args
        if a.worklist:
            wl = load_json(a.worklist)
            if not a.batch:
                die("--worklist needs --batch <id>; batches: " + ", ".join(b["id"] for b in wl.get("batches", [])))
            batch = next((b for b in wl.get("batches", []) if b["id"] == a.batch), None)
            if not batch:
                die("batch %s not in %s" % (a.batch, a.worklist))
            nb = [k for b in wl["batches"] if b["id"] in batch.get("neighbours", []) for k in b["keys"]]
            keys, batch_id = list(batch["keys"]), batch["id"]
        elif a.keys or a.keys_file:
            keys = [k.strip() for chunk in a.keys for k in chunk.split(",") if k.strip()]
            keys += read_keys_file(a.keys_file) if a.keys_file else []
            batch_id, nb = "keys", []
        elif a.prefix:
            keys = [k for k in self.strings if any(k == p or k.startswith(p + ".") for p in a.prefix)]
            batch_id, nb = "+".join(a.prefix), []
        else:
            die("select strings with --prefix, --keys, --keys-file or --worklist --batch")
        return self.expand_shields(keys), batch_id, self.expand_shields(nb)

    def target(self, key):
        """(text, plural, from_candidates) with candidates overriding the catalog target."""
        if key in self.candidates:
            return (*self.candidates[key], True)
        text, plural, _ = unit(self.strings.get(key, {}), self.locale)
        return text, plural, False

    def same_source(self, key, en):
        out = []
        for k, e in self.strings.items():
            if k == key or en_text(k, e) != en:
                continue
            t, p, _ = unit(e, self.locale)
            out.append({"key": k, "target": t if t is not None else p, "control": control_for(k, e.get("comment"))})
        return out

    def context_keys(self, excluded):
        """Target-bearing keys on the batch's screens, outside it, plus the worklist's neighbour batches."""
        selected = set(self.keys)
        prefixes = {".".join(k.split(".")[:2]) for k in self.keys if k.count(".") >= 2}
        out = []
        for k, e in self.strings.items():
            if k in selected or k in excluded:
                continue
            if k in self.neighbour_batches or any(k.startswith(p + ".") for p in prefixes):
                t, p, _ = unit(e, self.locale)
                if t is not None or p:
                    out.append(k)
        return out[:CONTEXT_LIMIT]

    def agreement_target(self, en, target_text):
        """Glossary noun the string must agree with; gender and number are the coordinator's to fill."""
        hay = (target_text or "").lower()
        for concept, t in self.glossary.get("terms", {}).items():
            forms = [t.get("preferred", "")] + list(t.get("forms", []))
            hit = next((f for f in forms if f and re.search(r"\b%s\b" % re.escape(f.lower()), hay)), None)
            if hit or re.search(r"\b%s\b" % re.escape(concept.replace("_", " ")), en, re.I):
                return {"term": t.get("preferred", ""), "matched": hit, "gender_number": None}
        return None

    def term_list(self):
        use = ["Moneyfesting"] + list(self.glossary.get("fixed", []))
        avoid = []
        for t in self.glossary.get("terms", {}).values():
            use.append(t.get("preferred", ""))
            avoid.extend(t.get("forbidden", []))
        for c in self.glossary.get("controls", {}).values():
            use.append(c.get("preferred", ""))
            use.extend(c.get("roles", {}).values())
        return {"use": sorted({x for x in use if x}), "avoid": sorted({x for x in avoid if x})}

    def build(self):
        excluded = self.findings.get("exclusions", {})
        tiers = self.findings.get("tiers", {})
        skipped = {k: (excluded[k] if k in excluded else
                       "not in catalog" + ("; pass --shield ShieldMessageCatalog.swift" if k.startswith("shield.") else ""))
                   for k in self.keys if k not in self.strings or k in excluded}
        keys = [k for k in self.keys if k not in skipped]
        context = self.context_keys(excluded)
        n_ids = {k: "n%02d" % (i + 1) for i, k in enumerate(context)}
        source, blind, id_map, hero_ids, consistency, markers = [], [], {}, [], [], []
        for i, key in enumerate(keys):
            sid = "s%02d" % (i + 1)
            id_map[sid] = key
            entry = self.strings[key]
            en = en_text(key, entry)
            comment = entry.get("comment") or ""
            text, plural, from_cand = self.target(key)
            cat_text, cat_plural, cat_state = unit(entry, self.locale)
            control = control_for(key, comment)
            kind = kind_for(key, en, comment, control)
            ph = placeholders(en, comment, self.locale, self.glossary)
            screen, state_desc = screen_and_state(comment)
            siblings = self.same_source(key, en)
            sites = self.sites.get(key, [])
            own_prefix = ".".join(key.split(".")[:2])
            neighbours = []
            if i > 0:
                neighbours.append("s%02d" % i)
            if i + 1 < len(keys):
                neighbours.append("s%02d" % (i + 2))
            neighbours += [n_ids[k] for k in context if k.startswith(own_prefix + ".") or k in self.neighbour_batches]
            hero = hero_for(key, comment)
            if hero:
                hero_ids.append(sid)
            value = text if text is not None else plural
            source.append({
                "id": sid, "key": key, "en": en, "comment": comment,
                "existing_target": cat_text if cat_text is not None else cat_plural,
                "state": cat_state, "candidate": value if from_cand else None,
                "variations": {"plural": sorted(plural)} if plural else {},
                "extractionState": entry.get("extractionState"), "kind": kind,
                "tier": tiers.get(key) or check_tier(key, entry, check_units(entry, "en")), "hero": hero,
                "invariants": invariants(en, control), "placeholders": ph, "control": control,
                "screen": screen, "screen_state": state_desc, "order": i + 1, "neighbours": neighbours,
                "slot": ".".join(key.split(".")[2:]) or key.split(".")[-1],
                "agreement_target": self.agreement_target(en, text or (plural or {}).get("other")),
                "same_source": siblings,
                "layout": {"sites": sites, "unresolved": key in self.constraints.get("unresolved", [])} if self.constraints else {},
                "evidence": {},
            })
            if value is None:
                markers.append({"id": sid, "marker": "no target yet"})
                continue
            blind.append({"id": sid, "text": text, "plural": plural, "control_role": control,
                          "tokens": blind_tokens(ph), "fit": fit_from_sites(sites)})
            for s in siblings:
                row = {"id": sid, "sibling_text": s["target"], "role": s["control"]}
                if s["target"] is not None and row not in consistency:
                    consistency.append(row)
            if plural:
                markers.append({"id": sid, "marker": "plural"})
            if text is not None and text == en and cat_state == "translated" and not from_cand:
                markers.append({"id": sid, "marker": "identical by design"})
            if en in BRANDS:
                markers.append({"id": sid, "marker": "fixed name"})
            if text and text.isupper() and en.isupper():
                markers.append({"id": sid, "marker": "uppercase by design"})
            if kind in ("attributed", "user"):
                markers.append({"id": sid, "marker": "attributed" if kind == "attributed" else "user content"})
        blind_neighbours = []
        for k in context:
            t, p, _ = unit(self.strings[k], self.locale)
            blind_neighbours.append({"id": n_ids[k], "text": t, "plural": p,
                                     "role": control_for(k, self.strings[k].get("comment"))})
        role = screen_role(keys)
        self.source_doc = {
            "locale": self.locale, "rev": self.rev, "batch": self.batch, "screen_role": role,
            "catalog": os.path.abspath(self.args.catalog), "catalog_commit": self.catalog_commit(),
            "constraints": os.path.abspath(self.args.constraints) if self.args.constraints else None,
            "glossary": os.path.abspath(self.args.glossary) if self.args.glossary else None, "shield": self.shield,
            "context_keys": {n_ids[k]: k for k in context}, "entries": source,
        }
        self.blind_doc = {
            "locale": self.locale, "screen_role": role, "rev": self.rev, "order": [s["id"] for s in blind],
            "strings": blind, "neighbours": blind_neighbours, "consistency": consistency,
            "term_list": self.term_list(), "hero": [h for h in hero_ids if any(s["id"] == h for s in blind)],
            "markers": markers, "scale": SCALE, "render": [],
        }
        self.id_map = {"locale": self.locale, "rev": self.rev, "batch": self.batch, "strings": id_map,
                       "neighbours": {v: k for k, v in n_ids.items()},
                       "siblings": {s["id"]: [x["key"] for x in s["same_source"]] for s in source if s["same_source"]},
                       "skipped": skipped}
        self.involved = keys + context + [x["key"] for s in source for x in s["same_source"]]

    def catalog_commit(self):
        cwd = os.path.dirname(os.path.abspath(self.args.catalog))
        commit = git(["log", "-1", "--format=%h", "--", os.path.abspath(self.args.catalog)], cwd)
        dirty = git(["status", "--porcelain", "--", os.path.abspath(self.args.catalog)], cwd)
        return (commit + ("+dirty" if dirty else "")) if commit else None

    def forbidden(self):
        """Every normalised English value, key, path and comment sentence the blind packet must not contain."""
        items = []
        for key in dict.fromkeys(self.involved):
            entry = self.strings.get(key, {})
            text, plural, _ = unit(entry, "en")
            for v in [text] + list((plural or {}).values()) + ([key] if text is None and not plural else []):
                if v:
                    items.append(("en value", v, key))
            items.append(("key", key, key))
            for sent in re.split(r"(?<!e\.g)(?<!i\.e)[.;:](?:\s+|$)", entry.get("comment") or ""):
                items.append(("comment", sent, key))
        for p in [self.args.catalog, self.shield] + [s["file"] for s in self.constraints.get("sites", [])]:
            if not p:
                continue
            items.append(("path", p, "-"))
            items.append(("path", os.path.basename(p), "-"))
        out = []
        for kind, raw, key in items:
            n = norm(raw)
            if len(n) >= 4 and re.search(r"[a-z]", n):
                out.append((kind, n, raw, key))
        return out

    def allowlist(self):
        """(allowed anywhere, allowed only in role and marker fields, allowed only in term_list.avoid)."""
        anywhere = {norm(b) for b in BRANDS} | {norm(a) for a in self.args.allow}
        for t in self.glossary.get("terms", {}).values():
            anywhere |= {norm(f) for f in [t.get("preferred", "")] + list(t.get("forms", []))}
        anywhere |= {norm(f) for f in self.glossary.get("fixed", [])}
        for s in self.source_doc["entries"]:
            if s["existing_target"] == s["en"] and s["state"] == "translated":
                anywhere.add(norm(s["en"]))
        avoid = {norm(f) for t in self.glossary.get("terms", {}).values() for f in t.get("forbidden", [])}
        vocabulary = {norm(v) for v in PACKET_VOCABULARY} | {norm(r) for _, r in SCREEN_ROLES} | {norm("app screen")}
        return {a for a in anywhere if a}, vocabulary, {a for a in avoid if a}

    def leak_check(self, blind_path):
        forb = self.forbidden()
        anywhere, fixed_fields, avoid = self.allowlist()
        fails, allowed, vocabulary = [], [], 0
        for path, value in walk_strings(self.blind_doc):
            n = norm(value)
            if not n:
                continue
            for kind, needle, raw, key in forb:
                if not contains_whole(n, needle):
                    continue
                line = "%s: contains %s of %s: %r" % (path, kind, key, raw)
                if needle in anywhere or (needle in avoid and AVOID_FIELD_RE.search(path)):
                    allowed.append(line)
                # a structural field holds the script's own vocabulary; an English word inside one of
                # its phrases ("profile" in "settings and profile") is not a leaked source string
                elif not TEXT_FIELD_RE.search(path) and any(contains_whole(v, needle) for v in fixed_fields):
                    vocabulary += 1
                else:
                    fails.append(line)
        path_tail = re.sub(r"[^a-z0-9]", "", "".join(os.path.abspath(self.args.out_dir).lower().split(os.sep)[-2:]))
        segments = {s for key in self.involved for s in re.split(r"[^a-z0-9]+", key.lower()) if len(s) >= 5}
        fails += ["dispatch path %s: contains key segment %r; name run and batch folders opaquely" % (self.args.out_dir, s)
                  for s in sorted(segments) if s in path_tail]
        status = "FAIL" if fails else "pass"
        lines = ["leak check: %s · %s · %d forbidden values · %d matches · %d allowlisted · %d role-vocabulary"
                 % (status, os.path.relpath(blind_path, self.args.out_dir), len(forb), len(fails), len(allowed), vocabulary)]
        lines += ["FAIL " + l for l in sorted(set(fails))] + ["allowed " + l for l in sorted(set(allowed))]
        lines += ["skipped %s: %s" % (k, v) for k, v in self.id_map.get("skipped", {}).items()]
        return not fails, "\n".join(lines) + "\n"


def merge_update(update_path, source_doc, blind_doc):
    """Merge fit and evidence from a coordinator-written file back into both packets by id or key."""
    upd = load_json(update_path)
    by_key = {s["key"]: s for s in source_doc["entries"]}
    by_id = {s["id"]: s for s in source_doc["entries"]}
    blind_by_id = {s["id"]: s for s in blind_doc["strings"]}
    for e in upd.get("entries", []):
        src = by_id.get(e.get("id")) or by_key.get(e.get("key"))
        if not src:
            die("update entry matches no packet string: %r" % e)
        src["evidence"].update(e.get("evidence", {}))
        target = blind_by_id.get(src["id"])
        if e.get("fit"):
            src.setdefault("layout", {})["fit"] = e["fit"]
            if target:
                target["fit"].update(e["fit"])
        if e.get("render") and target:
            blind_doc["render"].append({"id": src["id"], "path": e["render"]})
            target["fit"]["status"] = "rendered"


def carry_hand_fields(source_path, source_doc, blind_doc):
    """A rebuild keeps what the coordinator completed by hand for keys whose English and comment did not change."""
    if not os.path.exists(source_path):
        return
    old = {e["key"]: e for e in load_json(source_path).get("entries", [])}
    blind_by_id = {s["id"]: s for s in blind_doc["strings"]}
    for entry in source_doc["entries"]:
        prev = old.get(entry["key"])
        if not prev or (prev.get("en"), prev.get("comment")) != (entry["en"], entry["comment"]):
            continue
        for field in ("screen_state", "invariants"):
            if prev.get(field):
                entry[field] = prev[field]
        entry["evidence"].update(prev.get("evidence", {}))
        fit = (prev.get("layout") or {}).get("fit")
        if fit:
            entry["layout"]["fit"] = fit
            if entry["id"] in blind_by_id:
                blind_by_id[entry["id"]]["fit"].update(fit)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="Writes <out-dir>/coordinator/{source.json,id_map.json,leak_check.txt} and "
                                        "<out-dir>/blind/target.rev<N>.json; exit 1 when the leak check fails. "
                                        "--update <file> without --catalog merges {entries: [{id|key, fit, evidence, "
                                        "render}]} into the existing packets and re-runs the leak check. Tiers come "
                                        "from --findings, else from catalog_check.tier_for on the English. Sample "
                                        "values for %@ and counts are per locale in SAMPLES; a locale without an "
                                        "entry gets the generic table, so add one before a new locale's pilot batch.")
    ap.add_argument("--catalog", help="Localizable.xcstrings (or a catalog_slice.py --emit-xcstrings subset)")
    ap.add_argument("--locale", required=True, help="target locale, e.g. ro")
    ap.add_argument("--prefix", action="append", default=[], help="key prefix; repeatable")
    ap.add_argument("--keys", action="append", default=[], help="comma-separated keys; repeatable, order kept")
    ap.add_argument("--keys-file", help="one key per line (# comments), a JSON list, or {\"keys\": [...]}; a bare "
                                        "shield.<id> expands to its .title and .body")
    ap.add_argument("--worklist", help="worklist.json from worklist.py")
    ap.add_argument("--batch", help="batch id inside --worklist")
    ap.add_argument("--shield", help="ShieldMessageCatalog.swift; default ../ShieldSupport/ next to the catalog, "
                                     "skipped when absent (eval fixtures)")
    ap.add_argument("--constraints", help="layout_constraints.json from scan_layout_constraints.py")
    ap.add_argument("--glossary", help="glossary/<locale>.json; preferred forms become the blind term list")
    ap.add_argument("--findings", help="findings.json from catalog_check.py; supplies tiers and exclusions")
    ap.add_argument("--candidates", help="candidates.rev<N>.json; its values replace the catalog target in the blind packet")
    ap.add_argument("--rev", type=int, help="revision number for blind/target.rev<N>.json (default: candidates rev or 1)")
    ap.add_argument("--update", help="fit and evidence file to merge into the packets")
    ap.add_argument("--allow", action="append", default=[], help="extra allowlisted value for the leak check; repeatable")
    ap.add_argument("--out-dir", required=True, help="<run-dir>/<batch>")
    args = ap.parse_args()

    guard_out_dir(args.out_dir, args.catalog)
    coord = os.path.join(args.out_dir, "coordinator")
    if args.catalog:
        packet = Packet(args)
        packet.build()
        carry_hand_fields(os.path.join(coord, "source.json"), packet.source_doc, packet.blind_doc)
    elif args.update:
        packet = Packet.from_run(args)
    else:
        die("--catalog is required unless --update merges into existing packets")
    if args.update:
        merge_update(args.update, packet.source_doc, packet.blind_doc)

    blind_path = os.path.join(args.out_dir, "blind", "target.rev%d.json" % packet.rev)
    dump_json(os.path.join(coord, "source.json"), packet.source_doc)
    dump_json(os.path.join(coord, "id_map.json"), packet.id_map)
    dump_json(blind_path, packet.blind_doc)
    ok, report = packet.leak_check(blind_path)
    with open(os.path.join(coord, "leak_check.txt"), "w", encoding="utf-8") as fh:
        fh.write(report)
    print("packet %s · %d strings · %d blind · %d neighbours · %d siblings · rev %d · %s"
          % (packet.batch, len(packet.source_doc["entries"]), len(packet.blind_doc["strings"]),
             len(packet.blind_doc["neighbours"]), len(packet.blind_doc["consistency"]), packet.rev,
             report.splitlines()[0]))
    if not ok:
        print("blind packet is contaminated; do not dispatch B or C. See coordinator/leak_check.txt", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
