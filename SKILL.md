---
name: moneyfesting-localization
description: Translate or review Moneyfesting/Manifesting app copy, quotes and affirmations across locales. Use for natural wording, screen and flow context, mobile fit, terminology, quote fidelity, bulk translation and language readiness. Includes independent AI review and resumable batches. For generic iOS localization mechanics, use ios-localization.
---

# Moneyfesting localization

Make UI copy read as if a local product team wrote it, while preserving the app's behaviour and claims. Translate literary content in its own voice, preserving meaning, imagery and deliberate ambiguity. App writes stay within the authorized translation or project setup scope.

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

Choose the content route before gathering packets: UI and store copy use the screen workflow below; quote records use [Quote corpus workflow](references/agent-protocol.md#quote-corpus), its inventory/batch scripts and the live quote schema. Specialized agent configuration and the explicit-dispatch fallback are in [Hosts](references/agent-protocol.md#hosts). For another app, replace the project-specific paths, behaviour and voice with that app's brief; do not silently inherit Moneyfesting's claims or file structure.

## Establish the assignment

Find the Moneyfesting checkout and read its `AGENTS.md` and `CLAUDE.md` in full. Start with [project context](references/project-context.md) for surfaces, files, risk prefixes, build hooks and the archived conventions; treat its paths as discovery aids and verify live call sites before citing them.

For app work, follow the live `AGENTS.md` coordination rules. Codex uses only its `i18n/<topic>` worktree, `Codex-Moneyfesting` simulator and `<worktree>/DerivedData`; Claude uses its assigned worktree, simulator and build output. For the current Moneyfesting assignment, Codex owns all translation work; Claude owns navigation only. Use the hub to coordinate overlapping files and changed screen context, never to delegate translation to Claude.

Only the owner-started coordinator runs hub write commands. It reads the hub and posts its plan before the go-ahead, claims shared paths before editing, takes and releases the `heavy` lock for clean builds, full unit runs, UI schemes and timing, and releases claims as the app rules require. Subagents and reviewers may use only `hub status` and `hub tail`; they never edit shared files. No commit or merge without explicit owner approval. Keep the app's `Docs/Plans/LOCALIZATION_IMPLEMENTATION_PLAN.md` as a checkpoint linking run evidence, not a second hub.

Resolve source, target locale and variant, surfaces and the wanted output. Currencies are audiences, not languages: RON -> `ro` is safe, SAR -> `ar` needs a Gulf readability brief, EUR names no language at all. Map them with [locale decisions](references/locale-decisions.md), which also carries the standing owner preferences and the platform-term harvest to run once per locale. Check `AppLanguage.supportedLanguageCodes` live (`["en", "ro", "he"]` on 2026-09-27); a briefed language outside that set is an engineering flag before it is a translation job, and the in-app override cannot select a regional variant at all.

`en` is a locale for `audit` mode: run the target-language editor on the `en` flow packet (text, neutral control roles, order; intents withheld) as a US consumer-app reader and the final adjudicator with captured intents and behaviour, no back-translator. Findings are source-copy proposals, never silent edits; accepted ones become one source-copy batch applied before any target wave, because source changes invalidate review records.

Run state and owner lock:

- Packets, candidates, findings, verdicts and renders live at `<checkout>/.codex-tmp/localization/<locale>/<run-id>/<batch>/` (gitignored), split into `coordinator/` and `blind/` per batch. Use opaque run and batch names (`2026-09-26-a`, `b01`) to avoid leaking source-bearing keys through paths. Run-wide files sit in `<run-id>/coordinator/`; renders may also use `<checkout>/.screenshots/localization/`. For a read-only checkout or isolated skill evaluation, use an authorized external scratch directory and report it. Never write run artifacts into the skill package.
- Write every AI-written or AI-revised unit with `state: needs_review`. `translated` means owner-accepted and is never rewritten outside an explicitly named audit scope, which locks the mature `ro` copy by default with no question asked (`scripts/catalog_apply.py` refuses such units unless `--overwrite-translated` names that scope).
- Shield Swift pairs have no state field, so list AI-revised ids in the report.

Ask only about an ambiguity that blocks the current batch and keep the independent work moving.

## Build context before words

Inventory the requested surfaces, including copy outside `Localizable.xcstrings`: `InfoPlist.xcstrings`, the `ShieldMessageCatalog.swift` title and body pairs, and the widget copy files under `Manifesting/Foundation/WidgetSupport/` and `PlanWidgetSupport/`. Batch by complete screens or short connected flows with neighbouring screens available read-only; keep one coordinator responsible for shared edits while parallel agents return candidates. Before dispatching prepared packets, update their recorded mode and authorization to the active user-approved scope. Locked keys are read-only neighbours; proposed changes to them go into audit findings, not the catalog.

When terminology or interaction is unclear, optionally inspect about five comparable iOS screens across two or three products. Use `mobbin-search` if available, otherwise official screenshots and product documentation; continue without it when unavailable. Record the app, screen/action, actual language, URL, date and relevant lesson. A local storefront does not establish in-app language or local popularity. Foreign-language screens inform layout and interaction, not target terminology; keep visual evidence separate from documentation and note gaps. Distinguish the earned achievement, its badge artwork, milestones, functional rewards and system notification badges before choosing shared terms.

Load before drafting:

- `scripts/catalog_check.py --out findings.json` first (it supplies tiers and the exclusion classes), then `scripts/worklist.py --findings findings.json` to dispatch (it classifies each key from catalog state plus git and bounds batch sizes), and `scripts/catalog_slice.py --emit-xcstrings` for a subset catalog (eval fixtures, or a small catalog to hand `build_context_packet.py`), `--target-only` when a blind packet must be built by hand; `debugOnly`, `previewOnly`, `shadow` and `format` keys are not work, and `unchanged_passed` keys are skipped with a logged count unless runtime or language evidence exposes a defect. That classification records automated checks, not linguistic acceptance; reopen only the affected keys and equivalent states.
- `glossary/concepts.json` and `glossary/<locale>.json`, then `scripts/term_audit.py` before assembling packets and again after integration. A batch touching a concept aligns every occurrence on its screens and lists remaining keys as follow-up; a new preferred term is a recorded glossary decision, and catalog-wide alignment is its own follow-up batch so review invalidation stays scoped. The translator's glossary additions merge before the next wave. In `audit` mode report two terms for one concept as one term-decision finding with the affected keys and a recommended pick, never as per-string fixes; an `open` glossary entry carries its `recommended` option and reason, and the report repeats them.
- The locale brief, `references/locale-briefs/<locale>.md` (the decided target set has one; copy `TEMPLATE.md` for a locale that does not). Run `scripts/brief_check.py --locale <tag> --catalog <catalog> [--facts <harvest>]` before the pilot batch: it checks the brief against the template, the glossary schema and the control mirror, that every cited key exists, and that agent-researched rows are marked as seeds.
- The locale's examples file, `references/examples-<locale>.md`, for the translator and adjudicator only; a locale without one gets `examples-ro.md` as pattern illustration and its first batch returns six rows to seed its own. Never hand it to the editor: its EN column breaks packet separation.
- [Surface briefs](references/surface-briefs.md) for structure, CTA rule and the subscription checklist before writing paywall, welcome, widget, share, achievement or shield copy; [store metadata](references/store-metadata.md) for App Store text.

Include formatter-generated headings in the casing and render inventory even when they have no catalog key. For each string and each plural or device variation capture:

- Stable key and call site, English source, screen and state, control type, and the interaction before and after it; neighbours in flow order, including actions revealed by scrolling and which controls appear together versus in separate steps. Give blind reviewers each adjacent action's effect and whether it closes the screen; a generic "action control" note can hide different actions behind the same label. For errors, trace every operation caught and any completed side effects; a Save error need not mean persistence failed.
- What the user needs to understand, the control's real effect, and the invariants: actor, action, condition, timing, amount and unit, negation, certainty, outcome.
- Expected register and intended feeling for this string in this screen state, and the content kind. Celebrations may be warm and informal; settings, permissions, actions and criteria stay neutral or semi-formal as their purpose requires. Functional and explanatory copy keeps every proposition while its wording may change; disclaimers, legal lines and system-label mirrors reuse the locale's approved form. Formal legal precision does not itself change the locale's form of address. Promotional copy may change image and rhythm within the voice card's persuasion limits. Quote records follow the corpus route, including its literary fidelity and provenance rules. User content stays untouched. App-authored editable suggestions are localized when a new draft is created; saved names and user edits remain verbatim.
- A claim-ledger row (`claim -> implementing file:line -> true in this locale? -> wording constraint`) for any string carrying a number, unit, comparative, superlative, strengthening word (always, never, guaranteed, every, all, forever, lowest, only) or a billing, permission, freeze or privacy statement; a catalog comment that already states the constraint counts as the row.
- For any string under five words: its slot (noun phrase, imperative, state adjective or participle, unit suffix, header, prefix or suffix of a composed sentence, value label), its agreement target as the target-language noun with gender and number ("ziua, f. sg."), and its same-source siblings (other keys with the same English value, with their current target and control role).
- A confirmed `casing` record: UI role, standalone/continuation/template position, expected style from [the locale/role policy](references/casing-policy.json), catalog/view/formatter/system owner, protected spellings, exact exceptions with reasons, equivalent-control group and call-site evidence. Apply the rule to every variation; substitution fragments need their own context. Unknown context stays `needs_review`. Never choose the target rule from English capitals or the current translation.
- Placeholder identity, type and sample values; links, markup, plural branches and protected names. Show related counts together at reachable zero/one boundaries (such as `0/1` and `1/1`), not only as separate token samples or long values.
- Render evidence, width and line behaviour, font and Dynamic Type context, accessibility text. Character budgets guide drafting; only measurement or render establishes fit ([surface budgets](references/surface-budgets.md), which also gives the shortening order).

Generate packets with `scripts/build_context_packet.py`, feeding it `scripts/scan_layout_constraints.py` output for call-site constraints (a key it cannot resolve is filled by hand before dispatch). The script fills `screen_state` from the catalog comment and `invariants` from patterns only, so complete both for every ID before dispatch: the screen's job and feeling from the [surface briefs](references/surface-briefs.md#per-surface-table) table, what the user just did and what the control does next from the call site, and the actor, timing, certainty and outcome invariants the patterns cannot see. Use `--update` entries for verified `control`, `slot`, `agreement_target` and `placeholders`; supply source-free state, action, expected register and tone, syntax/fragment role and agreement notes in the existing `target_context` for blind readers. Check token samples against the call site: an earned date is not a money amount. A failing leak check blocks dispatch of B and C; blind agents receive exactly one path under `blind/` and never a hand-edited file. A rebuild for a later revision keeps those completed fields for keys whose English and comment did not change. Refresh read-only neighbours and same-source siblings from the recorded catalog too; each needs its own role and casing context. Judge the actual target word order, and distinguish earned messages from unlock criteria. `--update` refreshes uncandidated targets and rejects changed source, comment or variation structure; rebuild when it rejects the snapshot. Reuse prior translations only when meaning, context and voice still match; a source, glossary or behaviour change invalidates the affected review records.

## Translate and review

Follow [the agent protocol](references/agent-protocol.md) for role assignment, model and effort selection, review order, packet separation, acceptance evidence and bounded revision budgets. Independent locale batches can run in parallel; dependent review stages wait for the actual candidate.

1. A locale-focused translator writes each screen as a local product team would, then checks invariants.
   - Rewrite at sentence level: use natural target-language syntax, including inversion or emphasis where it belongs; reorder, change part of speech, split or merge, drop scaffolding ("Please", "In order to", "is:") and the English possessive habit, render fragments in the local fragment form, and apply the confirmed locale/role casing record. Preserve actor, logical scope and negation as well as the other captured invariants; good copy needs no rewrite.
   - Buttons take the locale brief's control form for their action and role; an English imperative does not impose that grammar on the target. Strings quoting iOS labels mirror the device.
   - Hero-set IDs return three angled candidates; everything else one draft (hero paragraph in the protocol).
2. A fresh editor reads the target as a local user first, from the blind packet, ranking hero candidates. After dispositions and rev2, a fresh editor rechecks changed IDs plus listed neighbours, then a fresh agent back-translates the claim-bearing tier of the revised target without seeing the source.
3. The coordinator compares propositions, never words: "It's raining cats and dogs" becomes "plouă cu găleata", and a blind back-translation that returns "it's pouring" is an acceptable adaptation, not an error. When no local idiom carries the same meaning and register, state the meaning plainly rather than translate the image, never invent an idiom the source does not carry, and split the verdict by role: back-translation checks claims, negation, amounts, conditions and what a control does, the editor checks naturalness, and on style the editor wins while on claims the back-translation wins.
4. Integrate within the authorized scope with `scripts/catalog_apply.py`, build and render, then a fresh final adjudicator reviews the exact final version and evidence; record the model alias it ran on, or `unknown`.
   - For every key you touch, write or upgrade the translator comment at the call site (screen > element: purpose; placeholders with samples; fit line and width; invariants).
   - When a helper drops the comment (`PlanWidgetCopy.text(_:_:)`), propose the one-line signature change as a flagged engineering note. `CLAUDE.md` line 37 (simplify, then deslop) applies to any source edit.

Run one pilot batch alone through every stage before fan-out on a locale's first run and after a change that affects translation behavior, the locale brief or a control-form glossary entry (`scripts/worklist.py --pilot` lists its members); the `ro` pilot runs in `translate` mode limited to `needs_review` keys, so it exercises every stage without touching owner copy.

If delegation is unavailable, produce a clearly provisional draft or review and name the independent stages that did not run.

## Voice and boundaries

Keep the brand name `Moneyfesting` exactly as written in every language and script; recreate the money-and-manifestation association in surrounding copy when the pun does not travel. Write as a local product team would: everyday words, short sentences, the local way of naming a control or a state, no jargon and no imported English sentence shapes. A local user must understand each line on first read without knowing English; plain beats clever, and a clearer common expression beats a rarer exact one. Keep the emotional purpose of each screen: reassurance during permissions, encouragement after effort, clarity during purchases, kindness after a broken streak.

Transcreate rhythm and imagery, not facts, within the persuasion limits in the [voice card](references/voice-card.md); paste the card whole into the translator packet and give blind reviewers only the target-language banned words from the locale brief's `## Money frame`. Do not turn estimated time value into earnings, an affirmation into a guarantee, a focus tool into a treatment, or permission copy into a privacy promise the code does not keep. Resolve ambiguous English against behaviour before translating it, and flag an off-voice source line (the card lists the known ones) instead of polishing it into a fluent target.

Shortening for fit cuts words, never facts. Moving a fact to a neighbour requires evidence that both elements remain visible together in every relevant state; otherwise hold the layout issue. Do not shorten canonical quotations to fill a widget. Strings that mirror iOS labels (`onboarding.widgets.howTo.*`) keep Apple's register beside the app's informal voice by design.

Follow the live quote schema with [project context](references/project-context.md) `## Content policy` and the owner's 2026-09-26 preservation rules: reconcile the union of existing language sets, retain distinct phrases even when their meanings coincide, and request a scoped decision before removing content. A failed source lookup is a provenance finding, not deletion authority. Each record keeps its own source language; English is the source for English originals, not the completeness test for all languages. App-authored affirmations are transcreated; attributed quotations retain their author and internal translation provenance without presenting translated wording as the original-language text; scripture takes that language's canonical published translation; a category ports completely or not at all, because a partial pool replaces English rather than supplementing it; user text is never touched. Agents are AI language specialists, not native people; describe their reviews honestly and never invent human approval, linguistic credentials or conversion gains.

Owner display decision (2026-09-27): do not show translation notices anywhere in the app, including author suffixes, cards, widgets, notifications, share output or accessibility text. Keep translation/source metadata internally. If an exception is genuinely necessary, explain the reason and exact proposed wording/location and obtain explicit owner approval before implementing it. Existing quote notices are a deferred correction, outside the current Romanian UI task; see [Content policy](references/project-context.md#content-policy).

## Verify and deliver

Keep independent verdicts for meaning, target-language editorial quality, structure and rendered UI plus accessibility; a pass in one never offsets a failure in another ([acceptance rules](references/agent-protocol.md#acceptance-and-evidence)).

- Validate flat UI translator/editor returns with `scripts/ui_review_check.py` as specified in [the protocol](references/agent-protocol.md#tiers-order-and-batches). Run `scripts/catalog_check.py` before dispatch and after each candidate revision; add `--app-root <checkout>` for a sliced catalog outside the checkout so literal keys still get classified. It is necessary, not sufficient: the `xcodebuild` per `CLAUDE.md` (schemes `Moneyfesting Development` / `Moneyfesting Production`, flags `-skipMacroValidation BUILD_ACTIVE_RESOURCES_ONLY=NO`) remains the structural gate, and agents review only what the script cannot decide.
- For the final casing gate add `--casing-context <coordinator/source.json>` for each batch and `--require-casing`. C12 reports coverage, initial/all-cap defects, protected names and equivalent-control drift; ambiguity requires an editorial disposition. Trace case transformations through live branches and inherited modifiers: a carried payload is not proof it is displayed. Prefer catalog-owned app copy; view-owned transformations need actual rendered text bound to the catalog value and locale. Shared keys serving different roles need occurrence evidence or remain unresolved. Both agents check the actual revision; [casing acceptance](references/agent-protocol.md#acceptance-and-evidence) requires resolved scope, documented exceptions and matching renders. Changed casing policy/context invalidates affected prior verdicts and triggers back-validation.
- Preserve keys, runtime tokens and argument order, plural and device branches, links and catalog metadata. Check the app and its extensions, selected language against formatting region and currency, live language changes and fallback.
- Capture render evidence with the procedure in [render evidence](references/render-evidence.md), using the app's supported text-size policy and the longest relevant sample values per placeholder and plural branch, VoiceOver labels and order, widgets and shields where in scope, and the RTL constraint noted for `ar` and `he`. Moneyfesting's main app is fixed at `.large`; do not add Dynamic Type testing to this assignment. Gallery captures are approximate, Home Screen captures exact; missing evidence means the visual verdict is `not_checked`, even when language review passed.
- Recommend a human read of the hero set, store text and shield pairs on a locale's first ship, when an adjudicator preference finding stays open, or when the brief was built without a native source (`ro` today); it is a recommendation, never an order, and `done` needs a named source.
- Update existing target entries and review records on repeat runs instead of duplicating them; preserve unrelated work.

Read [research provenance](references/research-provenance.md) when maintaining this skill; `scripts/install.sh` links it into both hosts and `scripts/check_paths.sh --app-root <checkout>` confirms every cited path still exists.

## Report

Always use this template, in this order:

```
### Localization run: <locales> / <surfaces> · mode <prepare|audit|translate> · catalog <commit> · run dir <path>
Keys: changed <n> · unchanged <n> · blocked <n> · needs_review left <n>
Checks: catalog_check pass|fail · term_audit pass|fail · build pass|fail|not_run (<scheme>) · tests <suites> · renders <n> (approximate|exact) | none
Reviews: A <model/effort|unknown> · B blind pass|fail|not_run (tier) · C blind pass|fail|not_run · D final pass|fail|not_run · primitive <Agent|spawn_agent> · human review: recommended|done|not needed
Decisions needed / blockers: ...
```

Expand the human-review field as `recommended (<n> strings, ~<w> words)`, `done by <who, date>` or `not needed because <reason>`. C and D take `not_run` when no separate agent ran them (the protocol's Hosts table), because a stage the coordinator did itself is never a blind pass. List AI-revised shield ids, glossary decisions and flagged source lines under decisions.

For a quote run, replace catalog and key counts with corpus revision and record counts; report per-category coverage, held provenance cases, source-aware fidelity review, display eligibility, resumable manifest path and observed cost/time (or `unknown`). Mark catalog checks `not_applicable`. Separate workflow completion, AI-reviewed quality, human-reviewed quality and release readiness; none implies the others.
