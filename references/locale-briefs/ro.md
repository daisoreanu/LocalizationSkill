# Locale brief: Romanian (`ro`)

Contents: Identity · Audience and register · Address and gender · Control forms · Header and label forms · Short forms and units · Numbers, dates, currency and punctuation · Idioms and figurative language · Platform terms · Length trigger · Emoji and intensity · Decided conflicts · Open decisions

Counts and keys below are snapshot 2026-09-15 of `Manifesting/Foundation/Localization/Localizable.xcstrings` (catalog commit c8a49dd); re-run `scripts/term_audit.py` before quoting them in a report.

## Identity

- Tag `ro`; the only target the app ships besides `en` (`AppLanguage.supportedLanguageCodes`, `Manifesting/Foundation/Localization/AppLanguage.swift:6`); no regional variant is selectable in-app.
- Audience: Romanian speakers in Romania and the diaspora using an iPhone in Romanian; Latin script, left to right, comma-below ș ț.
- Snapshot: 1135 ro units compared with their source, 35 plural keys, 9 units `needs_review` (all `widgets.focusRing.*`).
- Precedence: app `CLAUDE.md` (line 43: informal tu, comma-below ș/ț, preserve translator context), then the catalog majority, then `Docs/Archive/I18N_PLAN.md` section 7 and the `Docs/Archive/I18N_PROMPT.md` Romanian guide (archived; their Lokalise steps are obsolete). `glossary/ro.json` records the outcomes. Baseline rows are owner-accepted agent output, not native evidence: an editor finding against a `translated` row is legitimate, but the row changes only inside an audit scope the owner names.
- Tone examples: `references/examples-ro.md`; budgets: `references/surface-budgets.md`.

## Audience and register

- Friendly coach, everyday spoken Romanian, short sentences; a reader who knows no English understands each line at first read. Plain beats clever: "Lucru intens" for "Deep work" (`onboarding.welcome.preview.blocking.task`, `.planner.work`; the same-source `widgets.startFocus.sampleTask` "Lucru concentrat" is the C10 divergence to align on it in a named audit scope, and `focusTask.templates.deepWorkSession.name` "Sesiune de lucru profund" for "Deep work session" is the near-source neighbour to align in the same scope), "Statistici" for the Insights tab.
- Drop English scaffolding: 14 en keys say "Please", 0 ro keys say "te rog" or "te rugăm"; keep it that way.
- Imported shapes the editor flags. The first two columns are the marker list the coordinator appends to the editor prompt, target text only; the key column stays on the coordinator side (`references/agent-protocol.md` `## Packet separation`).

| Shape (marker) | Target example -> local form | Key (coordinator side) |
|---|---|---|
| a possessive on every line where the owner is obvious ("tău" 38 keys, "ta" 21, "tale" 20; Romanian drops it) | "E pe ecranul tău principal." -> "E pe ecranul principal." | `onboarding.widgets.howTo.placedConfirmation` |
| noun stacks and source word order where a local team would use a verb | "Acces la Poze necesar" -> "Ai nevoie de acces la Poze" | `share.alert.photoAccessDeniedTitle` |
| verb-for-verb rendering of a source phrase | "vezi cum se adună concentrarea" -> "vezi cum se strâng orele de concentrare" | `paywall.benefit.value.detail` |
| a doubled idea where one word carries it | "Estimare viitoare" -> one word that stays distinct from the month-end label read right after it ("Prognoză" beside "Estimare la final de lună"; open decision `forecast` in `glossary/ro.json`) | `insights.savings.forecast` (en "Forecast"), `insights.savings.monthEnd` |
| Title Case on app-owned copy, straight quotes, clipped fragments where Romanian needs a verb | none shipped today (0 straight quotes; the capitalized multi-word strings are proper names, Header and label forms) | grep aid, not a validator: a straight `"` or two adjacent capitalized words |

- Off-voice source lines are flagged, not repaired in ro (`references/project-context.md`).

## Address and gender

- `tu` throughout; no "dumneavoastră", no "Vă rugăm" (0 keys). The user's actions are second-person singular imperatives.
- The app speaks in first person plural in dialogs and states: 19 keys open with "Nu am putut" ("Nu am putut salva starea.", `insights.mood.saveError`), "Arătăm suma?" (`share.alert.moneyDisclosureTitle`), "Am acoperit ziua de %@" (`streakFreeze.usedBody`), "vom folosi %@" (`onboarding.hourlyWage.footer`), "Reîncercăm în curând" (`widgets.focusRing.a11y.unavailable`).
- UI copy is gender-neutral. Strategies the baseline already uses: imperatives ("Concentrează-te două zile la rând.", `achievements.badge.dayTwo.criterion`); the compound past, whose participle never inflects ("te-ai întors", `achievements.badge.rehired.earned`; "Te-ai concentrat %lld zile din 7", `achievements.streak.weekAccessibility`; "Bine ai revenit"); nominal achievement sentences ("Șapte zile la rând.", "O oră întreagă, fără pauze."); agreement with the object rather than the user ("%lld selectate" agrees with "teme", `themePicker.manageThemes.selectedCount`). Avoid predicate adjectives and role nouns aimed at the user.
- Shipped masculine forms, owner-accepted and changed only in a named audit scope: "Ai fost prezent" in all three plural forms of `achievements.streak.body` and in `achievements.badge.fullDaysFifty.earned`; badge role nouns `achievements.badge.hired.name` "Angajat", `achievements.badge.salaried.name` "Salariat", `achievements.badge.rehired.name` "Reangajat"; `user.gender.other` "Altul". Grep aid, not a validator: `prezent | angajat | salariat | Altul`.
- The stored profile gender (`Manifesting/Features/User/Domain/Entities/Gender.swift`) is not a copy input without a product decision.

## Control forms

Counts are catalog keys whose en value is exactly the control word, the same match `scripts/term_audit.py` makes. Preferred and role forms mirror `glossary/ro.json` `controls` (role names as the glossary spells them), because the script reads the glossary, not this table; a shipped form outside that match is recorded under Decided conflicts, never added here as a second truth.

| Control | Preferred | Roles and where they apply | Count |
|---|---|---|---|
| Cancel | Anulează | discard, quit, dismiss: Renunță (`common.editor.discard` "Renunță la modificări", `moneyfesting.details.stopConfirmationQuitButton`, `quotes.user.discard`, `share.screenshot.dismiss`) | 3 of 3 |
| Done | Gata | completed_count_header: Încheiate (`onboarding.welcome.preview.planner.done`); ios_mirror_pill: OK (`onboarding.widgets.howTo.doneLabel`); the uppercase section header `plan.dailyPlan.doneHeader` "FINALIZATE" (en "DONE") shows as `term_audit.py` drift and is a header form, not a control (Header and label forms) | 3 of 6, the other three are the named forms |
| Continue | Continuă | resume: Continuă (`moneyfesting.details.resumeButton`) | 4 of 4 |
| Save | Salvează, persist-data only (`common.save`; "Save Changes" -> "Salvează modificările", 2 keys) | save_money: Economisești, second person because the badge states what the reader gets ("Economisești 56%", `paywall.onboardingSubscription.annualPlanBadge`) | 1 of 1 |
| Edit | Editează | ios_mirror_pill: Editați (`onboarding.widgets.howTo.editPillLabel`) | 2 of 3 |
| Delete | Șterge | no glossary role; confirmation questions conjugate ("Ștergi acest citat?", `quotes.user.deleteTitle`) and compounds keep Șterge ("Șterge tot", `plan.dailyPlan.deleteAll`) | 1 of 1 |
| Skip | Sari peste | skip_for_now: Sari peste deocamdată (`onboarding.name.skip`, the only Skip key) | 1 |
| Allow / Don't allow | Permite / Nu permite | mock alerts only (`onboarding.notificationPermission.alertAllow`, `.alertDoNotAllow`, `onboarding.screenTimePermission.alertDoNotAllow`) | 1 / 2 |
| Got it | Am înțeles | | 2 of 2 |
| Retry | Reîncearcă (`common.retry`) | in_sentence: Încearcă din nou, also the form for "Try Again" (4 keys) and inside quotes ("Apasă „Încearcă din nou”", `component.errorView.message`) | 1 / 4 |
| Settings | Setări (the noun; no key carries the bare label) | open_button: Deschide Setările for "Open Settings" and "Go to Settings" (`insights.appUsage.openSettings`, `share.alert.openSettings`, `onboarding.alert.goToSettings`, `theme.picker.goToSettingsButton`); setup_noun: configurare ("Finalizează configurarea mementourilor.", `onboarding.notificationPermission.title`) | 0 bare / 4 open_button |

- Other shipped forms: Close -> Închide (4), OK -> OK (3), Not now -> Nu acum, Stop -> Oprește, Pause -> Pauză, Start Moneyfesting -> Pornește Moneyfesting (5), Get started -> Începe, Start Free Trial -> Începe proba, Learn more -> Află mai multe, Enable notifications -> Activează notificările, Restore -> Restaurează (unverified against the Subscriptions sheet).
- Apple mirrors in `onboarding.widgets.howTo.*` use Apple's polite plural because iOS Romanian does (Editați, Adăugați un widget, Personalizați, Eliminați widgetul, Solicitați Face ID, Partajați aplicația, Căutați widgeturi, OK for Done); they resolve against the device language at runtime (comment on `editPillLabel`), so the value must equal Apple's label, not the brief's form. The steps around them stay `tu` ("Atinge Editați în colțul de sus, apoi Adăugați un widget.", `step2`).

## Header and label forms

- Sentence case for app-owned copy; the only capitalized multi-word ro strings are proper names (Setările, Moneyfesting; 11 keys). Screen titles are sentence case even where en uses Title Case ("Set Your Hourly Wage" -> "Setează-ți tariful orar", `onboarding.hourlyWage.title`).
- Eyebrows and stat captions are uppercase in the string when en is (15 keys), diacritics kept: MOOD -> STARE DE SPIRIT, DAY STREAK -> ZILE ÎN SERIE, "%@ / HOUR" -> "%@ / ORĂ"; these expand hardest (Length trigger).
- Section headers are plural participles or nouns agreeing with the listed items (PLANIFICATE, FINALIZATE, ORICÂND in `plan.dailyPlan.*Header`; "Încheiate azi", `onboarding.welcome.preview.ring.completed`).
- Tab titles are nouns: Moneyfesting, Plan, Statistici, Profil (`main.tab.*`).
- Toggles and states take a participle agreeing with the labelled noun ("Aplicațiile alese sunt blocate"; "%lld aplicație restricționată" / "%lld aplicații restricționate", `screenTime.restrictedApps.appsRestricted`; "Focus în pauză"; "Concentrare în desfășurare"). A fragment with no visible noun agrees with the noun the screen implies: `widgets.streak.copy.frozen.small` "Acoperit cu îngheț." beside `widgets.streak.copy.frozen.medium` "Ieri a fost acoperită." is the agreement fault the editor checks against the packet's `agreement_target`.
- Status pills that describe the action, not the user, default to masculine singular ("Salvat", `common.editor.saved`).

## Short forms and units

One form per concept; exceptions are named per key.

| Concept | Form | Keys |
|---|---|---|
| minutes in running text and labels | `%lld min`, with a space | `share.duration.minutesOnly`, `component.templateTaskCard.duration`, `achievements.gauge.sessionMinutes`; the unit label is "min" where en shows "m" (`common.durationMinuteUnit`, `insights.sessions.durationMinuteUnit`) |
| minutes on compact widget lines | `%lldmin`, no space | `widgets.streak.focusedInStreak`, `widgets.streak.focusedMinutesSummary`, `screenTimeReport.durationMinutesOnly` |
| hours | `%lldh` | `share.duration.hoursShort`, `paywall.beforeAfter.hoursPerDayFormat` "%lldh pe zi" |
| seconds | `%llds` | `screenTimeReport.durationSecondsOnly` |
| share-card compact triple | `%lldz` / `%lldh` / `%lldm` | `share.duration.daysShort` / `hoursShort` / `minutesShort` only; the single letters mirror en "%lldd/%lldh/%lldm" on the image and are the sole uses of "z" and "m" |
| per-period price | `%@ /lună`, `%@ /săpt.` on the ladder; `%@ / lună` on the plan option | `paywall.price.perMonth` / `perWeek` mirror en "/mo", "/wk"; `paywall.onboardingSubscription.pricePerMonth` mirrors en "%@ / mo"; keep each key's spacing |
| hourly rate unit | `%@ / ORĂ` | `onboarding.hourlyWage.unit`, `profile.hourlyWage.unit` |
| discount badge | `-%lld%%` | `paywall.discountBadge`, `paywall.plan.annual.savingBadge` |

VoiceOver and share-card accessibility strings spell units out ("%lld de minute", "%lld de ore", "%lld de zile de lucru", `share.duration.*Spelled`); "min" and "min." inside `widgets.focusRing.a11y.firstRun`, `goalMet` and `progress` are the live violation, all `needs_review`, pinned that way by `ManifestingTests/Widgets/FocusRingCopyTests.swift:116` because a single `%lld` cannot take the partitive "de" ("%lld minute" is wrong from 20 up, "%lld de minute" below it); spelling the unit out needs ro plural variations on those keys plus that assertion changed, an owner decision to propose in the report, never a silent fix (Open decisions).

## Numbers, dates, currency and punctuation

- Runtime values arrive formatted through `AppLanguage.effectiveLocale` (app `CLAUDE.md:42`), so strings never hard-code decimals or currency (0 keys contain "lei" or "RON"; the placeholder carries the amount). A literal number in copy uses the point for thousands ("2.000 de ore", `achievements.badge.wageYear.*`).
- Time is 24-hour ("18:00", `insights.appUsage.axisSixPm`); ranges take an en dash without spaces ("1–3 ore", "18–24", "1–280 de caractere"); percent is glued ("56%", "100%", "-%lld%%"); multiplication uses × ("Orele de concentrare × tariful tău orar", `achievements.category.wages.description`).
- Quotes are „ ” (18 keys, 0 straight; `moneyfesting.details.quoteWrapper` "„%@”"), also around UI labels quoted in a sentence ("Apasă „Încearcă din nou”", `component.errorView.message`). Asides take a spaced em dash (9 keys); quote attribution is "– %@" (`quote.display.attribution`). Ellipsis: three periods (Decided conflicts).
- "de" links a numeral of 20 or more to its noun ("20 de zile", "60 de minute", "160 de ore"), never 2–19 ("7 zile", "15 minute").
- Plural categories one / few / other (35 keys): `few` never takes "de", `other` always does. CLDR puts 0, 2–19 and every number whose last two digits are 01–19 (except 1 itself) in `few`, so 101 reads "101 zile" while 100 and 120 take "de"; exercise 1, 2, 19, 20, 100, 101, 120. Running text spells the `one` value ("o zi", "o dată", "o temă": `achievements.streak.milestoneBody`, `profile.reminders.frequencyValue`, `themePicker.deleteThemes.title`); numeric labels keep "%lld zi" (`widgets.streak.daysCount`, `share.card.streakSupporting`). `achievements.streak.headline` mixes the two ("Serie de %lld zi"), an audit candidate. Occurrences: "o dată / de %lld ori / de %lld de ori".

## Idioms and figurative language

- Compare propositions, never words: "It's raining cats and dogs" is "plouă cu găleata", and a blind back-translation "it's pouring" is an acceptable adaptation.
- Baseline equivalents to reuse, the app's own recurring images first: "Close your ring." -> "Închide inelul." and "Build your momentum." -> "Prinde avânt." (`onboarding.welcome.slide.ring.headline`; "gain momentum" is an acceptable adaptation); "Your hours / have a price." -> "Orele tale / au un preț." (`paywall.onboardingSubscription.heroLineOne/Two`, plain on both sides, keep it plain); "streak freeze" -> "îngheț de serie" (`streakFreeze.usedBody`; `glossary/ro.json` `streak_freeze`); "You showed up %lld days in a row." -> "Ai fost prezent %lld zile la rând." (`achievements.streak.body`, locked and gendered; see Open decisions); "Seven days, no gaps." -> "Șapte zile la rând." (`achievements.badge.hired.earned`; back-translation "seven days in a row" is an acceptable adaptation); "come back strong" -> "revino în forță" (`moneyfesting.details.stopConfirmationMessage`); "Make it yours" -> "Așază-l cum îți place" (`onboarding.widgets.howTo.placeTitle`); "That's the habit." -> "Ăsta e obiceiul." (`achievements.streak.body`).
- No Romanian idiom carries "showing up": state the meaning plainly and neutrally ("un sezon întreg în care n-ai lipsit") instead of the image; the shipped "în care ai fost prezent" (`achievements.badge.fullDaysFifty.earned`) is the gendered literal.
- Never add an idiom the source lacks: disclaimers ("Nu sunt bani câștigați."), permissions, billing and the shield pairs stay plain. The Romanian in `Manifesting/Foundation/ShieldSupport/ShieldMessageCatalog.swift` sets the register ("Puțin spațiu pentru tine.", "Nu e grabă să deschizi asta."): short, calm, no exclamation.
- English feature copy personifies the product ("Streaks that forgive.", shipped as "Serii care iartă.", `paywall.benefit.streak.title`); Romanian UI copy reads naturally with the user as subject or a plain statement of what happens ("Poți rata o zi fără să-ți pierzi seria."), short where the line renders inline before its detail, and never stronger than the detail's condition (one earned freeze covers one day).
- On style the editor wins; on claims, amounts, negation, conditions and the action a control performs, the back-translation wins.

## Platform terms

This table is the one home for platform terms; `glossary/ro.json` polices only `screen_time`, whose forbidden form is the English name. The harvest procedure is `references/locale-decisions.md` `## Platform terms`. Status: seeded from the catalog and I18N_PLAN section 7; verify each row on the project simulator with the device language set to ro and fill "where seen | date".

| English | Romanian | Where seen | Status |
|---|---|---|---|
| Moneyfesting (brand) | unchanged in every position and script; Romanian carries the case on the noun before it ("Permite aplicației Moneyfesting…", `insights.mood.permissionMessage`; "Din aplicația Moneyfesting:", `share.text.fromTheApp`), quotes only where the source mirrors a system alert (`onboarding.alert.screenTimeMessage`); never "Moneyfesting-ul", "Moneyfestingului" or a translated pun | 36 ro occurrences, 1 quoted | verified |
| Screen Time | Timp de utilizare | 15 keys; `onboarding.screenTimePermission.alertTitle` mirrors the access alert ("„%@” dorește să acceseze Timp de utilizare") | seeded |
| Settings (app) | Setări; button "Deschide Setările" | 4 button keys, `insights.appUsage.permissionSettingsHint` | seeded |
| Photos (app) | Poze | `share.alert.savedToPhotosTitle` "Salvat în Poze"; `onboarding.alert.photoAccessDeniedMessage` says "galeria foto" for en "photo gallery", a generic noun, not the app name | seeded |
| Health (app) | aplicația Sănătate | 7 keys; `Manifesting/Foundation/Localization/InfoPlist.xcstrings` `NSHealthUpdateUsageDescription` | seeded |
| Messages | Mesaje | `share.destination.messages` | seeded |
| Home Screen | ecranul principal | 4 keys | seeded |
| Edit / Add Widget / Done / Customise / Remove Widget / Require Face ID | Editați / Adăugați un widget / OK / Personalizați / Eliminați widgetul / Solicitați Face ID | `onboarding.widgets.howTo.*`, resolved against the device language at runtime | seeded |
| widget, Face ID, App Store | unchanged; plural "widgeturi" without hyphen (5 keys) | `onboarding.widgets.howTo.editTitle`, `paywall.onboardingSubscription.legalText` | seeded |
| notification permission alert | „%@” dorește să-ți trimită notificări | `onboarding.notificationPermission.alertTitle` | seeded |
| Restore Purchases (Subscriptions) | Restaurează achizițiile (the bare verb reads as restoring a file, so the object stays) | `paywall.button.restore` | verb unverified until the Subscriptions sheet is read |
| Focus (system mode) | to harvest | if iOS ro calls it "Concentrare", the collision weighs on the open focus term | pending |

Verbatim for the mock alerts and the howTo mirrors; default for matching controls; deviate only with a recorded reason.

Fixed names for the translator prompt: the brand row above, the Apple terms in this table, quote authors and the restricted-apps group literal (`references/voice-card.md` `## Brand and fixed names`).

## Length trigger

- A ro string longer than 1.35× its en length gets a layout check (I18N_PLAN section 7); `scripts/catalog_check.py` C5 puts it on the render list, not among findings. At the snapshot 299 of 1135 ro units exceed it (ro length ÷ en length, plural `other` form), mostly one-word controls and uppercase captions: Ok -> Acceptabil 5.0×, MOOD -> STARE DE SPIRIT 3.75×, App -> Aplicație 3×, DONE -> FINALIZATE 2.5×.
- Counts never establish fit; verdicts come from render evidence against each view's own floor (`references/surface-budgets.md`, `references/render-evidence.md`). Shortening cuts words, never facts; accessibility strings are exempt.

## Emoji and intensity

- Preserve every source emoji and interjection, add none (I18N_PLAN section 7): all emoji keys keep theirs (`onboarding.notificationsSetup.motivationOn` "activat 💪🏼", `motivationOff` "dezactivat 😞", `screenTime.createRestrictedList.selectionInstructions` "⚠️ Trebuie să alegi…").
- Exclamation only where the source has it: 3 en keys, 3 ro keys, 0 mismatches (`plan.dailyPlan.futureEmptyMessage`, `plan.dailyPlan.timelinePotentialSuffix`, `streakFreeze.info.body`); flag the source line, do not add marks.
- Tests that ban intensity: `ManifestingTests/Onboarding/OnboardingWidgetsStepTests.swift:203-204` bans "!" and ro urmăre/monitoriz/ai ratat/câștig/miezul nopții on the widgets step; `ManifestingTests/Paywall/PaywallCopyTests.swift:89` bans wealth/earn/avere/câștig in the paywall hero ("Economisești 56%" sits outside both). Persuasion limits: `references/voice-card.md`.

## Decided conflicts

| Conflict | Winner | Rule |
|---|---|---|
| Cancel: archived guide "Renunță" vs catalog "Anulează" | Anulează for Cancel; Renunță for discard and quit roles | catalog majority (3 of 3) beats the archived guide |
| streak: "serie" vs "streak" (the guide left it to review) | serie (the serie family in 46 keys, 0 "streak") | catalog majority; `glossary/ro.json` forbids "streak" |
| disclaimer: "Nu sunt bani câștigați." (10 keys) vs "Nu reprezintă bani câștigați." (`widgets.monthlyTimeValue.description`) | "Nu sunt bani câștigați." | disclaimers take one approved form; the outlier is an audit candidate, not a silent edit |
| ellipsis: "..." (10 keys) vs "…" (`common.editor.saving`, `onboarding.personalGoal.placeholder`) | three periods | catalog majority; reopen only with an owner call |
| emoji and interjections | preserved | guide and catalog agree |
| Save: Salvează vs Economisește / Economisești | by role: persist data vs money; the money form is the shipped second person "Economisești 56%" (`paywall.onboardingSubscription.annualPlanBadge`, a statement about the reader, not a command) | guide and catalog agree on the split; the form is the catalog's Economisești over the guide's Economisește, recorded in `glossary/ro.json` `controls.Save.roles.save_money` |
| minutes short form "m" | share-card compact unit only; "min" everywhere else | catalog mirrors en per key |
| Insights tab | Statistici | catalog; en "Insights" has no plain one-word ro equivalent |

## Open decisions

- Focus term: "sesiune de focus" (archived guide; `profile.sessionDetails.analyticsTitle`, `widgets.streak.extendStreakHint`) vs "sesiune de concentrare" (`onboarding.welcome.preview.blocking.title`, `widgets.focusRing.a11y.firstRun`); "concentrare" and its verb appear in 71 keys (the noun alone in 56), "focus" in 29 ("sarcină de focus", "Focus total", "ore de focus"). `decided_by: user`, `status: open`, mirrored in `glossary/ro.json` `open`. Until decided, a new string follows its own screen's majority and the packet's same-source siblings, and the adjudicator lists every key that touched the term. Recommended: "sesiune de concentrare", plain Romanian a reader without English understands and the catalog majority, unless the Focus system-mode harvest shows a collision.
- Forecast label (`insights.savings.forecast`, "Estimare viitoare") versus the month-end figure (`insights.savings.monthEnd`, "Estimare la sfârșitul lunii"): VoiceOver reads them one after the other, so they need two different words. Recommended: "Prognoză" for the forecast line and "Estimare la final de lună" for the figure; `decided_by: user`, mirrored in `glossary/ro.json` `open`.
- Gendered rows in `translated` state (`achievements.streak.body`, `achievements.badge.fullDaysFifty.earned`, the badge names Angajat / Salariat / Reangajat, `user.gender.other` "Altul"): neutral rewrites exist ("n-ai lipsit"; "Alt gen"), but the badge metaphor is a product choice, so they wait for an owner-named audit scope.
- Apple's ro label for the Focus system mode: harvest pending; if it is "Concentrare", record the collision under the focus term.
- Focus ring VoiceOver units (`widgets.focusRing.a11y.firstRun`, `goalMet`, `progress`, all `needs_review`): the bare "min" stays while `ManifestingTests/Widgets/FocusRingCopyTests.swift:116` forbids " minute" and " de minute" in those labels; spelling the unit out means ro plural variations (few "minute", other "de minute") on the three keys plus a changed assertion. Propose it in the report with both costs; meanwhile agents leave the figure bare, never edit the test, and still fix word order and verbs that do not depend on the unit.
