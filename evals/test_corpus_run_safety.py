import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/corpus_run.py"


class CorpusRunSafetyTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.directory = Path(scratch.name)
        self.corpus = self.directory / "corpus.json"
        self.context = self.directory / "context.txt"
        self.context.write_text("Preserve every source record and its distinctions.\n")
        self.run = self.directory / "run"

    def write_json(self, path, value):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        return path

    def command(self, *arguments, success=True):
        result = subprocess.run(
            [sys.executable, str(RUNNER), *map(str, arguments)],
            capture_output=True, text=True,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def init(self, records, locales="en,ro,hu", success=True):
        self.write_json(self.corpus, {"schemaVersion": 2, "custom": {"retained": True},
                                      "quotes": records})
        return self.command("init", "--corpus", self.corpus, "--run-dir", self.run,
                            "--locales", locales, "--context", self.context,
                            success=success)

    def record(self, record_id, language="en", text="I welcome abundance.", **metadata):
        return {"id": record_id, "language": language, "category": "affirmations",
                "text": text, "verification": "authored", **metadata}

    def run_command(self, *arguments, success=True):
        return self.command(*arguments, "--run-dir", self.run, success=success)

    def batch(self, locale="ro", size=20, revise=False):
        options = ["--revise"] if revise else []
        result = self.run_command("batch", "--locale", locale, "--size", size, *options)
        dispatch = json.loads(result.stdout)
        return dispatch["batch"], json.loads(Path(dispatch["packet"]).read_text())

    def candidates(self, packet, text="Primesc belșugul."):
        return {"batch_hash": packet["batch_hash"],
                "translator": {"id": "translator", "model": "test", "effort": "test"},
                "entries": [{"id": entry["id"], "text": f"{text} {index}"}
                            for index, entry in enumerate(packet["entries"])]}

    def ingest(self, batch, candidates, success=True):
        path = self.write_json(self.directory / "candidates.json", candidates)
        return self.run_command("ingest", "--batch", batch, "--candidates", path,
                                success=success)

    def review_payload(self, batch, role, notes="Checked the supplied record."):
        result = self.run_command("review-packet", "--batch", batch, "--role", role)
        dispatch = json.loads(result.stdout)
        packet = json.loads(Path(dispatch["packet"]).read_text())
        return {"packet_hash": dispatch["packet_hash"],
                "reviewer": {"id": role, "model": "test", "effort": "test"},
                "entries": [{"id": entry["id"], "verdict": "pass", "notes": notes}
                            for entry in packet["entries"]]}

    def review(self, batch, role, payload=None, success=True):
        if payload is None:
            payload = self.review_payload(batch, role)
        path = self.write_json(self.directory / f"{role}-review.json", payload)
        return self.run_command("review", "--batch", batch, "--role", role,
                                "--input", path, success=success)

    def prepare_reviewed(self, records, locale="ro", size=20):
        self.init(records)
        batch, packet = self.batch(locale, size)
        candidate = self.candidates(packet)
        self.ingest(batch, candidate)
        for role in ("editor", "fidelity", "adjudicator"):
            self.review(batch, role)
        return batch, candidate

    def export(self, success=True, categories="affirmations", locales="ro"):
        return self.run_command("export", "--out", self.directory / "staged.json",
                                "--categories", categories, "--locales", locales,
                                success=success)

    def test_duplicate_ids_rejected_without_modifying_input(self):
        records = [self.record("same"), self.record("same", "ro")]
        self.init(records, success=False)
        self.assertEqual(json.loads(self.corpus.read_text())["quotes"], records)

    def test_init_does_not_rewrite_original_json(self):
        records = [self.record("en-first"), self.record("hu-only", "hu", "Megőrzött szöveg.",
                   source={"unknown": ["retain", 7]}, verification="mystery_status")]
        original = {"quotes": records, "custom": {"order": [3, 1, 2]}}
        self.corpus.write_text(json.dumps(original, ensure_ascii=False, separators=(",", ":")))
        before = self.corpus.read_bytes()
        self.command("init", "--corpus", self.corpus, "--run-dir", self.run,
                     "--locales", "en,ro,hu", "--context", self.context)
        self.assertEqual(self.corpus.read_bytes(), before)

    def test_bad_candidate_id_sets_are_atomic(self):
        self.init([self.record("first"), self.record("second", text="I welcome possibility.")])
        batch, packet = self.batch()
        candidate = self.candidates(packet)
        manifest = self.run / "manifest.json"
        before = manifest.read_bytes()
        variants = [candidate["entries"][:1], candidate["entries"] * 2,
                    candidate["entries"] + [{"id": "unexpected", "text": "Text"}]]
        for entries in variants:
            with self.subTest(entries=entries):
                self.ingest(batch, {**candidate, "entries": entries}, success=False)
                self.assertEqual(manifest.read_bytes(), before)

    def test_candidate_metadata_cannot_upgrade_verification(self):
        self.init([self.record("first")])
        batch, packet = self.batch()
        candidate = self.candidates(packet)
        candidate["entries"][0]["verification"] = "sourced"
        before = (self.run / "manifest.json").read_bytes()
        self.ingest(batch, candidate, success=False)
        self.assertEqual((self.run / "manifest.json").read_bytes(), before)

    def test_null_optional_metadata_can_be_translated(self):
        self.init([self.record("first", source=None, attribution=None)])
        batch, packet = self.batch()
        self.ingest(batch, self.candidates(packet))
        self.assertEqual(packet["entries"][0]["kind"], "authored")

    def test_successful_retry_preserves_reviews_and_export_preserves_originals(self):
        records = [self.record("first", pairId="pair", source={"opaque": [1, {"a": None}]}),
                   self.record("unrelated", "hu", "Ezt megőrizzük.",
                               category="retained", verification="unknown")]
        batch, candidate = self.prepare_reviewed(records)
        before = (self.run / "manifest.json").read_bytes()
        self.ingest(batch, candidate)
        self.assertEqual((self.run / "manifest.json").read_bytes(), before)
        self.export()
        staged = json.loads((self.directory / "staged.json").read_text())
        self.assertEqual(staged["quotes"][:len(records)], records)
        self.assertEqual(staged["custom"], {"retained": True})
        self.assertEqual(len(staged["quotes"]), len(records) + 1)
        self.assertEqual(staged["quotes"][-1]["reviewState"], "pending_owner_review")
        self.assertEqual(json.loads(self.corpus.read_text())["quotes"], records)

    def test_partial_category_cannot_export(self):
        self.prepare_reviewed([self.record("first"), self.record("second", text="Distinct line.")], size=1)
        self.export(success=False)
        self.assertFalse((self.directory / "staged.json").exists())

    def test_reverse_language_original_generates_missing_english(self):
        original = self.record("ro-original", "ro", "Îmi păstrez vocea.")
        self.prepare_reviewed([original], locale="en")
        self.export(locales="en")
        staged = json.loads((self.directory / "staged.json").read_text())["quotes"]
        self.assertEqual(staged[0], original)
        self.assertEqual(staged[1]["language"], "en")
        self.assertEqual(staged[1]["translationOf"], "ro-original")
        self.assertEqual(staged[1]["translatedFrom"], "ro")

    def test_source_changed_on_disk_blocks_export_without_sync(self):
        self.prepare_reviewed([self.record("first")])
        current = json.loads(self.corpus.read_text())
        current["quotes"][0]["text"] = "The source has changed."
        self.write_json(self.corpus, current)
        self.export(success=False)
        self.assertFalse((self.directory / "staged.json").exists())

    def test_changed_candidate_rejects_old_review(self):
        self.init([self.record("first")])
        batch, packet = self.batch()
        candidate = self.candidates(packet)
        self.ingest(batch, candidate)
        old_review = self.review_payload(batch, "editor")
        candidate["entries"][0]["text"] = "Îmi schimb formularea."
        self.ingest(batch, candidate, success=False)
        revised_batch, revised_packet = self.batch(revise=True)
        candidate["batch_hash"] = revised_packet["batch_hash"]
        self.ingest(revised_batch, candidate)
        self.review(revised_batch, "editor", old_review, success=False)
        self.ingest(batch, self.candidates(packet), success=False)
        self.review(batch, "editor", old_review, success=False)
        self.review(batch, "editor")

    def test_repeated_editor_review_invalidates_old_adjudicator_packet(self):
        self.init([self.record("first")])
        batch, packet = self.batch()
        self.ingest(batch, self.candidates(packet))
        self.review(batch, "editor")
        self.review(batch, "fidelity")
        old_adjudication = self.review_payload(batch, "adjudicator")
        changed_editor = self.review_payload(batch, "editor", notes="New editorial finding resolved differently.")
        self.review(batch, "editor", changed_editor)
        self.review(batch, "adjudicator", old_adjudication, success=False)

    def test_same_target_after_context_sync_cannot_reuse_blind_review(self):
        self.init([self.record("first")])
        old_batch, old_packet = self.batch()
        self.ingest(old_batch, self.candidates(old_packet))
        old_review = self.review_payload(old_batch, "editor")
        self.context.write_text("The revised policy changes the target register.\n")
        self.run_command("sync")
        new_batch, new_packet = self.batch()
        self.ingest(new_batch, self.candidates(new_packet))
        new_review = self.review_payload(new_batch, "editor")
        self.assertNotEqual(old_review["packet_hash"], new_review["packet_hash"])
        self.review(new_batch, "editor", old_review, success=False)

    def test_declared_translator_cannot_record_editor_review(self):
        self.init([self.record("first")])
        batch, packet = self.batch()
        self.ingest(batch, self.candidates(packet))
        payload = self.review_payload(batch, "editor")
        payload["reviewer"]["id"] = "translator"
        self.review(batch, "editor", payload, success=False)

    def test_unknown_eligibility_cannot_silently_complete_category(self):
        self.prepare_reviewed([self.record("first"), self.record("unclassified", "hu",
                              "Megőrzendő szöveg.", verification="future_status")])
        self.export(success=False)
        self.assertFalse((self.directory / "staged.json").exists())

    def test_distinct_sources_cannot_silently_collapse_to_one_target(self):
        records = [self.record("first"), self.record("second", text="I welcome possibility.")]
        self.init(records)
        batch, packet = self.batch()
        candidate = self.candidates(packet)
        for entry in candidate["entries"]:
            entry["text"] = "Primesc belșugul."
        self.ingest(batch, candidate)
        for role in ("editor", "fidelity", "adjudicator"):
            self.review(batch, role)
        self.export(success=False)
        status = json.loads(self.run_command("status").stdout)
        collision = status["target_collisions"][0]["id"]
        self.run_command("acknowledge-collision", "--collision", collision, "--reason", " ", success=False)
        self.run_command("acknowledge-collision", "--collision", collision,
                         "--reason", "Keep both original identities while the wording ambiguity is recorded.")
        self.export()
        staged = json.loads((self.directory / "staged.json").read_text())["quotes"]
        self.assertEqual(staged[:2], records)
        self.assertEqual(len(staged), 4)
        self.assertEqual(len({row["id"] for row in staged}), 4)

    def test_pending_batches_reserve_their_records(self):
        self.init([self.record("first"), self.record("second", text="Distinct line.")])
        _, first = self.batch(size=1)
        _, second = self.batch(size=1)
        self.assertNotEqual(first["entries"][0]["source"]["id"], second["entries"][0]["source"]["id"])
        self.assertIsNone(json.loads(self.run_command("batch", "--locale", "ro").stdout)["batch"])

    def test_sync_rejects_removed_original_without_replacing_manifest(self):
        self.init([self.record("first"), self.record("second", "hu", "Megőrzött sor.")])
        manifest = self.run / "manifest.json"
        before = manifest.read_bytes()
        current = json.loads(self.corpus.read_text())
        current["quotes"].pop()
        self.write_json(self.corpus, current)
        self.run_command("sync", success=False)
        self.assertEqual(manifest.read_bytes(), before)

    def test_blind_packet_excludes_source_identity_and_translator_notes(self):
        self.init([self.record("source-secret-id", text="SOURCE_SECRET_SENTENCE",
                   attribution={"name": "SOURCE_SECRET_AUTHOR"}, verification="supplied_unverified")])
        batch, packet = self.batch()
        candidate = self.candidates(packet)
        candidate["entries"][0]["notes"] = "TRANSLATOR_SECRET_REASONING"
        self.ingest(batch, candidate)
        dispatch = json.loads(self.run_command("review-packet", "--batch", batch,
                              "--role", "editor").stdout)
        blind = Path(dispatch["packet"]).read_text()
        for forbidden in ("source-secret-id", "SOURCE_SECRET_SENTENCE", "SOURCE_SECRET_AUTHOR",
                          "TRANSLATOR_SECRET_REASONING", str(self.corpus), str(self.context)):
            self.assertNotIn(forbidden, blind)

    def test_scripture_paraphrase_cannot_export_even_with_all_reviews(self):
        source = self.record("verse", text="Full original verse.", category="religion",
                             verification="sourced", source={"canonicalReference": "John 1:1",
                             "verifiedBy": "canonical_corpus"})
        self.write_json(self.corpus, {"quotes": [source]})
        canonical = self.write_json(self.directory / "canonical.json", {"entries": [{
            "locale": "ro", "reference": "John 1:1", "edition": "Fixture published edition",
            "text": "Exact full verse.", "source_url": "https://example.org/edition",
            "corpus_sha256": "a" * 64, "complete_verses": True,
        }]})
        self.run_command("init", "--corpus", self.corpus, "--locales", "en,ro",
                         "--context", self.context, "--canonical", canonical)
        batch, packet = self.batch()
        self.ingest(batch, self.candidates(packet, text="A fluent paraphrase."))
        for role in ("editor", "fidelity", "adjudicator"):
            self.review(batch, role)
        self.export(categories="religion", success=False)

    def test_new_attributed_text_does_not_inherit_original_verification(self):
        original = self.record("quote", attribution={"name": "Author"}, verification="sourced",
                               source={"title": "Work", "verifiedBy": "primary_edition",
                                       "url": "https://example.org/original"})
        self.prepare_reviewed([original])
        self.export()
        staged = json.loads((self.directory / "staged.json").read_text())["quotes"]
        self.assertEqual(staged[0], original)
        self.assertNotEqual(staged[1].get("verification"), "sourced")
        self.assertNotEqual(staged[1].get("source", {}).get("verifiedBy"), "primary_edition")


if __name__ == "__main__":
    unittest.main()
