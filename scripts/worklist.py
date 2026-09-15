#!/usr/bin/env python3
"""Classify catalog keys into work and bound them into review batches.

usage: worklist.py --catalog <xcstrings> --locale ro [--since <commit>] [--records <run-root>]
                   [--findings findings.json] [--shield ShieldMessageCatalog.swift]
                   [--order OnboardingRoutes.swift] [--pilot] --out worklist.json

Per-key status, first match wins after exclusions:
  new                   absent from the --since catalog; without --since, no target and no record
  changed_source        source_hash differs from the --since catalog or from the newest record
  changed_target_state  target unit is needs_review, new or missing
  stale_evidence        newest record passed at this hash but one of its evidence paths is gone
  unchanged_passed      translated at an unchanged hash: owner-accepted, skipped and counted

source_hash is sha256 over json.dumps([en value, en plural variations, comment, extractionState],
sort_keys=True, ensure_ascii=False). Shield pairs carry the id shield.<id> and hash
[titleEnglish, bodyEnglish]; --shield defaults to ../ShieldSupport/ShieldMessageCatalog.swift
next to the catalog.

Exclusions are the catalog_check findings classes (debugOnly, previewOnly, shadow, format)
plus the built-in rule that keys with no en unit ("literal") and format-only keys without a
target ("format") are never work; the findings class wins where both apply.

Batches seed from the first two key segments in catalog order (onboarding in route order with
--order), pack to 15-40 ids, 20 or fewer for paywall, permission and hero classes, never mixing
classes; a group over the bound splits by call-site file when grep finds several, else at
key-segment boundaries nearest an even share. Widget families and the shield set are one batch each.
neighbours are the adjacent batch ids in that order. --pilot emits only the pilot batch
(widgets.focusRing.*, the paywall hero lines, the frozen streak copy, three shield pairs) with
class widget so its render step runs; every pilot id is work regardless of status.

--records scans <run-root>/**/coordinator/verdict.json shaped
  {"keys": {"<id>": {"verdict": "pass|fail", "source_hash": "<sha256>", "evidence": ["<path>"]}}}
The newest file wins per id; evidence paths are absolute or relative to the checkout.
The checkout is read through git show/log and grep only and never written.
"""

import argparse
import glob
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalog_check import SHIELD_TARGET_FIELD, shield_fields  # noqa: E402

# Read-only git calls must not refresh the checkout's index.
os.environ.setdefault("GIT_OPTIONAL_LOCKS", "0")

BOUND, MIN_SIZE, MERGE_BELOW = 40, 15, 10
CLASS_BOUND = {"paywall": 20, "permission": 20, "hero": 20}
HERO = re.compile(r"hero|headline", re.I)
FORMAT_ONLY = re.compile(r"^(?:%\d*\$?(?:@|lld|ld|d|u|f)|[\s.,:·/()-])+$")
PILOT_PREFIX = "widgets.focusRing."
PILOT_KEYS = [
    "paywall.onboardingSubscription.heroLineOne",
    "paywall.onboardingSubscription.heroLineTwo",
    "paywall.onboardingSubscription.heroLineThree",
    "widgets.streak.copy.frozen.small",
    "widgets.streak.copy.frozen.medium",
]
PILOT_SHIELDS = 3
# Route case names that differ from the catalog's second key segment, or live in another feature.
ROUTE_ALIASES = {
    "focusTarget": ["onboarding.dailyFocusGoal"],
    "notificationSoundPicker": ["onboarding.notificationSoundPicker", "onboarding.notificationSound"],
    "photoPicker": ["onboarding.photosPicker"],
    "screenTimeSelectApps": ["onboarding.screenTimeApps"],
    "widgetsIntro": ["onboarding.widgets"],
    "themePicker": ["theme.picker"],
    "createTheme": ["theme.createTheme"],
    "currency": ["currency.root"],
    "subscriptionPaywall": ["paywall.onboardingSubscription"],
}


def die(message):
    print(f"worklist: {message}", file=sys.stderr)
    sys.exit(2)


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def repo_of(path):
    try:
        return git(os.path.dirname(os.path.abspath(path)), "rev-parse", "--show-toplevel").strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def en_source(entry):
    en = entry.get("localizations", {}).get("en", {})
    plural = en.get("variations", {}).get("plural", {})
    return en.get("stringUnit", {}).get("value"), {c: u.get("stringUnit", {}).get("value") for c, u in plural.items()}


def digest(parts):
    return hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def source_hash(entry):
    value, plural = en_source(entry)
    return digest([value, plural, entry.get("comment"), entry.get("extractionState")])


def target_state(entry, locale):
    loc = entry.get("localizations", {}).get(locale)
    if not loc:
        return "missing"
    units = [loc["stringUnit"]] if "stringUnit" in loc else [
        u.get("stringUnit", {}) for u in loc.get("variations", {}).get("plural", {}).values()]
    states = [u.get("state", "missing") if u.get("value") else "missing" for u in units] or ["missing"]
    for worst in ("missing", "needs_review", "new"):
        if worst in states:
            return worst
    return "translated"


def shield_entries(text, locale):
    """Shield pairs as (id, hash, target state); other locales have no struct field yet."""
    field = SHIELD_TARGET_FIELD.get(locale)
    out = {}
    for pair in shield_fields(text):
        if "id" not in pair or "titleEnglish" not in pair:
            continue
        has_target = bool(field and pair.get("title" + field) and pair.get("body" + field))
        out["shield." + pair["id"]] = (digest([pair["titleEnglish"], pair["bodyEnglish"]]), "translated" if has_target else "missing")
    return out


def fallback_exclusions(strings, locale):
    out = {}
    for key, entry in strings.items():
        value, plural = en_source(entry)
        if key == "" or (value is None and not plural):
            out[key] = "literal"
        elif locale not in entry.get("localizations", {}) and FORMAT_ONLY.match(value or ""):
            out[key] = "format"
    return out


def load_records(root):
    """Newest verdict per id across every run under root."""
    files = sorted(glob.glob(os.path.join(root, "**", "coordinator", "verdict.json"), recursive=True), key=os.path.getmtime)
    latest = {}
    for path in files:
        try:
            with open(path, encoding="utf-8") as handle:
                latest.update(json.load(handle).get("keys", {}))
        except (OSError, ValueError) as error:
            print(f"worklist: skipping {path}: {error}", file=sys.stderr)
    return latest


def evidence_missing(record, repo):
    return any(not os.path.exists(os.path.join(repo or "", path)) for path in record.get("evidence", []))


def classify(key, current_hash, state, baseline, record, repo):
    if baseline is not None:
        if key not in baseline:
            return "new"
        if baseline[key] != current_hash:
            return "changed_source"
    elif record is None and state == "missing":
        return "new"
    if record and record.get("source_hash") not in (None, current_hash):
        return "changed_source"
    if state != "translated":
        return "changed_target_state"
    if record and record.get("verdict") == "pass" and evidence_missing(record, repo):
        return "stale_evidence"
    return "unchanged_passed"


def route_order(path):
    with open(path, encoding="utf-8") as handle:
        match = re.search(r"enum OnboardingRoute\b[^{]*\{(.*?)\n\}", handle.read(), re.S)
    if not match:
        die(f"no OnboardingRoute enum in {path}")
    return re.findall(r"^\s*case (\w+)", match.group(1), re.M)


def group_id(key):
    """feature.screen per I18N_PLAN section 2; a two-segment key belongs to the feature's root group."""
    parts = key.split(".")
    return ".".join(parts[:2]) if len(parts) > 2 else parts[0] + ".root"


def group_class(gid, keys):
    feature, _, screen = gid.partition(".")
    if feature == "widgets":
        return "widget"
    if feature in ("paywall", "shield"):
        return feature
    if "permission" in screen.lower():
        return "permission"
    if any(HERO.search(seg) for key in keys for seg in key.split(".")[2:]):
        return "hero"
    return "general"


def call_site_files(repo, keys):
    """Map each key to the first Swift file quoting it, via one grep over the app sources."""
    if not repo:
        return {}
    patterns = "".join(f'"{key}"\n' for key in keys)
    out = subprocess.run(["grep", "-rHoF", "--include=*.swift", "-f", "/dev/stdin", os.path.join(repo, "Manifesting")],
                         input=patterns, capture_output=True, text=True).stdout
    files = {}
    for line in sorted(out.splitlines()):
        path, _, quoted = line.rpartition(":")
        files.setdefault(quoted.strip('"'), os.path.splitext(os.path.basename(path))[0])
    return files


def balanced_split(keys, bound):
    """One greedy pass: cut nearest an even share of what is left, at the shallowest key-segment boundary
    (depth 3, then 4, 5) within half a share so sibling screens stay together; hard cut when none fits."""
    chunks, start = [], 0
    while len(keys) - start > bound:
        left = len(keys) - start
        share = math.ceil(left / math.ceil(left / bound))
        low, high = start + share // 2, start + min(bound, share + share // 2)
        cut = start + share
        for depth in (3, 4, 5):
            cuts = [i for i in range(low, high + 1) if keys[i].split(".")[:depth] != keys[i - 1].split(".")[:depth]]
            if cuts:
                cut = min(cuts, key=lambda i: abs(i - start - share))
                break
        chunks.append(keys[start:cut])
        start = cut
    return chunks + [keys[start:]]


def split_group(gid, keys, bound, repo):
    files = call_site_files(repo, keys)
    by_file = {}
    for key in keys:
        by_file.setdefault(files.get(key), []).append(key)
    subgroups = [(f"{gid}:{stem}" if stem else gid, sub) for stem, sub in by_file.items()] if len(by_file) > 1 else [(gid, keys)]
    out = []
    for sid, sub in subgroups:
        chunks = [sub] if len(sub) <= bound else balanced_split(sub, bound)
        out += [(sid if len(chunks) == 1 else f"{sid}#{i + 1}", chunk) for i, chunk in enumerate(chunks)]
    return out


def pack(groups, repo):
    """groups: [(gid, class, keys)] in flow order -> [(gids, class, keys)], never mixing classes."""
    batches, cur_ids, cur_keys, cur_class = [], [], [], None

    def flush():
        # A leftover under MERGE_BELOW joins the previous batch of its class rather than shipping alone.
        nonlocal cur_ids, cur_keys
        if not cur_keys:
            return
        last = batches[-1] if batches else None
        if last and len(cur_keys) < MERGE_BELOW and last[1] == cur_class and len(last[2]) + len(cur_keys) <= CLASS_BOUND.get(cur_class, BOUND):
            batches[-1] = (last[0] + cur_ids, cur_class, last[2] + cur_keys)
        else:
            batches.append((cur_ids, cur_class, cur_keys))
        cur_ids, cur_keys = [], []

    for gid, cls, keys in groups:
        bound = CLASS_BOUND.get(cls, BOUND)
        if len(keys) > bound:
            flush()
            cur_class = cls
            for sid, chunk in split_group(gid, keys, bound, repo):
                cur_ids, cur_keys = [sid], list(chunk)
                flush()
            continue
        if cur_keys and (cls != cur_class or len(cur_keys) + len(keys) > bound or len(cur_keys) >= MIN_SIZE):
            flush()
        cur_class = cls
        cur_ids.append(gid)
        cur_keys.extend(keys)
    flush()
    return batches


def batch_id(gids):
    if len(gids) == 1:
        return gids[0]
    features = {g.split(".")[0] for g in gids}
    if len(features) == 1:
        return gids[0] + "+" + "+".join(g.split(".", 1)[1] for g in gids[1:])
    return "+".join(gids)


def adjacent(chain, item):
    i = chain.index(item)
    return chain[max(0, i - 1):i] + chain[i + 1:i + 2]


def build_batches(work_keys, shield_ids, repo, routes):
    groups = {}
    for key in work_keys:
        groups.setdefault(group_id(key), []).append(key)
    ordered = list(groups)
    route_gids = []
    if routes:
        for route in routes:
            route_gids += [g for g in ROUTE_ALIASES.get(route, [f"onboarding.{route}"]) if g in groups]
        onboarding = [g for g in route_gids if g.startswith("onboarding.")]
        onboarding += [g for g in ordered if g.startswith("onboarding.") and g not in onboarding]
        slots = iter(onboarding)
        ordered = [next(slots) if g.startswith("onboarding.") else g for g in ordered]
    by_feature = {}
    for gid in ordered:
        by_feature.setdefault(gid.split(".")[0], []).append((gid, group_class(gid, groups[gid]), groups[gid]))
    batches = []
    for feature, feature_groups in by_feature.items():
        packed = [([g], c, k) for g, c, k in feature_groups] if feature == "widgets" else pack(feature_groups, repo)
        chain = [batch_id(gids) for gids, _, _ in packed]
        for gids, cls, keys in packed:
            bid = batch_id(gids)
            batches.append({"id": bid, "class": cls, "keys": keys, "neighbours": adjacent(chain, bid), "groups": gids})
    if shield_ids:
        batches.append({"id": "shield", "class": "shield", "keys": shield_ids, "neighbours": [], "groups": ["shield"]})
    owner = {}
    for batch in batches:
        for gid in batch["groups"]:
            owner.setdefault(re.split(r"[:#]", gid)[0], []).append(batch["id"])
    sequence = list(dict.fromkeys(bid for gid in route_gids for bid in owner.get(gid, [])))
    for batch in batches:
        if batch["id"] in sequence:
            batch["neighbours"] = list(dict.fromkeys(adjacent(sequence, batch["id"]) + batch["neighbours"]))
    return batches


def pilot_batch(strings, shield_ids):
    keys = [k for k in strings if k.startswith(PILOT_PREFIX)] + [k for k in PILOT_KEYS if k in strings] + shield_ids[:PILOT_SHIELDS]
    return {"id": "pilot", "class": "widget", "pilot": True, "classes": ["widget", "paywall", "shield"], "keys": keys, "neighbours": []}


def catalog_git_state(repo, rel):
    """(last commit touching the catalog, whether the working tree differs from it)."""
    commit = git(repo, "log", "-1", "--format=%h", "--", rel).strip() or None
    return commit, bool(git(repo, "status", "--porcelain", "--", rel).strip())


def baseline_hashes(repo, since, catalog_rel, shield_rel, locale):
    """source_hash per id at the --since commit; a shield file absent there is simply not baselined."""
    try:
        base = json.loads(git(repo, "show", f"{since}:{catalog_rel}"))["strings"]
    except subprocess.CalledProcessError:
        die(f"--since {since}: no catalog at that commit ({catalog_rel})")
    hashes = {key: source_hash(entry) for key, entry in base.items()}
    if shield_rel:
        try:
            hashes.update({sid: h for sid, (h, _) in shield_entries(git(repo, "show", f"{since}:{shield_rel}"), locale).items()})
        except subprocess.CalledProcessError:
            pass
    return hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--locale", required=True)
    parser.add_argument("--since", metavar="COMMIT", help="baseline catalog commit, read with git show")
    parser.add_argument("--records", metavar="RUN_ROOT", help="run-state root holding coordinator/verdict.json files")
    parser.add_argument("--findings", metavar="JSON", help="catalog_check output: exclusions and tiers")
    parser.add_argument("--shield", metavar="SWIFT", help="ShieldMessageCatalog.swift; auto-detected next to the catalog")
    parser.add_argument("--order", metavar="SWIFT", help="OnboardingRoutes.swift for onboarding batch order")
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.catalog, encoding="utf-8") as handle:
        strings = json.load(handle)["strings"]
    catalog_dir = os.path.dirname(os.path.abspath(args.catalog))
    shield_path = args.shield or os.path.join(catalog_dir, "..", "ShieldSupport", "ShieldMessageCatalog.swift")
    shields = {}
    if os.path.exists(shield_path):
        with open(shield_path, encoding="utf-8") as handle:
            shields = shield_entries(handle.read(), args.locale)

    repo = repo_of(args.catalog)
    commit, dirty = catalog_git_state(repo, os.path.relpath(os.path.abspath(args.catalog), repo)) if repo else (None, False)
    baseline = None
    if args.since:
        if not repo:
            die("--since needs the catalog inside a git checkout")
        baseline = baseline_hashes(repo, args.since, os.path.relpath(os.path.abspath(args.catalog), repo),
                                   os.path.relpath(os.path.abspath(shield_path), repo) if shields else None, args.locale)

    findings = {}
    if args.findings:
        with open(args.findings, encoding="utf-8") as handle:
            findings = json.load(handle)
    excluded = {**fallback_exclusions(strings, args.locale), **findings.get("exclusions", {})}
    tiers = findings.get("tiers", {})
    records = load_records(args.records) if args.records else {}

    per_key = {}
    for key, entry in strings.items():
        if key in excluded:
            continue
        current = source_hash(entry)
        status = classify(key, current, target_state(entry, args.locale), baseline, records.get(key), repo)
        per_key[key] = {"status": status, "source_hash": current}
        if key in tiers:
            per_key[key]["tier"] = tiers[key]
    for sid, (current, state) in shields.items():
        per_key[sid] = {"status": classify(sid, current, state, baseline, records.get(sid), repo), "source_hash": current}

    if args.pilot:
        batches = [pilot_batch(strings, list(shields))]
        per_key = {k: per_key[k] for k in batches[0]["keys"] if k in per_key}
        batches[0]["keys"] = list(per_key)
        skipped = {"unchanged_passed": 0, "excluded": 0}
    else:
        work = [k for k, v in per_key.items() if v["status"] != "unchanged_passed"]
        batches = build_batches([k for k in work if k in strings], [k for k in work if k in shields], repo,
                                route_order(args.order) if args.order else None)
        skipped = {"unchanged_passed": len(per_key) - len(work), "excluded": len(excluded)}
    for batch in batches:
        for key in batch["keys"]:
            per_key[key]["batch"] = batch["id"]

    out = {"catalog_commit": commit, "catalog_dirty": dirty, "locale": args.locale, "since": args.since,
           "per_key": per_key, "batches": batches, "skipped": skipped, "excluded_keys": excluded}
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    counts = Counter(info["status"] for info in per_key.values())
    print(f"worklist: catalog {commit}{' (dirty)' if dirty else ''} · {len(per_key)} ids · "
          + " · ".join(f"{status} {n}" for status, n in sorted(counts.items())) + f" · excluded {skipped['excluded']}")
    print(f"batches {len(batches)}: " + ", ".join(f"{b['id']} {len(b['keys'])} {b['class']}" for b in batches))


if __name__ == "__main__":
    main()
