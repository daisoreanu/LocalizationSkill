import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from casing import check_casing, load_policy, policy_errors


class CasingTests(unittest.TestCase):
    def setUp(self):
        self.policy = load_policy()
        self.context = {"status": "confirmed", "role": "button", "position": "standalone",
                        "style": "sentence", "owner": "catalog", "protected_terms": [],
                        "exceptions": [], "evidence": "Button text is passed directly to Text."}

    def check(self, value, locale="ro", context=None):
        strings = {"test.button": {"localizations": {locale: {"stringUnit": {"value": value}}}}}
        packet = {"locale": locale, "entries": [{"key": "test.button", "kind": "functional",
                                                 "casing": context or self.context}]}
        return check_casing(strings, list(strings), locale, [packet], self.policy)

    def test_initial_and_unintended_caps(self):
        self.assertTrue(self.check("Începe sesiunea")[1]["complete"])
        for value in ("începe sesiunea", "ÎNCEPE SESIUNEA"):
            findings, coverage = self.check(value)
            self.assertFalse(coverage["complete"])
            self.assertTrue(any(x["severity"] == "major" for x in findings))

    def test_role_distinguishes_uppercase_and_continuation(self):
        heading = {**self.context, "role": "compact_heading", "style": "uppercase"}
        self.assertTrue(self.check("PLANIFICATE", context=heading)[1]["complete"])
        fragment = {**self.context, "role": "continuation", "position": "continuation", "style": "lowercase"}
        self.assertTrue(self.check("din 60 de minute", context=fragment)[1]["complete"])
        self.assertFalse(self.check("Din 60 de minute", context=fragment)[1]["complete"])

    def test_protected_names_and_acronyms(self):
        self.assertTrue(self.check("Deschide Moneyfesting")[1]["complete"])
        self.assertTrue(self.check("iPhone")[1]["complete"])
        self.assertTrue(self.check("USD")[1]["complete"])
        self.assertFalse(self.check("Deschide MoneyFesting")[1]["complete"])
        self.assertFalse(self.check("IPHONE", context={**self.context, "role": "compact_heading", "style": "uppercase"})[1]["complete"])

    def test_numbers_and_placeholders_do_not_capitalize_next_word(self):
        for value in ("20 de zile", "%lld de minute", "%1$lld/%2$lld h", "✅ Începe sesiunea"):
            self.assertTrue(self.check(value)[1]["complete"], value)

    def test_interior_caps_need_review_not_automatic_correction(self):
        findings, _ = self.check("Obiectiv Zilnic")
        self.assertTrue(any(x["severity"] == "needs_disposition" for x in findings))
        self.assertTrue(self.check("Începe. Apoi continuă.")[1]["complete"])
        self.assertTrue(self.check("Începe. Încă un pas.")[1]["complete"])
        self.assertTrue(self.check("Începe\nApoi continuă")[1]["complete"])

    def test_german_nouns_are_not_romanian_title_case(self):
        self.assertTrue(self.check("Tägliches Ziel", "de")[1]["complete"])
        self.assertTrue(self.check("für dein Ziel", "de", {**self.context, "role": "continuation",
                                                          "position": "continuation", "style": "lowercase"})[1]["complete"])

    def test_names_at_script_boundaries_and_decomposed_names(self):
        for value in ("IPHONEを開く", "MONEYFESTINGを開く"):
            self.assertFalse(self.check(value, "ja", {**self.context, "style": "uncased"})[1]["complete"])
        self.assertFalse(self.check("ȘTEFAN", context={**self.context, "protected_terms": ["S\u0326tefan"]})[1]["complete"])

    def test_capitals_after_count_or_name_and_lowercase_after_period_need_review(self):
        for value in ("20 Zile", "%lld Minute", "Moneyfesting Te ajută", "Începe. apoi continuă."):
            self.assertFalse(self.check(value)[1]["complete"], value)

    def test_uncased_scripts_still_preserve_latin_brands(self):
        for locale, text in (("he", "פתיחת Moneyfesting"), ("ja", "Moneyfestingを開く"), ("ko", "목표")):
            context = {**self.context, "style": "uncased"}
            self.assertTrue(self.check(text, locale, context)[1]["complete"])
        self.assertFalse(self.check("פתיחת MONEYFESTING", "he", {**self.context, "style": "uncased"})[1]["complete"])

    def test_title_case_cannot_be_selected_without_explicit_exception(self):
        context = {**self.context, "style": "title"}
        self.assertFalse(self.check("Obiectiv Zilnic", context=context)[1]["complete"])
        context["exceptions"] = [{"text": "Obiectiv Zilnic", "reason": "Exact external product name."}]
        self.assertTrue(self.check("Obiectiv Zilnic", context=context)[1]["complete"])
        self.assertFalse(self.check("Alt Titlu", context=context)[1]["complete"])

    def test_runtime_owner_needs_bound_observed_render(self):
        context = {**self.context, "role": "compact_heading", "style": "uppercase", "owner": "view",
                   "transform": {"operation": "uppercase", "file": "PlanView.swift", "line": 20}}
        self.assertFalse(self.check("istatistik", "tr", context)[1]["complete"])
        context["transform"].update(render_locale="tr", render_status="pass", render_evidence="screen.png",
                                    catalog_value="istatistik", rendered_value="İSTATİSTİK")
        self.assertTrue(self.check("istatistik", "tr", context)[1]["complete"])
        self.assertFalse(self.check("hedef", "tr", context)[1]["complete"])
        context["owner"] = "catalog"
        self.assertFalse(self.check("istatistik", "tr", context)[1]["complete"])

    def test_shared_key_checks_each_actual_display_role(self):
        context = {**self.context, "role": "value_label", "occurrences": [{"role": "compact_heading",
                   "style": "uppercase", "owner": "view", "transform": {"operation": "uppercase",
                   "file": "PlanView.swift", "line": 20,
                   "render_locale": "ro", "render_status": "pass", "render_evidence": "plan-card.png",
                   "catalog_value": "Plan anual", "rendered_value": "PLAN ANUAL"}}]}
        findings, coverage = self.check("Plan anual", context=context)
        self.assertEqual(findings, [])
        self.assertEqual(coverage["units"], 1)
        self.assertEqual(coverage["display_occurrences"], 2)
        context["occurrences"][0]["transform"]["rendered_value"] = "Plan anual"
        self.assertFalse(self.check("Plan anual", context=context)[1]["complete"])
        context["occurrences"][0]["transform"]["render_status"] = "not_checked"
        self.assertFalse(self.check("Plan anual", context=context)[1]["complete"])

    def test_missing_context_and_unknown_locale_never_pass(self):
        self.assertFalse(self.check("Începe", context={"status": "needs_review"})[1]["complete"])
        self.assertFalse(self.check("Start", "unconfigured")[1]["complete"])

    def test_all_briefed_locales_have_role_policy(self):
        for brief in (ROOT / "references/locale-briefs").glob("*.md"):
            if brief.stem != "TEMPLATE":
                self.assertEqual(policy_errors(self.policy, brief.stem), [], brief.stem)

    def test_equivalent_controls_share_case_but_different_roles_can_differ(self):
        strings = {"test.a": {"localizations": {"ro": {"stringUnit": {"value": "Începe"}}}},
                   "test.b": {"localizations": {"ro": {"stringUnit": {"value": "ÎNCEPE"}}}}}
        context = {**self.context, "equivalent_group": "start"}
        second = {**context, "exceptions": [{"text": "ÎNCEPE", "reason": "Legacy spelling under review."}]}
        packet = {"locale": "ro", "entries": [{"key": "test.a", "casing": context}, {"key": "test.b", "casing": second}]}
        findings, _ = check_casing(strings, list(strings), "ro", [packet], self.policy)
        self.assertTrue(any("equivalent controls" in f["message"] for f in findings))
        second.update(role="compact_heading", style="uppercase")
        self.assertTrue(check_casing(strings, list(strings), "ro", [packet], self.policy)[1]["complete"])

    def test_nested_substitution_needs_explicit_fragment_context(self):
        loc = {"stringUnit": {"value": "Ai %#@minutes@."}, "substitutions": {"minutes": {"variations": {
            "plural": {"one": {"stringUnit": {"value": "un minut"}}, "other": {"stringUnit": {"value": "%lld minute"}}}}}}}
        strings = {"test.label": {"localizations": {"ro": loc}}}
        context = copy.deepcopy(self.context)
        packet = {"locale": "ro", "entries": [{"key": "test.label", "casing": context}]}
        self.assertFalse(check_casing(strings, list(strings), "ro", [packet], self.policy)[1]["complete"])
        fragment = {"role": "continuation", "position": "continuation", "style": "lowercase"}
        context["units"] = {f"substitution:minutes/plural:{form}": fragment for form in ("one", "other")}
        self.assertTrue(check_casing(strings, list(strings), "ro", [packet], self.policy)[1]["complete"])

    def test_excluded_content_is_not_case_checked(self):
        strings = {"content.test": {"localizations": {"ro": {"stringUnit": {"value": "intentionally lowercase"}}}}}
        packet = {"locale": "ro", "entries": [{"key": "content.test", "kind": "attributed", "casing": {
            "status": "not_applicable", "evidence": "Attributed content uses separate fidelity route."}}]}
        findings, coverage = check_casing(strings, list(strings), "ro", [packet], self.policy)
        self.assertEqual(findings, [])
        self.assertEqual(coverage["excluded_keys"], 1)
        self.assertEqual(coverage["units"], 0)

    def test_final_cli_gate_fails_without_context(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "findings.json"
            result = subprocess.run([sys.executable, str(ROOT / "scripts/catalog_check.py"), "--catalog",
                                     str(ROOT / "evals/files/focus-ring.xcstrings"), "--locale", "ro",
                                     "--keys", "widgets.focusRing.firstRun", "--require-casing", "--out", str(out)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads(out.read_text())["casing"]["complete"])

    def test_final_cli_gate_succeeds_with_confirmed_context(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            catalog = folder / "Localizable.xcstrings"
            catalog.write_text(json.dumps({"sourceLanguage": "en", "strings": {"test.button": {
                "comment": "Start button", "localizations": {
                    "en": {"stringUnit": {"value": "Start", "state": "translated"}},
                    "ro": {"stringUnit": {"value": "Începe", "state": "needs_review"}}}}}}))
            packet = folder / "source.json"
            packet.write_text(json.dumps({"locale": "ro", "entries": [{"key": "test.button", "en": "Start",
                                                                        "comment": "Start button", "casing": self.context}]}))
            result = subprocess.run([sys.executable, str(ROOT / "scripts/catalog_check.py"), "--catalog", str(catalog),
                                     "--locale", "ro", "--casing-context", str(packet), "--require-casing",
                                     "--out", str(folder / "findings.json")], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads((folder / "findings.json").read_text())["casing"]["complete"])


if __name__ == "__main__":
    unittest.main()
