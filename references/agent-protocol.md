# Agent protocol

## Roles and scheduling

The coordinator owns context gathering, semantic comparison, integration, and technical evidence. Assign translator, blind back-translator, target-language editor, and final adjudicator as distinct agents. Multiple locales can proceed concurrently within available slots; dependent reviews wait for their actual input. With limited slots, schedule roles in waves. A completed translator must not be reused as its own independent reviewer.

Use the host's subagent tools, not user-visible new tasks. In Codex, use `collaboration.spawn_agent`; use `send_message`/`followup_task` for translator revisions. For a blind or fresh review, use `fork_turns="none"` and a self-contained prompt. Do not call the full skill in a blind agent: it would reveal English product context. Give only the role prompt below and its sanitized packet.

Before dispatch, record role, locale/market, model and reasoning effort if exposed, and exact source/candidate revision. For the final adjudicator, select the strongest model currently exposed by the host at its maximum supported effort; this skill's workflow requests that override. Do not invent model IDs or settings. If unavailable, report the actual fallback and the missing requested review level.

## Packet separation

Keep the source/context packet and target-only packet separate. Map opaque IDs such as `s01` to repository keys only in the coordinator's records. The target-only packet contains locale, exact target text, token signatures and neutral sample values, neutral control roles, ordering, target-only neighboring copy, and target-language screenshots if available.

Remove English originals, source-bearing keys/filenames, English glossary definitions, intended meaning/action descriptions, translator rationale, prior critiques/verdicts, and source text embedded in images. Do not hide a source string inside a supposedly neutral screen title. Give blind agents only the sanitized packet path; explicitly prohibit reading the repository, other run artifacts, or searching for Moneyfesting's source wording. Target-only access is context isolation, not a claim of filesystem sandboxing or statistical independence between models.

Keep legitimate brands and nontranslatable identifiers that appear in the actual target UI. If a review is contaminated by the source, discard its blindness claim and dispatch a fresh reviewer. Retain rejected candidates outside the blind packet.

Identify intentionally untranslated quotations and user-content blocks separately from translated IDs. Exclude them from blind translation verdicts; omit or redact them in blind evidence if they reveal the tested source. Retain the complete screen for final visual review.

## A. Forward translator

Use this task with the full source/context packet and locale brief:

> Write the specified Moneyfesting screen/flow as a skilled product copywriter for this locale and market. Preserve the stated functional and claim invariants, while using local syntax, idiom, and register. Return a candidate for every supplied ID/variation, brief rationale only for significant adaptations, glossary additions, and unresolved ambiguity. Flag contradictions in the source. Do not edit shared resources. Do not claim to be a native person or to have completed independent review.

Return one selected draft per ID; alternatives for hero lines are proposals, not simultaneous production choices. Keep complete sentences together when grammar needs agreement; flag an engineering constraint if fragmented source strings prevent it.

## B. Blind back-translator

Start fresh with only the target packet:

> Review this target-language UI for locale [locale/market]. Use only the supplied packet; do not read other files or seek the original wording. For every opaque ID, give a faithful English rendering of what is actually written, preserving ambiguity and awkwardness. State any implied benefit, obligation, negation, amount/time relationship, and what a user expects each control to do. Do not repair the target or infer what the author intended. Flag unclear readings and confidence limits. Do not claim human/native status.

Back-translation is diagnostic evidence. Compare propositions, not word overlap or an embedding threshold. A mismatch can be a forward error, a backward error, an acceptable adaptation, or unresolved ambiguity; record which and why.

## C. Target-language editor

Start separately with the same target-only screen/flow packet:

> Assess this UI as an AI language reviewer focused on everyday consumer-app usage in [locale/market]. Read it in order without seeking the English original. Does it sound natural, familiar, relaxed, and credible? Evaluate grammar, register, local conventions, terminology consistency, reading rhythm, emotional tone, CTA expectations, and transitions between screens. Flag literal English phrasing, unsuitable slang, generic motivational filler, confusing money claims, or wording that feels imported. Give exact issue spans, consequence, and a suggested correction. Treat layout fit as unverified unless the provided render supports it. Report no findings when that is the honest result; do not invent a native-human credential.

The editor may propose improvements, but does not silently replace the reviewed draft. For shared Arabic, check Saudi suitability and broader Gulf readability without claiming every Arabic-speaking audience has identical preferences.

## Reconcile and revise

For each finding record ID/variation, candidate version, severity, category, evidence, user impact, proposed fix, disposition, and reviewer role. Keep stylistic preferences distinct from errors. The coordinator compares source intent, observed behavior, back-translation, and editor findings; the translator revises with that feedback. Resolve locale terminology choices across all occurrences of the same concept.

Use at most two material revision rounds by default across the entire batch, including changes requested by the final adjudicator. If the budget is exhausted with a material finding unresolved, hold the affected scope as incomplete and continue unaffected work. Seek a user decision only for missing product intent or a true brand/content-policy choice. Do not require routine approval for ordinary grammar fixes.

Changing the target invalidates its backward/editorial verdicts. Recheck the changed strings plus affected neighboring flow; use fresh blind agents, since the old agents may now know the source. A global term change reopens every affected occurrence. A layout-only change requires new visual evidence; a source/behavior change requires a new meaning comparison.

## D. Final adjudicator

Dispatch a fresh highest-capability reviewer after revisions and technical/visual checks, with all evidence:

> Independently decide whether this exact candidate version is ready for the requested scope. Review the source and its actual UI behavior, target flow, blind back-translation, editorial findings and resolutions, glossary, placeholders/plurals, and rendered screen evidence. Challenge misleading time/money claims, changed actions or purchase conditions, mistranslation, unnatural marketing copy, register drift, quote provenance, RTL/accessibility issues, and stale review evidence. Classify round-trip discrepancies instead of demanding identical English. Give concrete findings and a verdict for each quality dimension and affected screen/locale. Distinguish checked evidence from unavailable evidence. Do not count earlier approvals as proof and do not introduce unreviewed final copy.

Within that same revision budget, send material copy changes through the affected earlier stages and obtain a final verdict on the resulting version. Do not reset the budget after a final-review rejection. The coordinator is not a substitute for this independent pass.

## Acceptance and evidence

| Dimension | Pass evidence | Blocking examples |
|---|---|---|
| Meaning and behavior | Source/behavior compared to target and blind rendering; discrepancies resolved | Earnings confused with time value; wrong negation, unit, amount, CTA, entitlement, billing period, permission or condition |
| Locale and editorial quality | Separate target-only flow review; concrete findings resolved | Unnatural literal syntax, mixed regional variants/register, mistranslated core concept, offensive or misleading adaptation |
| Structure and runtime | Relevant catalog/compiler/tests and all consuming targets checked | Lost/type-changed placeholder, wrong argument binding, missing reachable plural, broken markup, wrong bundle/fallback, stale language cache |
| Visual and accessibility | Exact candidate rendered on relevant screens/sizes; RTL and VoiceOver checked where applicable | Clipping, unreadable abbreviation, misleading truncation, scrambled number/currency order, unusable reading order |

Use `pass`, `fail`, or `not_checked` per dimension; `not_applicable` needs a scope reason. Do not average failures away. Any unresolved material finding prevents claiming that screen/locale is ready; unchanged languages may still be complete. A preparation-only run can complete its requested brief without passing app-runtime checks, but must not label the locale ready to ship.

Record the candidate revision/hash, covered IDs/variations, role identities and actual settings, substantive findings/resolutions, commands/results, and screenshot paths with device/locale/state. For imported review evidence, role labels alone do not establish human/AI identity, native fluency, model settings or isolation; leave those facts unknown when unsupported. Keep language review, runtime verification, and real human review as separate facts. “AI localization reviewed” describes agent work; conversion lift and native-user comprehension require separate evidence.
