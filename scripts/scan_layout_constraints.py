#!/usr/bin/env python3
"""Index catalog keys to SwiftUI call sites and record the layout constraints each site applies.

Heuristic regex over Swift, not a compiler: a modifier attributed to the wrong view is a finding
for the coordinator, not a fact. Constraints only; character budgets come from renders.

One hop per key: the literal at its lookup (LocalizedStringResource("key", String(localized: "key",
text("key", or `id: "key"` in ShieldMessageCatalog.swift) -> the enclosing accessor -> its usages
(`Type.name`, a file's typealias for the type, `self.name`, or the bare name inside the declaring
file) -> the view construct on or above the usage line, with its own modifier chain and the chains of
up to three enclosing containers, because stacks and groups pass lineLimit, minimumScaleFactor, font
and dynamicTypeSize down to every Text inside. A key used only inside another accessor, a state
function or a component initializer stops there as `passthrough` with `via` saying why and goes to
`unresolved`: fill those by hand with budgetSource "manual" before dispatch, or let the render decide.
"""

import argparse
import json
import os
import re
import sys
from bisect import bisect_right
from collections import Counter

SKIP_DIRS = {".git", ".claude", ".build", "DerivedData", ".codex-tmp", ".screenshots", "Pods", "build"}
LOOKUP_RES = [
    (re.compile(r'LocalizedStringResource\(\s*"([^"\\]+)"'), "LocalizedStringResource"),
    (re.compile(r'\blocalized:\s*"([^"\\]+)"'), "String(localized:)"),
    (re.compile(r'(?<![A-Za-z.])text\(\s*"([^"\\]+)"'), "text()"),
]
SHIELD_ID_RE = re.compile(r'\bid:\s*"([^"\\]+)"')
VIEW_CONSTRUCTS = {
    "Text", "Label", "Button", "Link", "Section", "Toggle", "TextField", "SecureField", "NavigationLink",
    "Picker", "Menu", "Stepper", "DatePicker", "ContentUnavailableView", "ShieldConfiguration",
    ".navigationTitle", ".tabItem", ".alert", ".confirmationDialog", ".accessibilityLabel",
    ".accessibilityHint", ".accessibilityValue", ".help", ".badge",
}
MODIFIERS = ["lineLimit", "minimumScaleFactor", "truncationMode", "fixedSize", "allowsTightening",
             "font", "textCase", "frame", "dynamicTypeSize"]
CONDITION_RE = re.compile(
    r"#if DEBUG|#Preview|ViewThatFits|isAccessibilitySize|widgetFamily|\bfamily\b|horizontalSizeClass|"
    r"dynamicTypeSize|widgetRenderingMode|showsWidgetContainerBackground|^\s*(if|guard|switch|else)\b|^\s*case\s+[.(let]"
)
MODS = (r"^\s*(?:@\w+(?:\([^)]*\))?\s+)*(?:(?:public|private|fileprivate|internal|open|static|class|final|"
        r"override|nonisolated|mutating|lazy|indirect)\s+)*")
DECL_RE = re.compile(MODS + r"(var|let|func)\s+(\w+)")
TYPE_RE = re.compile(MODS + r"(enum|struct|class|extension|actor|protocol)\s+([\w.]+)")
ALIAS_RE = re.compile(r"typealias\s+(\w+)\s*=\s*([\w.]+)")
FLOW_RE = re.compile(r"^\s*\}?\s*(if|else|guard|switch|for|while|do|catch|repeat)\b")
CALL_NAME_RE = re.compile(r"(\.?\w+)\s*\(")
STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"')
CONDITION_WINDOW = 15
CONTAINER_LEVELS = 3


def code_only(line):
    """Strip string literals and line comments so braces, parens and names inside them do not count."""
    return STRING_RE.sub('""', line).split("//")[0]


def depth_delta(line, opens="({[", closes=")}]"):
    code = code_only(line)
    return sum(code.count(c) for c in opens) - sum(code.count(c) for c in closes)


class SwiftFile:
    def __init__(self, path, rel):
        self.rel = rel
        with open(path, encoding="utf-8", errors="replace") as fh:
            self.text = fh.read()
        self.lines = self.text.split("\n")
        self.code_lines = [code_only(l) for l in self.lines]
        self.code = "\n".join(self.code_lines)
        self.starts, self.code_starts = [0], [0]
        for raw, code in zip(self.lines[:-1], self.code_lines[:-1]):
            self.starts.append(self.starts[-1] + len(raw) + 1)
            self.code_starts.append(self.code_starts[-1] + len(code) + 1)
        self.aliases = dict(ALIAS_RE.findall(self.code))

    def line_at(self, offset):
        return bisect_right(self.starts, offset) - 1

    def code_line_at(self, offset):
        return bisect_right(self.code_starts, offset) - 1

    def signature_start(self, i):
        """Line where a multi-line signature begins when line i is its `) -> T {` tail."""
        pending = depth_delta(self.lines[i], "(", ")")
        while pending < 0 and i > 0:
            i -= 1
            pending += depth_delta(self.lines[i], "(", ")")
        return i

    def enclosing(self, idx, include_self=False):
        """(decl (name, kind) or None, [types innermost first]) for line idx."""
        opened, decl, types = 0, None, []
        i = idx if include_self else idx - 1
        while i >= 0:
            if i != idx:
                opened += depth_delta(self.lines[i], "{", "}")
                if opened < 1:
                    i -= 1
                    continue
                opened = 0
                i = self.signature_start(i)
            line = self.code_lines[i]
            m = DECL_RE.match(line)
            if m and decl is None:
                decl = (m.group(2), m.group(1))
            else:
                t = TYPE_RE.match(line)
                if t:
                    types.append(t.group(2).split(".")[-1])
            i -= 1
        return decl, types

    def scope(self, idx):
        decl, types = self.enclosing(idx, include_self=True)
        return ".".join(x for x in [types[0] if types else None, decl[0] if decl else None] if x)

    def enclosing_call(self, idx, max_up=15):
        """Call enclosing line idx: a view construct on the line wins, else the nearest unclosed call above."""
        pending = 0
        for i in range(idx, max(-1, idx - max_up), -1):
            code = self.code_lines[i]
            names = CALL_NAME_RE.findall(code)
            if i == idx:
                for n in names:
                    if n in VIEW_CONSTRUCTS:
                        return n, i
                pending = depth_delta(code, "(", ")")
                if pending > 0 and names:
                    return names[0], i
                continue
            pending += depth_delta(code, "(", ")")
            if pending > 0:
                return (names[-1] if names else None), i
        return None, idx

    def chain(self, idx):
        """Modifier chain of the construct on line idx: its line, then dot-lines and multi-line arguments.
        Lines inside a closure the chain opens (a Button action, a Section body) belong to other views and are
        skipped; started on a closing brace, that brace is ignored."""
        buf, braces, parens = [], 0, 0
        for i in range(idx, min(len(self.lines), idx + 60)):
            code = self.code_lines[i].strip()
            if i == idx:
                code = code.lstrip("}")
            if i > idx and braces <= 0 and parens <= 0 and not code.startswith("."):
                break
            if braces <= 0:
                buf.append(self.lines[i].strip())
            braces += depth_delta(code, "{", "}")
            parens += depth_delta(code, "([", ")]")
        return "\n".join(buf)

    def opener(self, close):
        """Line that opened the block closing on line close."""
        depth = 0
        for i in range(close, -1, -1):
            depth += depth_delta(self.lines[i], "{", "}")
            if depth >= 0:
                return i
        return 0

    def containers(self, idx):
        """[(closing line, chain)] for up to CONTAINER_LEVELS containers around line idx, innermost first.
        Flow-control blocks carry no chain and do not count; the enclosing declaration's brace ends the walk."""
        out, depth, i = [], 0, idx
        while len(out) < CONTAINER_LEVELS and i < min(len(self.lines), idx + 400):
            depth += depth_delta(self.lines[i], "{", "}")
            if depth < 0:
                top = self.code_lines[self.signature_start(self.opener(i))]
                if DECL_RE.match(top) or TYPE_RE.match(top):
                    break
                if not FLOW_RE.match(top):
                    out.append((i, self.chain(i)))
                depth = 0
            i += 1
        return out

    def conditions(self, idx):
        found = []
        for i in range(max(0, idx - CONDITION_WINDOW), idx):
            line = self.lines[i].strip()
            if line and CONDITION_RE.search(line):
                found.append("L%d: %s" % (i + 1, line[:120]))
        return found


def parse_modifiers(chain_text):
    out = {}
    for name in MODIFIERS:
        for m in re.finditer(r"\.%s\(" % name, chain_text):
            start, depth, j = m.end(), 1, m.end()
            while j < len(chain_text) and depth:
                depth += {"(": 1, ")": -1}.get(chain_text[j], 0)
                j += 1
            arg = re.sub(r"\s+", " ", chain_text[start:j - 1]).strip()
            out[name] = arg if arg else True
    return out


def load_files(app_root):
    files = []
    for dirpath, dirnames, filenames in os.walk(app_root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.endswith(("Tests", "UITests")))
        for name in sorted(filenames):
            if name.endswith(".swift"):
                full = os.path.join(dirpath, name)
                files.append(SwiftFile(full, os.path.relpath(full, app_root)))
    return files


def in_scope(key, prefixes, keys):
    if not prefixes and not keys:
        return True
    return key in keys or any(key == p or key.startswith(p + ".") for p in prefixes)


class Scanner:
    def __init__(self, files):
        self.files = files
        # Types declared once (FocusRingCopy) are safe to match anywhere; the 50-odd per-screen
        # `LocalizedStrings` enums only through the using file's typealias or inside their own file.
        self.type_count = Counter(t.group(2).split(".")[-1] for f in files for line in f.code_lines
                                  for t in [TYPE_RE.match(line)] if t and t.group(1) != "extension")
        self.sites, self.seen = [], set()

    def lookups(self, prefixes, keys):
        found = []
        for f in self.files:
            if f.rel.endswith("ShieldMessageCatalog.swift"):
                for m in SHIELD_ID_RE.finditer(f.text):
                    key = "shield." + m.group(1)
                    if any(in_scope(k, prefixes, keys) for k in (key, key + ".title", key + ".body")):
                        found.append((key, f, f.line_at(m.start()), "shield"))
                continue
            for rx, kind in LOOKUP_RES:
                for m in rx.finditer(f.text):
                    if in_scope(m.group(1), prefixes, keys):
                        found.append((m.group(1), f, f.line_at(m.start()), kind))
        return found

    def emit(self, key, f, idx, view, via, modifiers=True):
        sig = (key, f.rel, idx + 1, view)
        if sig in self.seen:
            return
        self.seen.add(sig)
        scope = f.scope(idx)
        site = {"key": key, "file": f.rel, "line": idx + 1, "view": view, "modifiers": {}, "inherited": {},
                "conditions": (["scope: " + scope] if scope else []) + f.conditions(idx), "via": list(via),
                "budgetSource": "scanner"}
        if modifiers:
            site["modifiers"] = parse_modifiers(f.chain(idx))
            for close, chain in f.containers(idx):
                mods = parse_modifiers(chain)
                if mods:
                    site["via"].append("container L%d" % (close + 1))
                    for name, arg in mods.items():
                        site["inherited"].setdefault(name, arg)
        self.sites.append(site)

    def usages(self, f, decl, types):
        """(file, line) of each usage of the accessor declared in f."""
        name, _ = decl
        inner = types[0] if types else None
        outer = types[1] if len(types) > 1 else None
        full = "%s.%s" % (outer, inner) if outer else inner
        unique = self.type_count.get(inner, 0) == 1
        qualified = re.compile(r"(?<![\w])([\w.]+)\.%s\b" % re.escape(name))
        for g in self.files:
            if "." + name not in g.code:
                continue
            for m in qualified.finditer(g.code):
                q = m.group(1)
                if (q in ("self", "Self") and g is f) or (inner and (q == inner or q.endswith("." + inner)) and (
                        unique or g is f or q == full or g.aliases.get(inner) == full)):
                    yield g, g.code_line_at(m.start())
        bare = re.compile(r"(?<![\w.])%s\b" % re.escape(name))
        for i, code in enumerate(f.code_lines):
            m = DECL_RE.match(code)
            if not bare.search(code) or (m and m.group(2) == name):
                continue
            d, t = f.enclosing(i)
            if d and d[0] != name and t[:1] == types[:1]:
                yield f, i

    @staticmethod
    def qualified(decl, types):
        return "%s.%s" % (types[0], decl[0]) if types else decl[0]

    def stop_reason(self, g, idx, call, call_idx):
        d, t = g.enclosing(idx)
        where = self.qualified(d, t) if d else "?"
        if call:
            return "passed to %s(...) at L%d in %s" % (call, call_idx + 1, where)
        return "used in %s, not a view construct" % where

    def run(self, prefixes, keys):
        for key, f, idx, kind in self.lookups(prefixes, keys):
            if kind == "shield":
                self.shield_sites(key)
                continue
            call, call_idx = f.enclosing_call(idx)
            if call in VIEW_CONSTRUCTS:
                self.emit(key, f, call_idx, call, ["literal"])
                continue
            decl, types = f.enclosing(idx, include_self=True)
            if decl is None:
                self.emit(key, f, idx, "passthrough", ["literal", "no enclosing accessor"], modifiers=False)
                continue
            via, hit = [self.qualified(decl, types)], False
            for g, uidx in self.usages(f, decl, types):
                hit = True
                call, call_idx = g.enclosing_call(uidx)
                if call in VIEW_CONSTRUCTS:
                    self.emit(key, g, call_idx, call, via)
                else:
                    self.emit(key, g, uidx, "passthrough", via + [self.stop_reason(g, uidx, call, call_idx)],
                              modifiers=False)
            if not hit:
                self.emit(key, f, idx, "passthrough", via + ["no usage found"], modifiers=False)

    def shield_sites(self, key):
        """ShieldConfiguration is system-rendered: title and subtitle sit in fixed slots iOS truncates itself."""
        for g in self.files:
            for m in re.finditer(r"ShieldConfiguration\(", g.code):
                idx = g.code_line_at(m.start())
                for part, slot in (("title", "title"), ("body", "subtitle")):
                    self.emit("%s.%s" % (key, part), g, idx, "ShieldConfiguration(%s:)" % slot,
                              ["ShieldMessageCatalog", "system-rendered slot; no modifiers apply"], modifiers=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="Output: {sites: [{key, file, line, view, modifiers, inherited, conditions, via, "
                                        "budgetSource}], unresolved: [key], counts}. `modifiers` is the site's own "
                                        "chain, `inherited` merges the enclosing containers' chains with the inner "
                                        "value winning, and `via` names the accessor, each container line that "
                                        "contributed, or why the hop stopped, so a doubtful attribution can be "
                                        "checked. Shield pairs index as shield.<id>.title and .body. Never writes "
                                        "into --app-root.")
    ap.add_argument("--app-root", required=True, help="Moneyfesting checkout (read-only)")
    ap.add_argument("--prefix", action="append", default=[], help="key prefix to index; repeatable")
    ap.add_argument("--keys", action="append", default=[], help="comma-separated keys; repeatable")
    ap.add_argument("--catalog", help="Localizable.xcstrings; in-scope catalog keys with no site are then unresolved")
    ap.add_argument("--out", required=True, help="layout_constraints.json")
    args = ap.parse_args()

    keys = {k.strip() for chunk in args.keys for k in chunk.split(",") if k.strip()}
    app_root = os.path.abspath(args.app_root)
    out_path = os.path.abspath(args.out)
    if out_path.startswith(app_root + os.sep) and not out_path.startswith(os.path.join(app_root, ".codex-tmp") + os.sep):
        sys.exit("refusing to write inside the app checkout outside .codex-tmp/: " + args.out)
    scanner = Scanner(load_files(app_root))
    scanner.run(args.prefix, keys)

    resolved = {s["key"] for s in scanner.sites if s["view"] != "passthrough"}
    scope_keys = {s["key"] for s in scanner.sites}
    if args.catalog:
        with open(args.catalog, encoding="utf-8") as fh:
            scope_keys |= {k for k in json.load(fh)["strings"] if in_scope(k, args.prefix, keys)}
    unresolved = sorted(k for k in scope_keys if k not in resolved)
    scanner.sites.sort(key=lambda s: (s["key"], s["file"], s["line"], s["view"]))
    out = {"app_root": app_root, "sites": scanner.sites, "unresolved": unresolved,
           "counts": {"files": len(scanner.files), "sites": len(scanner.sites),
                      "keys_resolved": len(resolved), "keys_unresolved": len(unresolved)}}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("files %(files)d · sites %(sites)d · keys resolved %(keys_resolved)d · unresolved %(keys_unresolved)d"
          % out["counts"])


if __name__ == "__main__":
    main()
