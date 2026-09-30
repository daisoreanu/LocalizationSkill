import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from corpus_inventory import build_inventory, content_hash


def quote(record_id, language="en", **fields):
    record = {"id": record_id, "category": "motivation", "text": record_id,
              "language": language, "verification": "curated"}
    record.update(fields)
    return record


class CorpusInventoryTests(unittest.TestCase):
    def inventory(self, records, locales=None):
        return build_inventory({"schemaVersion": 2, "quotes": records}, locales or ["en", "ro", "hu"])

    def test_union_includes_records_only_in_opposite_locales(self):
        inventory = self.inventory([quote("ro-only", "ro"), quote("hu-only", "hu")])
        self.assertEqual(set(inventory["records"]), {"ro-only", "hu-only"})
        self.assertEqual(len(inventory["groups"]), 2)
        self.assertEqual({group["source_id"] for group in inventory["groups"]}, {"ro-only", "hu-only"})
        self.assertTrue(all(group["eligible"] for group in inventory["groups"]))

    def test_near_synonyms_do_not_join(self):
        records = [quote("one", text="Keep your focus."), quote("two", text="Stay focused.")]
        self.assertEqual(len(self.inventory(records)["groups"]), 2)

    def test_pair_and_translation_link_preserve_metadata(self):
        original = quote("en", pairId="a-1", custom={"owner": "accepted"})
        target = quote("ro", "ro", pairId="a-1", translationOf="en",
                       translatedFrom="en", reviewState="pending_owner_review")
        inventory = self.inventory([original, target])
        group = inventory["groups"][0]
        self.assertEqual(group["id"], "pair:motivation:a-1")
        self.assertEqual(group["source_id"], "en")
        self.assertEqual(group["members"], {"en": ["en"], "ro": ["ro"]})
        self.assertEqual(inventory["records"], {"en": original, "ro": target})
        self.assertEqual(group["missing_locales"], ["hu"])

    def test_group_id_is_stable_after_translation_added(self):
        original = quote("source")
        before = self.inventory([original])["groups"][0]["id"]
        after = self.inventory([original, quote("target", "ro", translationOf="source")])["groups"][0]["id"]
        self.assertEqual(before, after)
        with_new_pair = self.inventory([original, quote("target", "ro", translationOf="source", pairId="new-pair")])
        self.assertEqual(before, with_new_pair["groups"][0]["id"])

    def test_canonical_reference_matches_exact_category_and_span(self):
        source = lambda reference: {"canonicalReference": reference, "verifiedBy": "canonical_corpus"}
        records = [quote("en", category="religion", source=source("Isaiah 3:1")),
                   quote("ro", "ro", category="religion", source=source("Isaiah 3:1")),
                   quote("different", "hu", category="religion", source=source("Isaiah 3:1-2"))]
        inventory = self.inventory(records)
        self.assertEqual(len(inventory["groups"]), 2)
        joined = next(group for group in inventory["groups"] if "en" in group["members"])
        self.assertEqual(joined["members"]["ro"], ["ro"])
        self.assertTrue(any(item["code"] == "unknown_original_language" for item in joined["issues"]))

    def test_unverified_reference_cannot_claim_counterpart(self):
        records = [quote("one", source={"canonicalReference": "A 1:1"}),
                   quote("two", "ro", source={"canonicalReference": "A 1:1"})]
        inventory = self.inventory(records)
        self.assertEqual(len(inventory["groups"]), 2)
        self.assertEqual(len({group["id"] for group in inventory["groups"]}), 2)
        self.assertTrue(all(not group["eligible"] for group in inventory["groups"]))

    def test_multiple_translation_roots_block_english_fallback(self):
        records = [quote("ro-root", "ro", pairId="p"),
                   quote("en-child", "en", pairId="p", translationOf="ro-root"),
                   quote("de-root", "de", pairId="p"),
                   quote("hu-child", "hu", pairId="p", translationOf="de-root")]
        group = self.inventory(records, ["en", "ro", "hu", "es"])["groups"][0]
        self.assertFalse(group["eligible"])
        self.assertIn("ambiguous_source", {item["code"] for item in group["issues"]})

    def test_ambiguous_metadata_never_dedupes(self):
        records = [quote("one", pairId="a-1"), quote("two", pairId="a-1")]
        inventory = self.inventory(records)
        group = inventory["groups"][0]
        self.assertEqual(group["members"]["en"], ["one", "two"])
        self.assertFalse(group["eligible"])
        self.assertIn("ambiguous_locale", {item["code"] for item in group["issues"]})
        self.assertEqual(len(inventory["records"]), 2)

    def test_broken_links_and_cycles_are_held(self):
        records = [quote("missing", translationOf="absent"),
                   quote("a", translationOf="b"), quote("b", "ro", translationOf="a")]
        inventory = self.inventory(records)
        self.assertEqual(len(inventory["records"]), 3)
        self.assertTrue(all(not group["eligible"] for group in inventory["groups"]))
        self.assertIn("missing_translation_target", {item["code"] for item in inventory["issues"]})
        self.assertIn("translation_cycle", {item["code"] for item in inventory["issues"]})

    def test_cross_category_link_is_held_without_joining(self):
        records = [quote("source"), quote("translated", "ro", category="religion", translationOf="source")]
        inventory = self.inventory(records)
        self.assertEqual(len(inventory["groups"]), 2)
        target_group = next(group for group in inventory["groups"] if "translated" in group["members"].get("ro", []))
        self.assertFalse(target_group["eligible"])
        self.assertIn("cross_category_translation", {item["code"] for item in target_group["issues"]})
        self.assertTrue(all(not group["eligible"] for group in inventory["groups"]))

    def test_duplicate_ids_raise_without_mutating_input(self):
        records = [quote("same"), quote("same", "ro")]
        original = json.loads(json.dumps(records))
        with self.assertRaisesRegex(ValueError, "duplicate quote id"):
            self.inventory(records)
        self.assertEqual(records, original)

    def test_excluded_unknown_and_user_records_are_retained_but_held(self):
        records = [quote("rejected", verification="rejected"),
                   quote("unknown", verification="uncertain"),
                   quote("user", userCreated=True),
                   quote("external", "es", verification="supplied_unverified")]
        inventory = self.inventory(records)
        self.assertEqual(len(inventory["records"]), 4)
        eligibility = {group["source_id"]: group["eligible"] for group in inventory["groups"]}
        self.assertEqual(eligibility, {"rejected": False, "unknown": False,
                                       "user": False, "external": True})

    def test_missing_language_defaults_only_in_inventory(self):
        record = quote("legacy")
        record.pop("language")
        inventory = self.inventory([record])
        self.assertNotIn("language", inventory["records"]["legacy"])
        group = inventory["groups"][0]
        self.assertEqual(group["members"], {"en": ["legacy"]})
        self.assertTrue(group["eligible"])
        self.assertIn("assumed_english", {item["code"] for item in group["issues"]})

    def test_malformed_language_and_text_remain_visible_but_held(self):
        record = quote("bad", language="English", text="")
        inventory = self.inventory([record])
        group = inventory["groups"][0]
        self.assertEqual(group["members"], {"<invalid>": ["bad"]})
        self.assertFalse(group["eligible"])
        self.assertEqual({item["code"] for item in group["issues"]},
                         {"invalid_language", "invalid_text"})
        null_language = self.inventory([quote("null", language=None)])["groups"][0]
        self.assertFalse(null_language["eligible"])
        self.assertEqual(null_language["members"], {"<invalid>": ["null"]})

    def test_hash_covers_envelope_and_cli_never_overwrites_input(self):
        corpus = {"schemaVersion": 2, "generated": "first", "quotes": [quote("a")]}
        self.assertNotEqual(content_hash(corpus), content_hash({**corpus, "generated": "second"}))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.json"
            path.write_text(json.dumps(corpus), encoding="utf-8")
            before = path.read_bytes()
            result = subprocess.run([sys.executable, str(ROOT / "scripts/corpus_inventory.py"),
                                     "--corpus", str(path), "--locales", "en,ro", "--out", str(path)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(path.read_bytes(), before)
            output = Path(directory) / "inventory.json"
            result = subprocess.run([sys.executable, str(ROOT / "scripts/corpus_inventory.py"),
                                     "--corpus", str(path), "--locales", "en,ro", "--out", str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text())["corpus_hash"], content_hash(corpus))
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
