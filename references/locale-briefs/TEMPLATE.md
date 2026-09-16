# Locale brief: <language> (`<tag>`)

Contents: Identity · Audience and register · Address and gender · Control forms · Header and label forms · Short forms and units · Numbers, dates, currency and punctuation · Idioms and figurative language · Money frame · Platform terms · Length trigger · Emoji and intensity · Decided conflicts · Open decisions

Copy this file to `references/locale-briefs/<tag>.md` and fill every section, keeping the headings, their order and the Contents line above, because packets and the role prompts point at them by name. Write rules an agent can apply, each backed by the catalog count or key that proves it; date every snapshot fact. A locale with no shipped copy has no count to cite: back each rule with Apple's own wording from the iOS runtime (bundle | table | key and runtime build, as `Applications/Preferences.app` | `Localizable.strings` | `Screen Time`, iOS 26.1 (23B86)), with Foundation or ICU output (the call and the OS that ran it), or with a fetched local source (URL and fetch date), and name the `en` keys the rule governs. Mark every agent-researched row as a seed ("seed <date>" in the brief, `decided_by: "skill-seed-<date>"` in `glossary/<tag>.json`, as `glossary/ro.json` `restricted_list` does) that the owner may flip before the pilot, and replace its evidence with catalog counts once copy ships. Control forms, Money frame and Platform terms are required before a pilot batch; the other sections may start thin and grow from editor findings.

## Identity

One line each: resource tag, audience, region, script and direction, snapshot date with catalog commit, and the precedence line (app `CLAUDE.md`, then the catalog majority, then archived guides; `glossary/<tag>.json` records the outcomes and baseline rows are owner-accepted agent output, not native evidence).

## Audience and register

Who reads and how the app talks to them (a friendly coach in everyday words, short sentences, no jargon), plus the imported source-language shapes the editor should flag, each as a target-only pattern with a target example line the coordinator can append to the editor prompt, and the live key in a separate column that stays on the coordinator side. Where useful, add a compact table of how comparable local apps that genuinely ship this language word the app's own concepts — checked live through the App Store API (`## Platform terms` below), never assumed from a big rating count or an English-language listing — each row citing its app, id and fetch date.

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

## Money frame

This locale's forms of `references/voice-card.md` `## Money frame`, which keeps the rule, the English, the keys and the test citations. Four tables in this order; evidence cites catalog counts once copy ships and the seed evidence above until then.

- Fixed phrases: Source sentence | this locale's one form | evidence, one row per sentence in the card's order: Not money earned. / Estimated value of time, not money earned. / Time value, not earnings. / It is not a source of income. / Not money lost. The first row mirrors `glossary/<tag>.json` `terms.time_value_disclaimer` exactly (`preferred` is the form, a shipped variant goes under `forbidden`), because `scripts/term_audit.py` reads the glossary, not the brief.
- Banned outcome words: English | target forms | grep stem | evidence, one row each for earn, pays you, make money, cash out, wealth, income, guaranteed. List the forms a local writer reaches for (verb, noun, participle and their inflections), give the shortest stem that catches them, and name what else the stem hits: the fixed phrases, the card's earned freezes and badges, unrelated words sharing the letters. A negated disclaimer in this locale's fixed form is the frame itself, never a banned use.
- Widgets how-to bans: English | target forms | grep stem, one row each for track, monitor, you missed, midnight and "!"; earn and pays you from the table above apply on this screen too. `ManifestingTests/Onboarding/OnboardingWidgetsStepTests.swift:200-215` pins only `en` and `ro` (as `ManifestingTests/Paywall/PaywallCopyTests.swift:80-93` does for the hero's wealth and earn), so for any other locale these rows are the proposal for extending that test: list it in the report, never edit the test.
- Sanctioned value words: English | target forms | evidence for worth, value, price, costs, adds up, estimated, the words to use where the source prices time; no form may match a banned stem.

Routing: the target forms of the two banned tables travel to the blind editor as lines the coordinator appends after the editor prompt (`references/agent-protocol.md` `## Packet separation`), the widgets rows only for a batch holding that screen, each word with the fixed-phrase forms it may appear in negated; target text only. The English column, stems, evidence and the sanctioned table stay coordinator-side with the translator and the adjudicator, who get the brief whole.

## Platform terms

Table English | Apple target term | shipped form and keys | where seen | date | status, one row per term the app mirrors or names (the brand and how the language carries its case without inflecting it, Screen Time and its access alert, Focus, Settings and its Open Settings buttons, Photos, Health, Messages, Home Screen, each label the widgets how-to illustration draws, widget, Face ID, App Store, the notification alert, the Subscriptions sheet, Restore). Where seen reads `iOS <version> (<build>) runtime: <bundle> | <table> | <key>` (escape the pipes inside the table); status is verified when the shipped copy equals Apple's value, mismatch when it differs (with an owner item under Open decisions), harvested while no key names the term. This table is the one home for platform terms; add a `glossary/<tag>.json` row only where `term_audit.py` must police a form. State the verbatim/default/deviation rule and close with the fixed-names line the translator prompt relies on (`references/voice-card.md` `## Brand and fixed names`). Beyond terms the app mirrors verbatim, add a row for each of the app's own concepts (streak, goal, task, timer states, reminder, badge, blocked apps) with Apple's own nearest first-party wording for it, sourced the same way, marking agreement or a mismatch against the glossary the same as any other row; where the mismatch has no glossary term to change, raise it as an Open decision instead of a silent edit. The harvest procedure, including the App Store cross-reference, is in `references/locale-decisions.md` `## Platform terms`.

## Length trigger

The ratio that puts a string on the render list, its source, and the share of the catalog over it at the snapshot; counts never establish fit, because verdicts come from render evidence against each view's own floor (`references/surface-budgets.md`, `references/render-evidence.md`).

## Emoji and intensity

Whether source emoji, interjections and exclamation marks are preserved, whether any may be added, and the tests that ban words or marks on specific screens, pointing at `## Money frame` for the money and widgets-screen words instead of repeating them.

## Decided conflicts

One row per disagreement between sources: the conflict, the winner, the rule that decided it.

## Open decisions

Items only the owner can close, each with an id, the affected keys, the rule that applies, options with the evidence on each side, a recommended option with a one-sentence reason, and what agents do meanwhile (translated keys stay locked; findings go to an audit scope the owner names). Mirror them in `glossary/<tag>.json` `open` with the fields `scripts/term_audit.py` reads: `id`, `options` as countable target forms, `recommended`, `recommended_reason`, `decided_by`, `status`, and a `note` carrying the keys, the rule and the meanwhile.
