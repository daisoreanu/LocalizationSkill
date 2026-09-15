# Locale brief: <language> (`<tag>`)

Copy this file to `references/locale-briefs/<tag>.md` and fill every section, keeping the headings and their order, because packets and the role prompts point at them by name. Write rules an agent can apply, each backed by the catalog count or key that proves it; date every snapshot fact. Control forms and Platform terms are required before a pilot batch; the other sections may start thin and grow from editor findings.

## Identity

One line each: resource tag, audience, region, script and direction, snapshot date with catalog commit, and the precedence line (app `CLAUDE.md`, then the catalog majority, then archived guides; `glossary/<tag>.json` records the outcomes and baseline rows are owner-accepted agent output, not native evidence).

## Audience and register

Who reads and how the app talks to them (a friendly coach in everyday words, short sentences, no jargon), plus the imported source-language shapes the editor should flag, each as a target-only pattern with a target example line the coordinator can append to the editor prompt, and the live key in a separate column that stays on the coordinator side.

## Address and gender

Pronoun and formality, the app's own voice in dialogs and states, the neutral strategies this language offers, the shipped default where no neutral form exists (with the keys it touches), and a grep aid for gendered forms.

## Control forms

One row per control (Cancel, Done, Continue, Save, Edit, Delete, Skip, Allow/Don't allow, Got it, Retry, Settings): preferred form, role exceptions, catalog count; mark system mirrors whose value must equal Apple's label rather than the brief's form. Preferred and role forms mirror `glossary/<tag>.json` `controls` exactly, because `scripts/term_audit.py` reads the glossary, not the brief; a shipped form the glossary lacks goes to Decided conflicts or Open decisions, not into the table as a second truth.

## Header and label forms

Capitalization and grammatical form for nav titles, section headers, eyebrows, tab titles, toggles and state labels, with the agreement rule for fragments that have no visible noun.

## Short forms and units

One form per concept (duration units, day unit, per-period price, compact card units, discount badge) with exceptions named per key; accessibility strings spell units out, and where a pinned test forbids the spelled-out unit, record the conflict under Open decisions instead of overriding the test. Budgets stay in `references/surface-budgets.md`.

## Numbers, dates, currency and punctuation

Separators, ranges, time format, percent and currency placement, quote marks, dashes, ellipsis, the plural categories with the boundary values to exercise, and how the language attaches numerals to nouns.

## Idioms and figurative language

Meaning first: compare propositions, never words. "It's raining cats and dogs" becomes "plouă cu găleata", and a blind back-translation that says "it's pouring" is an acceptable adaptation, not an error. Moneyfesting example: "Close your ring. Build your momentum." ships in ro as "Închide inelul. Prinde avânt." (`onboarding.welcome.slide.ring.headline`); a back-translation "gain momentum" is an acceptable adaptation. When no local idiom carries the same meaning and register, state the meaning plainly rather than translating the image; never add an idiom the source lacks, and keep disclaimers, permissions, billing and shield pairs plain. List here the images this app repeats (streak, showing up, closing the ring, hours have a price, freeze) with the local equivalent or the plain rendering, the round-trip results that count as acceptable adaptations, and whether the language keeps English personification of features ("Streaks that forgive") or needs the user as subject.

## Platform terms

Table English | Apple target term | where seen | date, one row per term the app mirrors or names (the brand and how the language carries its case without inflecting it, Screen Time, Settings, Photos, Health, Home Screen, widget, Face ID, App Store, the Subscriptions sheet). This table is the one home for platform terms; add a `glossary/<tag>.json` row only where `term_audit.py` must police a form. State the verbatim/default/deviation rule and close with the fixed-names line the translator prompt relies on (`references/voice-card.md` `## Brand and fixed names`). The harvest procedure is in `references/locale-decisions.md` `## Platform terms`.

## Length trigger

The ratio that puts a string on the render list, its source, and the share of the catalog over it at the snapshot; counts never establish fit, because verdicts come from render evidence against each view's own floor (`references/surface-budgets.md`, `references/render-evidence.md`).

## Emoji and intensity

Whether source emoji, interjections and exclamation marks are preserved, whether any may be added, and the tests that ban words or marks on specific screens.

## Decided conflicts

One row per disagreement between sources: the conflict, the winner, the rule that decided it.

## Open decisions

Items only the owner can close, each with options, the evidence on each side and what agents do meanwhile; mirror them in `glossary/<tag>.json` `open`.
