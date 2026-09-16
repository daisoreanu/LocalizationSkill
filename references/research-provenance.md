# Research provenance

Sources reviewed 2026-09-12; package snapshot 2026-09-15. Read this file when maintaining the skill, not during a run. These instructions are an original synthesis: no third-party runtime or bulk skill text is bundled, and community workflows supply mechanisms, not proof of translation quality. Re-read a source before changing the behaviour adopted from it.

| Inspected source | Adopted mechanism | Deliberately omitted |
|---|---|---|
| [Anthropic skill creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) | Focused SKILL.md plus references, imperative voice, realistic evaluation and iteration (`evals/evals.json`) | Claude-specific CLI and model assumptions; automatic approval questions |
| [Localize Anything](https://github.com/xueyang-dev/localize-anything/blob/main/skills/localize-anything/SKILL.md), [context/memory](https://github.com/xueyang-dev/localize-anything/blob/main/skills/localize-anything/references/memory-and-context.md) | Surface inventory, concept glossary (`glossary/concepts.json`), separate structural, linguistic and visual evidence | Custom orchestration CLI and mandatory human-confirmation machinery |
| [Fidelity Translator](https://github.com/Tasdax123/claude-fidelity-translator/blob/main/plugins/fidelity-translator/skills/fidelity-translator/SKILL.md) | Translator, critic, revision and back-translation pattern with pinned terminology | English-similarity acceptance threshold, since a good local idiom back-translates to a different English sentence; its non-marketing scope and provider settings |
| [Translate Book](https://github.com/deusyu/translate-book/blob/main/SKILL.md) | Neighbour context in every packet, shared glossary, selective review invalidation | Book conversion and document or entity machinery |
| [neo.ai Translator](https://github.com/theneoai/awesome-skills/blob/main/skills/persona/creative/translator/SKILL.md) | Brand and market brief, meaningful creative alternatives, local idiom over literal image | Persona boilerplate and self-awarded verification labels |
| `ios-localization` (installed skill; String Catalogs, generated symbols, plural tables, FormatStyle, RTL, Dynamic Type) | Hand-off target for catalog mechanics, named in SKILL.md "Boundary" | Its generic coverage and naturalness advice, which knows nothing of Moneyfesting's claims, surfaces or `needs_review` rule |

The community repositories present MIT licensing and attribution. Follow each repository's actual license and preserve notices if a future revision copies substantial material; this package borrows workflow ideas and links to the originals.

## Romanian provenance

The Romanian conventions this skill seeds (`glossary/ro.json`, `references/locale-briefs/ro.md`, `references/examples-ro.md`) descend from `Docs/Archive/I18N_PROMPT.md` "Romanian translation guide" and `Docs/Archive/I18N_PLAN.md` section 7 in the app checkout, written as owner-directed agent output in commit `503cd42` (2026-08-11) and checked by review agents, not authored by a native product team. Where the guide and the shipped catalog differ, the catalog majority at `c8a49dd` is the stronger evidence, because the owner accepted it; the guide's Cancel = Renunță lost to the shipped Anulează that way, and "sesiune de focus" stays an open owner decision. For the same reason the ro pilot runs in `translate` mode limited to `needs_review` keys: its findings correct the brief and glossary, while the owner lock keeps `translated` units untouched.

## Locale research (2026-09-16)

The briefs for the decided target set were written from first-party evidence gathered in one pass; `references/locale-decisions.md` `## Platform terms` carries the reproducible procedure.

| Question | Method | Grounds |
|---|---|---|
| What does Apple call this in the target language? | decode every `en`/`Base`/`en_GB` `.strings` and `.stringsdict` in the iOS 26.1 (23B86) simulator runtime, find the key by its English value, read the same key in the locale's `lproj` | each brief's Platform terms rows and the system-mirror values, cited as `bundle \| table \| key` |
| Which plural categories does the locale really select? | ICU `uplrules_open`/`uplrules_select` over every integer below a million plus fractions, cross-checked with Xcode's own `PluralRule.ComplementedPluralKeys` table | `scripts/catalog_check.py` `PLURAL_REQUIRED` and `PLURAL_OPTIONAL`, and each brief's boundary values |
| How do numbers, money, dates and quotes render? | Foundation with the app's own `AppCurrency.format`/`formatCompact` replicated verbatim, invisible characters recorded as code points | the Numbers section of each brief and the compact-suffix engineering finding |
| Which tag does a device actually receive? | `Bundle.preferredLocalizations(from:forPreferences:)` against the runtime's real `lproj` lists and against candidate app tag sets | the catalog tag in each brief's Identity, and the `nb`/`no`, `he`/`iw`, `es-MX`/`es-419` and `pt-BR`/`pt` decisions |
| How much does the language expand? | ratio distribution of Apple's own translations against their English source, calibrated so the procedure returns `ro`'s shipped 1.35x | the length trigger in each brief, display-width based for `ja` and `ko` |
| Can the store list this language? | App Store Connect's published localization list, fetched 2026-09-16 | the store rows in each brief and the Icelandic and Bulgarian gaps |

Every row in a brief outside `ro` is agent research: no shipped copy, no native source, and no owner acceptance. Glossary rows carry `decided_by: "skill-seed-2026-09-16"` so an owner can tell research from accepted copy, and `scripts/brief_check.py` fails a brief that claims human approval. Two independent checks ran over each locale: a language specialist trying to refute the choices, and the script for structure, schema, cited keys and evidence.

## Primary references for maintenance

- [Apple localization](https://developer.apple.com/localization/) and [Code-along: Explore localization with Xcode](https://developer.apple.com/videos/play/wwdc2025/225/): catalog workflow, translator context and platform surfaces. Keep repository conventions where they intentionally differ from generic examples.
- [Apple StoreKit displayPrice](https://developer.apple.com/documentation/storekit/product/displayprice): preserve runtime-localized purchase prices once the app uses them; today it has none (`references/project-context.md` Subscription row).
- [Unicode CLDR plural rules](https://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html): target-specific plural categories; verify against the shipping runtime, since Romanian adds a `few` category that English lacks.
- [Microsoft locale guides](https://learn.microsoft.com/en-us/globalization/reference/microsoft-style-guides): language and region conventions, including Arabic, Hebrew and regional Portuguese and Spanish, used alongside Moneyfesting's own voice card, never instead of it.
- [MQM error typology](https://www.themqm.org/mqm-pillars/typology/): separate accuracy, linguistic, style, audience or locale and presentation findings. The acceptance criteria in `references/agent-protocol.md` "Acceptance and evidence" are Moneyfesting-specific, not MQM certification.
- [Smartling transcreation](https://help.smartling.com/hc/en-us/articles/4641758074523-What-is-Transcreation): intent and tone adaptation with creative alternatives; it does not demonstrate conversion lift for this app.
- [Experts, Errors, and Context](https://aclanthology.org/2021.tacl-1.87/): contextual professional evaluation, the reason every packet carries screen, state and neighbours.
- [Rethinking Round-Trip Translation for Machine Translation Evaluation](https://aclanthology.org/2023.findings-acl.22/): round-trip evaluation compares propositions, not surface forms, which is why a back-translation of "plouă cu găleata" reading "it's pouring" passes and a changed amount, negation or condition fails.

## Maintenance notes

- Paths: every checkout path cited in `references/*.md` is a snapshot. Run `scripts/check_paths.sh --app-root <checkout>` after the app repo moves files (commit `057a80d` moved the widget copy files once already) and before publishing a skill change; a missing path is a skill defect, not an app defect.
- Facts: counts and line numbers carry "snapshot 2026-09-15". Refresh them from `scripts/catalog_check.py` output and a fresh grep rather than editing numbers by hand; `references/project-context.md` "Catalog state" and "Enabling a locale" list what to re-verify.
- Pilot regression: after any change to SKILL.md, a locale brief, `references/voice-card.md` or the control-form entries of a glossary, run the pilot batch (`scripts/worklist.py --pilot`) alone through every stage before fan-out, per `references/agent-protocol.md` "Tiers, order and batches"; treat its findings as corrections to the brief and glossary and list them by category in the report.
- Evals: `evals/evals.json` holds the regression cases with fixtures under `evals/files/`; add a case whenever a run surfaces a failure class the protocol did not catch, and keep each case's expectation phrased in the report template's terms so runs stay comparable.
- Scripts: Python 3 standard library only, every script prints `--help`, and none writes into the app checkout except `scripts/catalog_apply.py` on an explicit path; keep that contract when adding a script.
- Workflow controls (fresh target-only agents, the leak check, bounded revision rounds, version-linked evidence, a final adjudicator) are proposed mechanisms: test their behaviour on the pilot and disclose any stage that did not run in the report's Reviews line.
