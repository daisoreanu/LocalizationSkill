import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/ui_review_check.py"


def translator_pair():
    packet = {"locale": "he", "rev": 1, "entries": [
        {"id": "s01", "hero": False, "source_units": {"": ""}, "target_units": {"": ""}, "variations": {}},
        {"id": "s02", "hero": False, "source_units": {"": "Continue"}, "variations": {}},
    ]}
    result = {"locale": "he", "candidate_revision": 1, "candidates": [
        {"id": "s01", "text": "", "casing_verdict": "pass", "syntax_verdict": "pass",
         "register_verdict": "pass", "uncertainty": []},
        {"id": "s02", "text": "המשך", "casing_verdict": "pass", "syntax_verdict": "pass",
         "register_verdict": "pass", "uncertainty": []},
    ], "holds": []}
    return packet, result


def editor_pair():
    packet = {"locale": "ro", "rev": 2, "hero": [], "strings": [
        {"id": "s01", "text": "Salut", "plural": None},
        {"id": "s02", "text": "Continuă", "plural": None},
    ]}
    result = {"locale": "ro", "candidate_revision": 2, "reviews": [
        {"id": identifier, "verdict": "pass", "casing_verdict": "pass", "syntax_verdict": "pass",
         "register_verdict": "pass", "findings": [], "uncertainties": []}
        for identifier in ("s01", "s02")
    ]}
    return packet, result


class UIReviewCheckTests(unittest.TestCase):
    def run_check(self, role, packet, result):
        with tempfile.TemporaryDirectory() as directory:
            packet_path = Path(directory) / "packet.json"
            result_path = Path(directory) / "result.json"
            packet_path.write_text(json.dumps(packet, ensure_ascii=False))
            result_path.write_text(json.dumps(result, ensure_ascii=False))
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--role", role, "--packet", str(packet_path),
                 "--result", str(result_path)], capture_output=True, text=True,
            )
        return completed.returncode, json.loads(completed.stdout)["diagnostics"]

    def assert_codes(self, role, packet, result, *codes):
        status, diagnostics = self.run_check(role, packet, result)
        self.assertNotEqual(status, 0)
        self.assertTrue(set(codes) <= {item["code"] for item in diagnostics}, diagnostics)

    def test_valid_flat_forms_and_intentional_empty_source(self):
        for role, pair in (("translator", translator_pair()), ("editor", editor_pair())):
            with self.subTest(role=role):
                self.assertEqual(self.run_check(role, *pair), (0, []))

    def test_coverage_duplicates_and_stale_result(self):
        packet, result = translator_pair()
        result["candidates"] = [result["candidates"][0], copy.deepcopy(result["candidates"][0])]
        result["candidates"].append({**result["candidates"][0], "id": "s99"})
        result["candidate_revision"] = 3
        result["locale"] = "ro"
        self.assert_codes("translator", packet, result, "duplicate", "missing", "extra", "mismatch")

    def test_candidate_and_hold_must_be_disjoint_and_complete(self):
        packet, result = translator_pair()
        result["holds"] = [{"id": "s01", "reason": "Awaiting product meaning"}, {"id": "s02", "reason": ""}]
        self.assert_codes("translator", packet, result, "overlap", "invalid")
        result["candidates"] = result["candidates"][:1]
        result["holds"] = [{"id": "s02", "reason": "Awaiting product meaning"}]
        self.assertEqual(self.run_check("translator", packet, result), (0, []))

    def test_bad_types_verdicts_and_unexplained_uncertainty(self):
        packet, result = translator_pair()
        result["candidates"][0].update(text=42, casing_verdict=[], syntax_verdict="not_checked", uncertainty=[])
        self.assert_codes("translator", packet, result, "invalid", "unexplained")
        result["candidates"][0].update(text="", casing_verdict="pass", uncertainty=["Missing casing context"])
        self.assertEqual(self.run_check("translator", packet, result), (0, []))
        result["candidates"][1]["text"] = ""
        self.assert_codes("translator", packet, result, "invalid")

    def test_editor_findings_and_not_checked(self):
        packet, result = editor_pair()
        review = result["reviews"][0]
        review.update(verdict="finding", syntax_verdict="finding")
        self.assert_codes("editor", packet, result, "invalid")
        review["findings"] = [{"severity": "major", "category": "grammar", "target_span": "Salut",
                               "reader_impact": "Wrong register", "suggestion": "Bună"}]
        self.assertEqual(self.run_check("editor", packet, result), (0, []))
        review["verdict"] = "pass"
        self.assert_codes("editor", packet, result, "invalid")
        review.update(verdict="not_checked", syntax_verdict="not_checked", findings=[], uncertainties=[])
        self.assert_codes("editor", packet, result, "unexplained")
        review["uncertainties"] = ["No syntax context"]
        self.assertEqual(self.run_check("editor", packet, result), (0, []))
        review["verdict"] = "not_applicable"
        self.assert_codes("editor", packet, result, "invalid")
        review.update(verdict="not_checked", syntax_verdict="pass", uncertainties=[])
        self.assert_codes("editor", packet, result, "unexplained")

    def test_editor_finding_shape_and_review_coverage(self):
        packet, result = editor_pair()
        result["reviews"] = [result["reviews"][0], copy.deepcopy(result["reviews"][0])]
        self.assert_codes("editor", packet, result, "duplicate", "missing")
        result = editor_pair()[1]
        review = result["reviews"][0]
        review.update(verdict="finding", findings=[{"severity": "severe", "category": "", "target_span": "",
                                                     "reader_impact": "", "suggestion": ""}])
        self.assert_codes("editor", packet, result, "invalid")

    def test_unsupported_hero_plural_and_nested_packets(self):
        packet, result = translator_pair()
        packet["entries"][0]["hero"] = True
        self.assert_codes("translator", packet, result, "unsupported")
        packet, result = translator_pair()
        packet["entries"][0]["source_units"] = {"one": "A", "other": "B"}
        self.assert_codes("translator", packet, result, "unsupported")
        packet, result = editor_pair()
        packet["hero"] = [{"id": "s01"}]
        packet["strings"][0]["plural"] = {"one": "Unu"}
        packet["strings"][1]["units"] = [{"id": "u01"}]
        self.assert_codes("editor", packet, result, "unsupported")

    def test_help_states_scope(self):
        completed = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0)
        self.assertIn("flat ordinary UI", completed.stdout)
        self.assertIn("unsupported", completed.stdout)


if __name__ == "__main__":
    unittest.main()
