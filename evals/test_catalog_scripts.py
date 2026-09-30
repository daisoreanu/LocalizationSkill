import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "evals/files/focus-ring.xcstrings"


class CatalogScriptTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.directory = Path(self.scratch.name)
        self.catalog = self.directory / "focus-ring.xcstrings"
        shutil.copyfile(FIXTURE, self.catalog)

    def apply(self, entries, locale="ro", *options):
        candidates = self.directory / "candidates.json"
        candidates.write_text(json.dumps({"locale": locale, "entries": entries}, ensure_ascii=False))
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/catalog_apply.py"), "--catalog", str(self.catalog),
             "--candidates", str(candidates), "--locale", locale, *options],
            capture_output=True, text=True,
        )

    def test_missing_placeholder_cannot_change_catalog(self):
        before = self.catalog.read_bytes()
        result = self.apply([{"key": "widgets.focusRing.a11y.firstRun", "value": "Încă nicio sesiune."}])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("placeholder d", result.stderr)
        self.assertEqual(self.catalog.read_bytes(), before)

    def test_missing_plural_category_cannot_change_catalog(self):
        before = self.catalog.read_bytes()
        result = self.apply([{"key": "component.daySelection.daysCount",
                              "plural": {"one": "%lld zi", "other": "%lld de zile"}}],
                            "ro", "--overwrite-translated")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing plural form 'few'", result.stderr)
        self.assertEqual(self.catalog.read_bytes(), before)

    def test_numbered_placeholders_and_extra_plural_branch_are_allowed(self):
        result = self.apply([{"key": "widgets.focusRing.a11y.progress",
                              "value": "%2$lld din %1$lld minute azi. %3$@ din obiectiv."}])
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.apply([{"key": "component.daySelection.daysCount",
                              "plural": {"one": "o zi", "few": "%lld zile",
                                         "other": "%lld de zile", "two": "%lld zile"}}],
                            "ro", "--overwrite-translated")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_scoped_apply_preserves_catalog_final_newline(self):
        original = self.catalog.read_bytes().removesuffix(b"\n")
        key = "widgets.focusRing.firstRun"
        old_value = json.loads(original)["strings"][key]["localizations"]["ro"]["stringUnit"]["value"]
        new_value = "Pornește prima sesiune"
        for ending in (b"", b"\n"):
            with self.subTest(ending=ending):
                before = original + ending
                self.catalog.write_bytes(before)
                result = self.apply([{"key": key, "value": new_value}])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.catalog.read_bytes(), before.replace(old_value.encode(), new_value.encode()))

    def test_existing_substitution_cannot_be_erased(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from catalog_apply import dump_xcstrings

        data = json.loads(self.catalog.read_text())
        target = data["strings"]["widgets.focusRing.a11y.goalMet"]["localizations"]["ro"]
        target["stringUnit"]["value"] = "%1$lld din %#@goalMinutes@ azi. Obiectiv atins."
        target["substitutions"] = {"goalMinutes": {"argNum": 2, "formatSpecifier": "lld",
                                                 "variations": {"plural": {
                                                     "one": {"stringUnit": {"state": "needs_review", "value": "%2$lld minut"}},
                                                     "few": {"stringUnit": {"state": "needs_review", "value": "%2$lld minute"}},
                                                     "other": {"stringUnit": {"state": "needs_review", "value": "%2$lld de minute"}},
                                                 }}}}
        self.catalog.write_text(dump_xcstrings(data))
        before = self.catalog.read_bytes()
        result = self.apply([{"key": "widgets.focusRing.a11y.goalMet",
                              "value": "%1$lld din %2$lld minute azi. Obiectiv atins."}])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("existing localization has substitutions", result.stderr)
        self.assertEqual(self.catalog.read_bytes(), before)

    def test_unknown_packet_key_cannot_create_blind_packet(self):
        output = self.directory / "packet"
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_context_packet.py"), "--catalog", str(self.catalog),
             "--locale", "ro", "--keys", "paywall.hero.reclaimFormat,widgets.focusRing.typo",
             "--out-dir", str(output)], capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("widgets.focusRing.typo", result.stderr)
        self.assertFalse((output / "blind/target.rev1.json").exists())

    def test_verified_context_reaches_blind_packet_and_survives_revision(self):
        output = self.directory / "b01"
        update = self.directory / "context.json"
        update.write_text(json.dumps({"entries": [{
            "key": "widgets.focusRing.a11y.money",
            "screen_state": "Coordinator-only source explanation",
            "control": "voiceover label",
            "placeholders": [{"token": "%@", "type": "date", "samples": ["12 mai"]}],
            "target_context": {"state": "Data realizării", "agreement_target": "realizare, feminin singular"},
        }]}))
        command = [sys.executable, str(ROOT / "scripts/build_context_packet.py"),
                   "--catalog", str(self.catalog), "--locale", "ro",
                   "--keys", "widgets.focusRing.a11y.money", "--out-dir", str(output)]
        first = subprocess.run(command + ["--update", str(update)], capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        second = subprocess.run(command + ["--rev", "2"], capture_output=True, text=True)
        self.assertEqual(second.returncode, 0, second.stderr)
        packet = json.loads((output / "blind/target.rev2.json").read_text())
        row = packet["strings"][0]
        self.assertEqual(row["tokens"], [{"token": "%@", "sample": "12 mai"}])
        self.assertEqual(row["context"]["agreement_target"], "realizare, feminin singular")
        self.assertNotIn("Coordinator-only", json.dumps(packet))

    def test_target_context_still_blocks_source_leaks(self):
        output = self.directory / "b01"
        update = self.directory / "context.json"
        update.write_text(json.dumps({"entries": [{
            "key": "widgets.focusRing.a11y.money",
            "target_context": {"state": "widgets.focusRing.a11y.money"},
        }]}))
        result = subprocess.run([
            sys.executable, str(ROOT / "scripts/build_context_packet.py"),
            "--catalog", str(self.catalog), "--locale", "ro",
            "--keys", "widgets.focusRing.a11y.money", "--update", str(update),
            "--out-dir", str(output),
        ], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contaminated", result.stderr)

    def packet(self, keys, *options):
        return subprocess.run([
            sys.executable, str(ROOT / "scripts/build_context_packet.py"),
            "--catalog", str(self.catalog), "--locale", "ro", "--keys", ",".join(keys),
            "--out-dir", str(self.directory / "b01"), *options,
        ], capture_output=True, text=True)

    def context_fixture(self):
        values = {
            "test.flow.main": ("Open details", "Vezi detaliile", "Primary button for detail screen"),
            "test.flow.neighbour": ("Next step", "Pasul următor", "Nearby screen heading"),
            "other.flow.sibling": ("Open details", "Deschide detaliile", "Secondary button after a result"),
        }
        self.catalog.write_text(json.dumps({"strings": {
            key: {"comment": comment, "localizations": {
                locale: {"stringUnit": {"state": "needs_review", "value": text}}
                for locale, text in (("en", english), ("ro", target))}}
            for key, (english, target, comment) in values.items()
        }}))
        return "test.flow.main", "test.flow.neighbour", "other.flow.sibling"

    def test_context_and_same_source_casing_is_blind_and_opaque(self):
        main, neighbour, sibling = self.context_fixture()
        first = self.packet([main])
        self.assertEqual(first.returncode, 0, first.stderr)
        initial = json.loads((self.directory / "b01/blind/target.rev1.json").read_text())
        self.assertEqual(initial["neighbours"][0]["casing"]["position"], "unknown")
        self.assertEqual(initial["consistency"][0]["casing"]["status"], "needs_review")
        update = self.directory / "context.json"
        update.write_text(json.dumps({"entries": [{"key": main, "kind": "explanatory"}], "context_entries": [
            {"key": neighbour, "control": "label", "casing": {"status": "confirmed", "role": "section_heading",
                "position": "standalone", "style": "sentence", "owner": "catalog",
                "protected_terms": [], "exceptions": [], "evidence": "Nearby screen heading source evidence"}},
            {"key": sibling, "control": "label", "casing": {"status": "confirmed", "role": "continuation",
                "position": "continuation", "style": "lowercase", "owner": "catalog",
                "protected_terms": [], "exceptions": [],
                "equivalent_group": "other.flow.sibling source group",
                "evidence": "Secondary button source evidence"}},
        ]}))
        result = self.packet([main], "--update", str(update))
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.directory / "b01"
        source = json.loads((output / "coordinator/source.json").read_text())
        packet = json.loads((output / "blind/target.rev1.json").read_text())
        self.assertEqual({row["key"] for row in source["context_entries"]}, {neighbour, sibling})
        self.assertEqual(packet["neighbours"][0]["casing"]["position"], "standalone")
        self.assertEqual(packet["consistency"][0]["casing"]["position"], "continuation")
        self.assertEqual(packet["consistency"][0]["casing"]["style"], "lowercase")
        self.assertEqual(packet["consistency"][0]["sibling_id"], "c01")
        self.assertEqual(packet["neighbours"][0]["role"], "label")
        self.assertEqual(packet["consistency"][0]["role"], "label")
        self.assertEqual(source["entries"][0]["same_source"][0]["control"], "label")
        self.assertEqual(source["entries"][0]["kind"], "explanatory")
        blind_text = json.dumps(packet)
        for source_only in (main, neighbour, sibling, "Open details", "Nearby screen heading",
                            "Secondary button", "source group", "evidence", "reason"):
            self.assertNotIn(source_only, blind_text)
        rebuilt = self.packet([main], "--rev", "2")
        self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
        carried = json.loads((output / "blind/target.rev2.json").read_text())
        self.assertEqual(carried["neighbours"][0]["casing"]["position"], "standalone")
        self.assertEqual(carried["consistency"][0]["casing"]["style"], "lowercase")
        self.assertEqual(carried["neighbours"][0]["role"], "label")
        self.assertEqual(carried["consistency"][0]["role"], "label")
        rebuilt_source = json.loads((output / "coordinator/source.json").read_text())
        self.assertEqual(rebuilt_source["entries"][0]["kind"], "explanatory")

    def test_update_refreshes_catalog_context_but_keeps_explicit_candidate(self):
        main, neighbour, sibling = self.context_fixture()
        other_selected = "test.flow.extra"
        data = json.loads(self.catalog.read_text())
        data["strings"][other_selected] = {"comment": "Another selected button", "localizations": {
            "en": {"stringUnit": {"state": "needs_review", "value": "Show more"}},
            "ro": {"stringUnit": {"state": "needs_review", "value": "Arată mai mult"}},
        }}
        self.catalog.write_text(json.dumps(data))
        candidates = self.directory / "candidates.json"
        candidates.write_text(json.dumps({"locale": "ro", "rev": 2, "entries": [
            {"key": main, "value": "Consultă detaliile"}]}))
        result = self.packet([main, other_selected], "--candidates", str(candidates))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(self.catalog.read_text())
        changed = {main: "Vezi informațiile", other_selected: "Descoperă mai mult",
                   neighbour: "Etapa următoare", sibling: "Arată detaliile"}
        for key, target in changed.items():
            data["strings"][key]["localizations"]["ro"]["stringUnit"]["value"] = target
        self.catalog.write_text(json.dumps(data))
        update = self.directory / "context.json"
        update.write_text('{"entries": []}')
        output = self.directory / "b01"
        result = subprocess.run([sys.executable, str(ROOT / "scripts/build_context_packet.py"),
                                 "--locale", "ro", "--out-dir", str(output), "--rev", "2",
                                 "--update", str(update)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        source = json.loads((output / "coordinator/source.json").read_text())
        packet = json.loads((output / "blind/target.rev2.json").read_text())
        self.assertEqual(packet["strings"][0]["text"], "Consultă detaliile")
        self.assertEqual(packet["strings"][1]["text"], changed[other_selected])
        self.assertEqual(source["entries"][0]["existing_target"], changed[main])
        self.assertEqual(source["entries"][0]["target_units"][""], "Consultă detaliile")
        self.assertEqual(packet["neighbours"][0]["text"], changed[neighbour])
        self.assertEqual(packet["consistency"][0]["sibling_text"], changed[sibling])
        self.assertEqual({row["key"]: row["target"] for row in source["context_entries"]},
                         {neighbour: changed[neighbour], sibling: changed[sibling]})
        rebuilt = self.packet([main, other_selected], "--rev", "3")
        self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
        data["strings"][main]["localizations"]["ro"]["stringUnit"]["value"] = "Mai multe informații"
        self.catalog.write_text(json.dumps(data))
        refreshed = subprocess.run([sys.executable, str(ROOT / "scripts/build_context_packet.py"),
                                    "--locale", "ro", "--out-dir", str(output), "--rev", "3",
                                    "--update", str(update)], capture_output=True, text=True)
        self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
        packet = json.loads((output / "blind/target.rev3.json").read_text())
        self.assertEqual(packet["strings"][0]["text"], "Mai multe informații")
        other_catalog = self.directory / "other.xcstrings"
        shutil.copyfile(self.catalog, other_catalog)
        different = subprocess.run([sys.executable, str(ROOT / "scripts/build_context_packet.py"),
                                    "--catalog", str(other_catalog), "--locale", "ro", "--keys", main,
                                    "--out-dir", str(output), "--update", str(update)],
                                   capture_output=True, text=True)
        self.assertNotEqual(different.returncode, 0)
        self.assertIn("recorded catalog", different.stderr)
        wrong_revision = subprocess.run([sys.executable, str(ROOT / "scripts/build_context_packet.py"),
                                         "--locale", "ro", "--out-dir", str(output), "--rev", "2",
                                         "--update", str(update)], capture_output=True, text=True)
        self.assertNotEqual(wrong_revision.returncode, 0)
        self.assertIn("revision differs", wrong_revision.stderr)

    def test_update_refreshes_flat_target_with_plural_candidate(self):
        key = "component.daySelection.daysCount"
        data = json.loads(self.catalog.read_text())
        data["strings"][key]["localizations"]["ro"] = {
            "stringUnit": {"state": "needs_review", "value": "%lld zile"}}
        self.catalog.write_text(json.dumps(data))
        first = self.packet([key])
        self.assertEqual(first.returncode, 0, first.stderr)
        output = self.directory / "b01"
        candidates = self.directory / "candidates.json"
        plural = {"one": "%lld zi", "few": "%lld zile", "other": "%lld de zile"}
        candidates.write_text(json.dumps({"locale": "ro", "rev": 1, "entries": [
            {"key": key, "plural": plural}]}))
        update = self.directory / "context.json"
        update.write_text('{"entries": []}')
        command = [sys.executable, str(ROOT / "scripts/build_context_packet.py"),
                   "--locale", "ro", "--out-dir", str(output), "--update", str(update)]
        refreshed = subprocess.run(command + ["--candidates", str(candidates), "--rev", "1"],
                                   capture_output=True, text=True)
        self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
        source = json.loads((output / "coordinator/source.json").read_text())
        blind = json.loads((output / "blind/target.rev1.json").read_text())
        self.assertEqual(source["entries"][0]["candidate"], plural)
        self.assertEqual(source["entries"][0]["variations"], {"plural": sorted(plural)})
        self.assertEqual(source["entries"][0]["target_units"], {
            "plural:" + category: value for category, value in plural.items()})
        self.assertEqual(blind["strings"][0]["plural"], plural)
        self.assertIsNone(blind["strings"][0]["text"])
        self.assertIn({"id": "s01", "marker": "plural"}, blind["markers"])
        self.assertIn("casing", blind["strings"][0])
        self.assertIn("leak check: pass", (output / "coordinator/leak_check.txt").read_text())
        preserved = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(preserved.returncode, 0, preserved.stderr)
        self.assertEqual(json.loads((output / "blind/target.rev1.json").read_text())["strings"][0]["plural"], plural)

    def test_update_candidate_rejects_wrong_revision_and_missing_placeholder(self):
        key = "widgets.focusRing.a11y.money"
        first = self.packet([key])
        self.assertEqual(first.returncode, 0, first.stderr)
        output = self.directory / "b01"
        before = (output / "blind/target.rev1.json").read_bytes()
        update = self.directory / "context.json"
        update.write_text('{"entries": []}')
        candidates = self.directory / "candidates.json"
        command = [sys.executable, str(ROOT / "scripts/build_context_packet.py"),
                   "--locale", "ro", "--out-dir", str(output), "--update", str(update),
                   "--candidates", str(candidates)]
        for rev, value, error in ((2, "Valoare estimată: %@", "candidates revision differs"),
                                  (1, "Valoare estimată", "placeholder")):
            with self.subTest(error=error):
                candidates.write_text(json.dumps({"locale": "ro", "rev": rev, "entries": [
                    {"key": key, "value": value}]}))
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(error, result.stderr)
                self.assertEqual((output / "blind/target.rev1.json").read_bytes(), before)

    def test_update_candidate_cannot_replace_substitution_units(self):
        key = "test.count"
        substitution = {"goalDays": {"argNum": 1, "formatSpecifier": "lld", "variations": {"plural": {
            "one": {"stringUnit": {"state": "needs_review", "value": "%lld zi"}},
        }}}}
        self.catalog.write_text(json.dumps({"strings": {key: {"comment": "Count label", "localizations": {
            "en": {"stringUnit": {"state": "translated", "value": "Days: %#@goalDays@"},
                   "substitutions": substitution},
            "ro": {"stringUnit": {"state": "needs_review", "value": "Zile: %#@goalDays@"},
                   "substitutions": substitution},
        }}}}))
        first = self.packet([key])
        self.assertEqual(first.returncode, 0, first.stderr)
        output = self.directory / "b01"
        before = (output / "blind/target.rev1.json").read_bytes()
        candidates = self.directory / "candidates.json"
        candidates.write_text(json.dumps({"locale": "ro", "entries": [
            {"key": key, "value": "Zile: %#@goalDays@"}]}))
        update = self.directory / "context.json"
        update.write_text('{"entries": []}')
        result = subprocess.run([sys.executable, str(ROOT / "scripts/build_context_packet.py"),
                                 "--locale", "ro", "--out-dir", str(output), "--update", str(update),
                                 "--candidates", str(candidates)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot bind", result.stderr)
        self.assertEqual((output / "blind/target.rev1.json").read_bytes(), before)

    def test_update_adds_first_target_candidate(self):
        key = "test.new.title"
        self.catalog.write_text(json.dumps({"strings": {key: {"comment": "Screen title", "localizations": {
            "en": {"stringUnit": {"state": "translated", "value": "Begin here"}}}}}}))
        first = self.packet([key])
        self.assertEqual(first.returncode, 0, first.stderr)
        output = self.directory / "b01"
        candidates = self.directory / "candidates.json"
        candidates.write_text(json.dumps({"locale": "ro", "rev": 1, "entries": [
            {"key": key, "value": "Începe aici"}]}))
        update = self.directory / "context.json"
        update.write_text('{"entries": []}')
        result = subprocess.run([sys.executable, str(ROOT / "scripts/build_context_packet.py"),
                                 "--locale", "ro", "--out-dir", str(output), "--update", str(update),
                                 "--candidates", str(candidates)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        blind = json.loads((output / "blind/target.rev1.json").read_text())
        self.assertEqual(blind["order"], ["s01"])
        self.assertEqual(blind["strings"][0]["text"], "Începe aici")
        self.assertNotIn({"id": "s01", "marker": "no target yet"}, blind["markers"])

    def test_update_flat_candidate_replaces_catalog_plural_units(self):
        key = "test.count.label"
        self.catalog.write_text(json.dumps({"strings": {key: {"comment": "Count label", "localizations": {
            "en": {"stringUnit": {"state": "translated", "value": "%lld days"}},
            "ro": {"variations": {"plural": {
                "one": {"stringUnit": {"state": "needs_review", "value": "%lld zi"}},
                "few": {"stringUnit": {"state": "needs_review", "value": "%lld zile"}},
                "other": {"stringUnit": {"state": "needs_review", "value": "%lld de zile"}},
            }}},
        }}}}))
        first = self.packet([key])
        self.assertEqual(first.returncode, 0, first.stderr)
        output = self.directory / "b01"
        candidates = self.directory / "candidates.json"
        candidates.write_text(json.dumps({"locale": "ro", "entries": [{"key": key, "value": "%lld zile"}]}))
        update = self.directory / "context.json"
        update.write_text('{"entries": []}')
        command = [sys.executable, str(ROOT / "scripts/build_context_packet.py"),
                   "--locale", "ro", "--out-dir", str(output), "--update", str(update)]
        refreshed = subprocess.run(command + ["--candidates", str(candidates)], capture_output=True, text=True)
        self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
        source = json.loads((output / "coordinator/source.json").read_text())
        blind = json.loads((output / "blind/target.rev1.json").read_text())
        self.assertEqual(source["entries"][0]["target_units"], {"": "%lld zile"})
        self.assertEqual(source["entries"][0]["variations"], {})
        self.assertEqual(blind["strings"][0]["text"], "%lld zile")
        self.assertIsNone(blind["strings"][0]["plural"])
        self.assertNotIn({"id": "s01", "marker": "plural"}, blind["markers"])
        preserved = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(preserved.returncode, 0, preserved.stderr)
        self.assertEqual(json.loads((output / "coordinator/source.json").read_text())["entries"][0]["target_units"],
                         {"": "%lld zile"})

    def test_context_casing_invalidates_when_source_comment_changes(self):
        main, neighbour, _ = self.context_fixture()
        update = self.directory / "context.json"
        update.write_text(json.dumps({"context_entries": [{"key": neighbour, "casing": {
            "status": "confirmed", "role": "section_heading", "position": "standalone",
            "style": "sentence", "owner": "catalog", "protected_terms": [], "exceptions": []}}]}))
        result = self.packet([main], "--update", str(update))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(self.catalog.read_text())
        data["strings"][neighbour]["comment"] = "Changed display context"
        self.catalog.write_text(json.dumps(data))
        output = self.directory / "b01"
        stale = subprocess.run([sys.executable, str(ROOT / "scripts/build_context_packet.py"),
                                "--locale", "ro", "--out-dir", str(output), "--update", str(update)],
                               capture_output=True, text=True)
        self.assertNotEqual(stale.returncode, 0)
        self.assertIn("source changed for context", stale.stderr)
        rebuilt = self.packet([main], "--rev", "2")
        self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
        source = json.loads((output / "coordinator/source.json").read_text())
        casing = next(row["casing"] for row in source["context_entries"] if row["key"] == neighbour)
        self.assertEqual(casing["status"], "needs_review")
        packet = json.loads((output / "blind/target.rev2.json").read_text())
        self.assertEqual(packet["neighbours"][0]["casing"]["position"], "unknown")

    def test_initial_casing_is_provisional_and_non_ui_is_explicit(self):
        data = json.loads(self.catalog.read_text())
        keys = ["test.button", "test.quote", "test.user"]
        for key, comment, text in zip(keys, ["Button", "Attributed quotation", "User-written text"],
                                      ["ÎNCEPE", "Un gând", "Cuvintele mele"]):
            data["strings"][key] = {"comment": comment, "localizations": {
                "en": {"stringUnit": {"state": "translated", "value": "Source phrase " + key}},
                "ro": {"stringUnit": {"state": "needs_review", "value": text}},
            }}
        data["strings"][keys[0]]["localizations"]["en"]["stringUnit"]["value"] = "START"
        self.catalog.write_text(json.dumps(data))
        result = self.packet(keys)
        self.assertEqual(result.returncode, 0, result.stderr)
        source = json.loads((self.directory / "b01/coordinator/source.json").read_text())
        blind = json.loads((self.directory / "b01/blind/target.rev1.json").read_text())
        casing = source["entries"][0]["casing"]
        self.assertEqual(casing["status"], "needs_review")
        self.assertEqual(casing["role"], "button")
        self.assertEqual(casing["style"], "unknown")
        self.assertEqual(casing["owner"], "unknown")
        self.assertTrue(all(row["casing"]["status"] == "not_applicable" for row in blind["strings"][1:]))
        self.assertTrue(all("evidence" not in row["casing"] for row in blind["strings"]))
        self.assertNotIn("uppercase by design", json.dumps(blind))
        self.assertIn({"id": "s03", "marker": "user content"}, blind["markers"])
        retained = [row for row in blind["markers"] if row["id"] != "s03"]
        update = self.directory / "context.json"
        update.write_text(json.dumps({"entries": [{"key": "test.user", "kind": "functional",
            "casing": {"status": "confirmed", "role": "value_label", "position": "standalone",
                       "style": "sentence", "owner": "catalog", "protected_terms": [], "exceptions": []}}]}))
        result = subprocess.run([sys.executable, str(ROOT / "scripts/build_context_packet.py"),
                                 "--locale", "ro", "--out-dir", str(self.directory / "b01"),
                                 "--update", str(update)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        updated = json.loads((self.directory / "b01/blind/target.rev1.json").read_text())
        self.assertEqual(updated["markers"], retained)
        rebuilt = self.packet(keys, "--rev", "2")
        self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
        carried = json.loads((self.directory / "b01/blind/target.rev2.json").read_text())
        self.assertEqual(carried["markers"], retained)
        self.assertEqual(carried["strings"][2]["casing"]["status"], "confirmed")

    def test_casing_context_survives_unchanged_source_without_leaking_rationale(self):
        keys = ["widgets.focusRing.firstRun", "widgets.focusRing.a11y.money"]
        casing = {"status": "confirmed", "role": "button", "position": "standalone", "style": "sentence",
                  "owner": "catalog", "protected_terms": ["Moneyfesting"],
                  "exceptions": [{"text": "USD", "reason": "Source rationale: quoted USD code"}],
                  "equivalent_group": "widgets.focusRing.buttons",
                  "transform": {"operation": "none", "file": "/source/FocusRing.swift", "line": 12,
                                "rendered_value": "Source rationale", "render_status": "pass", "render_locale": "ro"},
                  "units": {"": {"style": "lowercase", "evidence": "Source rationale"}},
                  "evidence": "Source rationale from widgets.focusRing.firstRun"}
        fragment = {**casing, "role": "continuation", "position": "continuation", "style": "lowercase"}
        update = self.directory / "context.json"
        update.write_text(json.dumps({"entries": [{"key": keys[0], "casing": casing},
                                                   {"key": keys[1], "casing": fragment}]}))
        first = self.packet(keys, "--update", str(update))
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.packet(keys, "--rev", "2")
        self.assertEqual(second.returncode, 0, second.stderr)
        source = json.loads((self.directory / "b01/coordinator/source.json").read_text())
        self.assertEqual(source["entries"][0]["casing"], casing)
        packet = json.loads((self.directory / "b01/blind/target.rev2.json").read_text())
        first, second = [row["casing"] for row in packet["strings"]]
        self.assertEqual(first["protected_terms"], ["Moneyfesting"])
        self.assertEqual(first["exceptions"], ["USD"])
        self.assertEqual(first["equivalent_group"], second["equivalent_group"])
        self.assertEqual(first["equivalent_group"], "g01")
        self.assertEqual(first["transform"], {"operation": "none"})
        self.assertEqual(first["units"]["u01"]["style"], "lowercase")
        self.assertEqual(first["units"]["u01"]["protected_terms"], ["Moneyfesting"])
        self.assertEqual(source["entries"][0]["casing_unit_ids"], {"": "u01"})
        self.assertEqual(packet["strings"][0]["units"][0]["text"], source["entries"][0]["existing_target"])
        self.assertEqual(second["position"], "continuation")
        self.assertEqual(second["style"], "lowercase")
        for forbidden in ("Source rationale", "widgets.focusRing.buttons", "FocusRing.swift", "reason", "evidence", "substitutions"):
            self.assertNotIn(forbidden, json.dumps(packet))
        data = json.loads(self.catalog.read_text())
        data["strings"][keys[0]]["comment"] = "Changed context"
        self.catalog.write_text(json.dumps(data))
        third = self.packet(keys, "--rev", "3")
        self.assertEqual(third.returncode, 0, third.stderr)
        source = json.loads((self.directory / "b01/coordinator/source.json").read_text())
        self.assertEqual(source["entries"][0]["casing"]["status"], "needs_review")
        self.assertEqual(source["entries"][1]["casing"], fragment)

    def test_free_text_casing_fields_cannot_use_structural_vocabulary_to_leak_source(self):
        key = "test.title"
        data = json.loads(self.catalog.read_text())
        data["strings"] = {key: {"comment": "Heading", "localizations": {
            "en": {"stringUnit": {"state": "translated", "value": "Title"}},
            "ro": {"stringUnit": {"state": "needs_review", "value": "Titlu"}},
        }}}
        self.catalog.write_text(json.dumps(data))
        casing = {"status": "confirmed", "role": "screen_title", "position": "standalone", "style": "sentence",
                  "owner": "catalog", "protected_terms": [], "exceptions": []}
        injections = [
            {"casing": {**casing, "protected_terms": ["Title"]}},
            {"casing": {**casing, "exceptions": [{"text": "Title", "reason": "A misleading exception"}]}},
            {"target_context": {"state": "Title"}},
            {"placeholders": [{"token": "%@", "samples": ["Title"]}]},
            {"fit": {"note": "This Title leaked"}},
        ]
        update = self.directory / "context.json"
        for fields in injections:
            with self.subTest(fields=fields):
                update.write_text(json.dumps({"entries": [{"key": key, **fields}]}))
                result = self.packet([key], "--update", str(update))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("contaminated", result.stderr)

    def test_update_rejects_stale_source_casing_context(self):
        key = "widgets.focusRing.firstRun"
        first = self.packet([key])
        self.assertEqual(first.returncode, 0, first.stderr)
        data = json.loads(self.catalog.read_text())
        data["strings"][key]["comment"] = "Changed display role"
        self.catalog.write_text(json.dumps(data))
        update = self.directory / "context.json"
        update.write_text(json.dumps({"entries": []}))
        result = subprocess.run([
            sys.executable, str(ROOT / "scripts/build_context_packet.py"), "--locale", "ro",
            "--out-dir", str(self.directory / "b01"), "--update", str(update),
        ], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source changed", result.stderr)

    def test_nested_unit_casing_has_opaque_ids_and_exact_target_branch_text(self):
        key = "test.count"
        data = json.loads(self.catalog.read_text())
        data["strings"] = {key: {"comment": "Count label", "localizations": {}}}
        for locale, value in (("en", "%lld completed day"), ("ro", "%lld zi")):
            data["strings"][key]["localizations"][locale] = {
                "stringUnit": {"state": "needs_review", "value": "Zile: %#@goalDays@" if locale == "ro" else "Days: %#@goalDays@"},
                "substitutions": {"goalDays": {"argNum": 1, "formatSpecifier": "lld", "variations": {"plural": {
                    "one": {"stringUnit": {"state": "needs_review", "value": value}},
                }}}},
            }
        self.catalog.write_text(json.dumps(data))
        result = self.packet([key])
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = json.loads((self.directory / "b01/blind/target.rev1.json").read_text())
        row = packet["strings"][0]
        self.assertEqual(row["casing"]["units"]["u01"]["status"], "needs_review")
        self.assertEqual(row["units"], [{"id": "u01", "text": "%lld zi"}])
        self.assertNotIn("substitution:goalDays", json.dumps(packet))
        source = json.loads((self.directory / "b01/coordinator/source.json").read_text())
        self.assertEqual(source["entries"][0]["casing_unit_ids"], {"substitution:goalDays/plural:one": "u01"})
        context = {"status": "confirmed", "role": "value_label", "position": "template", "style": "sentence",
                   "owner": "catalog", "protected_terms": [], "exceptions": [], "evidence": "Verified composed label",
                   "units": {"substitution:goalDays/plural:one": {
                       "role": "continuation", "position": "continuation", "style": "lowercase"}}}
        update = self.directory / "context.json"
        update.write_text(json.dumps({"entries": [{"key": key, "casing": context}]}))
        result = self.packet([key], "--update", str(update))
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = json.loads((self.directory / "b01/blind/target.rev1.json").read_text())
        self.assertEqual(packet["strings"][0]["casing"]["units"]["u01"]["status"], "confirmed")
        data["strings"][key]["localizations"]["en"]["substitutions"]["goalDays"]["variations"]["plural"]["one"]["stringUnit"]["value"] = "%lld fully completed day"
        self.catalog.write_text(json.dumps(data))
        result = self.packet([key], "--rev", "2")
        self.assertEqual(result.returncode, 0, result.stderr)
        source = json.loads((self.directory / "b01/coordinator/source.json").read_text())
        self.assertEqual(source["entries"][0]["casing"]["status"], "needs_review")
        candidates = self.directory / "candidates.json"
        candidates.write_text(json.dumps({"locale": "ro", "rev": 2, "entries": [
            {"key": key, "value": "Zile: %#@goalDays@", "units": {"substitution:goalDays/plural:one": "%lld ziua"}},
        ]}))
        result = self.packet([key], "--candidates", str(candidates))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot bind", result.stderr)
        data["strings"][key]["localizations"]["ro"]["substitutions"]["goalDays"]["variations"]["plural"]["one"]["stringUnit"]["value"] = "%lld fully completed day"
        self.catalog.write_text(json.dumps(data))
        result = self.packet([key])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contaminated", result.stderr)

    def test_device_only_variations_are_included_for_blind_review(self):
        key = "test.device"
        data = {"strings": {key: {"comment": "Device-specific button", "localizations": {
            locale: {"variations": {"device": {"iphone": {"variations": {"plural": {
                "one": {"stringUnit": {"state": "needs_review", "value": text}},
            }}}}}} for locale, text in (("en", "Start a session"), ("ro", "Începe o sesiune"))
        }}}}
        self.catalog.write_text(json.dumps(data))
        result = self.packet([key])
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = json.loads((self.directory / "b01/blind/target.rev1.json").read_text())
        self.assertEqual(len(packet["strings"]), 1)
        self.assertEqual(packet["strings"][0]["units"], [{"id": "u01", "text": "Începe o sesiune"}])
        self.assertNotIn("no target yet", json.dumps(packet))

    def test_shared_key_keeps_distinct_display_occurrences_without_source_leaks(self):
        key = "paywall.plan.annual.title"
        data = {"strings": {key: {"comment": "Shared plan title", "localizations": {
            locale: {"stringUnit": {"state": "needs_review", "value": text}}
            for locale, text in (("en", "Annual plan"), ("ro", "Plan anual"))
        }}}}
        self.catalog.write_text(json.dumps(data))
        casing = {"status": "confirmed", "role": "value_label", "position": "standalone", "style": "sentence",
                  "owner": "catalog", "protected_terms": ["Moneyfesting"], "exceptions": [],
                  "units": {"": {"role": "caption", "protected_terms": ["USD"]}},
                  "evidence": "singleOfferCard source explanation", "occurrences": [{
                      "id": "planCell", "role": "compact_heading", "style": "uppercase", "owner": "view",
                      "evidence": "planCell source explanation", "transform": {
                          "operation": "uppercase", "file": "OnboardingSubscriptionPaywallView.swift", "line": 420,
                          "rendered_value": "PLAN ANUAL", "render_status": "pass", "render_locale": "ro",
                      },
                  }]}
        update = self.directory / "context.json"
        update.write_text(json.dumps({"entries": [{"key": key, "casing": casing}]}))
        result = self.packet([key], "--update", str(update))
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.packet([key], "--rev", "2")
        self.assertEqual(result.returncode, 0, result.stderr)
        source = json.loads((self.directory / "b01/coordinator/source.json").read_text())
        self.assertEqual(source["entries"][0]["casing"], casing)
        self.assertEqual(source["entries"][0]["casing_occurrence_ids"], {"planCell": "o01"})
        packet = json.loads((self.directory / "b01/blind/target.rev2.json").read_text())
        row = packet["strings"][0]
        self.assertEqual(row["text"], "Plan anual")
        self.assertEqual(row["casing"]["style"], "sentence")
        occurrence = row["casing"]["occurrences"][0]
        self.assertEqual(occurrence["id"], "o01")
        self.assertEqual(occurrence["style"], "uppercase")
        self.assertEqual(occurrence["owner"], "view")
        self.assertEqual(occurrence["protected_terms"], ["Moneyfesting"])
        self.assertEqual(occurrence["transform"], {"operation": "uppercase"})
        unit = row["casing"]["units"]["u01"]
        self.assertEqual(unit["role"], "caption")
        self.assertEqual(unit["occurrences"][0]["role"], "compact_heading")
        self.assertEqual(unit["occurrences"][0]["protected_terms"], ["USD"])
        self.assertEqual(unit["occurrences"][0]["owner"], "view")
        for forbidden in (key, "Annual plan", "singleOfferCard", "planCell", "source explanation", "View.swift", "rendered_value"):
            self.assertNotIn(forbidden, json.dumps(packet))


if __name__ == "__main__":
    unittest.main()
