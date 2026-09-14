---
name: moneyfesting-localization
description: Translate, transcreate, or review Moneyfesting iOS copy in its screen and flow context. Use for app languages, localized onboarding, focus/Pomodoro, time-value copy, quotes, paywalls, widgets, shields, or store copy. Coordinates independent language review, blind back-translation, and a final senior review. Also supports preparation without translating; does not select profitable markets or redesign the app.
---

# Moneyfesting localization

Make each localized experience feel written for its audience: familiar, relaxed, credible, and clear about the next action. Preserve Moneyfesting's combination of money, aspirations, quotes, tasks, and focus while keeping its actual behavior and claims intact.

## Establish the assignment

Respect the requested mode: prepare context, audit existing copy, or translate and integrate. Preparing this skill or a localization brief does not authorize app translation. A translation request authorizes the necessary scoped resource edits; it does not authorize publishing or changing the product's promises.

Find the current Moneyfesting checkout and read its `AGENTS.md`/`CLAUDE.md`. Start with [project context](references/project-context.md); treat its paths and observations as discovery aids, then verify live call sites. Use an available iOS localization skill for implementation mechanics, while keeping the repository's existing key and lookup conventions.

Resolve source, target locale/variant, surfaces, and desired output from the request. For “languages from the currency list plus Hebrew,” inspect the live currency catalog and use [locale decisions](references/locale-decisions.md). State candidate mappings; do not treat currencies as language identifiers. Ask only about an ambiguity that blocks the current batch, and continue independent work.

## Build context before words

Inventory the requested surfaces, including resources outside `.xcstrings`. Batch by complete screens or short connected flows, with neighboring screens available read-only. Keep one coordinator responsible for shared catalog edits; parallel agents return candidates.

For each string or plural/device variation, capture:

- Stable key and file/call site, English source, screen/state, and preceding/following interaction.
- What the user needs to understand, the CTA's real effect, and facts that cannot change: actor, action, condition, timing, amount/unit, negation, certainty, and outcome.
- Register and intended feeling; whether the copy is functional, explanatory, promotional, an authored affirmation, attributed content, or user content.
- Placeholder identity/type/example values; links, markup, plural branches, and protected names.
- Screenshot or render evidence, control type, width/line behavior, font/Dynamic Type context, and accessibility text. Mark missing evidence explicitly; character counts alone do not establish fit.

Use a compact glossary of concepts with definitions, preferred/forbidden locale terms, register, and provenance. Preserve approved terms; inflect them naturally. Reuse prior translations only when meaning, context, and voice still match. Source, glossary, or behavior changes invalidate affected review records.

## Translate and review

Follow [the agent protocol](references/agent-protocol.md) for each batch. It defines the actual handoffs, source-blind packets, revision loop, and final reviewer settings.

1. A locale-focused translator writes the target flow from the source and context. Use ordinary local UI vocabulary for controls. For prominent creative copy, offer two useful options only when there is a real editorial choice.
2. A fresh agent back-translates the target into English without seeing the source. A separate fresh editor reads the target as a local user and assesses naturalness, credibility, and flow. These reviews can run in parallel.
3. The coordinator compares meaning and resolves findings with the translator. A different English phrasing is not an error by itself. Revise, then repeat affected reviews with uncontaminated reviewers.
4. Integrate within the authorized scope and verify actual screens and resource behavior. A fresh final adjudicator, using the strongest available model and its highest supported reasoning effort, reviews the exact final version and evidence.

Agents are AI language specialists, not native people. Describe their reviews honestly; do not invent human approval, linguistic credentials, or conversion gains. If delegation is unavailable, produce a clearly provisional draft or review and state which independent stages could not run.

## Voice and boundaries

Keep the brand name `Moneyfesting`. Recreate the money/manifestation association through surrounding copy when the pun does not travel; do not force a translated product name. Use warm, direct, locally natural phrasing without slang by default. Preserve the emotional purpose of a screen: reassurance during permissions, encouragement after effort, clarity during purchases, kindness after a broken streak.

Transcreate rhythm and imagery, not facts. Do not turn estimated time value into actual earnings, an affirmation into a financial guarantee, a focus tool into a treatment claim, or permission copy into an unsupported privacy promise. Resolve ambiguous English against behavior before translating it; flag a source defect instead of hiding it in a fluent target.

Follow the live quote policy. Distinguish app-authored affirmations from published quotations, scripture, definitions, and user-written text. Do not rewrite attributed content as marketing copy or translate user content automatically. See [project context](references/project-context.md) for the current provenance and identity constraints.

## Verify and deliver

Keep independent verdicts for semantic fidelity, target-language editorial quality, structural correctness, and rendered UI/accessibility. A high score in one does not offset a failure in another. See [the acceptance rules](references/agent-protocol.md#acceptance-and-evidence).

Preserve source keys, runtime tokens, correct argument reordering, plural/device branches, links, and catalog metadata. Use Xcode/compiler-aware checks for resource validity; do not treat a simple token regex or JSON parse as a complete validator. Check app and consuming extensions, selected language versus formatting region versus currency, live language changes, and fallback behavior. Use current repository build/test instructions when changing app resources or source.

Review affected screens at the smallest supported size and relevant accessibility sizes, with representative long values and real placeholder expansion. Include RTL/mixed-direction text for Arabic/Hebrew, VoiceOver labels/order, widgets and shield constraints where in scope. Missing runtime evidence means UI verification is incomplete, even if the language review passed.

Return a concise summary with locales/surfaces handled, changed files or proposed copy, material choices, actual check results, and remaining blockers. Keep candidate versions, glossary decisions, and review evidence in existing project artifacts or a temporary JSON review packet; do not create project reports or plans unless asked. Update existing target entries and review records on repeat runs instead of duplicating them. Preserve unrelated work and human-approved copy.

Read [research provenance](references/research-provenance.md) when maintaining or evaluating this skill. Use [the evaluation cases](evals/evals.json) to test workflow decisions without translating the app.
