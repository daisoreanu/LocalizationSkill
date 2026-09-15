---
name: moneyfesting-localization
description: Translates, transcreates or reviews copy for the Moneyfesting iOS app in Localizable.xcstrings, ShieldMessageCatalog.swift and the widget copy files, plus App Store text, with screen and flow context, a blind target-language editor, blind back-translation of claim-bearing strings and a final adjudication. Use whenever a request touches Moneyfesting or Manifesting strings, Romanian (ro) or a new app language, needs_review or missing translations, translator comments, plurals, or the wording of paywall, onboarding, focus, streak, widget or shield screens, including "does this sound natural in Romanian" or "does it fit the widget", even when the user never says localize; also to plan the next locales from the currency list and check readiness for Arabic, Hebrew, pt-BR or zh-Hant (candidates only, never market choice). Not for generic String Catalog, FormatStyle or RTL mechanics with no Moneyfesting copy involved (use ios-localization).
---

# Moneyfesting localization

Make each localized experience read as if a local product team wrote it: familiar, relaxed, credible, and clear about the next action, while Moneyfesting's behaviour, claims and money frame stay exactly what the code implements. The app checkout is read-only except for the resources a `translate` run is authorized to edit.

## Boundary

Load `ios-localization` (by name, if installed) for catalog JSON and generated symbols, plural tables, FormatStyle, RTL layout, Dynamic Type, pseudolocalization and XLIFF export. This skill owns Moneyfesting's surfaces and files, the claims that cannot change, per-locale voice, the blind review protocol, evidence and acceptance rules, and the project's render hooks.

Follow the app `CLAUDE.md` section "Localization and asset provenance" for key and lookup conventions. `needs_review` counts as untranslated here, whatever a generic coverage count says, because it marks AI-written copy the owner has not accepted. Nothing here selects markets or redesigns screens.

## Modes

| Mode | Runs | Produces |
|---|---|---|
| `prepare` | inventory, `catalog_check`, worklist, packets, brief and glossary seeds | packets, open questions, hand-off; no resource edits, no build |
| `audit` | prepare plus editor and adjudicator over existing copy (`en` allowed) | findings per key as proposals; applied only for keys the user names |
| `translate` | the full protocol through integration, build, render, adjudication | catalog and Swift edits within scope plus the report |

Take the mode from the request and say which one you are in. Preparing a localization brief does not authorize app translation; a translation request authorizes the scoped resource edits, never publishing or a change to the product's promises.

## Establish the assignment

Find the Moneyfesting checkout and read its `CLAUDE.md` (`AGENTS.md` if present). Start with [project context](references/project-context.md) for surfaces, files, risk prefixes, build hooks and the archived conventions; treat its paths as discovery aids and verify live call sites before citing them.

Resolve source, target locale and variant, surfaces and the wanted output. Currencies are audiences, not languages: RON -> `ro` is safe, SAR -> `ar` needs a Gulf readability brief, EUR names no language at all. Map them with [locale decisions](references/locale-decisions.md), which also carries the standing owner preferences and the platform-term harvest to run once per locale. `AppLanguage.supportedLanguageCodes` is `["en", "ro"]` (snapshot 2026-09-15) and the in-app override cannot select a regional variant, so a new language is an engineering flag before it is a translation job.

`en` is a locale for `audit` mode: run the target-language editor on the `en` flow packet (text, neutral control roles, order; intents withheld) as a US consumer-app reader and the final adjudicator with captured intents and behaviour, no back-translator. Findings are source-copy proposals, never silent edits; accepted ones become one source-copy batch applied before any target wave, because source changes invalidate review records.

Run state and owner lock:

- Packets, candidates, findings, verdicts and renders live at `<checkout>/.codex-tmp/localization/<locale>/<run-id>/<batch>/` (gitignored; the checkout's scratch location per `Docs/Plans/ProjectStructureCleanup.md`), split into `coordinator/` and `blind/` per batch (the level `scripts/build_context_packet.py --out-dir <run-dir>/<batch>` writes and `--update` reads); name `<run-id>` and `<batch>` opaquely (`2026-09-15-a`, `b01`), because a blind agent receives that path and the leak check fails on a key segment in it; run-wide files (`evidence.json`, `store.<locale>.json`, the report) sit in `<run-id>/coordinator/`. Renders may also go under `<checkout>/.screenshots/localization/`. Never use the skill directory or the OS temp dir.
- Write every AI-written or AI-revised unit with `state: needs_review`. `translated` means owner-accepted and is never rewritten outside an explicitly named audit scope, which locks the mature `ro` copy by default with no question asked (`scripts/catalog_apply.py` refuses such units unless `--overwrite-translated` names that scope).
- Shield Swift pairs have no state field, so list AI-revised ids in the report.

Ask only about an ambiguity that blocks the current batch and keep the independent work moving.

## Build context before words

Inventory the requested surfaces, including copy outside `Localizable.xcstrings`: `InfoPlist.xcstrings`, the `ShieldMessageCatalog.swift` title and body pairs, and the widget copy files under `Manifesting/Foundation/WidgetSupport/` and `PlanWidgetSupport/`. Batch by complete screens or short connected flows with neighbouring screens available read-only; keep one coordinator responsible for shared edits while parallel agents return candidates. Locked keys are read-only neighbours; proposed changes to them go into audit findings, not the catalog.

Load before drafting:

- `scripts/catalog_check.py --out findings.json` first (it supplies tiers and the exclusion classes), then `scripts/worklist.py --findings findings.json` to dispatch (it classifies each key from catalog state plus git and bounds batch sizes), and `scripts/catalog_slice.py --emit-xcstrings` for a subset catalog (eval fixtures, or a small catalog to hand `build_context_packet.py`), `--target-only` when a blind packet must be built by hand; `debugOnly`, `previewOnly`, `shadow` and `format` keys are not work, and `unchanged_passed` keys are skipped with a logged count.
- `glossary/concepts.json` and `glossary/<locale>.json`, then `scripts/term_audit.py` before assembling packets and again after integration. A batch touching a concept aligns every occurrence on its screens and lists remaining keys as follow-up; a new preferred term is a recorded glossary decision, and catalog-wide alignment is its own follow-up batch so review invalidation stays scoped. The translator's glossary additions merge before the next wave. In `audit` mode report two terms for one concept as one term-decision finding with the affected keys and a recommended pick, never as per-string fixes; an `open` glossary entry carries its `recommended` option and reason, and the report repeats them.
- The locale brief, `references/locale-briefs/<locale>.md` (`ro.md` exists; copy `TEMPLATE.md` for a new locale and fill it before the pilot batch).
- The locale's examples file, `references/examples-<locale>.md`, for the translator and adjudicator only; a locale without one gets `examples-ro.md` as pattern illustration and its first batch returns six rows to seed its own. Never hand it to the editor: its EN column breaks packet separation.
- [Surface briefs](references/surface-briefs.md) for structure, CTA rule and the subscription checklist before writing paywall, welcome, widget, share, achievement or shield copy; [store metadata](references/store-metadata.md) for App Store text.

For each string and each plural or device variation capture:

- Stable key and call site, English source, screen and state, control type, and the interaction before and after it; neighbours in flow order, because translators read the whole screen before writing a word.
- What the user needs to understand, the control's real effect, and the invariants: actor, action, condition, timing, amount and unit, negation, certainty, outcome.
- Register and intended feeling, and the content kind. Functional and explanatory copy keeps every proposition (nothing added, nothing dropped, at most reordered) while its wording is still rewritten at sentence level as in step 1; disclaimers, legal lines and system-label mirrors reuse the locale's one approved form; promotional and authored copy may also change image and rhythm within the voice card's persuasion limits; attributed and user content is out of scope.
- A claim-ledger row (`claim -> implementing file:line -> true in this locale? -> wording constraint`) for any string carrying a number, unit, comparative, superlative, strengthening word (always, never, guaranteed, every, all, forever, lowest, only) or a billing, permission, freeze or privacy statement; a catalog comment that already states the constraint counts as the row.
- For any string under five words: its slot (noun phrase, imperative, state adjective or participle, unit suffix, header, prefix or suffix of a composed sentence, value label), its agreement target as the target-language noun with gender and number ("ziua, f. sg."), and its same-source siblings (other keys with the same English value, with their current target and control role).
- Placeholder identity, type and sample values; links, markup, plural branches and protected names.
- Render evidence, width and line behaviour, font and Dynamic Type context, accessibility text. Character budgets guide drafting; only measurement or render establishes fit ([surface budgets](references/surface-budgets.md), which also gives the shortening order).

Generate packets with `scripts/build_context_packet.py`, feeding it `scripts/scan_layout_constraints.py` output for call-site constraints (a key it cannot resolve is filled by hand before dispatch). The script fills `screen_state` from the catalog comment and `invariants` from patterns only, so complete both by hand for every ID before dispatch: the screen's job and feeling from the [surface briefs](references/surface-briefs.md#per-surface-table) table, what the user just did and what the control does next from the call site, and the actor, timing, certainty and outcome invariants the patterns cannot see. A failing leak check blocks dispatch of B and C; blind agents receive exactly one path under `blind/` and never a hand-edited file. A rebuild for a later revision keeps those hand-completed fields for keys whose English and comment did not change. Reuse prior translations only when meaning, context and voice still match; a source, glossary or behaviour change invalidates the affected review records.

## Translate and review

Follow [the agent protocol](references/agent-protocol.md) for every batch: hosts and delegation primitive, roles, tiers, batch order, packet separation, the role prompts, reconciliation, acceptance evidence and the human-review rule. Two material revision rounds per batch; fit-only shortening is not a material round.

1. A locale-focused translator writes each screen as a local product team would, then checks invariants.
   - Rewrite at sentence level: reorder, change part of speech, split or merge, drop scaffolding ("Please", "In order to", "is:") and the English possessive habit, render fragments in the local fragment form, sentence case for app-owned copy except the uppercase eyebrows and captions the brief's header form names; only the captured invariants are fixed.
   - Buttons take the brief's control form: app-owned primary buttons are bare imperatives where the source is imperative, while strings quoting iOS labels mirror the device.
   - Hero-set IDs return three angled candidates; everything else one draft (hero paragraph in the protocol).
2. A fresh editor reads the target as a local user first, from the blind packet, ranking hero candidates. After dispositions and rev2, a fresh editor rechecks changed IDs plus listed neighbours, then a fresh agent back-translates the claim-bearing tier of the revised target without seeing the source.
3. The coordinator compares propositions, never words: "It's raining cats and dogs" becomes "plouă cu găleata", and a blind back-translation that returns "it's pouring" is an acceptable adaptation, not an error. When no local idiom carries the same meaning and register, state the meaning plainly rather than translate the image, never invent an idiom the source does not carry, and split the verdict by role: back-translation checks claims, negation, amounts, conditions and what a control does, the editor checks naturalness, and on style the editor wins while on claims the back-translation wins.
4. Integrate within the authorized scope with `scripts/catalog_apply.py`, build and render, then a fresh final adjudicator reviews the exact final version and evidence; record the model alias it ran on, or `unknown`.
   - For every key you touch, write or upgrade the translator comment at the call site (screen > element: purpose; placeholders with samples; fit line and width; invariants).
   - When a helper drops the comment (`PlanWidgetCopy.text(_:_:)`), propose the one-line signature change as a flagged engineering note. `CLAUDE.md` line 37 (simplify, then deslop) applies to any source edit.

Run one pilot batch alone through every stage before fan-out on a locale's first run and after any change to this skill, the brief or a control-form glossary entry (`scripts/worklist.py --pilot` lists its members); the `ro` pilot runs in `translate` mode limited to `needs_review` keys, so it exercises every stage without touching owner copy.

If delegation is unavailable, produce a clearly provisional draft or review and name the independent stages that did not run.

## Voice and boundaries

Keep the brand name `Moneyfesting` exactly as written in every language and script; recreate the money-and-manifestation association in surrounding copy when the pun does not travel. Write as a local product team would: everyday words, short sentences, the local way of naming a control or a state, no jargon and no imported English sentence shapes. A local user must understand each line on first read without knowing English; plain beats clever, and a clearer common expression beats a rarer exact one. Keep the emotional purpose of each screen: reassurance during permissions, encouragement after effort, clarity during purchases, kindness after a broken streak.

Transcreate rhythm and imagery, not facts, within the persuasion limits in the [voice card](references/voice-card.md); paste the card whole into the translator packet and give blind reviewers only its target-language banned list. Do not turn estimated time value into earnings, an affirmation into a guarantee, a focus tool into a treatment, or permission copy into a privacy promise the code does not keep. Resolve ambiguous English against behaviour before translating it, and flag an off-voice source line (the card lists the known ones) instead of polishing it into a fluent target.

Shortening for fit cuts words, never facts; a fact that must go moves to a neighbouring element and the key's comment says so. Strings that mirror iOS labels (`onboarding.widgets.howTo.*`) keep Apple's register beside the app's informal voice by design.

Follow the live quote policy in `Data/quotes/SCHEMA.md`: app-authored affirmations are transcreated; published quotations, scripture, definitions and user text are neither rewritten as marketing copy nor translated automatically. Agents are AI language specialists, not native people; describe their reviews honestly and never invent human approval, linguistic credentials or conversion gains.

## Verify and deliver

Keep independent verdicts for meaning, target-language editorial quality, structure and rendered UI plus accessibility; a pass in one never offsets a failure in another ([acceptance rules](references/agent-protocol.md#acceptance-and-evidence)).

- Run `scripts/catalog_check.py` before dispatch and after each candidate revision; add `--app-root <checkout>` for a sliced catalog outside the checkout so literal keys still get classified. It is necessary, not sufficient: the `xcodebuild` per `CLAUDE.md` (schemes `Moneyfesting Development` / `Moneyfesting Production`, flags `-skipMacroValidation BUILD_ACTIVE_RESOURCES_ONLY=NO`) remains the structural gate, and agents review only what the script cannot decide.
- Preserve keys, runtime tokens and argument order, plural and device branches, links and catalog metadata. Check the app and its extensions, selected language against formatting region and currency, live language changes and fallback.
- Capture render evidence with the procedure in [render evidence](references/render-evidence.md): each batch at `.large` and the view's own Dynamic Type cap, with the longest sample values per placeholder and plural branch, VoiceOver labels and order, widgets and shields where in scope, and the RTL constraint noted for `ar` and `he`. Gallery captures are approximate, Home Screen captures exact; missing evidence means the visual verdict is `not_checked`, even when language review passed.
- Recommend a human read of the hero set, store text and shield pairs on a locale's first ship, when an adjudicator preference finding stays open, or when the brief was built without a native source (`ro` today); it is a recommendation, never an order, and `done` needs a named source.
- Update existing target entries and review records on repeat runs instead of duplicating them; preserve unrelated work.

Read [research provenance](references/research-provenance.md) when maintaining this skill; `scripts/install.sh` links it into both hosts and `scripts/check_paths.sh --app-root <checkout>` confirms every cited path still exists.

## Report

Always use this template, in this order:

```
### Localization run: <locales> / <surfaces> · mode <prepare|audit|translate> · catalog <commit> · run dir <path>
Keys: changed <n> · unchanged <n> · blocked <n> · needs_review left <n>
Checks: catalog_check pass|fail · term_audit pass|fail · build pass|fail|not_run (<scheme>) · tests <suites> · renders <n> (approximate|exact) | none
Reviews: A <model|unknown> · B blind pass|fail|not_run (tier) · C blind pass|fail|not_run · D final pass|fail|not_run · primitive <Agent|spawn_agent> · human review: recommended|done|not needed
Decisions needed / blockers: ...
```

Expand the human-review field as `recommended (<n> strings, ~<w> words)`, `done by <who, date>` or `not needed because <reason>`. C and D take `not_run` when no separate agent ran them (the protocol's Hosts table), because a stage the coordinator did itself is never a blind pass. List AI-revised shield ids, glossary decisions and flagged source lines under decisions.

## Worked example

`widgets.focusRing.a11y.firstRun`, one of the nine `ro` units in `needs_review` (snapshot 2026-09-15), in a `translate` run scoped to those nine keys (the owner lock, not the mode, keeps `translated` units untouched):

- Packet entry: control `voiceover label`, tier A (`*.a11y.*`), placeholder `%lld` = daily goal in minutes with samples 1/25/90, `screen_state` from the comment ("VoiceOver label for a user who has never run a session") completed by hand: spoken on the small tile and as the first sentence of the medium one (`FocusRingWidget.swift:111`), goal already set, a tap deep-links into the app (`:86`); invariants `negation: No focus sessions yet` and `amount: %lld minutes` from the script, certainty (a goal, not a promise) added by hand; neighbours the visible status lines `widgets.focusRing.firstRun` and `.setUp`.
- Editor findings on the blind packet: `min` abbreviation inside a VoiceOver label (editorial: unnatural, major; spoken text spells units out) and a possessive where the owner is obvious (editorial: unnatural, minor).
- Translator rev2: `Încă nicio sesiune de concentrare. Obiectivul zilnic: %lld minute.` as `ro` plural variations one `%lld minut` · few `%lld minute` · other `%lld de minute` (the `de` Romanian needs from 20 up; `en` keeps its single unit, as six catalog keys already do). The focus term stays the glossary's open decision.
- `catalog_check` passes C1 and C2; the back-translation returns "No focus session yet. Daily goal: N minutes." (frame kept, claim kept).
- `ManifestingTests/Widgets/FocusRingCopyTests.swift:116` (`romanianAccessibilityLabelsAvoidTheCountedNoun`) asserts the ro labels carry neither " minute" nor " de minute", because a single `%lld` cannot take the partitive; the plural variations remove that reason but need a test change beside the catalog edit, so the run writes only the change that does not depend on it, the dropped possessive (`Încă nicio sesiune de concentrare. Obiectivul zilnic este %lld min.`, `catalog_apply --state needs_review`), holds the unit rewrite, reports `tests FocusRingCopyTests (assertion change proposed)`, and lists the plural rewrite plus the test change under Decisions needed; the spoken-unit finding stays open.
- Verdict: meaning pass, editorial fail (the major spoken-unit finding waits on the owner decision), structure pass, visual `not_checked` (VoiceOver only; accessibility labels are exempt from fit).
