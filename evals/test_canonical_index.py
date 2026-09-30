import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_canonical_index.py"
sys.path.insert(0, str(ROOT / "scripts"))
import build_canonical_index as builder  # noqa: E402


class CanonicalIndexTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.directory = Path(scratch.name)
        self.source = self.directory / "karoli.osis.xml"
        self.metadata = self.directory / "source.json"
        self.output = self.directory / "index.json"
        self.write_osis("""
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
  <verse osisID="Prov.3.5">Bízzál az Úrban <note>translator note</note> teljes szívedből!</verse>
  <verse osisID="Prov.3.6">Minden te utaidban<hi type="italic"> megismered</hi> őt.</verse>
  <verse osisID="Ps.23.1">Az Úr az én pásztorom; nem szűkölködöm.</verse>
</osis>
""")

    def write_osis(self, text):
        self.source.write_text(text.strip(), encoding="utf-8")
        self.write_metadata()

    def write_metadata(self, **changes):
        metadata = {
            "locale": "hu", "edition": builder.EDITION,
            "file": str(self.source),
            "sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "source_url": builder.PINNED_SOURCE_URL,
            **changes,
        }
        self.metadata.write_text(json.dumps(metadata))

    def extract(self, *references):
        verses = builder.parse_osis(self.source)
        return builder.select_verses(verses, references, "synthetic-source-hash")

    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--osis", str(self.source),
             "--source-metadata", str(self.metadata), "--out", str(self.output),
             *map(str, arguments)], capture_output=True, text=True,
        )

    def test_namespace_notes_tails_and_consecutive_range(self):
        before = self.source.read_bytes()
        result = self.extract("Proverbs 3:5-6")
        self.assertEqual(result["matched"], 1)
        self.assertEqual(result["unmatched"], [])
        self.assertEqual(result["entries"][0]["text"],
                         "Bízzál az Úrban teljes szívedből! Minden te utaidban megismered őt.")
        self.assertTrue(result["entries"][0]["complete_verses"])
        self.assertEqual(self.source.read_bytes(), before)

    def test_corpus_selection_reports_repeated_and_noncanonical_rows(self):
        corpus = self.directory / "quotes.json"
        corpus.write_text(json.dumps({"quotes": [
            {"category": "religion", "source": {"canonicalReference": "Proverbs 3:5"}},
            {"category": "religion", "source": {"canonicalReference": "Proverbs 3:5"}},
            {"category": "religion", "source": {}},
            {"category": "affirmations", "source": {"canonicalReference": "Psalms 23:1"}},
        ]}))
        before = corpus.read_bytes()
        references, repeated, without_reference = builder.requested_references(corpus, [])
        self.assertEqual(references, ["Proverbs 3:5"])
        self.assertEqual(repeated, 1)
        self.assertEqual(without_reference, 1)
        self.assertEqual(corpus.read_bytes(), before)

    def test_missing_member_of_range_reports_verse_without_partial_entry(self):
        result = self.extract("Proverbs 3:5-7")
        self.assertEqual(result["matched"], 0)
        self.assertEqual(result["unmatched"][0]["verse_ids"], ["Prov.3.7"])

    def test_unsupported_and_reversed_references_are_reported(self):
        result = self.extract("Psalm 23:1", "Proverbs 3:6-5")
        self.assertEqual(len(result["unmatched"]), 2)

    def test_duplicate_or_ambiguous_osis_verse_fails(self):
        for second_id in ("Prov.3.5", "Prov.3.5-6"):
            with self.subTest(second_id=second_id):
                self.write_osis(f'<osis><verse osisID="Prov.3.5">One</verse>'
                                f'<verse osisID="{second_id}">Two</verse></osis>')
                with self.assertRaisesRegex(ValueError, "OSIS verse ID"):
                    builder.parse_osis(self.source)

    def test_out_of_budget_text_is_reported_without_truncation(self):
        long_text = "Magyar teljes vers " + "szöveg " * 50
        self.write_osis(f'<osis><verse osisID="Prov.3.5">{long_text}</verse></osis>')
        result = self.extract("Proverbs 3:5")
        self.assertGreater(result["fit_findings"][0]["characters"], 300)
        self.assertEqual(result["entries"][0]["text"], long_text.strip())

    def test_cli_rejects_fabricated_source_with_matching_sidecar(self):
        result = self.run_cli("--reference", "Proverbs 3:5")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inspected Károli 1908 source hash", result.stderr)
        self.assertFalse(self.output.exists())

    def test_same_edition_wrong_sidecar_hash_and_url_are_rejected(self):
        synthetic_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()
        with patch.object(builder, "PINNED_SHA256", synthetic_hash):
            self.write_metadata(sha256="0" * 64)
            with self.assertRaisesRegex(ValueError, "pinned metadata"):
                builder.verify_source(self.source.resolve(), json.loads(self.metadata.read_text()))
            self.write_metadata(source_url="https://example.com/other.xml")
            with self.assertRaisesRegex(ValueError, "pinned source URL"):
                builder.verify_source(self.source.resolve(), json.loads(self.metadata.read_text()))

    def test_output_must_be_new_and_separate(self):
        self.output.write_text("existing")
        result = self.run_cli("--reference", "Proverbs 3:5")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.output.read_text(), "existing")


if __name__ == "__main__":
    unittest.main()
